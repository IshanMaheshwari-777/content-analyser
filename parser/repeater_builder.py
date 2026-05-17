"""
repeater_builder.py — Structures repeater fields via Groq LLM.
Uses llama-3.3-70b-versatile to extract structured JSON arrays from section text.
"""

import json
import re
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
    # Strip markdown fences
    raw = raw.strip()
    raw = re.sub(r"```json", "", raw)
    raw = re.sub(r"```", "", raw)
    raw = raw.strip()
    
    # If model returned a single object instead of array, wrap it
    if raw.startswith("{"):
        raw = f"[{raw}]"
    
    # Find the first [ and last ] and extract just that
    start = raw.find("[")
    end = raw.rfind("]")
    if start != -1 and end != -1:
        raw = raw[start:end+1]
    
    return json.loads(raw)


def build_repeater(field_name, subfields, heading, section_text, api_key):
    """
    Call Groq LLM to extract structured repeater data from a section.

    Args:
        field_name: ACF repeater field name (e.g. 'faqs')
        subfields: list of subfield keys
        heading: original document heading
        section_text: raw text content of the section
        api_key: Groq API key

    Returns:
        tuple: (data_list, status) where status is 'ai_mapped' or 'thin'
    """
    client = Groq(api_key=api_key)

    subfield_str = ", ".join(subfields)
    example = {sf: "..." for sf in subfields}

    prompt = (
        f'Extract {field_name} data from this section.\n'
        f'Section heading: "{heading}"\n'
        f'Content:\n{section_text}\n\n'
        f'Return ONLY a JSON array with this exact structure, '
        f'no explanation, no markdown:\n[{json.dumps(example)}]'
    )

    raw = ""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract structured data from Indian EdTech "
                        "content documents. Return ONLY a valid JSON array. "
                        "No preamble, no explanation, no markdown fences."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=1000,
        )

        raw = response.choices[0].message.content.strip()
        result = clean_and_parse(raw)
        return result, "ai_mapped"
    except Exception as e:
        content_val = raw[:500] if raw else "API Error or Empty Response"
        return [{"content": content_val}], "thin"


def get_subfields(field_name):
    """Return the subfield list for a repeater field, or None."""
    return REPEATER_SUBFIELDS.get(field_name)


def is_repeater_field(field_name):
    """Check if a field name is a repeater type."""
    return field_name in REPEATER_SUBFIELDS
