"""
FastAPI Server for Semantic Routing & Guardrails with Real-Time Token Analytics.
Serves interactive Web UI and REST API endpoints.
"""

import os
import sys
import time
import logging
import warnings
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Suppress logs
warnings.filterwarnings("ignore")
logging.getLogger("google_genai").setLevel(logging.ERROR)
logging.getLogger("langchain_google_genai").setLevel(logging.ERROR)

# Load environment variables
load_dotenv()
if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    parent_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(parent_env):
        load_dotenv(parent_env)
    alt_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fastapi-word-counter", ".env")
    if os.path.exists(alt_env):
        load_dotenv(alt_env)

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
    os.environ["GEMINI_API_KEY"] = api_key

# Import core pipeline components
from main import (
    classifier_chain,
    toxic_chain,
    code_chain,
    general_chain,
    model,
    StrOutputParser
)
from chat_history import (
    get_session_history,
    store,
    clear_session_history,
    get_text_content,
    get_history_summary,
    format_history_context
)
from token_tracker import TokenTracker

# Initialize Global Tracker
global_tracker = TokenTracker()

app = FastAPI(title="LangChain Semantic Routing & Guardrails API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default-session"


class ResetRequest(BaseModel):
    session_id: Optional[str] = "default-session"


@app.get("/")
async def serve_ui():
    """Serve the Web UI."""
    index_path = os.path.join(CURRENT_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "ok", "message": "Guardrail API is running."}


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """
    Process chat message through Semantic Router & Guardrails:
    1. Runs intent classifier
    2. Routes to toxic_chain, code_chain, or general_chain
    3. Retains multi-turn conversation context
    4. Computes token breakdown and latency metrics
    """
    user_input = req.message.strip()
    session_id = req.session_id or "default-session"

    if not user_input:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    global_tracker.start_turn(user_input)

    history_obj = get_session_history(session_id)
    history_messages = history_obj.messages
    history_context = format_history_context(session_id)

    config = {
        "configurable": {"session_id": session_id},
        "callbacks": [global_tracker.callback_handler]
    }

    try:
        # Step 1: Semantic Intent Classification
        classified_topic = classifier_chain.invoke(
            {"input": user_input, "history_context": history_context},
            config=config
        )

        # Step 2: Route Execution
        if classified_topic == "TOXIC":
            response_text = toxic_chain.invoke({"input": user_input})
            # We do NOT save toxic interactions in assistant conversation history
        elif classified_topic == "CODE_REQUEST":
            resp = code_chain.invoke(
                {"input": user_input, "history": history_messages},
                config=config
            )
            response_text = get_text_content(resp)
            history_obj.add_user_message(user_input)
            history_obj.add_ai_message(response_text)
        else:  # GENERAL
            resp = general_chain.invoke(
                {"input": user_input, "history": history_messages},
                config=config
            )
            response_text = get_text_content(resp)
            history_obj.add_user_message(user_input)
            history_obj.add_ai_message(response_text)

        # Finalize turn metrics
        turn_metrics = global_tracker.end_turn(response_text, classified_topic)

        # Prepare summary of conversation history
        history_summary = get_history_summary(session_id)

        return {
            "response": response_text,
            "route": classified_topic,
            "session_id": session_id,
            "turn_metrics": turn_metrics,
            "session_stats": global_tracker.session_stats,
            "history": history_summary
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reset")
async def reset_session(req: ResetRequest):
    """Reset session chat history."""
    session_id = req.session_id or "default-session"
    clear_session_history(session_id)
    return {"status": "success", "message": f"Session '{session_id}' cleared."}


@app.get("/api/stats")
async def get_session_stats():
    """Retrieve cumulative session metrics."""
    return global_tracker.session_stats


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    print(f"🚀 Starting Semantic Router & Guardrail Server on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
