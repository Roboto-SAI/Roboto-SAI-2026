FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY backend/requirements.txt ./backend/
COPY backend/constraints.txt ./backend/
COPY sdk/ /app/sdk/
RUN pip install --no-cache-dir -r ./backend/requirements.txt -c ./backend/constraints.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Copy backend code
COPY backend/ /app/backend/

# Set working directory to backend
WORKDIR /app/backend

# Set Python path
ENV PYTHONPATH=/app/backend

# Expose port
EXPOSE 5000

# Health Check - temporarily disabled for deployment
# HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=2 \
#     CMD python -c "import requests; requests.get('http://localhost:${PORT:-5000}/health')" || exit 1

# Run uvicorn
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-5000} --log-level info"]
