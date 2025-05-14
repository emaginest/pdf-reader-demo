"""
Configuration settings for the application.
"""

import os
from typing import Any, Optional

# Import for Pydantic v2
from pydantic import field_validator
from pydantic_settings import BaseSettings


class VectorStoreSettings(BaseSettings):
    """Settings for the vector store."""

    collection_name: str = "pdf_documents"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    chunk_method: str = "recursive"
    search_limit: int = 10  # Increased from 5 to 10 for better context
    embedding_model: str = "text-embedding-ada-002"

    # PDF processing settings
    max_pages: int = 100  # Maximum number of pages to process (0 for unlimited)
    page_batch_size: int = 10  # Process pages in batches
    max_chunks_per_batch: int = 50  # Process chunks in batches
    chunk_method: str = (
        "incremental"  # Method for chunking text ('incremental' or 'recursive')
    )
    max_chunk_time: float = 30.0  # Maximum time in seconds for chunking
    batch_size: int = 10000  # Process text in batches of this size

    # URL download settings
    download_timeout: int = 60  # Timeout in seconds for downloading PDFs

    model_config = {
        "extra": "allow",  # Allow extra fields from environment variables
    }


class LLMSettings(BaseSettings):
    """Settings for the LLM."""

    model_name: str = "gpt-4"
    temperature: float = 0.0
    max_tokens: int = 1000
    api_key: Optional[str] = None

    # Using field_validator for Pydantic v2
    @field_validator("api_key", mode="before")
    @classmethod
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return os.environ.get("OPENAI_API_KEY")
        return v

    model_config = {
        "extra": "allow",  # Allow extra fields from environment variables
    }


class APISettings(BaseSettings):
    """Settings for the API."""

    title: str = "PDF RAG API"
    description: str = "API for PDF RAG with version comparison"
    version: str = "0.1.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    root_path: str = ""

    # Request handling settings
    max_upload_size: int = 100 * 1024 * 1024  # 100 MB max upload size
    request_timeout: int = 300  # 5 minutes timeout for requests
    chunk_size: int = 1024 * 1024  # 1 MB chunks for streaming uploads

    model_config = {
        "extra": "allow",  # Allow extra fields from environment variables
    }


class DatabaseSettings(BaseSettings):
    """Settings for the database."""

    dsn: str = "postgresql://postgres:postgres@db:5432/pdf_rag"
    min_connections: int = 1
    max_connections: int = 10

    @field_validator("dsn", mode="before")
    @classmethod
    def validate_dsn(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v

        # Try to get from environment variables
        postgres_dsn = os.environ.get("POSTGRES_DSN")
        if postgres_dsn:
            return postgres_dsn

        # Build from individual environment variables
        # Use string formatting for Pydantic v2 compatibility
        user = os.environ.get("POSTGRES_USER", "postgres")
        password = os.environ.get("POSTGRES_PASSWORD", "postgres")
        host = os.environ.get(
            "POSTGRES_HOST", "db"
        )  # Use "db" as the default host in Docker
        port = os.environ.get("POSTGRES_PORT", "5432")
        db = os.environ.get("POSTGRES_DB", "pdf_rag")

        return f"postgresql://{user}:{password}@{host}:{port}/{db}"

    model_config = {
        "extra": "allow",  # Allow extra fields from environment variables
    }


class Settings(BaseSettings):
    """Main settings class."""

    debug: bool = False
    environment: str = "development"
    vector_store: VectorStoreSettings = VectorStoreSettings()
    llm: LLMSettings = LLMSettings()
    api: APISettings = APISettings()
    database: DatabaseSettings = DatabaseSettings()
    upload_dir: str = "uploads"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_nested_delimiter": "__",
        "extra": "allow",  # Allow extra fields from environment variables
    }


# Create settings instance
settings = Settings()
