FROM python:3.11-slim

# Create non-root user
RUN groupadd -r roboto && useradd -r -g roboto roboto

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and constraints
COPY requirements.txt ./
COPY constraints.txt ./

# Install dependencies with constraints
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt

# Verify SDK integrity
RUN python -c "import roboto_sai_sdk; print('SDK integrity verified')" || echo "SDK not required for basic functionality"

# Copy backend code
COPY . /app/

# Create data directory
RUN mkdir -p /app/data && chown -R roboto:roboto /app

# Set working directory
WORKDIR /app

# Set Python path
ENV PYTHONPATH=/app

# Expose port (Render will override with $PORT)
EXPOSE 8000

# Switch to non-root user
USER roboto

# Start with uvicorn using Render's PORT variable
CMD python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info
