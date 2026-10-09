"""
Centralized Configuration for MirAI Student Policy Advisor RAG System.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "MirAI Student Policy Advisor"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"

    # API Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY", ""))

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    CHROMA_DB_DIR: Path = BASE_DIR / "chroma_db"
    EVAL_CSV_PATH: Path = BASE_DIR / "rag_eval_scores.csv"
    HANDBOOK_FILENAME: str = "Mirai_SoT_Policy_Handbook_2026.pdf"

    # Ingestion & Chunking
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 80
    COLLECTION_NAME: str = "mirai_policy_handbook"

    # AI Models
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    LLM_MODEL: str = "gemini-flash-lite-latest"
    TEMPERATURE: float = 0.0

    # Retrieval
    TOP_K: int = 4
    MULTI_QUERY_COUNT: int = 3

    # Server Ports
    FASTAPI_PORT: int = 8000
    STREAMLIT_PORT: int = 8501

    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
