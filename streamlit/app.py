"""
Main Streamlit application for the PDF RAG system.
"""

import streamlit as st
import os
from utils.config import APP_SETTINGS

# Set page configuration
st.set_page_config(
    page_title=APP_SETTINGS["title"],
    page_icon=APP_SETTINGS["icon"],
    layout=APP_SETTINGS["layout"],
    initial_sidebar_state=APP_SETTINGS["initial_sidebar_state"],
)

# Main page content
st.title(f"{APP_SETTINGS['icon']} {APP_SETTINGS['title']}")

st.markdown(
    """
## Welcome to the PDF RAG System

This application allows you to interact with a RAG (Retrieval-Augmented Generation) system
for PDF documents. You can upload documents, ingest PDFs from URLs, query the system,
compare document versions, and more.

### Features

- **Upload PDF Documents**: Upload PDF files directly to the system
- **Ingest from URLs**: Add PDF documents from web URLs
- **Query the RAG System**: Ask questions about your documents
- **View Document Versions**: See all versions of a document
- **Compare Versions**: Compare different versions of the same document
- **Analyze Changes**: Get summaries and answers about document changes

### Getting Started

Use the sidebar to navigate to different features of the application.
"""
)

# Display information about the API connection
st.sidebar.title("PDF RAG System")
api_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
st.sidebar.info(f"Connected to API at: {api_url}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 PDF RAG System")
