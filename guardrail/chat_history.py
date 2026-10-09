"""
Chat History and Conversation Context Management.
Maintains in-memory message history for multi-turn conversational context.
"""

from typing import Dict, List, Any
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

# In-memory session store mapping session_id -> InMemoryChatMessageHistory
store: Dict[str, InMemoryChatMessageHistory] = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    Retrieve or initialize an in-memory chat message history for the given session ID.
    - Each session ID maintains its own independent conversation history.
    - Enables context retention across multiple turns.
    """
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


def get_text_content(content: Any) -> str:
    """
    Safely extract string content from various message content representations
    (strings, lists of content dicts, etc.).
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = [
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        ]
        return "".join(texts)
    return str(content)


def clear_session_history(session_id: str) -> None:
    """Clear message history for a specific session."""
    if session_id in store:
        store[session_id].clear()


def get_history_summary(session_id: str) -> List[Dict[str, str]]:
    """Return a clean list of message summaries in a session."""
    if session_id not in store:
        return []
    
    summary = []
    for msg in store[session_id].messages:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant" if isinstance(msg, AIMessage) else "System"
        summary.append({
            "role": role,
            "content": get_text_content(msg.content)
        })
    return summary


def format_history_context(session_id: str, max_messages: int = 4) -> str:
    """Format recent turns as a compact context string for intent classification."""
    if session_id not in store:
        return "None"
    msgs = store[session_id].messages[-max_messages:]
    if not msgs:
        return "None"
    lines = []
    for msg in msgs:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        content = get_text_content(msg.content).strip().replace("\n", " ")
        lines.append(f"{role}: {content[:90]}")
    return " | ".join(lines)

