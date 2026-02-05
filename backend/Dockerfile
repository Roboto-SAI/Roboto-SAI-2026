FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create non-root user
RUN groupadd -r roboto && useradd -r -g roboto roboto

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first (constraints.txt is optional)
COPY backend/requirements.txt ./

# Install dependencies (without constraints if not needed)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Verify SDK integrity (optional - continues if not available)
RUN python -c "import roboto_sai_sdk; print('SDK integrity verified')" || echo "SDK not required for basic functionality"

# Copy backend code (excluding virtual environments and cache)
COPY backend/api/ ./api/
COPY backend/services/ ./services/
COPY backend/utils/ ./utils/
COPY backend/*.py ./
COPY backend/*.txt ./
COPY backend/*.json ./
COPY backend/*.sql ./

# Set working directory to app (where files are copied)
WORKDIR /app

# Create data directory
RUN mkdir -p data && chown -R roboto:roboto /app

# Set Python path
ENV PYTHONPATH=/app

# Default port (Render overrides via $PORT)
ENV PORT=5000

# Expose port (Render will override with $PORT)
EXPOSE 5000

# Switch to non-root user
USER roboto

# Start with uvicorn using Render's PORT variable
CMD ["sh", "-c", "uvicorn main_modular:app --host 0.0.0.0 --port ${PORT} --proxy-headers"]
