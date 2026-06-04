# MedCipher — Medical Report Explanation Agent

## Project Overview

**MedCipher** is a task-oriented AI agent that accepts unstructured medical text — lab reports, radiology findings, discharge summaries — and returns clear, structured, patient-friendly explanations of every medical term found.

It is powered by **LLaMA 3.3 70B** (via the **Groq API**), built with **Streamlit**, and deployed on **Streamlit Cloud** so any user can access it from a browser without installing anything.

🔗 **Live App:** [https://medcipher-i-luv-my-med-assistant.streamlit.app/](https://medcipher-i-luv-my-med-assistant.streamlit.app/)


## What the Agent Does

| Input | Output per Term |
|-------|----------------|
| Any raw medical text | Plain-language definition |
| PDF files (text extraction) | Clinical relevance in context |
| Lab results, radiology reports, discharge notes | Suggested question to ask the doctor |
| Abbreviations: CBC, MRI, DVT, BID, AKI, etc. | Severity flag: Normal ✔ or Watch ⚠ |
| Follow-up questions via chat | Conversational answers with full report context |


## Key Features

### 📄 **Multiple Input Methods**
- **Paste text** directly into the interface
- **Upload PDF files** — text is automatically extracted using `pypdf`
- **Sample inputs** — one-click examples for testing

### 📋 **Export & Sharing**
- **Copy to clipboard** — copy the full explanation report as plain text
- **Download JSON** — save structured data for personal records
- **Plain text format** — easy to share with family or save in notes

### 💬 **Smart Summary**
After analysis, a plain-English summary sentence appears at the top, e.g.:
> *"Your report mentions 3 concerning findings related to kidney function and infection. Here is what each term means."*

This gives immediate context before showing detailed term cards.

### 🗣️ **Chat Follow-up Questions**
After the report is explained, users can type natural follow-up questions like:
- *"What does high creatinine mean for my diet?"*
- *"Should I be worried about these results?"*
- *"What questions should I ask my doctor?"*

The agent remembers the full report and previous conversation, providing contextual, compassionate answers.

### 🏷️ **Structured Term Cards**
Each medical term is displayed with:
- Plain-language definition
- Clinical relevance to the specific report
- A suggested question to ask the doctor
- Severity flag (Normal ✔ or Watch ⚠)
- Filter options (All / Watch only / Normal only)


## System Architecture

```
User (Browser)
     │
     ▼
Streamlit Web Interface  (app.py)
     │
     ▼
Input Pre-processing     (tokenize, clean, strip noise)
     │
     ▼
Prompt Template Engine   (build_prompt function)
     │   Wraps medical text in structured instructions
     ▼
Groq API  ──────────────────────────────────────────────
     │    Model: LLaMA-3.3-70B-Versatile (free tier)   │
     │    Temperature: 0.3  |  Max tokens: 4096         │
     ◄───────────────────────────────────────────────────
     │
     ▼
Response Parser          (JSON parsing with json.loads)
     │
     ▼
Output Formatter         (styled term cards in Streamlit)
     │
     ▼
User sees structured explanation report
```


## Technologies Used

| Technology | Purpose |
|------------|---------|
| Python 3.x | Core programming language |
| Groq API (LLaMA 3.3 70B) | LLM backend |
| `groq` Python SDK | API communication |
| Streamlit | Web interface framework |
| `pypdf` | PDF text extraction |
| `st.secrets` | Secure API key storage (never exposed to users) |
| `st.chat_input` | Chat interface for follow-up questions |
| `st.chat_message` | Chat bubble UI component |
| Streamlit Cloud | Free public deployment (no server required) |
| JSON / re | Response parsing and cleaning |

## Local Setup Instructions

### Step 1 — Clone the repository
```bash
git clone https://github.com/Alina1905/MedCipher
cd MedCipher
```

### Step 2 — Install dependencies
```bash
pip install streamlit groq pypdf
```

### Step 3 — Get a free Groq API key
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up — no credit card needed
3. Click **API Keys → Create API Key**
4. Copy the key

### Step 4 — Add your key to secrets
Open `.streamlit/secrets.toml` and replace the placeholder:
```toml
GROQ_API_KEY = "your_actual_groq_key_here"
```

### Step 5 — Run the app
```bash
streamlit run app.py
```
Opens at `http://localhost:8501`


## Deployment on Streamlit Cloud 

Streamlit Cloud hosts your app publicly at a shareable URL for free.

### Step 1 — Push code to GitHub
Upload these files to your GitHub repository:
```
app.py
requirements.txt
.gitignore
README.md
```
> Do NOT upload `.streamlit/secrets.toml` — the `.gitignore` blocks it automatically.

### Step 2 — Deploy
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Select your repo → set main file as `app.py` → click **Deploy**

### Step 3 — Add API key on the cloud
In your app dashboard on Streamlit Cloud:
- Go to **Settings → Secrets**
- Add the following:
```toml
GROQ_API_KEY = "your_actual_groq_key_here"
```
- Click **Save** — the app restarts automatically


## Project Structure

```
MedCipher/
├── app.py                      ← Main Streamlit application
├── requirements.txt            ← Python dependencies
├── .gitignore                  ← Prevents secrets from being uploaded
├── README.md                   ← This file
└── .streamlit/
    └── secrets.toml            ← API key (local only, never on GitHub)
```


## How the API Key is Kept Secret

MedCipher uses **Streamlit's built-in secrets system** instead:

| Environment | Where the key is stored |
|-------------|-------------------|
| Local | `.streamlit/secrets.toml` |
| Streamlit Cloud | Secrets panel in app dashboard |
| In the code | `st.secrets["GROQ_API_KEY"]` |

Users who visit the deployed app **never see or enter** the API key — it is loaded invisibly on the server side.


## Sample Output

**Input:**
> *"CBC shows leukocytosis (WBC 14,000/μL). BMP reveals elevated creatinine (2.1 mg/dL) and hyponatremia (Na 128 mEq/L). Impression: possible pneumonia with AKI."*

**Output:**

| # | Term | Definition | Severity |
|---|------|-----------|----------|
| 1 | CBC | Complete Blood Count — a blood test measuring types of blood cells | ✔ Normal |
| 2 | Leukocytosis | Higher-than-normal white blood cell count, often a sign of infection | ⚠ Watch |
| 3 | Creatinine | Waste product filtered by kidneys; elevated levels suggest kidney stress | ⚠ Watch |
| 4 | Hyponatremia | Low sodium level in blood; can cause fatigue, confusion, nausea | ⚠ Watch |
| 5 | AKI | Acute Kidney Injury — sudden decrease in kidney function | ⚠ Watch |
| 6 | BMP | Basic Metabolic Panel — group of blood tests checking organ function | ✔ Normal |


## Disclaimer

MedCipher is for **educational purposes only**. It does not provide medical advice. Always consult a qualified healthcare professional for medical decisions.


## References

- Sudarshan et al. (2024). Agentic LLM Workflows for Generating Patient-Friendly Medical Reports. arXiv:2408.01112
- Singhal et al. (2023). Large language models encode clinical knowledge. *Nature*, 620, 172–180.
- Xi et al. (2023). The rise and potential of large language model based agents. arXiv:2309.07864.
- Ayers et al. (2023). Comparing physician and AI chatbot responses to patient questions. *JAMA Internal Medicine*, 183(6), 589–596.
