"""
API client functions for interacting with the RAG system API.
"""

import json
import requests
from typing import Dict, List, Any, Optional, Union, BinaryIO
import streamlit as st

# Import from the local config module
from .config import API_ENDPOINTS


def handle_api_error(response: requests.Response) -> Dict[str, Any]:
    """Handle API error responses."""
    try:
        error_data = response.json()
        error_message = error_data.get("detail", str(error_data))
    except Exception:
        error_message = f"Error: {response.status_code} - {response.text}"

    return {"success": False, "error": error_message}


@st.cache_data(ttl=300)  # Cache for 5 minutes
def upload_document(
    file: BinaryIO,
    document_id: Optional[str] = None,
    version: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Upload a PDF document to the RAG system."""
    try:
        files = {"file": file}
        data = {}

        if document_id:
            data["document_id"] = document_id
        if version:
            data["version"] = version
        if metadata:
            data["metadata"] = json.dumps(metadata)

        response = requests.post(
            API_ENDPOINTS["upload"],
            files=files,
            data=data,
        )

        if response.status_code == 200:
            return {"success": True, **response.json()}
        else:
            return handle_api_error(response)
    except Exception as e:
        return {"success": False, "error": str(e)}


@st.cache_data(ttl=300)  # Cache for 5 minutes
def ingest_url(
    url: str,
    document_id: Optional[str] = None,
    version: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Ingest a PDF document from a URL."""
    try:
        data = {
            "url": url,
        }

        if document_id:
            data["document_id"] = document_id
        if version:
            data["version"] = version
        if metadata:
            data["metadata"] = metadata

        response = requests.post(
            API_ENDPOINTS["ingest_url"],
            json=data,
        )

        if response.status_code == 200:
            return {"success": True, **response.json()}
        else:
            return handle_api_error(response)
    except Exception as e:
        return {"success": False, "error": str(e)}


@st.cache_data(ttl=300)  # Cache for 5 minutes
def ingest_urls(
    urls: List[str],
    document_id: Optional[str] = None,
    version: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Ingest multiple PDF documents from URLs."""
    try:
        data = {
            "urls": urls,
        }

        if document_id:
            data["document_id"] = document_id
        if version:
            data["version"] = version
        if metadata:
            data["metadata"] = metadata

        response = requests.post(
            API_ENDPOINTS["ingest_urls"],
            json=data,
        )

        if response.status_code == 200:
            return {"success": True, **response.json()}
        else:
            return handle_api_error(response)
    except Exception as e:
        return {"success": False, "error": str(e)}


@st.cache_data(ttl=60)  # Cache for 1 minute
def query_rag(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Query the RAG system."""
    try:
        data = {
            "query": query,
        }

        if filters:
            data["filters"] = filters
        if limit:
            data["limit"] = limit

        response = requests.post(
            API_ENDPOINTS["query"],
            json=data,
        )

        if response.status_code == 200:
            return {"success": True, **response.json()}
        else:
            return handle_api_error(response)
    except Exception as e:
        return {"success": False, "error": str(e)}


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_document_versions(document_id: str) -> Dict[str, Any]:
    """Get all versions of a document."""
    try:
        url = API_ENDPOINTS["versions"].format(document_id=document_id)
        response = requests.get(url)

        if response.status_code == 200:
            return {"success": True, **response.json()}
        else:
            return handle_api_error(response)
    except Exception as e:
        return {"success": False, "error": str(e)}


@st.cache_data(ttl=60)  # Cache for 1 minute
def compare_documents(
    document_id: str,
    version1: str,
    version2: str,
) -> Dict[str, Any]:
    """Compare two versions of a document."""
    try:
        data = {
            "document_id": document_id,
            "version1": version1,
            "version2": version2,
        }

        response = requests.post(
            API_ENDPOINTS["compare"],
            json=data,
        )

        if response.status_code == 200:
            return {"success": True, **response.json()}
        else:
            return handle_api_error(response)
    except Exception as e:
        return {"success": False, "error": str(e)}


@st.cache_data(ttl=60)  # Cache for 1 minute
def summarize_changes(
    document_id: str,
    version1: str,
    version2: str,
) -> Dict[str, Any]:
    """Summarize changes between two versions of a document."""
    try:
        data = {
            "document_id": document_id,
            "version1": version1,
            "version2": version2,
        }

        response = requests.post(
            API_ENDPOINTS["summarize_changes"],
            json=data,
        )

        if response.status_code == 200:
            return {"success": True, **response.json()}
        else:
            return handle_api_error(response)
    except Exception as e:
        return {"success": False, "error": str(e)}


@st.cache_data(ttl=60)  # Cache for 1 minute
def query_changes(
    document_id: str,
    version1: str,
    version2: str,
    query: str,
) -> Dict[str, Any]:
    """Answer questions about changes between document versions."""
    try:
        data = {
            "document_id": document_id,
            "version1": version1,
            "version2": version2,
            "query": query,
        }

        response = requests.post(
            API_ENDPOINTS["query_changes"],
            json=data,
        )

        if response.status_code == 200:
            return {"success": True, **response.json()}
        else:
            return handle_api_error(response)
    except Exception as e:
        return {"success": False, "error": str(e)}
