"""
payload_validator.py — Validates the final ACF payload and generates a report.
"""


def validate_payload(payload, page_type, mapping_result, field_schema):
    """
    Validate the final payload and generate a quality report.

    Returns dict:
        mapped: fields mapped deterministically (confidence >= 90)
        ai_mapped: fields mapped via Groq (confidence 70-89)
        thin: wysiwyg fields with < 50 words
        missing: required fields not found
        unmapped_headings: headings that matched nothing
        score: 0-100 quality score
    """
    required = field_schema.get("required_fields", {})
    mappings = mapping_result.get("mappings", [])
    unmapped = mapping_result.get("unmapped_headings", [])

    mapped = []
    ai_mapped = []
    thin = []
    failed = []
    missing = []

    # Build lookup: acf_field -> mapping info
    field_info = {}
    for m in mappings:
        f = m.get("acf_field")
        if f and f != "__skip__":
            field_info[f] = m

    for field_key, field_def in required.items():
        value = payload.get(field_key)
        ftype = field_def.get("type", "text")

        if value is None or value == "" or value == []:
            missing.append(field_key)
            continue

        info = field_info.get(field_key, {})
        conf = info.get("confidence", 0)
        method = info.get("method", "unknown")

        if method == "failed":
            failed.append(field_key)
        elif method == "thin":
            thin.append(field_key)
        else:
            is_thin_wysiwyg = False
            if ftype == "wysiwyg" and isinstance(value, str):
                word_count = len(value.split())
                if word_count < 50:
                    is_thin_wysiwyg = True

            if is_thin_wysiwyg:
                thin.append(field_key)
            elif method in ("exact", "fuzzy") and conf >= 90:
                mapped.append(field_key)
            elif method in ("fuzzy", "ai", "ai_mapped") or (70 <= conf < 90):
                ai_mapped.append(field_key)
            else:
                mapped.append(field_key)

    total_attempted = len(mapped) + len(ai_mapped) + len(thin) + len(failed) + len(missing)

    if total_attempted == 0:
        score = 0
    else:
        score = round((
            (len(mapped) + len(ai_mapped)) * 100 +
            len(thin) * 60 +
            len(failed) * 20 +
            len(missing) * 0
        ) / total_attempted)

    return {
        "mapped": mapped,
        "ai_mapped": ai_mapped,
        "thin": thin,
        "missing": missing,
        "failed": failed,
        "unmapped_headings": [u["heading"] for u in unmapped],
        "score": min(score, 100),
    }
