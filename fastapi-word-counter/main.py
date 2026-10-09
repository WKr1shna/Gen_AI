import os
import time
import logging
import warnings
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from langchain_core.callbacks import BaseCallbackHandler

# Import shared RunnableWithMessageHistory, store, get_session_history from chat_history
from chat_history import (
    with_message_history,
    store,
    get_session_history,
    get_text_content
)

warnings.filterwarnings("ignore")
logging.getLogger("google_genai").setLevel(logging.ERROR)
logging.getLogger("langchain_google_genai").setLevel(logging.ERROR)

# Load environment variables
load_dotenv()
if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Translater", ".env")
    if os.path.exists(parent_env):
        load_dotenv(parent_env)

import contextvars

# Context variable for request-scoped token tracking
request_token_usage = contextvars.ContextVar("request_token_usage", default=None)


class TokenUsageCallbackHandler(BaseCallbackHandler):
    """LangChain callback handler to capture token usage per request."""
    def on_llm_end(self, response, **kwargs):
        ctx = request_token_usage.get()
        if ctx is None:
            return
        
        # Check generation message usage metadata
        for gen_list in response.generations:
            for gen in gen_list:
                msg = getattr(gen, "message", None)
                usage = getattr(msg, "usage_metadata", None)
                if usage:
                    ctx["prompt_tokens"] += usage.get("input_tokens", 0)
                    ctx["completion_tokens"] += usage.get("output_tokens", 0)
                    ctx["total_tokens"] += usage.get("total_tokens", 0)
                    ctx["calls"] += 1


# Global session metrics tracker
session_stats = {
    "total_requests": 0,
    "cumulative_total_tokens": 0,
    "cumulative_prompt_tokens": 0,
    "cumulative_completion_tokens": 0,
    "cumulative_words": 0
}


app = FastAPI(title="Technical Jargon & Conversational AI API")

# Enable CORS for local development and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Process-Time",
        "X-Prompt-Tokens",
        "X-Completion-Tokens",
        "X-Total-Tokens",
        "X-Tokens-Per-Word",
        "X-Avg-Tokens-Per-Request",
        "X-Total-Requests"
    ]
)


# Middleware: track token usage per request and attach headers
@app.middleware("http")
async def track_token_usage_middleware(request: Request, call_next):
    # Initialize token counter for this request
    token_stats = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "calls": 0,
        "words": 0
    }
    token = request_token_usage.set(token_stats)
    
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        process_time = time.perf_counter() - start_time
        stats = request_token_usage.get()
        request_token_usage.reset(token)

    # Calculate metrics
    words = stats.get("words", 0)
    tokens_per_word = round(stats["total_tokens"] / words, 2) if words > 0 else 0.0

    if stats["total_tokens"] > 0:
        session_stats["total_requests"] += 1
        session_stats["cumulative_total_tokens"] += stats["total_tokens"]
        session_stats["cumulative_prompt_tokens"] += stats["prompt_tokens"]
        session_stats["cumulative_completion_tokens"] += stats["completion_tokens"]
        session_stats["cumulative_words"] += words

    avg_tokens_req = (
        round(session_stats["cumulative_total_tokens"] / session_stats["total_requests"], 2)
        if session_stats["total_requests"] > 0 else 0.0
    )

    # Attach response headers
    response.headers["X-Process-Time"] = f"{process_time:.6f}s"
    response.headers["X-Prompt-Tokens"] = str(stats["prompt_tokens"])
    response.headers["X-Completion-Tokens"] = str(stats["completion_tokens"])
    response.headers["X-Total-Tokens"] = str(stats["total_tokens"])
    response.headers["X-Tokens-Per-Word"] = str(tokens_per_word)
    response.headers["X-Avg-Tokens-Per-Request"] = str(avg_tokens_req)
    response.headers["X-Total-Requests"] = str(session_stats["total_requests"])

    # Server-side terminal logging
    if stats["total_tokens"] > 0:
        req_num = session_stats["total_requests"]
        avg_word = (
            round(session_stats["cumulative_total_tokens"] / session_stats["cumulative_words"], 2)
            if session_stats["cumulative_words"] > 0 else 0.0
        )
        print("\n" + "=" * 62, flush=True)
        print(f" 🚀 [SERVER-SIDE METRICS] Request #{req_num}: {request.method} {request.url.path}", flush=True)
        print("=" * 62, flush=True)
        print(f"  ⏱️  Latency:        {process_time:.4f}s (HTTP {response.status_code})", flush=True)
        print(f"  ⚡ Tokens Spent:   {stats['total_tokens']} total ({stats['prompt_tokens']} prompt + {stats['completion_tokens']} completion)", flush=True)
        print(f"  📝 Tokens / Word:  {tokens_per_word} t/w ({words} words total)", flush=True)
        print("  " + "-" * 58, flush=True)
        print(f"  📊 Session Total:  {session_stats['cumulative_total_tokens']} tokens across {req_num} requests", flush=True)
        print(f"  📈 Avg Tokens/Req: {avg_tokens_req} tokens/request", flush=True)
        print(f"  📈 Avg Tokens/Word:{avg_word} tokens/word", flush=True)
        print("=" * 62 + "\n", flush=True)
    else:
        print(f"[{request.method}] {request.url.path} - HTTP {response.status_code} in {process_time:.4f}s", flush=True)

    return response


# Serve Frontend UI
@app.get("/", response_class=FileResponse)
def serve_frontend():
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "index.html not found"}


# Existing endpoints
@app.get("/health")
def health_check():
    return {
        "status": "Server is running"
    }


@app.post("/word-count")
def word_count(text: str):
    words = text.split()
    return {
        "word_count": len(words)
    }


class TranslateRequest(BaseModel):
    jargon: Optional[str] = None
    input: Optional[str] = None
    session_id: Optional[str] = "sports-session"


# POST /translate endpoint using RunnableWithMessageHistory
@app.post("/translate")
async def translate(request: TranslateRequest):
    try:
        user_input = request.input or request.jargon or ""
        session_id = request.session_id or "sports-session"

        # Diagnostic logging required for session verification
        print("\n" + "=" * 62, flush=True)
        print(f"🧠 [CONVERSATION TURN] Session ID: {session_id}", flush=True)
        print("SESSION ID:", session_id, flush=True)
        history_before = get_session_history(session_id).messages
        print("HISTORY BEFORE:", history_before, flush=True)
        print("USER INPUT:", user_input, flush=True)
        print("=" * 62, flush=True)

        # Asynchronously execute the pipeline with token callback handler
        callback = TokenUsageCallbackHandler()
        config = {
            "configurable": {
                "session_id": session_id
            },
            "callbacks": [callback]
        }

        # Invoke through the shared RunnableWithMessageHistory
        response = await with_message_history.ainvoke(
            {"input": user_input},
            config=config
        )

        translated = get_text_content(response.content if hasattr(response, "content") else response)

        history_after = get_session_history(session_id).messages
        print("\n" + "-" * 62, flush=True)
        print("HISTORY AFTER:", history_after, flush=True)
        print(f"Stored message count for session '{session_id}': {len(history_after)}", flush=True)
        print("-" * 62 + "\n", flush=True)
        
        # Calculate word counts for metrics
        prompt_words = len(user_input.split())
        output_words = len(translated.split())
        total_words = prompt_words + output_words

        stats = request_token_usage.get() or {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "words": 0
        }
        stats["words"] = total_words

        return {
            "translation": translated,
            "response": translated,
            "session_id": session_id,
            "history_length": len(history_after),
            "token_usage": {
                "prompt_tokens": stats.get("prompt_tokens", 0),
                "completion_tokens": stats.get("completion_tokens", 0),
                "total_tokens": stats.get("total_tokens", 0),
            }
        }
    except Exception as e:
        print(f"❌ Error in /translate: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)