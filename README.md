# ⚕️ RxPlain — Medical Report Explanation Agent

> **AI Assignment 2 — UET Taxila | Software Engineering Department**
> Course: Artificial Intelligence | Instructor: Dr. Kanwal Yousaf
> Team: Alina Nisar (23-SE-3) & Ayesha Zainab (23-SE-19)

---

## 📌 Project Overview

**RxPlain** is a task-oriented AI agent that accepts unstructured medical text — lab reports, radiology findings, discharge summaries — and returns clear, structured, patient-friendly explanations of every medical term found.

It is powered by **LLaMA 3.3 70B** (via the **Groq API**), built with **Streamlit**, and deployed on **Streamlit Cloud** so any user can access it from a browser without installing anything.

🔗 **Live App:** `https://YOUR-USERNAME-rxplain.streamlit.app` ← replace after deployment

---

## 🎯 What the Agent Does

| Input | Output per Term |
|-------|----------------|
| Any raw medical text | ✅ Plain-language definition |
| Lab results, radiology reports, discharge notes | ✅ Clinical relevance in context |
| Abbreviations: CBC, MRI, DVT, BID, AKI, etc. | ✅ Suggested question to ask the doctor |
| Drug names, diagnostic phrases | ✅ Severity flag: Normal ✔ or Watch ⚠ |

---

## 🧠 System Architecture

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

---

## 🔧 Technologies Used

| Technology | Purpose |
|------------|---------|
| Python 3.x | Core programming language |
| Groq API (LLaMA 3.3 70B) | LLM backend — free, fast, no credit card needed |
| `groq` Python SDK | API communication |
| Streamlit | Web interface framework |
| `st.secrets` | Secure API key storage — never exposed to users |
| Streamlit Cloud | Free public deployment (no server required) |
| JSON / re | Response parsing and cleaning |

---

## 🚀 Local Setup Instructions

### Step 1 — Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/rxplain.git
cd rxplain
```

### Step 2 — Install dependencies
```bash
pip install streamlit groq
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
> ⚠️ This file is listed in `.gitignore` and will **never** be pushed to GitHub.

### Step 5 — Run the app
```bash
streamlit run app.py
```
Opens at `http://localhost:8501`

---

## 🌐 Deployment on Streamlit Cloud (Free)

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

Your app is now live at a public URL. No localhost, no terminal — works on any device.

---

## 📁 Project Structure

```
rxplain/
├── app.py                      ← Main Streamlit application
├── requirements.txt            ← Python dependencies
├── .gitignore                  ← Prevents secrets from being uploaded
├── README.md                   ← This file
└── .streamlit/
    └── secrets.toml            ← API key (local only, never on GitHub)
```

---

## 🔐 How the API Key is Kept Secret

A common mistake is hardcoding the API key directly in `app.py`. If pushed to GitHub, anyone can steal it.

RxPlain uses **Streamlit's built-in secrets system** instead:

| Environment | Where key is stored |
|-------------|-------------------|
| Local (your PC) | `.streamlit/secrets.toml` |
| Streamlit Cloud | Secrets panel in app dashboard |
| In the code | `st.secrets["GROQ_API_KEY"]` |

Users who visit the deployed app **never see or enter** the API key — it is loaded invisibly on the server side.

---

## 📊 Sample Output

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

---

## ⚠️ Disclaimer

RxPlain is for **educational purposes only**. It does not provide medical advice. Always consult a qualified healthcare professional for medical decisions.

---

## 📚 References

- Sudarshan et al. (2024). Agentic LLM Workflows for Generating Patient-Friendly Medical Reports. arXiv:2408.01112
- Singhal et al. (2023). Large language models encode clinical knowledge. *Nature*, 620, 172–180.
- Xi et al. (2023). The rise and potential of large language model based agents. arXiv:2309.07864.
- Ayers et al. (2023). Comparing physician and AI chatbot responses to patient questions. *JAMA Internal Medicine*, 183(6), 589–596.
