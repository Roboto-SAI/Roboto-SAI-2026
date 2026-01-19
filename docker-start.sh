#!/bin/bash
# Roboto SAI 2026 - Quick Start Script for Unix/Linux/Mac
# Usage: ./docker-start.sh [dev|prod|build|stop]

set -e

COMMAND=${1:-dev}

echo "🔥 Roboto SAI 2026 - Fuego Eterno Edition 🔥"
echo "=================================================="

case $COMMAND in
    dev)
        echo "🚀 Starting development environment..."
        echo "   Hot reload enabled on http://localhost:8080"
        docker-compose --profile dev up
        ;;
    prod)
        echo "🏭 Starting production environment..."
        echo "   Production build on http://localhost"
        docker-compose --profile prod up -d
        echo ""
        echo "✅ Production container running in background"
        echo "   View logs: ./docker-start.sh logs"
        ;;
    build)
        echo "🔨 Building Docker images..."
        docker build --target development -t roboto-sai:dev .
        docker build --target production -t roboto-sai:prod .
        echo ""
        echo "✅ Build complete!"
        ;;
    stop)
        echo "🛑 Stopping all containers..."
        docker-compose down
        echo "✅ All containers stopped"
        ;;
    logs)
        echo "📋 Showing container logs..."
        docker-compose logs -f
        ;;
    clean)
        echo "🧹 Cleaning up Docker resources..."
        docker-compose down -v
        docker system prune -f
        echo "✅ Cleanup complete!"
        ;;
    *)
        echo "Usage: $0 [dev|prod|build|stop|logs|clean]"
        exit 1
        ;;
esac

echo ""
echo "© 2025-2026 Roberto Villarreal Martinez"
echo "Roboto SAI - All Rights Reserved"
