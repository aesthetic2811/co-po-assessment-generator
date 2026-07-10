"""
CO/PO-Aligned Assessment Generator
-----------------------------------
Maps course syllabus topics to Course Outcomes (COs), generates a tagged
question bank (AI-assisted if an API key is supplied, template-based
fallback otherwise), and visualizes coverage + difficulty gaps.

Run locally:  streamlit run app.py
Deploy free:  push this repo to GitHub -> share.streamlit.io -> New app
"""

import io
import json
import random

import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="CO/PO Assessment Generator", page_icon="📊", layout="wide")

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
if "topics" not in st.session_state:
    st.session_state.topics = pd.DataFrame(
        [
            {"Topic": "Minimax Algorithm", "CO": "CO1 - Search & Reasoning"},
            {"Topic": "Alpha-Beta Pruning", "CO": "CO1 - Search & Reasoning"},
            {"Topic": "Bayesian Networks", "CO": "CO2 - Probabilistic Reasoning"},
            {"Topic": "Fuzzy Logic", "CO": "CO2 - Probabilistic Reasoning"},
            {"Topic": "K-Means Clustering", "CO": "CO3 - Unsupervised Learning"},
        ]
    )

if "question_bank" not in st.session_state:
    st.session_state.question_bank = pd.DataFrame(
        columns=["Topic", "CO", "Question", "Type", "Difficulty"]
    )

DIFFICULTIES = ["Easy", "Medium", "Hard"]
QUESTION_TYPES = ["MCQ", "Short Answer"]

TEMPLATES = {
    "MCQ": [
        "Which of the following best describes {topic}?",
        "In the context of {topic}, which statement is TRUE?",
        "{topic} is primarily used to solve which type of problem?",
    ],
    "Short Answer": [
        "Explain the working principle of {topic} with a suitable example.",
        "Compare {topic} with a related technique covered in this course.",
        "Discuss one real-world application of {topic} and its limitations.",
    ],
}


def template_generate(topic: str, co: str, n_mcq: int, n_short: int):
    rows = []
    for _ in range(n_mcq):
        q = random.choice(TEMPLATES["MCQ"]).format(topic=topic)
        rows.append(
            {
                "Topic": topic,
                "CO": co,
                "Question": q,
                "Type": "MCQ",
                "Difficulty": random.choice(DIFFICULTIES),
            }
        )
    for _ in range(n_short):
        q = random.choice(TEMPLATES["Short Answer"]).format(topic=topic)
        rows.append(
            {
                "Topic": topic,
                "CO": co,
                "Question": q,
                "Type": "Short Answer",
                "Difficulty": random.choice(DIFFICULTIES),
            }
        )
    return rows


def ai_generate(topic: str, co: str, n_mcq: int, n_short: int, api_key: str):
    """Uses Claude API to generate higher-quality, CO-aligned questions."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""You are an assessment designer for an engineering course.
Topic: {topic}
Course Outcome it must align to: {co}

Generate exactly {n_mcq} MCQ question(s) and {n_short} short-answer question(s)
that directly test the above Course Outcome. Tag each with a difficulty
(Easy/Medium/Hard).

Respond ONLY with valid JSON, no preamble, in this exact schema:
[{{"question": "...", "type": "MCQ", "difficulty": "Easy"}}, ...]
"""
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    text = text.strip().strip("```json").strip("```").strip()
    data = json.loads(text)
    rows = []
    for item in data:
        rows.append(
            {
                "Topic": topic,
                "CO": co,
                "Question": item["question"],
                "Type": item["type"],
                "Difficulty": item["difficulty"],
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Sidebar - configuration
# ---------------------------------------------------------------------------
st.sidebar.title("⚙️ Configuration")
api_key = st.sidebar.text_input(
    "Anthropic API key (optional)",
    type="password",
    help="Leave blank to use the built-in template generator instead of live AI generation.",
)
n_mcq = st.sidebar.slider("MCQs per topic", 0, 5, 2)
n_short = st.sidebar.slider("Short-answer questions per topic", 0, 5, 1)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Built as a mini-simulation of course-index → question-bank → "
    "CO/PO coverage dashboard workflows."
)

# ---------------------------------------------------------------------------
# Main - title
# ---------------------------------------------------------------------------
st.title("📊 CO/PO-Aligned Assessment Generator")
st.caption(
    "Map syllabus topics to Course Outcomes, auto-generate a tagged question "
    "bank, and spot coverage gaps before they become a client complaint."
)

tab1, tab2, tab3 = st.tabs(["1️⃣ Course Index", "2️⃣ Question Bank", "3️⃣ Coverage Dashboard"])

# ---------------------------------------------------------------------------
# Tab 1: Course Index (Topic -> CO mapping)
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Course Index — Topic to Course Outcome Mapping")
    st.write("Edit, add, or remove rows. Each row is one syllabus topic mapped to a CO.")
    edited = st.data_editor(
        st.session_state.topics,
        num_rows="dynamic",
        use_container_width=True,
        key="topic_editor",
    )
    st.session_state.topics = edited

    if st.button("🚀 Generate Question Bank from this Course Index", type="primary"):
        all_rows = []
        with st.spinner("Generating questions..."):
            for _, row in st.session_state.topics.iterrows():
                topic, co = row["Topic"], row["CO"]
                if not topic or not co:
                    continue
                if api_key:
                    try:
                        rows = ai_generate(topic, co, n_mcq, n_short, api_key)
                    except Exception as e:
                        st.warning(f"AI generation failed for '{topic}' ({e}); used template fallback.")
                        rows = template_generate(topic, co, n_mcq, n_short)
                else:
                    rows = template_generate(topic, co, n_mcq, n_short)
                all_rows.extend(rows)
        st.session_state.question_bank = pd.DataFrame(all_rows)
        st.success(f"Generated {len(all_rows)} questions across {st.session_state.topics.shape[0]} topics. Check the next tab.")

# ---------------------------------------------------------------------------
# Tab 2: Question Bank
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("Generated Question Bank")
    if st.session_state.question_bank.empty:
        st.info("No questions yet — generate a question bank from the Course Index tab first.")
    else:
        qb = st.session_state.question_bank
        col1, col2 = st.columns(2)
        co_filter = col1.multiselect("Filter by CO", options=qb["CO"].unique(), default=list(qb["CO"].unique()))
        diff_filter = col2.multiselect("Filter by Difficulty", options=DIFFICULTIES, default=DIFFICULTIES)

        filtered = qb[qb["CO"].isin(co_filter) & qb["Difficulty"].isin(diff_filter)]
        st.dataframe(filtered, use_container_width=True, height=400)

        buf = io.BytesIO()
        filtered.to_excel(buf, index=False, engine="openpyxl")
        st.download_button(
            "⬇️ Download Question Bank (Excel)",
            data=buf.getvalue(),
            file_name="question_bank.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# ---------------------------------------------------------------------------
# Tab 3: Coverage Dashboard
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("Coverage & Gap Analysis")
    if st.session_state.question_bank.empty:
        st.info("Generate a question bank first to see coverage analytics.")
    else:
        qb = st.session_state.question_bank

        c1, c2 = st.columns(2)
        with c1:
            co_counts = qb.groupby("CO").size().reset_index(name="Question Count")
            fig1 = px.bar(co_counts, x="CO", y="Question Count", title="Questions per Course Outcome", color="CO")
            st.plotly_chart(fig1, use_container_width=True)

        with c2:
            diff_counts = qb.groupby("Difficulty").size().reset_index(name="Count")
            fig2 = px.pie(diff_counts, names="Difficulty", values="Count", title="Difficulty Distribution")
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### ⚠️ Weak Coverage Alerts")
        threshold = st.slider("Flag COs with fewer than N questions", 1, 10, 3)
        weak = co_counts[co_counts["Question Count"] < threshold]
        if weak.empty:
            st.success("No COs are below the coverage threshold. Looks balanced.")
        else:
            for _, row in weak.iterrows():
                st.error(f"**{row['CO']}** has only {row['Question Count']} question(s) — needs more coverage.")

st.markdown("---")
st.caption("Prototype tool — template mode works fully offline; add an Anthropic API key for live AI-generated questions.")
