"""
CO/PO-Aligned Assessment Generator
-----------------------------------
Bulk-maps course syllabus topics (via CSV or manual entry) to Course
Outcomes (COs), generates a cached/deduplicated question bank, computes
an auto-balancing recommendation for weak COs, and visualizes coverage +
difficulty gaps end to end.

Run locally:  streamlit run app.py
Deploy free:  push this repo to GitHub -> share.streamlit.io -> New app
"""

import hashlib
import io
import json
import random

import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="CO/PO Assessment Generator", page_icon="📊", layout="wide")

# ---------------------------------------------------------------------------
# Custom styling
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .main { background-color: #F7F9FC; }
    .metric-card {
        background: linear-gradient(135deg, #1F3864 0%, #2E5C87 100%);
        padding: 18px 20px; border-radius: 12px; color: white;
        text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.12);
    }
    .metric-card h2 { margin: 0; font-size: 30px; }
    .metric-card p { margin: 2px 0 0 0; font-size: 13px; opacity: 0.85; }
    .hero {
        background: linear-gradient(90deg, #1F3864 0%, #2E5C87 100%);
        padding: 26px 30px; border-radius: 14px; color: white; margin-bottom: 18px;
    }
    .hero h1 { margin: 0; font-size: 30px; }
    .hero p { margin: 6px 0 0 0; opacity: 0.9; font-size: 15px; }
    div[data-testid="stMetricValue"] { color: #1F3864; }
    </style>
    """,
    unsafe_allow_html=True,
)

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

if "gen_cache" not in st.session_state:
    # Avoids re-calling the API / re-rolling templates for a topic+CO+count
    # combination that's already been generated once in this session —
    # real cost/time saving, not just a UI wrapper around a single prompt.
    st.session_state.gen_cache = {}

DIFFICULTIES = ["Easy", "Medium", "Hard"]
QUESTION_TYPES = ["MCQ", "Short Answer"]

TEMPLATES = {
    "MCQ": [
        "Which of the following best describes {topic}?",
        "In the context of {topic}, which statement is TRUE?",
        "{topic} is primarily used to solve which type of problem?",
        "Which limitation is most commonly associated with {topic}?",
    ],
    "Short Answer": [
        "Explain the working principle of {topic} with a suitable example.",
        "Compare {topic} with a related technique covered in this course.",
        "Discuss one real-world application of {topic} and its limitations.",
        "Walk through how {topic} would be applied to a practical scenario.",
    ],
}


def cache_key(topic, co, n_mcq, n_short, mode):
    raw = f"{topic}|{co}|{n_mcq}|{n_short}|{mode}"
    return hashlib.md5(raw.encode()).hexdigest()


def template_generate(topic: str, co: str, n_mcq: int, n_short: int):
    rows = []
    for _ in range(n_mcq):
        q = random.choice(TEMPLATES["MCQ"]).format(topic=topic)
        rows.append({"Topic": topic, "CO": co, "Question": q, "Type": "MCQ",
                      "Difficulty": random.choice(DIFFICULTIES)})
    for _ in range(n_short):
        q = random.choice(TEMPLATES["Short Answer"]).format(topic=topic)
        rows.append({"Topic": topic, "CO": co, "Question": q, "Type": "Short Answer",
                      "Difficulty": random.choice(DIFFICULTIES)})
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
        rows.append({"Topic": topic, "CO": co, "Question": item["question"],
                      "Type": item["type"], "Difficulty": item["difficulty"]})
    return rows


def generate_for_topic(topic, co, n_mcq, n_short, api_key):
    mode = "ai" if api_key else "template"
    key = cache_key(topic, co, n_mcq, n_short, mode)
    if key in st.session_state.gen_cache:
        return st.session_state.gen_cache[key], True  # from cache
    if api_key:
        try:
            rows = ai_generate(topic, co, n_mcq, n_short, api_key)
        except Exception as e:
            st.warning(f"AI generation failed for '{topic}' ({e}); used template fallback.")
            rows = template_generate(topic, co, n_mcq, n_short)
    else:
        rows = template_generate(topic, co, n_mcq, n_short)
    st.session_state.gen_cache[key] = rows
    return rows, False


# ---------------------------------------------------------------------------
# Sidebar - configuration
# ---------------------------------------------------------------------------
st.sidebar.title("⚙️ Configuration")
api_key = st.sidebar.text_input(
    "Anthropic API key (optional)",
    type="password",
    help="Leave blank to use the built-in template generator instead of live AI generation.",
)
n_mcq = st.sidebar.slider("MCQs per topic", 0, 15, 3)
n_short = st.sidebar.slider("Short-answer questions per topic", 0, 10, 1)
target_per_co = st.sidebar.slider("Target questions per CO (for balancing)", 3, 30, 10)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Repeat generations for the same topic + CO + count are served from an "
    "in-session cache instead of re-calling the model — avoids redundant "
    "API cost and keeps output consistent across tabs."
)

# ---------------------------------------------------------------------------
# Main - hero header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>📊 CO/PO-Aligned Assessment Generator</h1>
        <p>Bulk-map a syllabus to Course Outcomes, generate a deduplicated question bank,
        and get a data-driven recommendation on exactly how many more questions each CO needs.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs(["1️⃣ Course Index", "2️⃣ Question Bank", "3️⃣ Coverage Dashboard"])

# ---------------------------------------------------------------------------
# Tab 1: Course Index (Topic -> CO mapping) + bulk CSV import
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Course Index — Topic to Course Outcome Mapping")

    up_col, dl_col = st.columns([2, 1])
    with up_col:
        uploaded = st.file_uploader(
            "Bulk import a course index (CSV with 'Topic' and 'CO' columns)",
            type=["csv"],
        )
        if uploaded is not None:
            try:
                new_df = pd.read_csv(uploaded)
                assert {"Topic", "CO"}.issubset(new_df.columns)
                st.session_state.topics = new_df[["Topic", "CO"]]
                st.success(f"Imported {len(new_df)} topics from CSV.")
            except Exception:
                st.error("CSV must contain 'Topic' and 'CO' columns.")
    with dl_col:
        template_csv = pd.DataFrame(
            [{"Topic": "Your topic here", "CO": "CO1 - Your outcome here"}]
        ).to_csv(index=False)
        st.download_button("⬇️ Download CSV template", template_csv, "course_index_template.csv", "text/csv")

    st.write("Or edit directly below. Add/remove rows as needed — useful for a handful of topics; use CSV import above for a full semester at once.")
    edited = st.data_editor(
        st.session_state.topics,
        num_rows="dynamic",
        use_container_width=True,
        key="topic_editor",
    )
    st.session_state.topics = edited

    if st.button("🚀 Generate Question Bank from this Course Index", type="primary"):
        all_rows = []
        cache_hits = 0
        progress = st.progress(0.0, text="Starting...")
        rows_list = list(st.session_state.topics.iterrows())
        for i, (_, row) in enumerate(rows_list):
            topic, co = row.get("Topic"), row.get("CO")
            if not topic or not co or pd.isna(topic) or pd.isna(co):
                continue
            progress.progress((i + 1) / max(len(rows_list), 1), text=f"Processing: {topic}")
            rows, from_cache = generate_for_topic(topic, co, n_mcq, n_short, api_key)
            cache_hits += int(from_cache)
            all_rows.extend(rows)
        progress.empty()
        st.session_state.question_bank = pd.DataFrame(all_rows)
        msg = f"Generated {len(all_rows)} questions across {st.session_state.topics.shape[0]} topics."
        if cache_hits:
            msg += f" ({cache_hits} topic(s) served from cache — no redundant generation.)"
        st.success(msg + " Check the next tab.")

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

        c1, c2 = st.columns(2)
        with c1:
            buf = io.BytesIO()
            filtered.to_excel(buf, index=False, engine="openpyxl")
            st.download_button(
                "⬇️ Download Question Bank (Excel)",
                data=buf.getvalue(),
                file_name="question_bank.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        with c2:
            st.download_button(
                "⬇️ Download Question Bank (CSV)",
                data=filtered.to_csv(index=False),
                file_name="question_bank.csv",
                mime="text/csv",
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
        co_counts = qb.groupby("CO").size().reset_index(name="Question Count")

        # --- Top metric cards ---
        m1, m2, m3, m4 = st.columns(4)
        total_q = len(qb)
        total_co = qb["CO"].nunique()
        weak_count = (co_counts["Question Count"] < target_per_co).sum()
        avg_per_co = round(total_q / max(total_co, 1), 1)
        for col, val, label in zip(
            [m1, m2, m3, m4],
            [total_q, total_co, avg_per_co, weak_count],
            ["Total Questions", "COs Covered", "Avg Q / CO", "COs Below Target"],
        ):
            col.markdown(
                f'<div class="metric-card"><h2>{val}</h2><p>{label}</p></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.bar(co_counts, x="CO", y="Question Count", title="Questions per Course Outcome", color="CO")
            st.plotly_chart(fig1, use_container_width=True)

        with c2:
            diff_counts = qb.groupby("Difficulty").size().reset_index(name="Count")
            fig2 = px.pie(diff_counts, names="Difficulty", values="Count", title="Difficulty Distribution")
            st.plotly_chart(fig2, use_container_width=True)

        # --- Auto-balancing recommendation ---
        st.markdown("#### 🎯 Auto-Balance Recommendation")
        st.caption(f"Target: {target_per_co} questions per CO (adjustable in the sidebar).")
        co_counts["Needed"] = (target_per_co - co_counts["Question Count"]).clip(lower=0)
        needing_more = co_counts[co_counts["Needed"] > 0].sort_values("Needed", ascending=False)
        if needing_more.empty:
            st.success("Every CO already meets the target question count. Coverage is balanced.")
        else:
            for _, row in needing_more.iterrows():
                st.error(
                    f"**{row['CO']}** — has {row['Question Count']}, needs "
                    f"**{int(row['Needed'])} more** to hit the target of {target_per_co}."
                )

st.markdown("---")
st.caption(
    "Prototype tool — template mode works fully offline; add an Anthropic API key "
    "for live AI-generated questions. Repeat generations are cached in-session."
)
