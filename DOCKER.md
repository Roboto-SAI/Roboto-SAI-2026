# Docker Setup for Roboto SAI 2026 - Fuego Eterno Edition

This guide covers containerization for the Roboto SAI application with both Node.js and Python support.

## Architecture

The Dockerfile uses a multi-stage build process:

1. **Base Stage**: Node.js 20 + Python 3 + build tools
2. **Development Stage**: Hot-reload enabled development environment
3. **Build Stage**: Production build compilation
4. **Production Stage**: Optimized nginx-alpine with Python support

## Quick Start

### Development Mode

Run the application in development mode with hot reload:

```bash
# Using Docker Compose (recommended)
docker-compose --profile dev up

# Or using Docker directly
docker build --target development -t roboto-sai:dev .
docker run -p 8080:8080 -v ${PWD}:/app -v /app/node_modules roboto-sai:dev
```

Access the application at: http://localhost:8080

### Production Mode

Build and run the optimized production container:

```bash
# Using Docker Compose (recommended)
docker-compose --profile prod up -d

# Or using Docker directly
docker build --target production -t roboto-sai:prod .
docker run -p 80:80 roboto-sai:prod
```

Access the application at: http://localhost

## Available Commands

### Build Commands

```bash
# Build development image
docker build --target development -t roboto-sai:dev .

# Build production image
docker build --target production -t roboto-sai:prod .

# Build specific stage
docker build --target base -t roboto-sai:base .
docker build --target build -t roboto-sai:build .
```

### Run Commands

```bash
# Run development (with volume mount for hot reload)
docker run -p 8080:8080 -v ${PWD}:/app -v /app/node_modules roboto-sai:dev

# Run production
docker run -p 80:80 roboto-sai:prod

# Run with custom port
docker run -p 3000:80 roboto-sai:prod
```

### Docker Compose Commands

```bash
# Start development environment
docker-compose --profile dev up

# Start development in background
docker-compose --profile dev up -d

# Start production environment
docker-compose --profile prod up -d

# Stop services
docker-compose down

# Rebuild and start
docker-compose --profile dev up --build

# View logs
docker-compose logs -f

# Remove all containers and volumes
docker-compose down -v
```

## Features

### Python Support

Both development and production images include Python 3:

- **Development**: Python 3 + pip + venv on Debian-based Node.js image
- **Production**: Python 3 + pip on Alpine-based nginx image

This enables future integration with Python backends, ML models, or data processing scripts.

### Hot Reload (Development)

The development container mounts your source code as a volume, enabling instant hot reload when you make changes.

### Optimized Production Build

The production image:
- Uses nginx-alpine (lightweight ~40MB)
- Includes security headers
- Configures SPA routing (all routes → index.html)
- Sets cache headers for static assets
- Includes Python for backend flexibility

### Security Features

Production nginx configuration includes:
- X-Frame-Options: SAMEORIGIN
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Cache-Control for static assets

## Environment Variables

You can pass environment variables to containers:

```bash
# Development
docker run -p 8080:8080 -e NODE_ENV=development roboto-sai:dev

# Production
docker run -p 80:80 -e NODE_ENV=production roboto-sai:prod
```

## Volumes

### Development Volumes

```bash
# Mount entire project (hot reload)
-v ${PWD}:/app

# Preserve node_modules (anonymous volume)
-v /app/node_modules
```

## Ports

- **Development**: 8080 (Vite dev server)
- **Production**: 80 (nginx)

To use different ports:

```bash
# Development on port 3000
docker run -p 3000:8080 roboto-sai:dev

# Production on port 8080
docker run -p 8080:80 roboto-sai:prod
```

## Troubleshooting

### Container won't start

```bash
# Check container logs
docker logs roboto-sai-dev
docker logs roboto-sai-prod

# Or with Docker Compose
docker-compose logs
```

### Hot reload not working

Ensure you're mounting volumes correctly:

```bash
docker run -p 8080:8080 -v ${PWD}:/app -v /app/node_modules roboto-sai:dev
```

### Build fails

```bash
# Clean build (no cache)
docker build --no-cache --target development -t roboto-sai:dev .

# Check Docker disk space
docker system df
docker system prune
```

### Port already in use

```bash
# Find process using port 8080
netstat -ano | findstr :8080

# Use different port
docker run -p 3000:8080 roboto-sai:dev
```

## Future Enhancements

The current setup is ready for:

1. **Python Backend Integration**: Uncomment the backend service in docker-compose.yml
2. **Database Services**: Add PostgreSQL, MongoDB, or Redis
3. **Reverse Proxy**: Add Traefik or nginx proxy for multi-service routing
4. **CI/CD**: GitHub Actions or GitLab CI for automated builds
5. **Kubernetes**: Use the Dockerfile as base for K8s deployments

## License

© 2025-2026 Roberto Villarreal Martinez - All Rights Reserved Worldwide  
See LICENSE file for full terms (RVM-ECOL v1.0 & RVM-GUL v1.0)
