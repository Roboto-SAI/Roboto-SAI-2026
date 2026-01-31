# Roboto SAI 2026 - Fuego Eterno Edition
# Multi-stage Dockerfile with Node.js and Python support
# Created for development flexibility and production optimization

# Stage 1: Base with Python support
FROM node:20-slim AS base

# Install Python and essential build tools
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python command and create an isolated venv for Python packages to avoid PEP 668
RUN ln -s /usr/bin/python3 /usr/bin/python \
    && python -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --upgrade pip setuptools wheel \
    && /opt/venv/bin/pip install --no-cache-dir uv \
    && ln -s /opt/venv/bin/uvx /usr/local/bin/uvx

# Ensure virtualenv binaries are on PATH
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm ci --legacy-peer-deps

# Stage 2: Development
FROM base AS development

# Set development environment
ENV NODE_ENV=development

# Copy application code
COPY . .

# Expose Vite dev server port (from vite.config.ts)
EXPOSE 8080

# Start development server with host binding
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Stage 3: Build
FROM base AS build

# Accept build arguments for environment variables
ARG VITE_API_BASE_URL
ARG VITE_API_URL
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY

# Set environment variables for build
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Stage 4: Production
FROM nginx:alpine AS production

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Create nginx config for SPA routing with PORT support
COPY <<'EOF' /docker-entrypoint.d/40-port-config.sh
#!/bin/sh
set -e

# Use PORT from environment or default to 80
PORT=${PORT:-80}

# Update nginx config with dynamic port
sed -i "s/listen 80;/listen $PORT;/g" /etc/nginx/conf.d/default.conf

echo "Nginx configured to listen on port $PORT"
EOF

RUN chmod +x /docker-entrypoint.d/40-port-config.sh

# Create nginx config for SPA routing
RUN echo 'server { \
    listen 80; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    # Security headers \
    add_header X-Frame-Options "SAMEORIGIN" always; \
    add_header X-Content-Type-Options "nosniff" always; \
    add_header X-XSS-Protection "1; mode=block" always; \
    # Cache static assets \
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
