from fastapi import APIRouter
from .health import router as health_router
from .status import router as status_router
from .auth import router as auth_router
from .chat import router as chat_router
from .analyze import router as analyze_router
from .code import router as code_router
from .reap import router as reap_router
from .essence import router as essence_router
from .hyperspeed import router as hyperspeed_router
from .quantum import router as quantum_router

router = APIRouter()

# Mount all routers
router.include_router(health_router)
router.include_router(status_router)
router.include_router(auth_router, prefix="/auth")  # Fixed: add /auth prefix
router.include_router(chat_router)
router.include_router(analyze_router)
router.include_router(code_router)
router.include_router(reap_router)
router.include_router(essence_router)
router.include_router(hyperspeed_router)
router.include_router(quantum_router)