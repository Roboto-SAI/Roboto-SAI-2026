FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# SDK via pip install -e (host mount dev, git prod)
# COPY sdk/roboto_sai_sdk ./backend/sdk  # Disabled - use mount

# Copy SDK package directory (repo root) and install as editable package
# The SDK repo layout may be either:
# - sdk/roboto-sai-sdk/pyproject.toml
# - sdk/roboto-sai-sdk/roboto-sai-sdk/pyproject.toml
COPY sdk/roboto-sai-sdk /app/sdk/roboto-sai-sdk

# Copy requirements/constraints and install dependencies
COPY backend/requirements.txt ./backend/
COPY backend/constraints.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt -c ./backend/constraints.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Install SDK as editable package (handle nested or root layout)
RUN if [ -f /app/sdk/roboto-sai-sdk/pyproject.toml ] || [ -f /app/sdk/roboto-sai-sdk/setup.py ]; then \
            pip install --no-cache-dir -e /app/sdk/roboto-sai-sdk -c ./backend/constraints.txt; \
        elif [ -f /app/sdk/roboto-sai-sdk/roboto-sai-sdk/pyproject.toml ] || [ -f /app/sdk/roboto-sai-sdk/roboto-sai-sdk/setup.py ]; then \
            pip install --no-cache-dir -e /app/sdk/roboto-sai-sdk/roboto-sai-sdk -c ./backend/constraints.txt; \
        else \
            echo "Roboto SAI SDK not found in image"; \
            exit 1; \
        fi

# Copy backend code
COPY backend/ .

WORKDIR /app/backend

# Expose port - Render will set PORT env var to the exposed port | default to 5000
EXPOSE 5000

# Health Check - check if uvicorn is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=2 \
    CMD pgrep -f uvicorn || exit 1

# Run uvicorn with PORT env var (Render sets this automatically to match EXPOSE)  
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-5000} --log-level info"]
