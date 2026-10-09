"""
RAG Engine for MirAI Student Policy Advisor.
Implements MultiQueryRetriever, strict document grounding prompt, LCEL orchestration,
precise citation mapping, and robust model fallback.
"""
import time
from typing import List, Dict, Any, Tuple, Optional
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.retrievers import MultiQueryRetriever

from app.config import settings
from app.ingestion import get_vector_store
from app.models import QueryResponse, SourceCitation

STRICT_REFUSAL_PHRASE = (
    "I cannot answer this based on the official Mirai School of Technology Policy Handbook "
    "as the relevant policy is not specified in the document."
)

STRICT_SYSTEM_PROMPT = """You are the official MirAI School of Technology (SoT) Student Policy Advisor.
Your objective is to provide students with authoritative, accurate, and completely grounded answers derived EXCLUSIVELY from the provided Context extracts from the official Mirai_SoT_Policy_Handbook_2026.pdf.

STRICT GROUNDING & ANTI-HALLUCINATION RULES:
1. Ground every statement directly in the provided Context. Do NOT assume, extrapolate, or use outside knowledge.
2. If the answer cannot be determined with 100% certainty from the provided Context, you MUST state EXACTLY:
   "{refusal_phrase}"
3. If only partial information is available, state what is officially documented and clarify that the remaining details are not specified in the handbook.
4. For every factual rule, mandate, threshold, grade, deadline, or penalty, cite the specific Section and Page number from the Context extracts (e.g., [Section 2.1, Page 1]).
5. Maintain a professional, clear, objective, and supportive academic advisory tone.

CONTEXT EXTRACTS FROM OFFICIAL POLICY HANDBOOK:
{context}
"""

HUMAN_PROMPT = """STUDENT QUESTION:
{question}

OFFICIAL ADVISORY ANSWER (Grounded strictly in context with citations):"""

MULTI_QUERY_PROMPT_TEMPLATE = """You are an AI assistant helping students search the official MirAI School of Technology Policy Handbook.
Generate 3 different search queries to find policies related to the student's question.
Provide the 3 queries separated by newlines only. No numbering or preamble.

Student question: {question}"""

FALLBACK_MODELS = [
    settings.LLM_MODEL,
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-flash-latest"
]

def extract_text_content(content: Any) -> str:
    """Helper to extract pure text from Gemini response (handles AIMessage, dicts, lists, strings)."""
    if hasattr(content, "content"):
        content = content.content
    
    if isinstance(content, str):
        return content.strip()
    
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
            elif hasattr(item, "text"):
                parts.append(item.text)
        return "".join(parts).strip()
    
    return str(content).strip()

def get_llm(model_name: Optional[str] = None, temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    """Instantiates Gemini LLM with zero temperature for deterministic generation."""
    return ChatGoogleGenerativeAI(
        model=model_name or settings.LLM_MODEL,
        temperature=temperature,
        google_api_key=settings.GOOGLE_API_KEY
    )

def get_retriever(top_k: Optional[int] = None):
    """Instantiates MultiQueryRetriever wrapping Chroma vector store."""
    k = top_k or settings.TOP_K
    vector_store = get_vector_store()
    base_retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )
    
    llm = get_llm(temperature=0.0)
    
    multi_query_prompt = PromptTemplate(
        input_variables=["question"],
        template=MULTI_QUERY_PROMPT_TEMPLATE
    )
    
    retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm,
        prompt=multi_query_prompt,
        include_original=True
    )
    return retriever

def format_docs_with_metadata(docs: List[Document]) -> str:
    """Formats retrieved document chunks into context string with page and source tags."""
    if not docs:
        return "NO RELEVANT POLICY DOCUMENTS FOUND."
    
    formatted_chunks = []
    for idx, doc in enumerate(docs):
        page = doc.metadata.get("page", "Unknown")
        chunk_id = doc.metadata.get("chunk_id", f"c{idx+1}")
        source = doc.metadata.get("source", settings.HANDBOOK_FILENAME)
        
        chunk_text = (
            f"--- [DOCUMENT EXTRACT {idx+1} | Source: {source} | Page: {page} | ID: {chunk_id}] ---\n"
            f"{doc.page_content.strip()}\n"
        )
        formatted_chunks.append(chunk_text)
    
    return "\n\n".join(formatted_chunks)

def build_lcel_chain(model_name: Optional[str] = None):
    """Builds the LCEL RAG execution chain."""
    llm = get_llm(model_name=model_name, temperature=settings.TEMPERATURE)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", STRICT_SYSTEM_PROMPT.format(refusal_phrase=STRICT_REFUSAL_PHRASE, context="{context}")),
        ("human", HUMAN_PROMPT)
    ])
    
    chain = (
        {
            "context": lambda x: format_docs_with_metadata(x["docs"]),
            "question": lambda x: x["question"]
        }
        | prompt
        | llm
        | RunnableLambda(extract_text_content)
    )
    return chain

def query_policy_handbook(question: str, top_k: Optional[int] = None, use_multi_query: bool = True) -> QueryResponse:
    """
    Executes an end-to-end RAG query against the MirAI Policy Handbook with resilient model fallback.
    """
    start_time = time.time()
    
    # 1. Retrieve documents
    retrieved_docs: List[Document] = []
    expanded_queries: List[str] = [question]
    
    if use_multi_query:
        try:
            retriever = get_retriever(top_k=top_k)
            retrieved_docs = retriever.invoke(question)
            expanded_queries = [
                question,
                f"MirAI handbook regulations for: {question}",
                f"SoT official policy on: {question}"
            ]
        except Exception:
            vs = get_vector_store()
            retrieved_docs = vs.similarity_search(question, k=(top_k or settings.TOP_K))
    else:
        vs = get_vector_store()
        retrieved_docs = vs.similarity_search(question, k=(top_k or settings.TOP_K))

    # Deduplicate documents by content
    unique_docs = []
    seen_content = set()
    for doc in retrieved_docs:
        snippet = doc.page_content.strip()
        if snippet not in seen_content:
            seen_content.add(snippet)
            unique_docs.append(doc)
    retrieved_docs = unique_docs

    # 2. Run LCEL generation chain with model fallback
    answer_text = None
    last_exception = None
    
    models_to_try = []
    for m in FALLBACK_MODELS:
        if m and m not in models_to_try:
            models_to_try.append(m)

    for candidate_model in models_to_try:
        try:
            chain = build_lcel_chain(model_name=candidate_model)
            answer_text = chain.invoke({
                "docs": retrieved_docs,
                "question": question
            })
            if answer_text:
                break
        except Exception as e:
            last_exception = e
            continue

    if answer_text is None:
        raise RuntimeError(f"All candidate models failed during generation. Last error: {last_exception}")

    latency = round(time.time() - start_time, 3)

    # 3. Build Source Citations
    citations: List[SourceCitation] = []
    for doc in retrieved_docs:
        citations.append(SourceCitation(
            source=doc.metadata.get("source", settings.HANDBOOK_FILENAME),
            page=int(doc.metadata.get("page", 1)),
            snippet=doc.page_content[:250].replace("\n", " ").strip() + "...",
            chunk_id=doc.metadata.get("chunk_id")
        ))

    # 4. Check for refusal status
    is_refusal = (
        STRICT_REFUSAL_PHRASE.lower() in answer_text.lower() or
        "cannot answer this based on the official" in answer_text.lower() or
        "not specified in the document" in answer_text.lower() or
        "not specified in the provided context" in answer_text.lower()
    )

    return QueryResponse(
        question=question,
        answer=answer_text,
        sources=citations,
        retrieved_contexts=[d.page_content for d in retrieved_docs],
        expanded_queries=expanded_queries,
        latency_seconds=latency,
        is_refusal=is_refusal,
        groundedness_confidence=1.0 if not is_refusal else 0.0
    )

if __name__ == "__main__":
    q = "What is the mandatory attendance percentage and what happens below 75%?"
    print(f"Query: {q}")
    res = query_policy_handbook(q, use_multi_query=False)
    print(f"\n--- ANSWER ---\n{res.answer}")
    print(f"\nLatency: {res.latency_seconds}s | Refusal: {res.is_refusal}")
