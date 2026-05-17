"""
heading_mapper.py — Heading-to-ACF field mapping with fuzzy matching.
Uses keyword lookup tables + rapidfuzz for fuzzy heading matching.
"""

import re
from rapidfuzz import fuzz

STRIP_WORDS = [
    "amity university online", "amity university", "amity online",
    "amity", "nmims", "narsee monjee", "of the", "of amity", "of amity online",
    "of amity university", "the", "online"
]

def normalize_heading(heading: str) -> str:
    h = heading.lower().strip()
    # Strip known university/brand words first (longest first to avoid partial replacements)
    for word in sorted(STRIP_WORDS, key=len, reverse=True):
        h = h.replace(word, " ")
    # Remove leftover special characters
    h = re.sub(r"[^a-z0-9\s/&]", "", h)
    # Collapse multiple spaces
    h = re.sub(r"\s+", " ", h).strip()
    return h

# ─── Heading Maps ───────────────────────────────────────────────────────


UNIVERSITY_MAP = {
    "short description": "meta_description",
    "meta description": "meta_description",
    "about": "about_content",
    "about the university": "about_content",
    "about amity online": "about_content",
    "about amity university online": "about_content",
    "facts": "highlights",
    "university facts": "highlights",
    "online facts": "highlights",
    "amity university online facts": "highlights",
    "amity online facts": "highlights",
    "detail": "quick_facts",
    "online detail": "quick_facts",
    "university detail": "quick_facts",
    "amity online detail": "quick_facts",
    "amity university online detail": "quick_facts",
    "pros": "why_choose_content",
    "why choose": "why_choose_content",
    "advantages": "why_choose_content",
    "pros of the amity university online": "why_choose_content",
    "pros of the amity university online:": "why_choose_content",
    "pros of amity online": "why_choose_content",
    "accreditations": "accreditations",
    "approvals": "accreditations",
    "recognitions": "accreditations",
    "accreditations of amity online": "accreditations",
    "admission process": "admission_steps",
    "how to apply": "admission_steps",
    "amity university online admission process": "admission_steps",
    "emi details": "emi_content",
    "emi": "emi_content",
    "financial aid": "emi_content",
    "emi details of amity online": "emi_content",
    "examination process": "exam_content",
    "examination pattern": "exam_content",
    "examination process of amity online": "exam_content",
    "courses": "programs",
    "programs offered": "programs",
    "courses offered": "programs",
    "fee structure": "programs",
    "amity university online courses": "programs",
    "faculty members": "faculty",
    "faculty": "faculty",
    "faculty members of amity online": "faculty",
    "placement partners": "placement_content",
    "placement": "placement_content",
    "career": "placement_content",
    "placement partners of amity online": "placement_content",
    "hiring partners": "hiring_partners",
    "top recruiters": "hiring_partners",
    "recruiters": "hiring_partners",
    "faqs": "faqs",
    "faq": "faqs",
    "frequently asked questions": "faqs",
    "amity online faqs": "faqs",
    "reviews": "reviews",
    "student reviews": "reviews",
    "testimonials": "reviews",
    "amity university online reviews": "reviews",
    "amity online reviews": "reviews",
    "amity online": None,
    "amity university online": None,
    "sample certificate photo": None,
}

COURSE_MAP = {
    "meta description": "meta_description",
    "short description": "meta_description",
    "about the program": "about_content",
    "about the course": "about_content",
    "about": "about_content",
    "course details": "about_content",
    "about amity university online mba course": "about_content",
    "about amity online mba": "about_content",
    "program highlights": "highlights",
    "course highlights": "highlights",
    "course facts": "highlights",
    "highlights": "highlights",
    "accreditations": "accreditations",
    "approvals": "accreditations",
    "eligibility criteria": "eligibility_content",
    "eligibility": "eligibility_content",
    "who can apply": "eligibility_content",
    "admission process": "admission_steps",
    "how to apply": "admission_steps",
    "amity online mba admission process": "admission_steps",
    "amity university online mba admission process": "admission_steps",
    "specializations offered": "specializations",
    "specializations": "specializations",
    "choose your specialization": "specializations",
    "specialization wise fees": "fee_plans",
    "specialization fee": "fee_plans",
    "fee structure": "fee_plans",
    "fees": "fee_plans",
    "amity university online mba fee": "fee_plans",
    "emi details": "emi_content",
    "emi": "emi_content",
    "syllabus": "syllabus_content",
    "curriculum": "syllabus_content",
    "syllabus/curriculum": "syllabus_content",
    "exam pattern": "exam_content",
    "examination pattern": "exam_content",
    "placement partners": "placement_content",
    "placement": "placement_content",
    "career": "placement_content",
    "hiring partners": "hiring_partners",
    "top recruiters": "hiring_partners",
    "job roles": "job_profiles",
    "job roles & salary": "job_profiles",
    "job prospects": "job_profiles",
    "career opportunities": "job_profiles",
    "faqs": "faqs",
    "faq": "faqs",
    "reviews": "reviews",
    "student reviews": "reviews",
    "university reviews": "reviews",
    "amity university online reviews": "reviews",
    "amity online mba reviews": "reviews",
    "amity online mba": None,
    "additional information": None,
    "additional information:": None,
    "course": None,
    "sample certificate photo": None,
}

SPECIALIZATION_MAP = {
    "course details": "about_content",
    "about the specialization": "about_content",
    "about the program": "about_content",
    "about": "about_content",
    "amity online mba in data science": None,
    "course facts": "highlights",
    "program highlights": "highlights",
    "specialization highlights": "highlights",
    "highlights": "highlights",
    "eligibility criteria": "eligibility_content",
    "eligibility": "eligibility_content",
    "who can apply": "eligibility_content",
    "specialization fee": "fee_plans",
    "fee structure": "fee_plans",
    "fees": "fee_plans",
    "emi details": "emi_content",
    "emi": "emi_content",
    "admission process": "admission_steps",
    "how to apply": "admission_steps",
    "amity online mba admission process": "admission_steps",
    "syllabus": "syllabus_content",
    "curriculum": "syllabus_content",
    "examination pattern": "exam_content",
    "exam pattern": "exam_content",
    "placement": "placement_content",
    "placements": "placement_content",
    "career outcomes": "placement_content",
    "hiring partners": "hiring_partners",
    "recruiters": "hiring_partners",
    "job roles": "job_profiles",
    "job roles & salary": "job_profiles",
    "job profiles": "job_profiles",
    "other specializations": "other_specs",
    "explore other specializations": "other_specs",
    "faqs": "faqs",
    "faq": "faqs",
    "reviews": "reviews",
    "student reviews": "reviews",
    "university reviews": "reviews",
    "amity university online reviews": "reviews",
    "amity university online mba reviews": "reviews",
    "additional information": None,
    "additional information:": None,
    "sample certificate photo": None,
}

# ─── Stat Key Map ───────────────────────────────────────────────────────

STAT_KEY_MAP = {
    "established": "established_year",
    "students": "stat_students",
    "alumni": "stat_alumni",
    "hiring partners": "stat_hiring_partners",
    "faculty": "stat_faculty",
    "naac": "naac_grade",
    "ugc": "ugc_status",
    "mode": "mode_of_learning",
    "nirf": "nirf_rank",
    "fee": "stat_fee",
    "duration": "stat_duration",
    "approval": "ugc_status",
}

QUICK_FACTS_ALIASES = [
    "detail", "facts", "quick facts", "online detail",
    "university detail", "course facts", "university facts",
]

PAGE_TYPE_MAPS = {
    "university": UNIVERSITY_MAP,
    "course": COURSE_MAP,
    "specialization": SPECIALIZATION_MAP,
}

FUZZY_THRESHOLD = 65


def map_headings(sections, page_type):
    """Map document headings to ACF fields using keyword + fuzzy matching."""
    heading_map = PAGE_TYPE_MAPS.get(page_type, COURSE_MAP)
    mappings = []
    unmapped_headings = []
    quick_facts = {}

    for section in sections:
        raw_heading = section["heading"]
        heading_lower = raw_heading.lower().strip()
        normalized = normalize_heading(raw_heading)

        # Guard: if normalization reduced heading to empty string, skip it
        if not normalized or len(normalized) < 2:
            mappings.append({"heading": raw_heading, "acf_field": "__skip__",
                             "confidence": 100, "method": "exact_skip"})
            continue

        # Step 1: exact match on raw lowercase heading
        if heading_lower in heading_map:
            acf_field = heading_map[heading_lower]
            if acf_field is None:
                mappings.append({"heading": raw_heading, "acf_field": "__skip__",
                                 "confidence": 100, "method": "exact_skip"})
                continue
            mappings.append({"heading": raw_heading, "acf_field": acf_field,
                             "confidence": 100, "method": "exact"})
            if acf_field == "quick_facts" or _is_qf(heading_lower):
                quick_facts = _extract_stats(section)
            continue

        # Step 1.5: exact match on normalized heading
        if normalized in heading_map:
            acf_field = heading_map[normalized]
            if acf_field is None:
                mappings.append({"heading": raw_heading, "acf_field": "__skip__",
                                 "confidence": 100, "method": "exact_skip"})
                continue
            mappings.append({"heading": raw_heading, "acf_field": acf_field,
                             "confidence": 100, "method": "exact"})
            if acf_field == "quick_facts" or _is_qf(normalized):
                quick_facts = _extract_stats(section)
            continue

        # Step 2: fuzzy match on normalized heading
        best_match, best_score, best_key = None, 0, None
        for key, field in heading_map.items():
            score = fuzz.token_sort_ratio(normalized, key)
            if score > best_score:
                best_score = score
                best_match = field
                best_key = key

        if best_score >= FUZZY_THRESHOLD and best_match is not None:
            mappings.append({"heading": raw_heading, "acf_field": best_match,
                             "confidence": best_score, "method": "fuzzy",
                             "matched_key": best_key})
            if best_match == "quick_facts" or _is_qf(best_key):
                quick_facts = _extract_stats(section)
        elif best_score >= FUZZY_THRESHOLD and best_match is None:
            mappings.append({"heading": raw_heading, "acf_field": "__skip__",
                             "confidence": best_score, "method": "fuzzy_skip"})
        else:
            unmapped_headings.append({
                "heading": raw_heading,
                "raw": raw_heading,
                "normalized": normalized,
                "best_match": best_key,
                "score": best_score,
                "best_candidate": best_key,
                "best_score": best_score
            })

    if unmapped_headings:
        print("\n⚠️  UNMAPPED HEADINGS:")
        for u in unmapped_headings:
            print(f"  raw: '{u['raw']}' → normalized: '{u['normalized']}' → best fuzzy: '{u['best_match']}' ({u['score']})")

    return {"mappings": mappings, "unmapped_headings": unmapped_headings,
            "quick_facts": quick_facts}


def _is_qf(h):
    for a in QUICK_FACTS_ALIASES:
        if a in h or fuzz.token_sort_ratio(h, a) >= 80:
            return True
    return False


def _extract_stats(section):
    stats = {}
    lines = section.get("raw_text", "").split("\n")
    for table in section.get("tables", []):
        for row in table:
            if len(row) >= 2:
                lines.append(f"{row[0]}: {row[1]}")
    pat = re.compile(r"(.+?)[\-–:]+\s*(.+)")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = pat.match(line)
        if m:
            key_raw = m.group(1).strip().lower()
            value = m.group(2).strip()
            field = _match_stat_key(key_raw)
            if field:
                stats[field] = value[:6] if len(value) > 6 else value
    return stats


def _match_stat_key(key_raw):
    for kw, field in STAT_KEY_MAP.items():
        if kw in key_raw:
            return field
    best_f, best_s = None, 0
    for kw, field in STAT_KEY_MAP.items():
        s = fuzz.token_sort_ratio(key_raw, kw)
        if s > best_s and s >= 70:
            best_s = s
            best_f = field
    return best_f


def get_all_acf_fields(page_type):
    """Get sorted list of all ACF field names for a page type."""
    hmap = PAGE_TYPE_MAPS.get(page_type, COURSE_MAP)
    return sorted({f for f in hmap.values() if f is not None})


def get_field_schema(page_type):
    """Load the field schema JSON for a given page type."""
    import json, os
    schema_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schema")
    with open(os.path.join(schema_dir, f"{page_type}_fields.json")) as f:
        return json.load(f)
