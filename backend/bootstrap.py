"""
Bootstrap script for Roboto SAI FastAPI backend
Handles import verification and startup logging
"""
import os
import sys
import logging

# Configure logging immediately
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG") else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

logger.info("🚀 Roboto SAI Backend Bootstrap Starting...")
logger.info(f"Python: {sys.version}")
logger.info(f"Working Directory: {os.getcwd()}")
logger.info(f"PORT: {os.getenv('PORT', 'NOT SET - will use default')}")

# Test critical imports
try:
    logger.info("Testing critical imports...")
    import fastapi
    logger.debug(f"✅ FastAPI {fastapi.__version__}")
    
    import uvicorn
    logger.debug(f"✅ Uvicorn {uvicorn.__version__}")
    
    import pydantic
    logger.debug(f"✅ Pydantic {pydantic.__version__}")
    
    logger.info("✅ Core dependencies available")
except ImportError as e:
    logger.error(f"❌ Missing core dependency: {e}")
    sys.exit(1)

# Test optional imports
try:
    from roboto_sai_sdk import RobotoSAIClient
    logger.info("✅ Roboto SAI SDK available")
except ImportError as e:
    logger.warning(f"⚠️ Roboto SAI SDK not available: {e}")

# Import application
try:
    logger.info("Importing main application...")
    from main import app
    logger.info("✅ Main application imported successfully")
except Exception as e:
    logger.error(f"❌ Failed to import app: {e}", exc_info=True)
    sys.exit(1)

# Start uvicorn
logger.info("🚀 Starting uvicorn server...")
port = int(os.getenv("PORT", 5000))
logger.info(f"Listening on 0.0.0.0:{port}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
        reload=False
    )
