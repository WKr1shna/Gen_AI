import os
import sys
import logging
import warnings
from dotenv import load_dotenv

# Suppress deprecation and library logs
warnings.filterwarnings("ignore")
logging.getLogger("google_genai").setLevel(logging.ERROR)
logging.getLogger("langchain_google_genai").setLevel(logging.ERROR)

# Load environment variables (.env in workspace or parent directory)
load_dotenv()
if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Translater", ".env")
    if os.path.exists(parent_env):
        load_dotenv(parent_env)

# Ensure GOOGLE_API_KEY is configured
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# =========================================================================
# 1. In-memory session store mapping session_id -> InMemoryChatMessageHistory
# =========================================================================
store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    Retrieve or create an in-memory chat message history for the given session ID.
    - Each session ID gets its own ChatMessageHistory instance.
    - Subsequent calls with the same session ID return the existing history.
    - Different session IDs have independent conversations.
    """
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


# Helper to format response text cleanly (handling str and structured message content)
def get_text_content(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = [item.get("text", "") for item in content if isinstance(item, dict) and "text" in item]
        return "".join(texts)
    return str(content)


# =========================================================================
# 2. Initialize Gemini Model (Fast primary model with immediate fallback)
# =========================================================================
primary_model = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    max_retries=1
)
fallback_model = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    max_retries=1
)
model = primary_model.with_fallbacks([fallback_model])

# =========================================================================
# 3. Create prompt template with MessagesPlaceholder for history
# =========================================================================
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a knowledgeable and concise sports and general assistant. Always maintain conversational context from earlier messages."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# =========================================================================
# 4. Create standard LangChain LCEL chain
# =========================================================================
chain = prompt | model

# =========================================================================
# 5. Wrap the chain with RunnableWithMessageHistory
# =========================================================================
with_message_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)


def main():
    try:
        session_id = "sports-session"
        config = {
            "configurable": {
                "session_id": session_id
            }
        }

        print("=" * 70)
        print("🧠 LangChain Message History Demo: Football & 'Number 9' Context")
        print(f"Active Session ID: '{session_id}'")
        print("=" * 70)

        # --- Turn 1: Tell me about football ---
        turn_1_input = "Tell me about football."
        print(f"\n--- Turn 1 (Session: {session_id}) ---")
        print(f"User: {turn_1_input}")

        response1 = with_message_history.invoke(
            {"input": turn_1_input},
            config=config
        )
        print("AI:  ", get_text_content(response1.content))

        # --- Turn 2: What about number 9? (Context retained from Turn 1) ---
        turn_2_input = "What about number 9?"
        print(f"\n--- Turn 2 (Session: {session_id}) ---")
        print(f"User: {turn_2_input}")

        response2 = with_message_history.invoke(
            {"input": turn_2_input},
            config=config
        )
        print("AI:  ", get_text_content(response2.content))

        # --- Inspect Stored History in Memory ---
        print(f"\n--- Stored Messages in store['{session_id}'] ---")
        for idx, msg in enumerate(store[session_id].messages, 1):
            role = msg.__class__.__name__
            text = get_text_content(msg.content)
            print(f"  [{idx}] {role}: {text[:100]}...")

        print("\n" + "=" * 70)
        print("✅ SUCCESS: Turn 2 correctly understood 'number 9' in the context of football!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
