"""
Configuration settings for the Streamlit application.
"""

import os
from typing import Dict, Any

# API base URL - default to localhost if not specified
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

# API endpoints
API_ENDPOINTS = {
    "upload": f"{API_BASE_URL}/api/v1/documents/upload",
    "ingest_url": f"{API_BASE_URL}/api/v1/documents/ingest-url",
    "ingest_urls": f"{API_BASE_URL}/api/v1/documents/ingest-urls",
    "query": f"{API_BASE_URL}/api/v1/rag/query",
    "versions": f"{API_BASE_URL}/api/v1/documents/{{document_id}}/versions",
    "compare": f"{API_BASE_URL}/api/v1/documents/compare",
    "summarize_changes": f"{API_BASE_URL}/api/v1/documents/summarize-changes",
    "query_changes": f"{API_BASE_URL}/api/v1/documents/query-changes",
}

# Streamlit app settings
APP_SETTINGS = {
    "title": "PDF RAG System",
    "icon": "📄",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# UI settings
UI_SETTINGS = {
    "max_file_size": 100 * 1024 * 1024,  # 100 MB
    "allowed_file_types": ["pdf"],
    "max_urls": 10,  # Maximum number of URLs to ingest at once
    "default_query_limit": 5,  # Default number of results to use for RAG queries
}

# Default values for forms
DEFAULT_VALUES = {
    "document_id": "",
    "version": "",
    "query": "",
    "filters": {},
    "url": "",
    "urls": [],
}

# Help texts for UI elements
HELP_TEXTS = {
    "upload": "Upload a PDF document to the RAG system.",
    "document_id": "Unique identifier for the document. Leave blank to generate automatically.",
    "version": "Version identifier for the document. Leave blank to generate automatically.",
    "metadata": "Additional metadata for the document in JSON format.",
    "url": "URL of the PDF document to ingest.",
    "urls": "URLs of PDF documents to ingest (one per line).",
    "query": "Question or query to answer using the RAG system.",
    "filters": "Optional metadata filters in JSON format.",
    "limit": "Maximum number of results to use for the query.",
    "version1": "First version to compare.",
    "version2": "Second version to compare.",
}
