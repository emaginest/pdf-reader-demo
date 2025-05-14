@echo off
echo Starting Streamlit application...
echo API URL: http://host.docker.internal:8000

set API_BASE_URL=http://host.docker.internal:8000
cd %~dp0

echo Installing dependencies...
pip install streamlit==1.28.0 requests pandas PyPDF2 Pillow
echo Installing package in development mode...
pip install -e . > nul 2>&1

echo Starting Streamlit...
streamlit run app.py
