# PDF RAG System - Streamlit UI

This is a Streamlit-based user interface for the PDF RAG (Retrieval-Augmented Generation) system. It provides a user-friendly way to interact with the RAG system's API endpoints.

## Features

- Upload PDF documents
- Ingest PDFs from URLs
- Query the RAG system
- View document versions
- Compare document versions
- Analyze changes between versions

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set the API base URL (optional):

```bash
export API_BASE_URL=http://localhost:8000
```

## Usage

### Option 1: Using the run script

#### Windows:
```bash
run.bat
```

#### Linux/Mac:
```bash
chmod +x run.sh
./run.sh
```

### Option 2: Manual configuration

Set the API URL environment variable and run Streamlit:

```bash
# Windows (PowerShell)
$env:API_BASE_URL="http://localhost:8000"
streamlit run app.py

# Linux/Mac
export API_BASE_URL=http://localhost:8000
streamlit run app.py
```

This will start the Streamlit server and open the application in your default web browser.

## Pages

The application consists of the following pages:

- **Home**: Overview and introduction
- **Upload**: Upload PDF documents
- **Ingest URL**: Ingest PDFs from URLs
- **Query**: Query the RAG system
- **Versions**: View document versions
- **Compare**: Compare document versions
- **Changes**: Query about changes between versions

## Configuration

You can configure the application by modifying the `config.py` file:

- API endpoints
- UI settings
- Default values
- Help texts

## API Connection

By default, the application connects to the API at `http://localhost:8000`. You can change this by setting the `API_BASE_URL` environment variable.

### Important Note for Docker

When running in Docker, the API URL needs to be set correctly:

1. For users accessing Streamlit from their browser, the API URL should be `http://localhost:8000` because the browser makes requests from the user's machine.

2. For container-to-container communication in Docker Compose, the API URL would be `http://app:8000` (using the service name).

The current configuration is set up for users accessing Streamlit from their browser, which is the most common use case.
