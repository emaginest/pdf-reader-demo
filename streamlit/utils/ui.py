"""
UI helper functions for the Streamlit application.
"""

import json
import streamlit as st
from typing import Dict, List, Any, Optional, Union, Tuple
import pandas as pd
import base64
from io import BytesIO

def display_success(message: str) -> None:
    """Display a success message."""
    st.success(message)

def display_error(message: str) -> None:
    """Display an error message."""
    st.error(message)

def display_info(message: str) -> None:
    """Display an info message."""
    st.info(message)

def display_warning(message: str) -> None:
    """Display a warning message."""
    st.warning(message)

def display_json(data: Dict[str, Any], expanded: bool = True) -> None:
    """Display JSON data in an expandable container."""
    st.json(data, expanded=expanded)

def parse_json_input(json_str: str) -> Tuple[bool, Union[Dict[str, Any], str]]:
    """Parse JSON input and return success status and result."""
    if not json_str or json_str.strip() == "":
        return True, {}
    
    try:
        data = json.loads(json_str)
        return True, data
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"

def display_document_info(document_info: Dict[str, Any]) -> None:
    """Display document information."""
    if not document_info:
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Document ID:**", document_info.get("document_id", "N/A"))
        st.write("**Version:**", document_info.get("version", "N/A"))
    
    with col2:
        st.write("**Success:**", document_info.get("success", False))
        st.write("**Message:**", document_info.get("message", "N/A"))
    
    if "metadata" in document_info and document_info["metadata"]:
        with st.expander("Metadata", expanded=False):
            st.json(document_info["metadata"])

def display_query_result(result: Dict[str, Any]) -> None:
    """Display query result."""
    if not result:
        return
    
    if "error" in result and result["error"]:
        display_error(result["error"])
        return
    
    st.markdown("### Response")
    st.markdown(result.get("response", "No response"))
    
    if "sources" in result and result["sources"]:
        with st.expander("Sources", expanded=False):
            for i, source in enumerate(result["sources"]):
                st.markdown(f"**Source {i+1}**")
                st.write("Document ID:", source.get("document_id", "N/A"))
                st.write("Version:", source.get("version", "N/A"))
                st.write("Page:", source.get("page", "N/A"))
                st.write("Chunk:", source.get("chunk_id", "N/A"))
                st.markdown("---")
                st.markdown(source.get("text", "No text"))
                st.markdown("---")

def display_comparison_result(result: Dict[str, Any]) -> None:
    """Display comparison result."""
    if not result:
        return
    
    if "error" in result and result["error"]:
        display_error(result["error"])
        return
    
    st.markdown("### Comparison")
    st.markdown(result.get("comparison", "No comparison available"))
    
    if "metadata_changes" in result and result["metadata_changes"]:
        with st.expander("Metadata Changes", expanded=False):
            st.json(result["metadata_changes"])

def display_summary_result(result: Dict[str, Any]) -> None:
    """Display summary result."""
    if not result:
        return
    
    if "error" in result and result["error"]:
        display_error(result["error"])
        return
    
    st.markdown("### Summary of Changes")
    st.markdown(result.get("summary", "No summary available"))
    
    if "metadata_changes" in result and result["metadata_changes"]:
        with st.expander("Metadata Changes", expanded=False):
            st.json(result["metadata_changes"])

def display_change_query_result(result: Dict[str, Any]) -> None:
    """Display change query result."""
    if not result:
        return
    
    if "error" in result and result["error"]:
        display_error(result["error"])
        return
    
    st.markdown("### Query")
    st.markdown(f"*{result.get('query', 'No query')}*")
    
    st.markdown("### Response")
    st.markdown(result.get("response", "No response"))

def display_versions_table(versions: List[Dict[str, Any]]) -> None:
    """Display versions table."""
    if not versions:
        st.info("No versions found for this document.")
        return
    
    # Create a DataFrame from the versions
    df = pd.DataFrame(versions)
    
    # Reorder columns if needed
    columns = ["version", "created_at", "page_count", "chunk_count"]
    display_columns = [col for col in columns if col in df.columns]
    other_columns = [col for col in df.columns if col not in columns]
    df = df[display_columns + other_columns]
    
    # Format datetime columns
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    
    st.dataframe(df)

def get_pdf_display_html(pdf_bytes: bytes) -> str:
    """Convert PDF bytes to base64 for HTML display."""
    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    return f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf">'

def display_pdf_preview(pdf_file) -> None:
    """Display a preview of a PDF file."""
    if pdf_file is None:
        return
    
    # Read the PDF file
    pdf_bytes = pdf_file.getvalue()
    
    # Display the PDF
    st.markdown(get_pdf_display_html(pdf_bytes), unsafe_allow_html=True)

def create_document_selector(
    document_id: Optional[str] = None,
    on_change: Optional[callable] = None,
) -> str:
    """Create a document ID input field."""
    return st.text_input(
        "Document ID",
        value=document_id or "",
        help="Enter the document ID",
        on_change=on_change if on_change else None,
    )

def create_version_selector(
    versions: List[Dict[str, Any]],
    label: str,
    key: str,
) -> str:
    """Create a version selector dropdown."""
    if not versions:
        return st.text_input(label, key=key)
    
    version_options = [v["version"] for v in versions if "version" in v]
    return st.selectbox(label, options=version_options, key=key)
