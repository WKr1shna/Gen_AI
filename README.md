# Generative AI Coursework & Projects

This repository contains practical implementations, architectures, and assignments for GenAI topics including RAG (Retrieval-Augmented Generation), semantic guardrails & routing, dynamic context compression, and LLM-powered backend services.

---

## 📁 Repository Overview

| Directory | Description | Stack / Key Tech |
| :--- | :--- | :--- |
| [`Summary_AI`](./Summary_AI) | **MirAI Student Policy Advisor** — Deterministic, zero-hallucination RAG system grounded on university policy handbooks with MultiQuery retrieval and LLM-as-a-judge evaluation suite. | FastAPI, Streamlit, LangChain, ChromaDB, Gemini |
| [`guardrail`](./guardrail) | **Semantic Router & Guardrails** — Guardrail system with dynamic token tracking, real-time safety classification, input validation, and conversational chat history. | FastAPI, Gemini API, HTML/JS frontend |
| [`Dim_context`](./Dim_context) | **Context Engineering & Dimension Reducer** — Techniques for dynamic context management, document chunking, and semantic vector representations. | FastAPI, LangChain, ChromaDB, PyPDF |
| [`fastapi-word-counter`](./fastapi-word-counter) | **FastAPI Word Counter & Assistant** — Lightweight LLM-assisted text analyzer with conversation memory. | FastAPI, Groq, Gemini API |

---

## 🚀 Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/WKr1shna/Gen_AI.git
   cd Gen_AI
   ```

2. **Setup environment variables:**
   Each project contains its own `.env.example` file. Copy it to `.env` and fill in your API keys (e.g. `GOOGLE_API_KEY`, `GEMINI_API_KEY`):
   ```bash
   cp Summary_AI/.env.example Summary_AI/.env
   cp guardrail/.env.example guardrail/.env
   cp Dim_context/.env.example Dim_context/.env
   cp fastapi-word-counter/.env.example fastapi-word-counter/.env
   ```

3. **Explore individual projects:**
   Check the `README.md` within each project folder for specific installation instructions, dependency management, and run commands.
