# CO/PO-Aligned Assessment Generator

**A Streamlit tool that maps syllabus topics to Course Outcomes (COs), auto-generates a tagged question bank, and flags exactly where CO coverage is uneven — before an assessment goes out, not after.**

🔗 **Live app:** [co-po-assessment-generator.streamlit.app](https://co-po-assessment-generator-mjcrmfijqe4c85u4jgdyss.streamlit.app/)

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [How It Works](#how-it-works)
- [Walkthrough Example](#walkthrough-example)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Deployment](#deployment)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [Author](#author)

---

## Problem Statement

Outcome-Based Education (OBE) frameworks require every assessment to test each Course Outcome (CO) with reasonably balanced coverage — not just touch on it in passing. In practice, this CO–question mapping is tracked by hand in a spreadsheet, which makes uneven coverage easy to miss: a few COs end up over-tested while one or two are barely represented, and nobody catches it until the exam paper is already finalized.

This tool closes that gap. Given a course index (topic → CO mapping), it generates a difficulty-tagged question bank per topic and gives a direct, numeric readout of which COs are under-covered — and by exactly how many questions — so the fix happens at the drafting stage instead of during a post-exam audit.

---

## How It Works

The app is organized into three tabs that mirror the actual assessment-design workflow:

### 1. Course Index

Build a table of `Topic → CO` pairs by editing rows directly in the app, or bulk-import a CSV — useful when mapping a full semester's syllabus rather than a handful of topics. A downloadable CSV template is provided so column names line up exactly with what the app expects, avoiding import errors.

### 2. Question Generation

For every row in the course index, the app produces a set of MCQs and short-answer questions, each tagged with a difficulty level (Easy / Medium / Hard). Two generation paths are supported:

| Mode | How it works | API key needed? | Cost |
|---|---|---|---|
| **Template mode** *(default)* | Fills question templates with the topic name | No | Free, fully offline |
| **AI mode** | Sends each topic/CO pair to Claude with a prompt asking for questions aligned specifically to that CO, returned as structured JSON | Yes (Anthropic API key, entered in the sidebar) | Pay-per-use via your own key |

Every generation is cached against a hash of `(topic, CO, question counts, mode)`. If the same topic is generated twice in a session — say, after tweaking the target count elsewhere — the app serves the cached result instead of re-calling the model. This matters more once AI mode is in use against a live API, where redundant calls cost both time and money.

### 3. Coverage Dashboard

Once a question bank exists, the app:
- Aggregates questions by CO and difficulty
- Renders a bar chart of question count per CO and a pie chart of difficulty spread
- Runs a gap calculation: for a target number of questions per CO (set in the sidebar), it subtracts the current count from the target for every CO and lists exactly how many more questions each one needs — sorted by the largest gap first

---

## Walkthrough Example

**Course index:**

| Topic | CO |
|---|---|
| Minimax Algorithm | CO1 — Search & Reasoning |
| Alpha-Beta Pruning | CO1 — Search & Reasoning |
| Bayesian Networks | CO2 — Probabilistic Reasoning |

With 3 MCQs and 1 short-answer question generated per topic, this produces **12 questions total** — 8 tagged CO1, 4 tagged CO2.

If the target is set to **10 questions per CO**, the coverage dashboard immediately shows:

| CO | Current Count | Target | Gap |
|---|---|---|---|
| CO1 — Search & Reasoning | 8 | 10 | 2 more needed |
| CO2 — Probabilistic Reasoning | 4 | 10 | **6 more needed** |

CO2 is flagged first since it has the largest gap — exactly the kind of imbalance that's easy to miss in a manual spreadsheet.

---

## Features

- 📋 **Course index editor** — manual row entry plus bulk CSV import/export
- 🧩 **Dual generation modes** — free offline templates, or Claude-powered generation for context-aware questions
- 🏷️ **Difficulty tagging** — every generated question is labeled Easy, Medium, or Hard
- ⚡ **Session-level caching** — avoids redundant (and costly) regeneration calls
- 📊 **Coverage dashboard** — per-CO counts, difficulty distribution, and a numeric gap recommendation, sorted by severity
- 📤 **Flexible export** — question bank downloadable as Excel or CSV, filterable by CO and difficulty before export

---

## Tech Stack

| Layer | Tool |
|---|---|
| App framework | Streamlit |
| Data handling | Pandas |
| Charts | Plotly |
| AI generation (optional) | Anthropic API |
| Excel export | OpenPyXL |
| Language | Python |

---

## Project Structure

```
co-po-assessment-generator/
├── app.py                 # Main Streamlit app — tabs, routing, session state
├── requirements.txt        # Python dependencies
├── templates/               # Question templates used in offline mode
├── assets/                  # CSV template(s) for course index import
└── README.md
```

*(Adjust this section to match your actual repo layout if it differs.)*

---

## Getting Started

### Run locally

```bash
git clone https://github.com/aesthetic2811/co-po-assessment-generator.git
cd co-po-assessment-generator
pip install -r requirements.txt
streamlit run app.py
```

The app will open at `http://localhost:8501`.

### Using AI mode

1. Get an API key from the [Anthropic Console](https://console.anthropic.com/).
2. Paste it into the sidebar field inside the app.
3. Switch the generation mode toggle from Template to AI.

Your key is used only for the current session and is never stored or logged by the app.

---

## Deployment

Deployed on **Streamlit Community Cloud**. To deploy your own copy:

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, and create a new app.
3. Point it at your fork — branch `main`, main file `app.py` — and deploy.

---

## Limitations

- **Template mode is generic by design.** Since it isn't context-aware, phrasing can feel repetitive across topics — it's meant as a free fallback, not a substitute for AI mode's quality.
- **No cross-session persistence.** Closing the tab clears the generated question bank and course index, aside from whatever is cached within that browser session.
- **CO/PO mapping is manual.** The tool doesn't parse a syllabus PDF or extract COs automatically — it assumes the topic-to-CO mapping is already known and entered by the user.

---

## Roadmap

Ideas being considered for future versions:

- [ ] Persistent storage (save/reload a course index and question bank across sessions)
- [ ] Automated syllabus PDF parsing to pre-fill the course index
- [ ] PO-level (Program Outcome) coverage tracking in addition to CO-level
- [ ] Bloom's Taxonomy tagging alongside difficulty level
- [ ] Multi-user / multi-course support for department-wide use

---

## Author

**Janvi Sharma**
B.Tech Information Technology, MSIT (GGSIPU)

If you find this useful or have suggestions, feel free to open an issue or reach out.
