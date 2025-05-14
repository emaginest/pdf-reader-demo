"""
URL ingestion page for the PDF RAG system.
"""

import streamlit as st
import json
from typing import Dict, Any, List, Optional

from utils.api import ingest_url, ingest_urls
from utils.ui import (
    display_success,
    display_error,
    display_document_info,
    parse_json_input,
)
from utils.config import HELP_TEXTS, UI_SETTINGS

# Set page title
st.title("🔗 Ingest PDF from URL")

# Create tabs for single URL and multiple URLs
tab1, tab2 = st.tabs(["Single URL", "Multiple URLs"])

# Single URL tab
with tab1:
    st.markdown("### Ingest PDF from URL")

    url = st.text_input(
        "PDF URL",
        help=HELP_TEXTS["url"],
    )

    document_id = st.text_input(
        "Document ID (optional)",
        help=HELP_TEXTS["document_id"],
        key="single_doc_id",
    )

    version = st.text_input(
        "Version (optional)",
        help=HELP_TEXTS["version"],
        key="single_version",
    )

    metadata_str = st.text_area(
        "Metadata (JSON, optional)",
        help=HELP_TEXTS["metadata"],
        height=150,
        key="single_metadata",
    )

    # Parse metadata JSON
    is_valid_json, metadata_result = parse_json_input(metadata_str)

    if metadata_str and not is_valid_json:
        st.error(f"Invalid metadata JSON: {metadata_result}")
        metadata = None
    else:
        metadata = metadata_result

    # Ingest button
    ingest_button = st.button(
        "Ingest PDF",
        disabled=False,
        key="single_ingest",
        use_container_width=True,
    )

    # Handle URL ingestion
    if ingest_button and url:
        with st.spinner("Ingesting PDF from URL..."):
            # Call the API to ingest the PDF
            result = ingest_url(
                url=url,
                document_id=document_id if document_id else None,
                version=version if version else None,
                metadata=metadata,
            )

            # Display the result
            if result.get("success", False):
                display_success("PDF ingested successfully!")
                display_document_info(result)

                # Store the document ID in session state for other pages
                if "document_id" in result:
                    st.session_state["last_document_id"] = result["document_id"]
                if "version" in result:
                    st.session_state["last_version"] = result["version"]
            else:
                display_error(
                    f"Failed to ingest PDF: {result.get('error', 'Unknown error')}"
                )

# Multiple URLs tab
with tab2:
    st.markdown("### Ingest Multiple PDFs from URLs")

    urls_str = st.text_area(
        "PDF URLs (one per line)",
        help=HELP_TEXTS["urls"],
        height=150,
    )

    # Parse URLs
    urls = [url.strip() for url in urls_str.split("\n") if url.strip()]

    document_id = st.text_input(
        "Document ID (optional)",
        help=HELP_TEXTS["document_id"],
        key="multi_doc_id",
    )

    version = st.text_input(
        "Version (optional)",
        help=HELP_TEXTS["version"],
        key="multi_version",
    )

    metadata_str = st.text_area(
        "Metadata (JSON, optional)",
        help=HELP_TEXTS["metadata"],
        height=150,
        key="multi_metadata",
    )

    # Parse metadata JSON
    is_valid_json, metadata_result = parse_json_input(metadata_str)

    if metadata_str and not is_valid_json:
        st.error(f"Invalid metadata JSON: {metadata_result}")
        metadata = None
    else:
        metadata = metadata_result

    # Display URL count
    st.info(f"Number of URLs: {len(urls)}")

    # Ingest button
    ingest_button = st.button(
        "Ingest PDFs",
        disabled=False,
        key="multi_ingest",
        use_container_width=True,
    )

    # Handle URL ingestion
    if ingest_button and urls:
        with st.spinner("Ingesting PDFs from URLs..."):
            # Call the API to ingest the PDFs
            result = ingest_urls(
                urls=urls,
                document_id=document_id if document_id else None,
                version=version if version else None,
                metadata=metadata,
            )

            # Display the result
            if result.get("success", False):
                display_success("PDFs ingested successfully!")
                st.json(result)
            else:
                display_error(
                    f"Failed to ingest PDFs: {result.get('error', 'Unknown error')}"
                )
