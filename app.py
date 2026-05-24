import streamlit as st
import json
import re
from datetime import datetime
from groq import Groq

st.set_page_config(page_title="Medical Report Explanation Agent", page_icon="🏥", layout="wide")

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a5f, #2980b9);
        padding: 20px 30px; border-radius: 12px;
        color: white; margin-bottom: 25px;
    }
    .term-card {
        background: #1e2a3a;
        border-left: 5px solid #2980b9;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 12px 0;
    }
    .term-card-watch {
        background: #2a1f10 !important;
        border-left-color: #e67e22 !important;
    }
    .term-card p {
        color: #dce8f5 !important;
        margin: 5px 0 10px 0;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    .term-card em { color: #c8dff0 !important; }
    .term-title {
        color: #7ec8f0;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .lbl {
        color: #90aec4;
        font-weight: 700;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        display: block;
        margin-bottom: 2px;
    }
    .badge-safe  { background:#27ae60; color:#fff; padding:2px 10px; border-radius:12px; font-size:0.75rem; margin-left:8px; }
    .badge-watch { background:#e67e22; color:#fff; padding:2px 10px; border-radius:12px; font-size:0.75rem; margin-left:8px; }
    .sidebar-box { background:#1a2a3a; border-radius:8px; padding:12px; font-size:0.85rem; color:#b0cce0; line-height:1.7; }
    .sidebar-box a { color:#5ab4e0; }
</style>
""", unsafe_allow_html=True)


# ─── API KEY: loaded from Streamlit secrets, never shown to user ───────────────
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]


# ─── PROMPT ────────────────────────────────────────────────────────────────────
def build_prompt(medical_text: str) -> str:
    return f"""You are a Medical Report Explanation Agent helping patients understand their medical reports.

A patient has submitted the following medical text:
---
{medical_text}
---

Your task:
1. Identify ALL medical terms, abbreviations, drug names, and clinical phrases.
2. For EACH term provide a structured explanation.

Return ONLY a valid JSON array — no text before or after, no markdown fences. Format:
[
  {{
    "term": "exact term from the text",
    "plain_definition": "simple definition a 6th-grader can understand (max 40 words)",
    "clinical_relevance": "why this matters in the context of this specific report",
    "patient_question": "one important question the patient should ask their doctor",
    "severity_flag": "normal or watch"
  }}
]

Rules:
- severity_flag must be "watch" if the term relates to something abnormal or needs follow-up, else "normal".
- Be compassionate and reassuring in tone.
- Do NOT skip any abbreviation (CBC, MRI, DVT, BID, etc.).
- Return pure JSON only.
"""


# ─── API CALL ──────────────────────────────────────────────────────────────────
def call_groq(prompt: str) -> list:
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a medical terminology explanation agent. Always respond with valid JSON only. No markdown, no extra text."},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.3,
        max_tokens=4096,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


# ─── RENDER CARD ───────────────────────────────────────────────────────────────
def render_term_card(item: dict, idx: int):
    flag     = item.get("severity_flag", "normal").lower()
    is_watch = flag == "watch"
    badge    = '<span class="badge-watch">⚠ Watch</span>' if is_watch else '<span class="badge-safe">✔ Normal</span>'
    cls      = "term-card term-card-watch" if is_watch else "term-card"

    st.markdown(f"""
<div class="{cls}">
  <div class="term-title">#{idx} &nbsp; {item.get('term','—')} {badge}</div>
  <p><span class="lbl"> Definition</span>{item.get('plain_definition','—')}</p>
  <p><span class="lbl"> Clinical Relevance</span>{item.get('clinical_relevance','—')}</p>
  <p><span class="lbl"> Ask Your Doctor</span><em>{item.get('patient_question','—')}</em></p>
</div>
""", unsafe_allow_html=True)


# ─── SESSION STATE ─────────────────────────────────────────────────────────────
if "history"     not in st.session_state: st.session_state.history     = []
if "results"     not in st.session_state: st.session_state.results     = []
if "last_filter" not in st.session_state: st.session_state.last_filter = "All"
if "sample_text" not in st.session_state: st.session_state.sample_text = ""


# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/hospital.png", width=60)
    st.title("Medical Report\nExplanation Agent")
    st.markdown("---")
    st.markdown("### Sample Inputs")

    samples = {
        "Lab Result":        "Patient presents with dyspnea and tachycardia. CBC shows leukocytosis (WBC 14,000/μL). BMP reveals elevated creatinine (2.1 mg/dL) and hyponatremia (Na 128 mEq/L). Chest X-ray shows bilateral infiltrates. Impression: possible pneumonia with AKI.",
        "Radiology Report":  "MRI of the lumbar spine demonstrates L4-L5 disc herniation with mild foraminal stenosis. Moderate degenerative changes at L3-L4. No cord compression. Impression: lumbar radiculopathy.",
        "Discharge Summary": "Patient discharged following CABG procedure. Prescribed metoprolol 50mg BID for post-op hypertension. Continue aspirin 81mg QD. Follow up with cardiologist in 2 weeks. Monitor for signs of DVT.",
    }
    for label, text in samples.items():
        if st.button(f" {label}", use_container_width=True):
            st.session_state.sample_text = text
            st.rerun()

    st.markdown("---")
    st.caption(" This tool is for educational purposes only. Always consult a qualified doctor.")

    if st.session_state.history:
        st.markdown("---")
        st.markdown(f"###  History ({len(st.session_state.history)})")
        for txt, _, ts in reversed(st.session_state.history[-5:]):
            st.caption(f"[{ts}] {txt[:38]}…")


# ─── MAIN PAGE ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1 style='margin:0'> Medical Report Explanation Agent</h1>
  <p style='margin:4px 0 0 0; opacity:0.85'>Paste any medical report, lab result, or discharge summary — get plain-language explanations instantly.</p>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader(" Input Medical Text")
    medical_text = st.text_area(
        "Paste your medical report here:",
        value=st.session_state.sample_text,
        height=320,
        placeholder="e.g. CBC shows leukocytosis (WBC 14,000/μL)…"
    )
    run_btn = st.button(" Explain Medical Terms", type="primary", use_container_width=True)
    if medical_text.strip():
        st.caption(f" {len(medical_text.split())} words")

with col_right:
    st.subheader(" Explanations")

    # ── Step 1: call API only when button is clicked ─────────────────────────
    if run_btn:
        if not medical_text.strip():
            st.warning("Please paste some medical text on the left.")
        else:
            with st.spinner(" Analyzing medical terms… (3–5 seconds)"):
                try:
                    results = call_groq(build_prompt(medical_text))
                    ts = datetime.now().strftime("%H:%M")
                    # Save results into session state so they survive re-runs
                    st.session_state.results = results
                    st.session_state.history.append((medical_text, results, ts))
                except json.JSONDecodeError:
                    st.error("Model returned unexpected format. Please try again.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # ── Step 2: display results from session state (survives filter clicks) ──
    if st.session_state.results:
        results = st.session_state.results

        watch_count  = sum(1 for r in results if r.get("severity_flag","").lower() == "watch")
        normal_count = len(results) - watch_count

        c1, c2, c3 = st.columns(3)
        c1.metric("Terms Found", len(results))
        c2.metric("⚠ Watch",     watch_count)
        c3.metric("✔ Normal",    normal_count)
        st.markdown("---")
        show = st.radio("Show:", ["All", "Watch only", "Normal only"], horizontal=True)

        if show == "Watch only":
            filtered = [r for r in results if r.get("severity_flag","").lower() == "watch"]
        elif show == "Normal only":
            filtered = [r for r in results if r.get("severity_flag","").lower() != "watch"]
        else:
            filtered = results

        if not filtered:
            st.info("No terms found for this filter.")
        else:
            for idx, item in enumerate(filtered, 1):
                render_term_card(item, idx)

        st.download_button(
            " Download Report (JSON)",
            data=json.dumps(results, indent=2),
            file_name="medical_explanation.json",
            mime="application/json"
        )
    elif not run_btn:
        st.info("👈 Paste a medical report on the left and click **Explain Medical Terms**.")
