FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies
RUN pip install --no-cache-dir agents-hub>=0.1.4 pydantic-settings>=2.0.0 fastapi>=0.100.0

# Copy application code (includes custom text splitter implementation)
COPY . .

# Create upload directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Run the application with increased timeouts and limits
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300", "--limit-concurrency", "20", "--timeout-graceful-shutdown", "30"]
