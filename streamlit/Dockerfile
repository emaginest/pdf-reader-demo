FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir streamlit==1.28.0

# Copy application code
COPY . .

# Install the package in development mode
RUN pip install -e .

# Expose port
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    API_BASE_URL=http://host.docker.internal:8000

# Create a simple wrapper script to ensure proper module imports
RUN echo '#!/bin/bash\n\
    cd /app\n\
    python -c "import sys; print(sys.path)"\n\
    streamlit run app.py --server.port=8501 --server.address=0.0.0.0\n\
    ' > /app/run_streamlit.sh && chmod +x /app/run_streamlit.sh

# Run the application
CMD ["/app/run_streamlit.sh"]
