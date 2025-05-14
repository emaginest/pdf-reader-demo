"""
Document comparison page for the PDF RAG system.
"""

import streamlit as st
from typing import Dict, Any, List, Optional

from utils.api import get_document_versions, compare_documents, summarize_changes
from utils.ui import (
    display_success,
    display_error,
    display_comparison_result,
    display_summary_result,
    create_document_selector,
    create_version_selector,
)
from utils.config import HELP_TEXTS, DEFAULT_VALUES

# Set page title
st.title("🔍 Compare Document Versions")

# Document selector
document_id = create_document_selector(
    document_id=st.session_state.get("last_document_id", DEFAULT_VALUES["document_id"]),
)

# Get versions if document ID is provided
versions = []
if document_id:
    # Check if we already have versions for this document
    if (
        "document_versions" in st.session_state
        and st.session_state.get("last_document_id", "") == document_id
    ):
        versions = st.session_state["document_versions"]
    else:
        # Get versions from API
        with st.spinner("Getting document versions..."):
            result = get_document_versions(document_id=document_id)
            if result.get("success", False):
                versions = result.get("versions", [])
                st.session_state["document_versions"] = versions
                st.session_state["last_document_id"] = document_id

# Version selectors
col1, col2 = st.columns(2)

with col1:
    version1 = create_version_selector(
        versions=versions,
        label="Version 1",
        key="version1",
    )

with col2:
    version2 = create_version_selector(
        versions=versions,
        label="Version 2",
        key="version2",
    )

# Create tabs for comparison and summary
tab1, tab2 = st.tabs(["Compare", "Summarize Changes"])

# Compare tab
with tab1:
    compare_button = st.button(
        "Compare Versions",
        disabled=False,
        key="compare_button",
        use_container_width=True,
    )

    # Handle comparison request
    if compare_button and document_id and version1 and version2:
        with st.spinner("Comparing document versions..."):
            # Call the API to compare document versions
            result = compare_documents(
                document_id=document_id,
                version1=version1,
                version2=version2,
            )

            # Store the result in session state
            st.session_state["comparison_result"] = result

            # Display the result
            if result.get("success", False):
                display_comparison_result(result)
            else:
                display_error(
                    f"Failed to compare document versions: {result.get('error', 'Unknown error')}"
                )

    # Display previous comparison result if available
    elif "comparison_result" in st.session_state:
        display_comparison_result(st.session_state["comparison_result"])

# Summarize tab
with tab2:
    summarize_button = st.button(
        "Summarize Changes",
        disabled=False,
        key="summarize_button",
        use_container_width=True,
    )

    # Handle summary request
    if summarize_button and document_id and version1 and version2:
        with st.spinner("Summarizing changes..."):
            # Call the API to summarize changes
            result = summarize_changes(
                document_id=document_id,
                version1=version1,
                version2=version2,
            )

            # Store the result in session state
            st.session_state["summary_result"] = result

            # Display the result
            if result.get("success", False):
                display_summary_result(result)
            else:
                display_error(
                    f"Failed to summarize changes: {result.get('error', 'Unknown error')}"
                )

    # Display previous summary result if available
    elif "summary_result" in st.session_state:
        display_summary_result(st.session_state["summary_result"])
