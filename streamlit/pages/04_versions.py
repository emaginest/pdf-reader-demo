"""
Document versions page for the PDF RAG system.
"""

import streamlit as st
from typing import Dict, Any, List, Optional

from utils.api import get_document_versions
from utils.ui import (
    display_success,
    display_error,
    display_versions_table,
    create_document_selector,
)
from utils.config import DEFAULT_VALUES

# Set page title
st.title("📚 Document Versions")

# Document selector
document_id = create_document_selector(
    document_id=st.session_state.get("last_document_id", DEFAULT_VALUES["document_id"]),
)

# Get versions button
get_versions_button = st.button(
    "Get Versions",
    disabled=False,
    use_container_width=True,
)

# Handle get versions request
if get_versions_button and document_id:
    with st.spinner("Getting document versions..."):
        # Call the API to get document versions
        result = get_document_versions(document_id=document_id)

        # Display the result
        if result.get("success", False):
            st.markdown(f"### Versions for Document: {document_id}")

            # Store versions in session state
            versions = result.get("versions", [])
            st.session_state["document_versions"] = versions

            # Display versions table
            display_versions_table(versions)

            # Store the document ID in session state for other pages
            st.session_state["last_document_id"] = document_id
        else:
            display_error(
                f"Failed to get document versions: {result.get('error', 'Unknown error')}"
            )

# Display previous versions if available
elif "document_versions" in st.session_state and document_id == st.session_state.get(
    "last_document_id", ""
):
    st.markdown(f"### Versions for Document: {document_id}")
    display_versions_table(st.session_state["document_versions"])
