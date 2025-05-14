"""
Changes query page for the PDF RAG system.
"""

import streamlit as st
from typing import Dict, Any, List, Optional

from utils.api import get_document_versions, query_changes
from utils.ui import (
    display_success,
    display_error,
    display_change_query_result,
    create_document_selector,
    create_version_selector,
)
from utils.config import HELP_TEXTS, DEFAULT_VALUES

# Set page title
st.title("🔄 Query Document Changes")

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
        key="changes_version1",
    )

with col2:
    version2 = create_version_selector(
        versions=versions,
        label="Version 2",
        key="changes_version2",
    )

# Query input
st.markdown("### Ask a Question About Changes")

query = st.text_area(
    "Question",
    help="Ask a question about the changes between the two versions",
    height=100,
    value=st.session_state.get("last_changes_query", ""),
)

# Query button
query_button = st.button(
    "Submit Query",
    disabled=False,
    use_container_width=True,
)

# Handle query submission
if query_button and document_id and version1 and version2 and query:
    with st.spinner("Processing query..."):
        # Store the query in session state
        st.session_state["last_changes_query"] = query

        # Call the API to query about changes
        result = query_changes(
            document_id=document_id,
            version1=version1,
            version2=version2,
            query=query,
        )

        # Store the result in session state
        st.session_state["changes_query_result"] = result

        # Display the result
        if result.get("success", False):
            display_change_query_result(result)
        else:
            display_error(
                f"Failed to process query: {result.get('error', 'Unknown error')}"
            )

# Display previous query result if available
elif "changes_query_result" in st.session_state:
    display_change_query_result(st.session_state["changes_query_result"])

# Display example questions
with st.expander("Example Questions", expanded=False):
    st.markdown(
        """
    Here are some example questions you can ask about document changes:

    - What are the main differences between these versions?
    - What sections were added in the newer version?
    - What information was removed from the older version?
    - How did the conclusion change between versions?
    - Were there any changes to the financial data?
    - What figures or tables were updated?
    - Summarize the key changes in the executive summary.
    """
    )
