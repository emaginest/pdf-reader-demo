#!/bin/bash
echo "Starting Streamlit application..."
echo "API URL: http://host.docker.internal:8000"

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export API_BASE_URL=http://host.docker.internal:8000
cd $DIR

echo "Installing dependencies..."
pip install streamlit==1.28.0 requests pandas PyPDF2 Pillow
echo "Installing package in development mode..."
pip install -e . > /dev/null 2>&1

echo "Starting Streamlit..."
streamlit run app.py
