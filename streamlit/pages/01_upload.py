"""
Document upload page for the PDF RAG system.
"""

import streamlit as st
import json
from typing import Dict, Any, Optional

from utils.api import upload_document
from utils.ui import (
    display_success,
    display_error,
    display_document_info,
    display_pdf_preview,
    parse_json_input,
)
from utils.config import HELP_TEXTS, UI_SETTINGS

# Set page title
st.title("📤 Upload PDF Document")

# Create two columns for the form and preview
col1, col2 = st.columns([1, 1])

with col1:
    # File upload form
    st.markdown("### Upload PDF")

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=UI_SETTINGS["allowed_file_types"],
        help=HELP_TEXTS["upload"],
        accept_multiple_files=False,
    )

    # Document metadata form
    st.markdown("### Document Metadata")

    document_id = st.text_input(
        "Document ID (optional)",
        help=HELP_TEXTS["document_id"],
    )

    version = st.text_input(
        "Version (optional)",
        help=HELP_TEXTS["version"],
    )

    metadata_str = st.text_area(
        "Metadata (JSON, optional)",
        help=HELP_TEXTS["metadata"],
        height=150,
    )

    # Parse metadata JSON
    is_valid_json, metadata_result = parse_json_input(metadata_str)

    if metadata_str and not is_valid_json:
        st.error(f"Invalid metadata JSON: {metadata_result}")
        metadata = None
    else:
        metadata = metadata_result

    # Upload button
    upload_button = st.button(
        "Upload Document",
        disabled=False,
        use_container_width=True,
    )

with col2:
    # PDF preview
    if uploaded_file is not None:
        st.markdown("### PDF Preview")
        display_pdf_preview(uploaded_file)
    else:
        st.info("Upload a PDF file to see a preview.")

# Handle document upload
if upload_button and uploaded_file is not None:
    with st.spinner("Uploading document..."):
        # Reset file pointer to beginning
        uploaded_file.seek(0)

        # Call the API to upload the document
        result = upload_document(
            file=uploaded_file,
            document_id=document_id if document_id else None,
            version=version if version else None,
            metadata=metadata,
        )

        # Display the result
        if isinstance(result, dict):
            # Check if the result is a dictionary with a success field
            if result.get("success", False):
                # Success case
                if "message" in result:
                    display_success(result["message"])
                else:
                    display_success("Document uploaded successfully!")

                display_document_info(result)

                # Store the document ID in session state for other pages
                if "document_id" in result:
                    st.session_state["last_document_id"] = result["document_id"]
                if "version" in result:
                    st.session_state["last_version"] = result["version"]
            elif "error" in result and result["error"]:
                # Error case with error field
                display_error(f"Failed to upload document: {result['error']}")
            else:
                # Unknown error case
                display_error(f"Failed to upload document: Unknown error")
        else:
            # Not a dictionary
            display_error(f"Failed to upload document: Invalid response format")
