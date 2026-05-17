# 🎓 DegreeBaba Content Publishing Micro App

DegreeBaba Content Publishing is a powerful, high-performance Python + Streamlit web application that automates the process of parsing university, course, and specialization content from Microsoft Word (`.docx`) files and mapping them directly to WordPress Advanced Custom Fields (ACF) schemas.

It integrates a state-of-the-art multi-layered **exact + fuzzy heading mapper** and **Groq Cloud LLM (Llama-3.3-70b-versatile)** to structure complex, repetitive layout sections (like FAQs, admission steps, fees, accreditations, and faculty members) into clean, production-ready JSON arrays.

---

## ✨ Features

- **Multi-Page Types Support:** Fully supports `University`, `Course`, and `Specialization` page structures with custom schema validations.
- **Fail-Safe Heading Mapper:** Implements a layered lookup strategy:
  1. *Exact raw match* (case-insensitive) to capture highly specific, predefined brand variants without modification.
  2. *Normalized exact match* (removing brand names like "Amity Online" and filler words) to catch stylized variants.
  3. *Fuzzy match fallback* using RapidFuzz with a tuned similarity threshold (65%).
- **Llama 3.3 Structuring (via Groq):** Leverages `llama-3.3-70b-versatile` to ingest raw text and output clean JSON arrays matching strict ACF schema specifications.
- **Aggressive JSON Healing & Fail-Safe Fallbacks:** 
  - Automatically heals malformed JSON, strips markdown code block wrappers, and wraps single-dictionary responses.
  - Automatically captures API or parsing failures and falls back to structured placeholder values (`thin` status) so that no field is left completely empty, preserving data continuity.
- **High-Fidelity Quality Scoring:** Uses a weighted accuracy metric reflecting the completeness and structuring quality of your parsed documents:
  $$\text{Score} = \frac{(\text{Mapped} + \text{AI Mapped}) \times 100 + \text{Thin} \times 60 + \text{Failed} \times 20 + \text{Missing} \times 0}{\text{Total Attempted}}$$
- **Beautiful & Intuitive UI:** Modern, user-friendly Streamlit dashboard with drag-and-drop file upload, live mapping summaries, interactive field assignment overrides, and copy-pasteable JSON output payloads.

---

## 📂 Project Structure

```bash
degreebaba/
├── app.py                      # Main Streamlit web application & UI layer
├── parser/
│   ├── __init__.py
│   ├── extractor.py            # Extracts clean headings and text blocks from .docx
│   ├── heading_mapper.py       # Implements normalizations and multi-layered mapping
│   └── repeater_builder.py     # Structures nested repeaters using Groq Llama 3.3
├── schema/
│   ├── __init__.py
│   ├── university_fields.json  # University ACF required fields & types
│   ├── course_fields.json      # Course ACF required fields & types
│   └── specialization_fields.json # Specialization ACF required fields & types
├── validator/
│   ├── __init__.py
│   └── payload_validator.py    # Generates completeness validation metrics and scores
├── .gitignore                  # Keeps caches, virtualenvs, and secrets clean
├── requirements.txt            # Project Python dependencies
└── test_app.py                 # Integration testing suite
```

---

## 🚀 Getting Started

### 1. Prerequisites
Make sure you have Python 3.8+ installed on your system.

### 2. Install Dependencies
Clone the repository and install the required Python packages:
```bash
pip install -r requirements.txt
```

### 3. Setup Your Groq API Key
Obtain a free Groq API key from the [Groq Console](https://console.groq.com/). Create a file named `.env` in the root of the project directory and paste your API key:
```env
GROQ_API_KEY=your_actual_groq_api_key_here
```

### 4. Run the Streamlit Application
Start the server and launch the micro-app in your local browser:
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser to begin publishing content!

---

## 🧪 Running Integration Tests
To verify heading normalization, parsing, schema validation, and score metrics, run the included integration testing suite:
```bash
python3 test_app.py
```
