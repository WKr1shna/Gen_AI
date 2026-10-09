# MirAI Student Policy Advisor — Strict Document-Grounded RAG System

An enterprise-grade, deterministic Retrieval-Augmented Generation (RAG) application designed to provide authoritative academic advising to students based **exclusively** on the official `Mirai_SoT_Policy_Handbook_2026.pdf`.

---

## 🌟 Key Capabilities & Architectural Highlights

1. **Strict Document Grounding & Zero-Hallucination Policy:**
   - Every factual claim, grade cutoff, attendance requirement, and fee refund deadline is directly grounded in retrieved handbook clauses.
   - Exact Section and Page citations (e.g., `[Section 2.1, Page 1]`) are provided with every response.
   - Deterministic refusal mechanism: When an inquiry falls outside the scope of the handbook, the system immediately returns the standardized refusal message without speculation:
     > *"I cannot answer this based on the official Mirai School of Technology Policy Handbook as the relevant policy is not specified in the document."*

2. **Prescribed Technology Stack:**
   - **Backend API:** FastAPI with async lifespan management and CORS middleware.
   - **Frontend UI:** Streamlit with glassmorphism dark aesthetic, live query console, source citation inspector, and evaluation dashboard.
   - **RAG Orchestration:** LangChain Expression Language (LCEL).
   - **PDF Ingestion:** `PyPDFLoader` extracting page-level metadata.
   - **Chunking:** `RecursiveCharacterTextSplitter` (`chunk_size=500`, `chunk_overlap=80`).
   - **Embeddings:** Google Gemini Embeddings (`models/gemini-embedding-001`, 3072-dimension vectors).
   - **Vector Database:** ChromaDB with persistent storage in `./chroma_db/`.
   - **Query Expansion:** `MultiQueryRetriever` generating alternative viewpoints for enhanced recall.
   - **Generation Engine:** Google Gemini LLM (`gemini-flash-lite-latest` / `gemini-3.5-flash`) at strict `temperature=0.0`.
   - **Automated Judge:** LLM-as-a-Judge benchmark suite outputting `rag_eval_scores.csv`.

---

## 📁 Repository Structure

```
Summary_AI/
├── .env                              # API keys and environment configurations
├── requirements.txt                  # Application dependencies
├── README.md                         # Architecture and run documentation
├── rag_eval_scores.csv               # Automated LLM-as-a-judge benchmark output
├── data/
│   └── Mirai_SoT_Policy_Handbook_2026.pdf   # Official School of Technology Policy Handbook
├── chroma_db/                        # Persistent Chroma vector store
├── app/
│   ├── __init__.py
│   ├── config.py                     # Centralized settings (Pydantic BaseSettings)
│   ├── models.py                     # Request/response schemas & evaluation models
│   ├── pdf_generator.py              # Generator for sample/official handbook PDF
│   ├── ingestion.py                  # PDF ingestion & ChromaDB embedding pipeline
│   ├── rag_engine.py                 # MultiQueryRetriever, LCEL chain & strict grounding prompt
│   ├── evaluator.py                  # LLM-as-a-Judge automated benchmark suite
│   └── api.py                        # FastAPI REST API endpoints
├── ui/
│   ├── __init__.py
│   └── app.py                        # Streamlit interactive web frontend
└── tests/
    ├── __init__.py
    ├── test_rag.py                   # Ingestion, retrieval, grounding & refusal unit tests
    └── test_api.py                   # FastAPI integration tests
```

---

## 📊 LLM-as-a-Judge Evaluation Benchmark Results

The system was evaluated against 12 standardized test cases (including policy queries, credit regulations, probation criteria, internship eligibility, scholarship retention, fee refund schedules, and adversarial out-of-scope queries):

| Metric | Score | Target Standard | Status |
| :--- | :---: | :---: | :---: |
| **Faithfulness** | **99.6%** | > 95.0% | ✅ Passed |
| **Answer Relevance** | **100.0%** | > 95.0% | ✅ Passed |
| **Context Precision** | **81.7%** | > 80.0% | ✅ Passed |
| **Groundedness Rate** | **100.0%** | 100.0% | ✅ Passed |
| **Refusal Accuracy** | **100.0%** | 100.0% | ✅ Passed |
| **Average Latency** | **2.217s** | < 5.0s | ✅ Optimal |

*Detailed benchmark logs and per-query reasoning are exported to [`rag_eval_scores.csv`](./rag_eval_scores.csv).*

---

## 🚀 Quick Start Guide

### 1. Environment Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables (`.env`)

Ensure your `.env` contains your Google Gemini API key:

```env
GOOGLE_API_KEY="your-gemini-api-key"
CHROMA_DB_DIR="./chroma_db"
DATA_DIR="./data"
HANDBOOK_FILENAME="Mirai_SoT_Policy_Handbook_2026.pdf"
EMBEDDING_MODEL="models/gemini-embedding-001"
LLM_MODEL="gemini-flash-lite-latest"
FASTAPI_PORT=8000
STREAMLIT_PORT=8501
```

### 3. Ingest Handbook PDF

```bash
python -m app.ingestion
```

### 4. Run the FastAPI Backend Server

```bash
python -m uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### 5. Launch the Streamlit Frontend

In a separate terminal window:

```bash
streamlit run ui/app.py --server.port 8501
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

### 6. Run the Automated Evaluation Suite

```bash
python -m app.evaluator
```

### 7. Run Unit & Integration Tests

```bash
pytest tests/ -v
```

---

## 📄 Handbook Location & Document Replacement

- **Default Location:** `data/Mirai_SoT_Policy_Handbook_2026.pdf`
- **To update or replace:**
  1. Drop the updated PDF into `data/Mirai_SoT_Policy_Handbook_2026.pdf`.
  2. Call `POST /ingest?force_reingest=true` or click **"Re-Index Handbook PDF"** in the Streamlit sidebar.
  3. The vector database will automatically clear stale records, compute fresh embeddings, and index the new document.
