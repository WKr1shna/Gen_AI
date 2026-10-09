"""
Streamlit Frontend for MirAI Student Policy Advisor RAG System.
Features modern glassmorphism design, real-time query interface, source citations,
handbook ingestion hub, and LLM-as-a-judge evaluation dashboard.
"""
import os
import sys
import time
import pandas as pd
import requests
import streamlit as st
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.config import settings
from app.rag_engine import query_policy_handbook, STRICT_REFUSAL_PHRASE
from app.ingestion import ingest_handbook, get_db_stats, ensure_handbook_exists
from app.evaluator import run_evaluation_suite, BENCHMARK_TEST_CASES

# Page Configuration
st.set_page_config(
    page_title="MirAI Student Policy Advisor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern Glassmorphism Aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    /* Global Dark Gradient Background */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(15, 23, 42, 0.98) 0%, rgba(2, 6, 23, 1.0) 90%);
        color: #F8FAFC;
    }

    /* Custom Header Container */
    .hero-banner {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    .hero-title {
        font-size: 28px;
        font-weight: 700;
        background: linear-gradient(90deg, #60A5FA, #A78BFA, #38BDF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    
    .hero-subtitle {
        font-size: 14px;
        color: #94A3B8;
        margin: 0;
    }

    /* Metric Cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        backdrop-filter: blur(8px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(96, 165, 250, 0.4);
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #38BDF8;
        font-family: 'JetBrains Mono', monospace;
    }
    .metric-label {
        font-size: 12px;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 4px;
    }

    /* Citation Pill */
    .citation-badge {
        display: inline-block;
        background: rgba(59, 130, 246, 0.2);
        border: 1px solid rgba(96, 165, 250, 0.4);
        color: #93C5FD;
        font-size: 12px;
        font-weight: 500;
        padding: 4px 10px;
        border-radius: 20px;
        margin-right: 6px;
        margin-bottom: 6px;
    }

    /* Refusal Alert */
    .refusal-box {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(248, 113, 113, 0.4);
        border-radius: 10px;
        padding: 16px;
        color: #FCA5A5;
        font-size: 14px;
        margin: 12px 0;
    }

    /* Grounded Pill */
    .grounded-badge {
        background: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(74, 222, 128, 0.4);
        color: #86EFAC;
        font-size: 12px;
        padding: 4px 10px;
        border-radius: 12px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    /* Code & Mono blocks */
    code {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 13px !important;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        background-color: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(148, 163, 184, 0.1);
        color: #94A3B8;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(37, 99, 235, 0.3) !important;
        border-color: rgba(96, 165, 250, 0.6) !important;
        color: #F8FAFC !important;
    }
</style>
""", unsafe_allow_html=True)

# Top Hero Banner
st.markdown("""
<div class="hero-banner">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div class="hero-title">🎓 MirAI Student Policy Advisor</div>
            <p class="hero-subtitle">Strictly Grounded Multi-Query RAG Engine for School of Technology Policies (AY 2026–2027)</p>
        </div>
        <div style="text-align: right;">
            <span class="grounded-badge">🛡️ Strict Anti-Hallucination Enabled</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar System Health & Controls
with st.sidebar:
    st.markdown("### ⚙️ System Controls")
    
    # DB Status Check
    stats = get_db_stats()
    indexed_count = stats.get("indexed_chunks", 0)
    
    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 10px; padding: 12px; margin-bottom: 15px;">
        <div style="font-size: 11px; color: #94A3B8; text-transform: uppercase;">Vector Store Status</div>
        <div style="font-size: 16px; font-weight: 600; color: {'#4ADE80' if indexed_count > 0 else '#F87171'};">
            ● {'Indexed (' + str(indexed_count) + ' Chunks)' if indexed_count > 0 else 'Database Empty'}
        </div>
        <div style="font-size: 11px; color: #CBD5E1; margin-top: 4px;">
            Doc: <code>{settings.HANDBOOK_FILENAME}</code>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🤖 Model Specifications")
    st.text(f"LLM: {settings.LLM_MODEL}")
    st.text(f"Embeddings: {settings.EMBEDDING_MODEL.split('/')[-1]}")
    st.text("Temperature: 0.0 (Strict)")

    st.markdown("---")
    st.markdown("#### 🔄 Ingestion Management")
    if st.button("⚡ Re-Index Handbook PDF", use_container_width=True):
        with st.spinner("Processing PDF and populating ChromaDB..."):
            res = ingest_handbook(force_reingest=True)
            st.success(f"Indexed {res.get('chunks_created')} chunks!")
            time.sleep(1)
            st.rerun()

    st.markdown("---")
    st.markdown("#### 📖 Handbook Sections Index")
    sections = [
        "1. Academic Credits (20-26/sem, 160 total)",
        "2. Attendance (85% min, 75-84% condonation)",
        "3. Grading Scale & Probation (Min 5.0 CGPA)",
        "4. AI & Plagiarism Policy (<10% ok, >25% SDC)",
        "5. Hackathons & 8th Sem Internship (7.5 CGPA)",
        "6. Hostel Curfew (9:30 PM / 10:30 PM)",
        "7. Scholarship (8.5 CGPA) & Fee Refund",
        "8. Grievance Redressal (14 days timeline)"
    ]
    for s in sections:
        st.caption(f"• {s}")

# Main Tabs
tab1, tab2, tab3 = st.tabs([
    "💬 Policy Advisory Console",
    "📊 LLM-as-a-Judge Benchmark",
    "📚 Document Ingestion & Chunks"
])

# -------------------------------------------------------------
# TAB 1: Policy Advisory Console (Chat & Search)
# -------------------------------------------------------------
with tab1:
    st.markdown("#### Ask Any Academic Policy Question")
    st.caption("Answers are synthesized exclusively from the official Policy Handbook with precise citations and strict refusal for out-of-scope inquiries.")

    # Preset Questions for Quick Testing
    preset_cols = st.columns(4)
    preset_q = None
    with preset_cols[0]:
        if st.button("📋 Attendance & Condonation", use_container_width=True):
            preset_q = "What is the minimum attendance required for exams and how does medical condonation work?"
    with preset_cols[1]:
        if st.button("💼 8th Sem Internship Rule", use_container_width=True):
            preset_q = "What are the eligibility criteria and minimum CGPA for an 8th-semester industry internship?"
    with preset_cols[2]:
        if st.button("💰 Scholarship Retention", use_container_width=True):
            preset_q = "What CGPA must I maintain to keep my merit scholarship, and are backlogs permitted?"
    with preset_cols[3]:
        if st.button("🚫 Out-of-Scope Test (Refusal)", use_container_width=True):
            preset_q = "What is the dress code and DJ rules for swimming pool parties on campus?"

    # Query Input
    user_query = st.text_input(
        "Enter your student inquiry:",
        value=preset_q if preset_q else "",
        placeholder="e.g., What happens if my course similarity index is 18%?",
        key="query_input"
    )

    col_btn, col_opt1, col_opt2 = st.columns([2, 2, 2])
    with col_btn:
        submit_query = st.button("🔍 Search Policy Handbook", type="primary", use_container_width=True)
    with col_opt1:
        use_multi = st.checkbox("MultiQuery Expansion", value=True, help="Generates 3 query variations for higher recall")
    with col_opt2:
        top_k_val = st.slider("Retrieved Context Chunks", min_value=2, max_value=8, value=4)

    if submit_query and user_query.strip():
        with st.spinner("Retrieving handbook clauses and generating strict grounded answer..."):
            try:
                res = query_policy_handbook(
                    question=user_query.strip(),
                    top_k=top_k_val,
                    use_multi_query=use_multi
                )

                st.markdown("---")
                
                # Header Status Banner
                if res.is_refusal:
                    st.markdown("""
                    <div class="refusal-box">
                        <b>⚠️ Unspecified Policy / Out-of-Scope:</b> The question cannot be answered from the official MirAI Policy Handbook. System deterministically refused to extrapolate or hallucinate.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="margin-bottom: 12px;">
                        <span class="grounded-badge">✅ Verified Grounded Answer</span>
                        <span style="font-size: 12px; color: #94A3B8; margin-left: 12px;">Generated in <b>""" + str(res.latency_seconds) + """s</b></span>
                    </div>
                    """, unsafe_allow_html=True)

                # Advisory Answer Body
                st.markdown("### 📜 Official Policy Advisory Response")
                st.markdown(res.answer)

                # Citations Section
                if res.sources:
                    st.markdown("#### 📌 Policy Handbook Citations")
                    cit_cols = st.columns(min(len(res.sources), 4))
                    for idx, src in enumerate(res.sources):
                        with cit_cols[idx % 4]:
                            st.markdown(f"""
                            <div class="metric-card" style="text-align: left; padding: 12px; margin-bottom: 10px;">
                                <div style="font-size: 11px; color: #60A5FA; font-weight: 600;">{src.source}</div>
                                <div style="font-size: 14px; font-weight: 700; color: #F8FAFC;">Page {src.page} ({src.chunk_id})</div>
                                <div style="font-size: 11px; color: #94A3B8; margin-top: 4px; line-height: 1.3;">{src.snippet}</div>
                            </div>
                            """, unsafe_allow_html=True)

                # Expanded Queries & Context Inspector
                with st.expander("🔍 Inspect Query Expansion & Raw Context Chunks"):
                    if res.expanded_queries:
                        st.markdown("**MultiQuery Expansion Variations:**")
                        for eq in res.expanded_queries:
                            st.markdown(f"- `{eq}`")
                    
                    st.markdown("**Retrieved Context Chunks Fed to LLM:**")
                    for c_idx, ctx in enumerate(res.retrieved_contexts):
                        st.text_area(f"Chunk #{c_idx+1}", ctx, height=120, disabled=True)

            except Exception as e:
                st.error(f"Error executing policy query: {str(e)}")

# -------------------------------------------------------------
# TAB 2: LLM-as-a-Judge Evaluation Dashboard
# -------------------------------------------------------------
with tab2:
    st.markdown("#### 🎯 LLM-as-a-Judge Automated Benchmark Suite")
    st.caption("Evaluates the RAG pipeline on Faithfulness, Answer Relevance, Context Precision, Groundedness, and Refusal Accuracy across standardized test cases.")

    eval_col1, eval_col2 = st.columns([2, 4])
    with eval_col1:
        run_eval_btn = st.button("🚀 Run Full Benchmark (12 Test Cases)", type="primary", use_container_width=True)
    with eval_col2:
        st.info("Results are computed using temperature 0.0 deterministic evaluation and saved to `rag_eval_scores.csv`.")

    csv_path = settings.EVAL_CSV_PATH

    if run_eval_btn:
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("Starting benchmark evaluation...")
        
        with st.spinner("Executing queries and LLM-as-a-judge assessments..."):
            summary = run_evaluation_suite(use_multi_query=False)
            progress_bar.progress(100)
            status_text.text("Benchmark complete!")
            st.success("Evaluation completed and scores saved to `rag_eval_scores.csv`!")

    # Display results if CSV exists
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        
        # Metric Cards Row
        st.markdown("### 📈 Overall Benchmark Summary")
        m_col1, m_col2, m_col3, m_col4, m_col5, m_col6 = st.columns(6)
        
        avg_faith = df["faithfulness_score"].mean() * 100
        avg_rel = df["answer_relevance_score"].mean() * 100
        avg_prec = df["context_precision_score"].mean() * 100
        grounded_pct = (df["grounded"].sum() / len(df)) * 100
        refusal_pct = (df["refusal_accurate"].sum() / len(df)) * 100
        avg_lat = df["latency_seconds"].mean()

        with m_col1:
            st.markdown(f"""<div class="metric-card"><div class="metric-value">{avg_faith:.1f}%</div><div class="metric-label">Faithfulness</div></div>""", unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"""<div class="metric-card"><div class="metric-value">{avg_rel:.1f}%</div><div class="metric-label">Relevance</div></div>""", unsafe_allow_html=True)
        with m_col3:
            st.markdown(f"""<div class="metric-card"><div class="metric-value">{avg_prec:.1f}%</div><div class="metric-label">Context Precision</div></div>""", unsafe_allow_html=True)
        with m_col4:
            st.markdown(f"""<div class="metric-card"><div class="metric-value">{grounded_pct:.1f}%</div><div class="metric-label">Groundedness</div></div>""", unsafe_allow_html=True)
        with m_col5:
            st.markdown(f"""<div class="metric-card"><div class="metric-value">{refusal_pct:.1f}%</div><div class="metric-label">Refusal Accuracy</div></div>""", unsafe_allow_html=True)
        with m_col6:
            st.markdown(f"""<div class="metric-card"><div class="metric-value">{avg_lat:.2f}s</div><div class="metric-label">Avg Latency</div></div>""", unsafe_allow_html=True)

        st.markdown("---")
        
        # Download Button
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download rag_eval_scores.csv",
            data=csv_data,
            file_name="rag_eval_scores.csv",
            mime="text/csv"
        )

        # Detailed Table
        st.markdown("#### 📋 Test Case Breakdown")
        display_df = df[[
            "test_id", "query", "is_refusal_expected", "is_refusal_observed",
            "faithfulness_score", "answer_relevance_score", "context_precision_score",
            "grounded", "latency_seconds", "judge_reasoning"
        ]]
        st.dataframe(display_df, use_container_width=True)

        # Answers Inspector
        with st.expander("🔬 View Generated Answers & Judge Reasoning for each Test"):
            for _, row in df.iterrows():
                st.markdown(f"**[{row['test_id']}]** `{row['query']}`")
                st.markdown(f"- **Expected Topic:** {row['expected_policy_topic']}")
                st.markdown(f"- **Generated Answer:**\n> {row['generated_answer']}")
                st.markdown(f"- **Judge Reasoning:** *{row['judge_reasoning']}*")
                st.markdown(f"- **Scores:** Faithfulness: `{row['faithfulness_score']}` | Relevance: `{row['answer_relevance_score']}` | Precision: `{row['context_precision_score']}` | Latency: `{row['latency_seconds']}s`")
                st.markdown("---")
    else:
        st.warning("No evaluation scores recorded yet. Click 'Run Full Benchmark' to evaluate the system.")

# -------------------------------------------------------------
# TAB 3: Document Ingestion & Chunks Explorer
# -------------------------------------------------------------
with tab3:
    st.markdown("#### 📚 Document Ingestion & Chunking Architecture")
    st.caption("Inspect how the official policy handbook PDF is loaded, split via RecursiveCharacterTextSplitter, and embedded.")

    ensure_handbook_exists()
    handbook_path = settings.DATA_DIR / settings.HANDBOOK_FILENAME

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Handbook Document", settings.HANDBOOK_FILENAME)
    with c2:
        st.metric("ChromaDB Collection", settings.COLLECTION_NAME)
    with c3:
        st.metric("Total Indexed Chunks", get_db_stats().get("indexed_chunks", 0))

    st.markdown("---")
    st.markdown("#### 🔧 Ingestion Technical Parameters")
    tech_params = [
        {"Parameter": "Loader", "Value": "PyPDFLoader (LangChain)"},
        {"Parameter": "Text Splitter", "Value": "RecursiveCharacterTextSplitter"},
        {"Parameter": "Chunk Size", "Value": f"{settings.CHUNK_SIZE} characters"},
        {"Parameter": "Chunk Overlap", "Value": f"{settings.CHUNK_OVERLAP} characters"},
        {"Parameter": "Embedding Model", "Value": settings.EMBEDDING_MODEL},
        {"Parameter": "Vector Store", "Value": "ChromaDB (Persistent)"},
        {"Parameter": "Orchestration Pipeline", "Value": "LangChain Expression Language (LCEL)"},
        {"Parameter": "Query Expansion", "Value": "MultiQueryRetriever (LangChain)"},
        {"Parameter": "LLM Temperature", "Value": "0.0 (Deterministic Generation)"},
    ]
    st.table(pd.DataFrame(tech_params))

    st.markdown("---")
    st.markdown("#### 📄 Document Location & Replacement Instructions")
    st.markdown(f"""
    To replace or update the official Policy Handbook:
    1. Place your official PDF at: `data/{settings.HANDBOOK_FILENAME}`
    2. Click the **Re-Index Handbook PDF** button in the sidebar.
    3. The ingestion pipeline will extract text, regenerate vector embeddings, and update ChromaDB automatically.
    """)
