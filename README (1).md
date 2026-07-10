# 📊 CO/PO-Aligned Assessment Generator

A tool that simulates a real assessment-design workflow: it takes a course
syllabus, maps each topic to a Course Outcome (CO), auto-generates a
difficulty-tagged question bank, and visualizes coverage gaps so you know
exactly where an assessment is weak before it goes out to students.

**Live demo:** _add your deployed Streamlit link here after deployment_

---

## 🧩 Problem Statement

When designing course assessments, instructors and ed-tech teams need to
make sure every Course Outcome (CO) and Program Outcome (PO) is actually
tested — not just covered on paper. Manually tracking "how many questions
exist per CO" and "is the difficulty balanced" across a large question bank
is tedious and error-prone. This tool automates that mapping, generation,
and gap-detection process.

## ✨ Features

- **Course Index Builder** — editable table to map syllabus topics to COs
- **Automated Question Bank Generation** — MCQs + short-answer questions
  per topic, each tagged with difficulty (Easy / Medium / Hard)
- **Two generation modes:**
  - Template-based generator (works fully offline, no API key needed)
  - AI-generated mode (via Anthropic Claude API) for more context-aware,
    higher-quality questions
- **Coverage Dashboard** — bar chart of questions per CO, pie chart of
  difficulty distribution, and automatic alerts for under-covered COs
- **Excel Export** — download the filtered question bank directly

## 🛠️ Tech Stack

| Layer | Tool |
|---|---|
| UI / App framework | Streamlit |
| Data handling | Pandas |
| Visualization | Plotly |
| AI question generation | Anthropic Claude API |
| Export | OpenPyXL (Excel) |

## ⚙️ How It Works

1. User builds/edits a **Course Index**: a table of `Topic → Course Outcome`.
2. On clicking generate, each topic is sent either to a **template
   engine** or the **Claude API** (if a key is provided) to produce
   MCQ + short-answer questions tagged with difficulty.
3. The generated question bank is stored in-session and can be filtered
   by CO or difficulty, then exported to Excel.
4. The **Coverage Dashboard** aggregates the question bank to show
   per-CO question counts and difficulty spread, flagging any CO that
   falls below a configurable question-count threshold.

## 🚀 Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## ☁️ Deploy for Free (Streamlit Community Cloud)

1. Push this repo to GitHub (`app.py`, `requirements.txt`, `README.md`).
2. Go to [share.streamlit.io](https://share.streamlit.io) → sign in with GitHub.
3. Click **New app** → select this repo → branch `main` → main file `app.py` → **Deploy**.
4. You'll get a live URL like `https://<app-name>.streamlit.app` — add it to
   the top of this README and to your resume.

## 🔒 Notes on API Key

The Anthropic API key field in the sidebar is only used client-side during
your session — it is never stored or logged. Leave it blank to use the
offline template generator.

## 👤 Author

Janvi Sharma — B.Tech Information Technology, MSIT (GGSIPU)
