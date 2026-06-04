import streamlit as st
import json
import re
import io
from datetime import datetime
from groq import Groq
import pypdf

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
    .summary-box {
        background: linear-gradient(135deg, #1a3a2a, #1e4a3a);
        border: 1px solid #2ecc71;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 16px;
        color: #a8f0c8 !important;
        font-size: 1.0rem;
        line-height: 1.6;
    }
    .summary-box-warn {
        background: linear-gradient(135deg, #3a2a1a, #4a3010);
        border: 1px solid #e67e22;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 16px;
        color: #f0d0a8 !important;
        font-size: 1.0rem;
        line-height: 1.6;
    }
    /* Chat section divider */
    .chat-header {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #2980b9;
        border-radius: 10px;
        padding: 14px 20px;
        margin: 30px 0 16px 0;
        color: #7ec8f0 !important;
        font-size: 1.05rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ─── API KEY ───────────────────────────────────────────────────────────────────
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]


# ─── PDF EXTRACTION ────────────────────────────────────────────────────────────
def extract_pdf_text(uploaded_file) -> str:
    reader = pypdf.PdfReader(io.BytesIO(uploaded_file.read()))
    pages  = [page.extract_text() for page in reader.pages if page.extract_text()]
    return "\n".join(pages).strip()


# ─── PROMPTS ───────────────────────────────────────────────────────────────────
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


def build_summary_prompt(watch_terms: list, total_terms: int) -> str:
    terms_str = ", ".join(watch_terms) if watch_terms else "none"
    return f"""A medical report was analyzed.
Total terms found: {total_terms}.
Terms needing attention: {terms_str}.

Write exactly ONE plain-English sentence (max 30 words) that:
- Mentions how many concerning findings there are
- Briefly says what they relate to (e.g. kidney function, heart, infection)
- Ends with: "Here is what each term means."
- Is calm and reassuring
- Has NO medical jargon

Return the sentence only. No quotes, no extra text."""


# ─── CHAT FOLLOW-UP PROMPT ────────────────────────────────────────────────────
# This builds the full message history for the chat API call.
# We pass:
#   1. A system message giving the model the full medical report context
#   2. The entire chat history so far (so the model remembers previous turns)
#   3. The new user question
# This way the model always answers in the context of the specific report.
def build_chat_messages(medical_text: str, results: list, chat_history: list, user_question: str) -> list:
    # Summarise the explained terms so the model has structured context
    terms_summary = "\n".join([
        f"- {r['term']}: {r['plain_definition']} (severity: {r['severity_flag']})"
        for r in results
    ])

    system_msg = f"""You are a helpful, compassionate medical assistant.
A patient has just had their medical report explained. Here is the original report and the explained terms:

ORIGINAL REPORT:
{medical_text}

EXPLAINED TERMS:
{terms_summary}

Your job is to answer the patient's follow-up questions about this specific report.
Rules:
- Use plain, simple language — no unnecessary jargon
- Be compassionate and reassuring
- If the question is outside what you can answer safely, advise them to consult their doctor
- Keep answers concise (3-5 sentences max) unless more detail is genuinely needed
- Never diagnose or prescribe — you are an explainer, not a doctor"""

    messages = [{"role": "system", "content": system_msg}]

    # Add all previous chat turns so the model has full conversation context
    for turn in chat_history:
        messages.append({"role": turn["role"], "content": turn["content"]})

    # Add the new question
    messages.append({"role": "user", "content": user_question})
    return messages


# ─── API CALLS ─────────────────────────────────────────────────────────────────
def call_groq(prompt: str, json_mode: bool = True) -> str:
    client  = Groq(api_key=GROQ_API_KEY)
    sys_msg = (
        "You are a medical terminology explanation agent. Always respond with valid JSON only. No markdown, no extra text."
        if json_mode else
        "You are a compassionate medical assistant. Respond with a single plain-English sentence only."
    )
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": sys_msg},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.3,
        max_tokens=4096 if json_mode else 120,
    )
    return response.choices[0].message.content.strip()


def get_explanations(medical_text: str) -> list:
    raw = call_groq(build_prompt(medical_text), json_mode=True)
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$",       "", raw)
    return json.loads(raw)


def get_summary(watch_terms: list, total_terms: int) -> str:
    return call_groq(build_summary_prompt(watch_terms, total_terms), json_mode=False)


def get_chat_reply(medical_text: str, results: list, chat_history: list, user_question: str) -> str:
    # Chat uses a different call — passes full message history, not just one prompt
    client   = Groq(api_key=GROQ_API_KEY)
    messages = build_chat_messages(medical_text, results, chat_history, user_question)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.5,   # slightly higher than analysis for more natural conversation
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()


# ─── COPY TEXT FORMATTER ───────────────────────────────────────────────────────
def results_to_plain_text(results: list) -> str:
    lines = ["MEDICAL REPORT EXPLANATION", "=" * 42]
    for i, item in enumerate(results, 1):
        flag = "⚠ WATCH — discuss with your doctor" \
               if item.get("severity_flag", "").lower() == "watch" \
               else "✔ Normal"
        lines.append(f"\n#{i}  {item.get('term', '—')}  [{flag}]")
        lines.append(f"Definition : {item.get('plain_definition', '—')}")
        lines.append(f"Relevance  : {item.get('clinical_relevance', '—')}")
        lines.append(f"Ask Doctor : {item.get('patient_question', '—')}")
    lines.append("\n" + "=" * 42)
    lines.append("This report is for educational purposes only.")
    lines.append("Always consult a qualified doctor.")
    return "\n".join(lines)


# ─── RENDER TERM CARD ──────────────────────────────────────────────────────────
def render_term_card(item: dict, idx: int):
    flag     = item.get("severity_flag", "normal").lower()
    is_watch = flag == "watch"
    badge    = '<span class="badge-watch">⚠ Watch</span>' if is_watch \
               else '<span class="badge-safe">✔ Normal</span>'
    cls      = "term-card term-card-watch" if is_watch else "term-card"
    st.markdown(f"""
<div class="{cls}">
  <div class="term-title">#{idx} &nbsp; {item.get('term','—')} {badge}</div>
  <p><span class="lbl">📖 Definition</span>{item.get('plain_definition','—')}</p>
  <p><span class="lbl">🩺 Clinical Relevance</span>{item.get('clinical_relevance','—')}</p>
  <p><span class="lbl">❓ Ask Your Doctor</span><em>{item.get('patient_question','—')}</em></p>
</div>
""", unsafe_allow_html=True)


# ─── SESSION STATE ─────────────────────────────────────────────────────────────
if "history"      not in st.session_state: st.session_state.history      = []
if "results"      not in st.session_state: st.session_state.results      = []
if "summary"      not in st.session_state: st.session_state.summary      = ""
if "last_filter"  not in st.session_state: st.session_state.last_filter  = "All"
if "sample_text"  not in st.session_state: st.session_state.sample_text  = ""
if "medical_text" not in st.session_state: st.session_state.medical_text = ""
if "pdf_text"     not in st.session_state: st.session_state.pdf_text     = ""
if "active_tab"   not in st.session_state: st.session_state.active_tab   = "paste"
# chat_history stores dicts: {"role": "user"/"assistant", "content": "..."}
if "chat_history" not in st.session_state: st.session_state.chat_history = []


# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/hospital.png", width=60)
    st.title("Medical Report\nExplanation Agent")
    st.markdown("---")
    st.markdown("### 📄 Sample Inputs")

    samples = {
        "Lab Result":        "Patient presents with dyspnea and tachycardia. CBC shows leukocytosis (WBC 14,000/μL). BMP reveals elevated creatinine (2.1 mg/dL) and hyponatremia (Na 128 mEq/L). Chest X-ray shows bilateral infiltrates. Impression: possible pneumonia with AKI.",
        "Radiology Report":  "MRI of the lumbar spine demonstrates L4-L5 disc herniation with mild foraminal stenosis. Moderate degenerative changes at L3-L4. No cord compression. Impression: lumbar radiculopathy.",
        "Discharge Summary": "Patient discharged following CABG procedure. Prescribed metoprolol 50mg BID for post-op hypertension. Continue aspirin 81mg QD. Follow up with cardiologist in 2 weeks. Monitor for signs of DVT.",
    }
    for label, text in samples.items():
        if st.button(f"📄 {label}", use_container_width=True):
            st.session_state.sample_text  = text
            st.session_state.results      = []
            st.session_state.summary      = ""
            st.session_state.chat_history = []   # clear chat when new report loaded
            st.session_state.medical_text = ""
            st.rerun()

    st.markdown("---")
    st.caption("⚠️ This tool is for educational purposes only. Always consult a qualified doctor.")

    if st.session_state.history:
        st.markdown("---")
        st.markdown(f"### 🕘 History ({len(st.session_state.history)})")
        for txt, _, ts in reversed(st.session_state.history[-5:]):
            st.caption(f"[{ts}] {txt[:38]}…")


# ─── MAIN PAGE ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1 style='margin:0'>🏥 Medical Report Explanation Agent</h1>
  <p style='margin:4px 0 0 0; opacity:0.85'>
    Upload a PDF or paste any medical report — get plain-language explanations, then ask follow-up questions.
  </p>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1], gap="large")

# ─── LEFT COLUMN: input ────────────────────────────────────────────────────────
with col_left:
    st.subheader("📋 Input Medical Text")

    # ── PDF uploader (optional) ───────────────────────────────────────────────
    # When a PDF is uploaded, its text is extracted and placed into the
    # text area below. If the user removes the PDF, the text area clears.
    # If no PDF is uploaded, the user just types/pastes directly.
    uploaded_pdf = st.file_uploader(
        "📎 Upload a PDF (optional)",
        type=["pdf"],
        help="Uploading a PDF fills the text box below automatically."
    )

    if uploaded_pdf is not None:
        # New PDF uploaded — extract and store in session state
        if st.session_state.get("last_pdf_name") != uploaded_pdf.name:
            with st.spinner("📄 Extracting text from PDF…"):
                try:
                    extracted = extract_pdf_text(uploaded_pdf)
                    if extracted:
                        st.session_state.pdf_text      = extracted
                        st.session_state.last_pdf_name = uploaded_pdf.name
                        st.success(f"✅ Extracted {len(extracted.split())} words — text loaded below.")
                    else:
                        st.session_state.pdf_text      = ""
                        st.session_state.last_pdf_name = ""
                        st.error("Could not extract text — PDF may be a scanned image. Paste manually instead.")
                except Exception as e:
                    st.session_state.pdf_text      = ""
                    st.session_state.last_pdf_name = ""
                    st.error(f"PDF read error: {e}")
        text_area_value = st.session_state.pdf_text
    else:
        # No PDF — clear stored pdf text so it never bleeds into text area
        st.session_state.pdf_text      = ""
        st.session_state.last_pdf_name = ""
        text_area_value = st.session_state.sample_text

    # ── Single text area — used for both paste and PDF ─────────────────────
    # When PDF is uploaded: pre-filled with extracted text (editable)
    # When no PDF: empty for manual paste
    medical_text = st.text_area(
        "Medical report text:",
        value=text_area_value,
        height=260,
        placeholder="Paste your report here, or upload a PDF above…"
    )
    if medical_text.strip():
        st.caption(f"📝 {len(medical_text.split())} words")

    run_btn = st.button("🔍 Explain Medical Terms", type="primary", use_container_width=True)


# ─── RIGHT COLUMN: results ─────────────────────────────────────────────────────
with col_right:
    st.subheader("📖 Explanations")

    if run_btn:
        if not medical_text.strip():
            st.warning("Please paste some medical text or upload a PDF on the left.")
        else:
            with st.spinner("🔬 Analyzing medical terms… (3–5 seconds)"):
                try:
                    results     = get_explanations(medical_text)
                    watch_terms = [r["term"] for r in results
                                   if r.get("severity_flag", "").lower() == "watch"]
                    summary     = get_summary(watch_terms, len(results))
                    ts          = datetime.now().strftime("%H:%M")

                    st.session_state.results      = results
                    st.session_state.summary      = summary
                    st.session_state.medical_text = medical_text   # save for chat context
                    st.session_state.chat_history = []             # reset chat for new report
                    st.session_state.history.append((medical_text, results, ts))

                except json.JSONDecodeError:
                    st.error("Model returned unexpected format. Please try again.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    if st.session_state.results:
        results      = st.session_state.results
        summary      = st.session_state.summary
        watch_count  = sum(1 for r in results if r.get("severity_flag","").lower() == "watch")
        normal_count = len(results) - watch_count

        if summary:
            box_cls = "summary-box-warn" if watch_count > 0 else "summary-box"
            st.markdown(f'<div class="{box_cls}">💬 &nbsp; {summary}</div>',
                        unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Terms Found", len(results))
        c2.metric("⚠ Watch",     watch_count)
        c3.metric("✔ Normal",    normal_count)
        st.markdown("---")

        with st.expander("📋 Copy full report as plain text"):
            st.code(results_to_plain_text(results), language=None)

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
            "⬇️ Download Report (JSON)",
            data=json.dumps(results, indent=2),
            file_name="medical_explanation.json",
            mime="application/json"
        )

    elif not run_btn:
        st.info("👈 Paste a medical report or upload a PDF, then click **Explain Medical Terms**.")


# ═══════════════════════════════════════════════════════════════════════════════
# CHAT SECTION — appears below the two columns, full width
# Only shown after a report has been analyzed
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.results:

    st.markdown("""
    <div class="chat-header">
      💬 &nbsp; <b>Ask a Follow-Up Question</b> &nbsp;—&nbsp;
      Ask anything about your report, e.g. <i>"What does high creatinine mean for my diet?"</i>
    </div>
    """, unsafe_allow_html=True)

    # ── Render existing chat history ──────────────────────────────────────────
    # st.chat_message("user") / st.chat_message("assistant") render
    # chat bubbles with the correct avatar automatically.
    for turn in st.session_state.chat_history:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])

    # ── Chat input box ────────────────────────────────────────────────────────
    # st.chat_input() sticks to the bottom of the section and only triggers
    # a re-run when the user presses Enter — works like any chat app.
    user_question = st.chat_input("Type your question here and press Enter…")

    if user_question:
        # Show the user's message immediately
        with st.chat_message("user"):
            st.markdown(user_question)

        # Get reply from Groq with full context
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    reply = get_chat_reply(
                        medical_text  = st.session_state.medical_text,
                        results       = st.session_state.results,
                        chat_history  = st.session_state.chat_history,
                        user_question = user_question
                    )
                    st.markdown(reply)

                    # Save both turns to history so next question has context
                    st.session_state.chat_history.append({"role": "user",      "content": user_question})
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})

                except Exception as e:
                    st.error(f"Chat error: {str(e)}")

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear chat", use_container_width=False):
            st.session_state.chat_history = []
            st.rerun()
