"""
app.py — DegreeBaba Content Publishing Micro App
Streamlit UI with 4 screens: Upload → Mapping Review → Validation → JSON Output
"""

import json
import os
import streamlit as st
from dotenv import load_dotenv

# Load env variables from .env file
load_dotenv()

# Get Groq API Key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

from parser.extractor import extract_sections, detect_page_type
from parser.heading_mapper import (
    map_headings, get_all_acf_fields, get_field_schema,
)
from parser.repeater_builder import (
    build_repeater, get_subfields, is_repeater_field,
)
from validator.payload_validator import validate_payload

# ─── Page Config ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="DegreeBaba · Content Publisher",
    page_icon="🎓",
    layout="wide",
)

# ─── Brand CSS ──────────────────────────────────────────────────────────

st.markdown("""
<style>
:root {
  --navy: #0E1F3D;
  --orange: #E84010;
  --green: #3B6D11;
  --amber: #854F0B;
  --red: #A32D2D;
}
[data-testid="stSidebar"] { background: #0E1F3D; }
[data-testid="stSidebar"] * { color: white !important; }
.stButton button[kind="primary"] { background: #E84010; border: none; }
h1, h2, h3 { color: #0E1F3D; }
.green-row  { background-color: #d4edda !important; }
.amber-row  { background-color: #fff3cd !important; }
.red-row    { background-color: #f8d7da !important; }
div[data-testid="stMetric"] {
    background: #f8f9fa; border-radius: 8px; padding: 12px;
    border-left: 4px solid #E84010;
}
.score-green { color: #3B6D11; font-weight: 700; font-size: 2rem; }
.score-amber { color: #854F0B; font-weight: 700; font-size: 2rem; }
.score-red   { color: #A32D2D; font-weight: 700; font-size: 2rem; }
</style>
""", unsafe_allow_html=True)

# ─── Session State Defaults ─────────────────────────────────────────────

for key, default in {
    "screen": 1,
    "groq_api_key": GROQ_API_KEY,
    "extracted": None,
    "page_type": None,
    "mapping_result": None,
    "payload": None,
    "validation": None,
    "overrides": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Sidebar ────────────────────────────────────────────────────────────

with st.sidebar:
    st.sidebar.markdown("""
        <div style='padding: 16px 0 24px 0;'>
            <span style='color:#E84010; font-size:20px; font-weight:700;'>degree</span>
            <span style='color:white; font-size:20px; font-weight:700;'>baba</span>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("### Content Publisher")
    st.markdown("---")
    st.markdown(f"**Screen:** {st.session_state['screen']} / 4")
    if st.session_state["page_type"]:
        st.markdown(
            f"**Page Type:** {st.session_state['page_type'].title()}"
        )
    if st.session_state["validation"]:
        sc = st.session_state["validation"]["score"]
        st.markdown(f"**Quality Score:** {sc}/100")
    st.markdown("---")
    st.caption("DegreeBaba © 2026")


# =====================================================================
#  SCREEN 1 — Upload
# =====================================================================

def screen_upload():
    st.title("🎓 DegreeBaba Content Publisher")
    st.markdown("Upload a `.docx` Word file to parse and map to WordPress ACF fields.")

    # Status/Alert banner for the API Key load state
    api_key = st.session_state.get("groq_api_key", "").strip()
    # if api_key:
    #     st.success("🟢 Groq API Key loaded successfully from environment variable.")
    # else:
    #     st.error("🔴 Groq API Key is missing. Please configure `GROQ_API_KEY` in your `.env` file and restart the app.")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded = st.file_uploader(
            "📄 Upload Word Document", type=["docx"]
        )

    with col2:
        page_type_choice = st.radio(
            "📌 Page Type",
            ["Auto-detect", "University", "Course", "Specialization"],
        )

    if st.button("🚀 Parse & Map", type="primary", use_container_width=True):
        if not api_key:
            st.error("Groq API Key is missing! Please configure `GROQ_API_KEY` in your `.env` file.")
            return
        if not uploaded:
            st.error("Please upload a .docx file.")
            return

        with st.spinner("Parsing document…"):
            docx_bytes = uploaded.read()
            extracted = extract_sections(docx_bytes)
            st.session_state["extracted"] = extracted

            # Detect or use chosen page type
            if page_type_choice == "Auto-detect":
                ptype = detect_page_type(
                    uploaded.name, extracted["sections"]
                )
            else:
                ptype = page_type_choice.lower()
            st.session_state["page_type"] = ptype

        with st.spinner("Mapping headings to ACF fields…"):
            mapping_result = map_headings(extracted["sections"], ptype)
            st.session_state["mapping_result"] = mapping_result

        with st.spinner("Building repeater fields via Groq AI…"):
            payload = _build_payload(extracted, mapping_result, ptype, api_key)
            st.session_state["payload"] = payload

        with st.spinner("Validating payload…"):
            schema = get_field_schema(ptype)
            validation = validate_payload(
                payload, ptype, mapping_result, schema
            )
            st.session_state["validation"] = validation

        st.session_state["screen"] = 2
        st.rerun()



# =====================================================================
#  SCREEN 2 — Mapping Review
# =====================================================================

def screen_mapping_review():
    st.title("📋 Mapping Review")

    mapping_result = st.session_state["mapping_result"]
    ptype = st.session_state["page_type"]
    all_fields = ["(skip)"] + get_all_acf_fields(ptype)

    # ── Mapped Headings Table ──
    st.subheader("Mapped Headings")
    mappings = mapping_result["mappings"]

    for i, m in enumerate(mappings):
        if m["acf_field"] == "__skip__":
            continue
        conf = m["confidence"]
        confidence_display = int(round(conf, 0))
        if conf >= 90:
            color = "🟢"
        elif conf >= 70:
            color = "🟡"
        else:
            color = "🔴"

        cols = st.columns([3, 3, 1, 1, 3])
        cols[0].markdown(f"**{m['heading']}**")
        cols[1].text(m["acf_field"])
        cols[2].text(f"{confidence_display}%")
        cols[3].text(f"{color} {m['method']}")

        override_key = f"override_{i}"
        current_idx = (
            all_fields.index(m["acf_field"])
            if m["acf_field"] in all_fields else 0
        )
        new_field = cols[4].selectbox(
            "Override",
            all_fields,
            index=current_idx,
            key=override_key,
            label_visibility="collapsed",
        )
        if new_field != m["acf_field"]:
            st.session_state["overrides"][m["heading"]] = new_field

    # ── Unmapped Headings ──
    unmapped = mapping_result["unmapped_headings"]
    if unmapped:
        st.subheader("⚠️ Unmapped Headings")
        for j, u in enumerate(unmapped):
            cols = st.columns([4, 4, 2])
            cols[0].markdown(f"**{u['heading']}**")
            best_score_display = int(round(u['best_score'], 0))
            cols[1].caption(
                f"Best candidate: {u['best_candidate']} "
                f"({best_score_display}%)"
            )
            assign = cols[2].selectbox(
                "Assign",
                all_fields,
                index=0,
                key=f"unmapped_{j}",
                label_visibility="collapsed",
            )
            if assign != "(skip)":
                st.session_state["overrides"][u["heading"]] = assign

    st.markdown("---")
    if st.button("✅ Confirm Mappings", type="primary", use_container_width=True):
        # Apply overrides and rebuild payload
        if st.session_state["overrides"]:
            _apply_overrides()
        st.session_state["screen"] = 3
        st.rerun()

    if st.button("⬅️ Back to Upload"):
        st.session_state["screen"] = 1
        st.rerun()


# =====================================================================
#  SCREEN 3 — Validation Report
# =====================================================================

def screen_validation():
    st.title("📊 Validation Report")

    v = st.session_state["validation"]
    payload = st.session_state["payload"]

    # Metric cards
    col1, col2, col3, col4 = st.columns(4)

    mapped_count = len(v.get("mapped", []))
    ai_mapped_count = len(v.get("ai_mapped", []))
    thin_count = len(v.get("thin", []))
    missing_count = len(v.get("missing", []))

    with col1:
        st.markdown(f"""
        <div style='background:#EAF3DE;border:1px solid #B6D98A;border-radius:10px;padding:16px 20px;'>
            <div style='font-size:28px;font-weight:700;color:#3B6D11;'>{mapped_count}</div>
            <div style='font-size:13px;color:#3B6D11;margin-top:4px;'>✅ Mapped</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style='background:#E6F1FB;border:1px solid #93C4EE;border-radius:10px;padding:16px 20px;'>
            <div style='font-size:28px;font-weight:700;color:#185FA5;'>{ai_mapped_count}</div>
            <div style='font-size:13px;color:#185FA5;margin-top:4px;'>🤖 AI Mapped</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style='background:#FAEEDA;border:1px solid #F5C97A;border-radius:10px;padding:16px 20px;'>
            <div style='font-size:28px;font-weight:700;color:#854F0B;'>{thin_count}</div>
            <div style='font-size:13px;color:#854F0B;margin-top:4px;'>⚠️ Thin Content</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style='background:#FCEBEB;border:1px solid #F09595;border-radius:10px;padding:16px 20px;'>
            <div style='font-size:28px;font-weight:700;color:#A32D2D;'>{missing_count}</div>
            <div style='font-size:13px;color:#A32D2D;margin-top:4px;'>❌ Missing</div>
        </div>""", unsafe_allow_html=True)

    # Score badge
    score = v["score"]
    score_color = "#3B6D11" if score >= 80 else "#854F0B" if score >= 60 else "#A32D2D"
    score_bg = "#EAF3DE" if score >= 80 else "#FAEEDA" if score >= 60 else "#FCEBEB"
    score_border = "#B6D98A" if score >= 80 else "#F5C97A" if score >= 60 else "#F09595"

    st.markdown(f"""
    <div style='text-align:center;margin:24px 0;'>
        <div style='display:inline-block;background:{score_bg};border:2px solid {score_border};
        border-radius:12px;padding:16px 40px;'>
            <div style='font-size:36px;font-weight:700;color:{score_color};'>{score}/100</div>
            <div style='font-size:13px;color:{score_color};margin-top:4px;'>Quality Score</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Field status table
    st.subheader("Field Status")
    schema = get_field_schema(st.session_state["page_type"])
    required = schema.get("required_fields", {})

    status_styles = {
        "mapped":    ("✅", "#EAF3DE", "#3B6D11"),
        "ai_mapped": ("🤖", "#E6F1FB", "#185FA5"),
        "thin":      ("⚠️", "#FAEEDA", "#854F0B"),
        "missing":   ("❌", "#FCEBEB", "#A32D2D"),
        "failed":    ("🔴", "#FCEBEB", "#A32D2D"),
    }

    for field_key, field_def in required.items():
        value = payload.get(field_key)
        label = field_def.get("label", field_key)

        if field_key in v.get("missing", []):
            status = "missing"
        elif field_key in v.get("failed", []):
            status = "failed"
        elif field_key in v.get("thin", []):
            status = "thin"
        elif field_key in v.get("ai_mapped", []):
            status = "ai_mapped"
        elif field_key in v.get("mapped", []):
            status = "mapped"
        else:
            status = "n/a"

        emoji, bg, color = status_styles.get(status, ("•", "#F3F4F6", "#4B5563"))
        
        with st.expander(f"{emoji} {status.replace('_', ' ').title()} — {label} (`{field_key}`)"):
            if value is not None and value != "" and value != []:
                preview = _preview(value)
                st.markdown(f"<div style='color:#4B5563;font-size:13px;'>{preview[:300]}...</div>",
                           unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='color:#A32D2D;font-size:13px;'>No content found</div>",
                           unsafe_allow_html=True)

    # Unmapped headings
    if v["unmapped_headings"]:
        st.subheader("Unmapped Headings")
        for h in v["unmapped_headings"]:
            st.warning(h)

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("⬅️ Back to Mapping"):
            st.session_state["screen"] = 2
            st.rerun()
    with col_b:
        if st.button(
            "📄 View JSON Output", type="primary", use_container_width=True
        ):
            st.session_state["screen"] = 4
            st.rerun()


# =====================================================================
#  SCREEN 4 — JSON Output
# =====================================================================

def screen_json_output():
    st.title("📄 JSON Output")

    payload = st.session_state["payload"]
    ptype = st.session_state["page_type"]
    extracted = st.session_state["extracted"]

    name_key = {
        "university": "university_name",
        "course": "course_name",
        "specialization": "specialization_name",
    }.get(ptype, "document_name")
    doc_name = payload.get(name_key, extracted["document_title"])

    json_str = json.dumps(payload, indent=2, ensure_ascii=False)

    st.code(json_str, language="json")

    safe_name = (
        doc_name.replace(" ", "_").replace("/", "_")[:50]
        if doc_name else "output"
    )
    st.download_button(
        label="⬇️ Download JSON",
        data=json_str,
        file_name=f"{safe_name}_{ptype}.json",
        mime="application/json",
        use_container_width=True,
    )

    st.info(
        "💡 Paste this JSON into the WordPress REST API publisher "
        "or your WP plugin."
    )

    if st.button("⬅️ Back to Validation"):
        st.session_state["screen"] = 3
        st.rerun()
    if st.button("🔄 Start Over"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# =====================================================================
#  Helpers
# =====================================================================

def _build_payload(extracted, mapping_result, ptype, api_key):
    """Build the full ACF payload from extracted data + mappings."""
    payload = {}
    sections = extracted["sections"]
    html_sections = extracted["html_sections"]

    # Set document title / name
    name_key = {
        "university": "university_name",
        "course": "course_name",
        "specialization": "specialization_name",
    }.get(ptype, "document_name")
    payload[name_key] = extracted["document_title"]

    # Add quick facts / stat fields
    qf = mapping_result.get("quick_facts", {})
    payload.update(qf)

    # Process each mapping
    schema = get_field_schema(ptype)
    required = schema.get("required_fields", {})

    for m in mapping_result["mappings"]:
        acf_field = m["acf_field"]
        if acf_field == "__skip__":
            continue

        heading = m["heading"]
        section = _find_section(sections, heading)
        if section is None:
            continue

        field_def = required.get(acf_field, {})
        ftype = field_def.get("type", "text")

        if ftype == "wysiwyg":
            # Use mammoth HTML — never truncate
            html = html_sections.get(heading, "")
            if not html:
                # Fallback: wrap paragraphs
                html = "".join(
                    f"<p>{p}</p>" for p in section["paragraphs"]
                )
            payload[acf_field] = html

        elif ftype == "repeater":
            subfields = get_subfields(acf_field)
            if subfields:
                raw_text = section.get("raw_text", "")
                if raw_text.strip():
                    try:
                        data, status = build_repeater(
                            acf_field, subfields, heading, raw_text, api_key
                        )
                        payload[acf_field] = data
                        m["method"] = status
                        if status == "ai_mapped":
                            m["confidence"] = min(m["confidence"], 85)
                    except Exception:
                        payload[acf_field] = []
                        m["method"] = "failed"
                else:
                    payload[acf_field] = []

        elif ftype == "text":
            payload[acf_field] = " ".join(section["paragraphs"])

        elif ftype == "stat_group":
            pass  # Stats already extracted above

    return payload


def _find_section(sections, heading):
    """Find a section dict by heading text."""
    for s in sections:
        if s["heading"] == heading:
            return s
    return None


def _apply_overrides():
    """Apply manual field assignment overrides and rebuild."""
    overrides = st.session_state["overrides"]
    extracted = st.session_state["extracted"]
    ptype = st.session_state["page_type"]
    api_key = st.session_state["groq_api_key"]
    mapping_result = st.session_state["mapping_result"]

    # Update mappings
    for m in mapping_result["mappings"]:
        if m["heading"] in overrides:
            new_field = overrides[m["heading"]]
            if new_field == "(skip)":
                m["acf_field"] = "__skip__"
            else:
                m["acf_field"] = new_field
                m["method"] = "manual"
                m["confidence"] = 100

    # Move unmapped → mapped if assigned
    new_unmapped = []
    for u in mapping_result["unmapped_headings"]:
        if u["heading"] in overrides:
            new_field = overrides[u["heading"]]
            if new_field != "(skip)":
                mapping_result["mappings"].append({
                    "heading": u["heading"],
                    "acf_field": new_field,
                    "confidence": 100,
                    "method": "manual",
                })
        else:
            new_unmapped.append(u)
    mapping_result["unmapped_headings"] = new_unmapped

    # Rebuild payload
    payload = _build_payload(extracted, mapping_result, ptype, api_key)
    st.session_state["payload"] = payload

    schema = get_field_schema(ptype)
    validation = validate_payload(payload, ptype, mapping_result, schema)
    st.session_state["validation"] = validation
    st.session_state["overrides"] = {}


def _preview(value, max_chars=200):
    """Generate a preview string of a field value."""
    if isinstance(value, list):
        s = json.dumps(value, ensure_ascii=False)
    elif isinstance(value, dict):
        s = json.dumps(value, ensure_ascii=False)
    else:
        s = str(value)
    if len(s) > max_chars:
        return s[:max_chars] + "…"
    return s


# ─── Router ─────────────────────────────────────────────────────────────

SCREENS = {
    1: screen_upload,
    2: screen_mapping_review,
    3: screen_validation,
    4: screen_json_output,
}

SCREENS.get(st.session_state["screen"], screen_upload)()
