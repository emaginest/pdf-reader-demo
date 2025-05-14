"""
Query page for the PDF RAG system.
"""

import streamlit as st
import json
from typing import Dict, Any, Optional

from utils.api import query_rag
from utils.ui import (
    display_success,
    display_error,
    display_query_result,
    parse_json_input,
)
from utils.config import HELP_TEXTS, UI_SETTINGS, DEFAULT_VALUES

# Set page title
st.title("❓ Query the RAG System")

# Query form
st.markdown("### Ask a Question")

query = st.text_area(
    "Question",
    help=HELP_TEXTS["query"],
    height=100,
    value=st.session_state.get("last_query", DEFAULT_VALUES["query"]),
)

# Advanced options in an expander
with st.expander("Advanced Options", expanded=False):
    filters_str = st.text_area(
        "Metadata Filters (JSON, optional)",
        help=HELP_TEXTS["filters"],
        height=100,
    )

    # Parse filters JSON
    is_valid_json, filters_result = parse_json_input(filters_str)

    if filters_str and not is_valid_json:
        st.error(f"Invalid filters JSON: {filters_result}")
        filters = None
    else:
        filters = filters_result

    limit = st.number_input(
        "Result Limit",
        min_value=1,
        max_value=20,
        value=UI_SETTINGS["default_query_limit"],
        help=HELP_TEXTS["limit"],
    )

# Query button
query_button = st.button(
    "Submit Query",
    disabled=False,
    use_container_width=True,
)

# Handle query submission
if query_button and query:
    with st.spinner("Processing query..."):
        # Store the query in session state
        st.session_state["last_query"] = query

        # Call the API to query the RAG system
        result = query_rag(
            query=query,
            filters=filters,
            limit=limit,
        )

        # Display the result
        if result.get("success", False):
            display_query_result(result)
        else:
            display_error(
                f"Failed to process query: {result.get('error', 'Unknown error')}"
            )

# Display previous query if available
if "last_query_result" in st.session_state and not query_button:
    st.markdown("### Previous Query Result")
    display_query_result(st.session_state["last_query_result"])
