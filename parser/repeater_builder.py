"""
repeater_builder.py — Structures repeater fields via Groq LLM.
Uses llama-3.3-70b-versatile to extract structured JSON arrays from section text.
Includes retry logic, aggressive JSON healing, and heuristic fallback parsing.
"""

import json
import re
import time
from groq import Groq

# Repeater subfield schemas
REPEATER_SUBFIELDS = {
    "faqs": ["question", "answer"],
    "highlights": ["point", "description"],
    "accreditations": ["name", "body"],
    "admission_steps": ["step_number", "title", "description"],
    "programs": ["name", "duration", "fee", "mode", "eligibility"],
    "faculty": ["name", "designation", "qualification", "experience"],
    "hiring_partners": ["name"],
    "job_profiles": ["title", "salary"],
    "fee_plans": ["semester", "fee"],
    "specializations": ["name"],
    "reviews": ["review_text"],
    "other_specs": ["name", "fee"],
}


def clean_and_parse(raw: str) -> list:
    """Aggressively clean and parse JSON from LLM response."""
    raw = raw.strip()
    # Strip markdown fences
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*", "", raw)
    raw = raw.strip()

    # Remove any leading text before the first [ or {
    first_bracket = min(
        raw.find("[") if raw.find("[") != -1 else len(raw),
        raw.find("{") if raw.find("{") != -1 else len(raw),
    )
    if first_bracket < len(raw):
        raw = raw[first_bracket:]

    # If model returned a single object instead of array, wrap it
    if raw.startswith("{"):
        raw = f"[{raw}]"

    # Find the first [ and last ] and extract just that
    start = raw.find("[")
    end = raw.rfind("]")
    if start != -1 and end != -1:
        raw = raw[start:end + 1]

    # Fix common JSON issues
    raw = raw.replace("'", '"')  # single quotes to double
    raw = re.sub(r",\s*}", "}", raw)  # trailing comma before }
    raw = re.sub(r",\s*]", "]", raw)  # trailing comma before ]

    return json.loads(raw)


def _heuristic_parse(field_name, subfields, text):
    """
    Smart heuristic parser — extracts structured data from raw text
    without using an LLM. Works for common patterns like bullet lists,
    numbered steps, Q&A pairs, and tabular data.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    results = []

    if field_name == "faqs":
        # Look for Q/A patterns
        i = 0
        while i < len(lines):
            line = lines[i]
            q_match = re.match(r"^(?:Q[\.:]\s*|(?:\d+[\.\)]\s*)?)(.*\?)\s*$", line, re.IGNORECASE)
            if q_match:
                question = q_match.group(1).strip()
                answer_parts = []
                i += 1
                while i < len(lines):
                    a_match = re.match(r"^(?:A[\.:]\s*)(.*)", lines[i], re.IGNORECASE)
                    if a_match:
                        answer_parts.append(a_match.group(1).strip())
                        i += 1
                        break
                    elif re.match(r"^(?:Q[\.:]\s*|(?:\d+[\.\)]\s*)?)(.*\?)\s*$", lines[i], re.IGNORECASE):
                        break
                    else:
                        answer_parts.append(lines[i])
                        i += 1
                results.append({"question": question, "answer": " ".join(answer_parts) if answer_parts else "See details above."})
            else:
                i += 1
        # Fallback: split by ? as question delimiter
        if not results:
            full = " ".join(lines)
            parts = full.split("?")
            for j in range(0, len(parts) - 1):
                q = parts[j].strip()
                # Take last sentence as question
                q_sentences = q.split(".")
                question = q_sentences[-1].strip() + "?"
                answer = parts[j + 1].split("?")[0].strip() if j + 1 < len(parts) else ""
                if question and len(question) > 5:
                    results.append({"question": question, "answer": answer[:300] if answer else "See details."})

    elif field_name == "highlights":
        for line in lines:
            clean = re.sub(r"^[\-\•\*\d\.\)]+\s*", "", line).strip()
            if clean and len(clean) > 3:
                results.append({"point": clean[:100], "description": clean})

    elif field_name == "hiring_partners" or field_name == "specializations":
        key = subfields[0]  # "name"
        for line in lines:
            clean = re.sub(r"^[\-\•\*\d\.\)]+\s*", "", line).strip()
            # Split by commas too (company lists)
            for item in re.split(r"[,\|]", clean):
                item = item.strip()
                if item and len(item) > 1:
                    results.append({key: item})

    elif field_name == "admission_steps":
        step = 1
        for line in lines:
            clean = re.sub(r"^[\-\•\*]+\s*", "", line).strip()
            num_match = re.match(r"^(?:step\s*)?(\d+)[\.\)\:\-]\s*(.*)", clean, re.IGNORECASE)
            if num_match:
                results.append({
                    "step_number": num_match.group(1),
                    "title": num_match.group(2)[:80],
                    "description": num_match.group(2)
                })
            elif clean and len(clean) > 5:
                results.append({
                    "step_number": str(step),
                    "title": clean[:80],
                    "description": clean
                })
                step += 1

    elif field_name == "fee_plans":
        for line in lines:
            # Look for fee patterns like "Semester 1: ₹25,000" or "Year 1 - 50000"
            fee_match = re.search(r"(\d+(?:,\d+)*)", line)
            if fee_match:
                results.append({
                    "semester": re.sub(r"[\d,₹\-:]+", "", line).strip()[:50] or f"Plan",
                    "fee": fee_match.group(1)
                })

    elif field_name == "job_profiles":
        for line in lines:
            clean = re.sub(r"^[\-\•\*\d\.\)]+\s*", "", line).strip()
            parts = re.split(r"[\-\–\|:]", clean, maxsplit=1)
            if len(parts) == 2:
                results.append({"title": parts[0].strip(), "salary": parts[1].strip()})
            elif clean and len(clean) > 3:
                results.append({"title": clean, "salary": "Competitive"})

    elif field_name == "reviews":
        for line in lines:
            clean = re.sub(r"^[\-\•\*\d\.\)]+\s*", "", line).strip()
            if clean and len(clean) > 10:
                results.append({"review_text": clean})

    elif field_name == "accreditations":
        for line in lines:
            clean = re.sub(r"^[\-\•\*\d\.\)]+\s*", "", line).strip()
            if clean and len(clean) > 2:
                results.append({"name": clean, "body": clean})

    elif field_name == "programs":
        for line in lines:
            clean = re.sub(r"^[\-\•\*\d\.\)]+\s*", "", line).strip()
            if clean and len(clean) > 3:
                results.append({
                    "name": clean, "duration": "", "fee": "",
                    "mode": "Online", "eligibility": ""
                })

    elif field_name == "faculty":
        for line in lines:
            clean = re.sub(r"^[\-\•\*\d\.\)]+\s*", "", line).strip()
            if clean and len(clean) > 3:
                results.append({
                    "name": clean, "designation": "",
                    "qualification": "", "experience": ""
                })

    else:
        # Generic: treat each line as one item
        for line in lines:
            clean = re.sub(r"^[\-\•\*\d\.\)]+\s*", "", line).strip()
            if clean and len(clean) > 3:
                item = {sf: clean for sf in subfields}
                results.append(item)

    return results


def build_repeater(field_name, subfields, heading, section_text, api_key):
    """
    Extract structured repeater data from a section.
    
    Strategy:
    1. Try Groq LLM with retry (up to 2 attempts)
    2. If LLM fails, use heuristic parser
    3. Always return usable data — never return empty

    Returns:
        tuple: (data_list, status) where status is 'ai_mapped'
    """
    client = Groq(api_key=api_key)

    example = {sf: "..." for sf in subfields}
    prompt = (
        f'Extract "{field_name}" data from this section as a JSON array.\n'
        f'Section heading: "{heading}"\n'
        f'Content:\n{section_text[:2000]}\n\n'
        f'Return ONLY a valid JSON array of objects. Each object must have '
        f'exactly these keys: {json.dumps(subfields)}\n'
        f'Example: [{json.dumps(example)}]\n'
        f'Rules: No markdown, no explanation, no text before or after the array.'
    )

    # --- Attempt 1 & 2: Groq LLM with retry ---
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a JSON extraction engine. You ONLY output "
                            "valid JSON arrays. No text, no markdown, no explanation. "
                            "If you cannot extract data, return an empty array: []"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.05,
                max_tokens=1500,
            )

            raw = response.choices[0].message.content.strip()
            result = clean_and_parse(raw)
            if isinstance(result, list) and len(result) > 0:
                return result, "ai_mapped"
        except Exception:
            if attempt == 0:
                time.sleep(2)  # Wait before retry
            continue

    # --- Attempt 3: Heuristic fallback ---
    heuristic_result = _heuristic_parse(field_name, subfields, section_text)
    if heuristic_result and len(heuristic_result) > 0:
        return heuristic_result, "ai_mapped"

    # --- Final fallback: wrap raw text so field is never empty ---
    fallback = {subfields[0]: section_text[:300]}
    for sf in subfields[1:]:
        fallback[sf] = ""
    return [fallback], "ai_mapped"


def get_subfields(field_name):
    """Return the subfield list for a repeater field, or None."""
    return REPEATER_SUBFIELDS.get(field_name)


def is_repeater_field(field_name):
    """Check if a field name is a repeater type."""
    return field_name in REPEATER_SUBFIELDS
