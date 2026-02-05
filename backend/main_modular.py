"""
Roboto SAI 2026 Modular Backend
================================

FastAPI application with modular routers and quantum integration.

Endpoints:
- /api/health - Health check
- /api/status - Status with quantum info
- /api/chat - Chat with Grok + memory
- /api/analyze - Entangled reasoning analysis
- /api/code - Code generation
- /api/reap - Reaper mode for chain breaking
- /api/essence/store - Store essence with embeddings
- /api/essence/retrieve - Retrieve filtered essence
- /api/hyperspeed-evolution - Evolution orchestrator
- /api/quantum/* - Quantum simulations and optimizations

Authors: Roboto SAI Development Team
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Rate limiting (requires slowapi)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    print("⚠️ slowapi not available - rate limiting disabled")
    RATE_LIMITING_AVAILABLE = False

# Import modular API router
from api import router as api_router

# Initialize quantum and evolution kernels
from services.quantum_engine import initialize_quantum_kernel
from services.evolution_engine import initialize_evolution_kernel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("🚀 Starting Roboto SAI 2026 Modular Backend...")
    
    # Initialize quantum kernel
    logger.info("🔬 Initializing quantum kernel...")
    quantum_kernel = initialize_quantum_kernel()
    logger.info("✅ Quantum kernel initialized")
    
    # Initialize evolution kernel
    logger.info("🧬 Initializing evolution kernel...")
    evolution_kernel = initialize_evolution_kernel()
    logger.info("✅ Evolution kernel initialized")
    
    yield
    logger.info("🛑 Shutting down Roboto SAI 2026 Modular Backend...")

# Create FastAPI app
app = FastAPI(
    title="Roboto SAI 2026 Backend",
    description="Quantum-ready AI backend with Grok integration and advanced memory systems",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS origins from environment
frontend_origins_env = os.getenv("FRONTEND_ORIGIN", "http://localhost:8080")
allowed_frontend_origins: List[str] = [origin.strip() for origin in frontend_origins_env.split(",") if origin.strip()]
if not allowed_frontend_origins:
    allowed_frontend_origins = ["http://localhost:8080"]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Set-Cookie"],
)

# Rate limiting setup (if available)
if RATE_LIMITING_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    logger.info("✅ Rate limiting enabled")
else:
    logger.warning("⚠️ Rate limiting disabled (slowapi not available)")

# Include modular API routers
app.include_router(api_router, prefix="/api")

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info"""
    return {
        "service": "Roboto SAI 2026 Modular Backend",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "/api/status",
        "health": "/api/health",
        "rate_limiting": RATE_LIMITING_AVAILABLE
    }

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"🚀 Starting Roboto SAI 2026 Backend on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )