#!/bin/bash
echo "Building and running Streamlit in Docker..."

cd ..
docker-compose up -d streamlit

echo ""
echo "Streamlit UI is now running at http://localhost:8501"
echo ""
