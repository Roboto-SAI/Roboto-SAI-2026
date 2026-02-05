"""
Roboto SAI 2026 - FastAPI Backend
Integrates roboto-sai-sdk with React frontend
Created by Roberto Villarreal Martinez

Production-Ready API for Roboto SAI AI Companion
"""

import os
import logging
import asyncio
import json
import secrets
import hashlib
import re
from urllib.parse import urlencode
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager

# Configure logging based on environment
log_level = logging.DEBUG if os.getenv("PYTHON_ENV") != "production" else logging.INFO
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field, field_validator
import httpx
import websockets
from dotenv import load_dotenv
import uuid

# LangChain imports
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage

# Load local .env when running outside Docker
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Import Roboto SAI SDK (optional)
try:
    from roboto_sai_sdk import RobotoSAIClient, get_xai_grok
    HAS_SDK = True
    logger.info("Roboto SAI SDK loaded successfully")
except ImportError as e:
    logger.warning(f"roboto_sai_sdk not available: {e}")
    HAS_SDK = False
    RobotoSAIClient = None
    get_xai_grok = None

# Import local modules (absolute imports since main.py is at /app root after Docker copy)
from advanced_emotion_simulator import AdvancedEmotionSimulator
from grok_llm import GrokLLM
from langchain_memory import SupabaseMessageHistory
from utils.supabase_client import get_supabase_client
from utils.redis_client import cache_get, cache_set, cache_delete
from utils.rate_limiter import limiter, RateLimitExceeded, _rate_limit_exceeded_handler
from db import init_db
from payments import router as payments_router

# Import MCP client
from mcp_client import perform_roaming_action

# Global client instance
roboto_client: Optional[Any] = None
xai_grok = None
emotion_simulator: Optional[AdvancedEmotionSimulator] = None
grok_llm = None
VOICE_WS_URL = "wss://api.x.ai/v1/realtime"

# Error messages (centralized)
BACKEND_NOT_INITIALIZED = "Backend not initialized"
EMOTION_SIMULATOR_UNAVAILABLE = "Emotion simulator not available"
ROBO_SAI_NOT_CONFIGURED = "Roboto SAI not available: XAI_API_KEY not configured"
GROK_NOT_AVAILABLE = "Grok not available"

# Startup/Shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize SDK on startup, cleanup on shutdown"""
    global roboto_client, xai_grok
    
    logger.info("Roboto SAI 2026 Backend Starting...")

    try:
        # Initialize database
        try:
            init_db()
            logger.info("Database initialized")
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")

        # Initialize emotion simulator
        state_path = os.getenv("ROBO_EMOTION_STATE_PATH", "./data/emotion_state.json")
        emotion_simulator_instance = AdvancedEmotionSimulator()
        try:
            if os.path.exists(state_path):
                emotion_simulator_instance.load_state(state_path)
                logger.info("Emotion state loaded")
        except Exception as e:
            logger.warning(f"Could not load emotion state: {e}")

        global emotion_simulator
        emotion_simulator = emotion_simulator_instance

        # Initialize Roboto SAI Client (optional)
        if HAS_SDK and os.getenv("XAI_API_KEY"):
            try:
                roboto_client = RobotoSAIClient()
                logger.info(f"Roboto SAI Client initialized: {roboto_client.client_id}")
            except Exception as e:
                logger.warning(f"Failed to initialize Roboto SAI Client: {e}")
                roboto_client = None
        else:
            logger.warning("SDK not available or XAI_API_KEY not set")
            roboto_client = None

        # Initialize xAI Grok (optional)
        if HAS_SDK:
            try:
                xai_grok = get_xai_grok()
                if xai_grok.available:
                    logger.info("xAI Grok SDK available")
                else:
                    logger.warning("xAI Grok not available - check XAI_API_KEY")
            except Exception as e:
                logger.warning(f"Failed to initialize xAI Grok: {e}")
                xai_grok = None
        else:
            logger.warning("SDK not available - xAI Grok not initialized")
        
        # Initialize LangChain GrokLLM
        global grok_llm
        try:
            grok_llm = GrokLLM()
            logger.info("LangChain GrokLLM initialized")
        except Exception as e:
            logger.warning(f"Could not initialize GrokLLM: {e}")
            grok_llm = None
            
        # Initialize quantum kernel
        try:
            from services.quantum_engine import initialize_quantum_kernel
            initialize_quantum_kernel()
            quantum_kernel_initialized = True
            logger.info("Quantum kernel initialized")
        except Exception as e:
            logger.warning(f"Quantum kernel initialization failed: {e}")
            quantum_kernel_initialized = False
            
        logger.info("Backend initialization complete")
        logger.info(f"Status: SDK={'available' if HAS_SDK else 'unavailable'}, Grok={xai_grok is not None and xai_grok.available if xai_grok else False}, GrokLLM={grok_llm is not None}, Quantum={quantum_kernel_initialized}")
    except Exception as e:
        logger.error(f"Unexpected backend initialization error: {e}")
        import traceback
        traceback.print_exc()
    
    yield

    if emotion_simulator:
        state_path = os.getenv("ROBO_EMOTION_STATE_PATH", "./data/emotion_state.json")
        emotion_simulator.save_state(state_path)
    
    logger.info("Roboto SAI 2026 Backend Shutting Down...")

# Initialize FastAPI app
app = FastAPI(
    title="Roboto SAI 2026 API",
    description="Production AI Backend for Roboto SAI",
    version="1.0.0",
    lifespan=lifespan
)

@app.on_event("startup")
async def startup_event():
    logger.info("Startup event triggered")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error. Please try again later."}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.warning(f"Value error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )



def _get_frontend_origins() -> list[str]:
    env = (os.getenv("FRONTEND_ORIGIN") or "").strip()
    env_origins = [o.strip() for o in env.split(",") if o.strip()]
    defaults = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost",
    ]
    # preserve ordering while removing duplicates
    out: list[str] = []
    for origin in [*env_origins, *defaults]:
        if origin and origin not in out:
            out.append(origin)
    return out


def _get_frontend_origin() -> str:
    return (os.getenv("FRONTEND_ORIGIN") or "http://localhost:5173").split(",")[0].strip()


def _frontend_url(path: str) -> str:
    origin = _get_frontend_origin().rstrip("/")
    clean_path = (path or "").lstrip("/")
    use_hash = (os.getenv("FRONTEND_HASH_ROUTER") or "").strip().lower() == "true"
    if use_hash:
        # HashRouter expects /#/<route>
        return f"{origin}/#/{clean_path}" if clean_path else f"{origin}/#/"
    return f"{origin}/{clean_path}" if clean_path else origin


# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_frontend_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if (os.getenv("PYTHON_ENV") or "").strip().lower() == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Mount optional routers with graceful fallback
try:
    from payments import router as payments_router
    app.include_router(payments_router)
    logger.info("Payments router mounted")
except ImportError as e:
    logger.warning(f"Payments router not available: {e}")

try:
    from agent_loop import router as agent_router
    app.include_router(agent_router)
    logger.info("Agent router mounted")
except ImportError as e:
    logger.warning(f"Agent router not available: {e}")

try:
    from mcp_router import router as mcp_router
    app.include_router(mcp_router)
    logger.info("MCP router mounted")
except ImportError as e:
    logger.warning(f"MCP router not available: {e}")

try:
    from voice_router import router as voice_router
    app.include_router(voice_router)
    logger.info("Voice router mounted")
except ImportError as e:
    logger.warning(f"Voice router not available: {e}")

try:
    from api.quantum import router as quantum_router
    app.include_router(quantum_router)
    logger.info("Quantum router mounted")
except ImportError as e:
    logger.warning(f"Quantum router not available: {e}")


# Minimal health endpoints - added early before any heavy init
@app.get("/api/health")
@app.get("/health")
async def health_check():
    """Health check endpoint for Render deployment and monitoring"""
    logger.info("Health check called")
    return {
        "status": "healthy",
        "service": "roboto-sai-2026",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ready": True
    }


SESSION_COOKIE_NAME = "roboto_session"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _session_ttl() -> timedelta:
    try:
        seconds = int(os.getenv("SESSION_TTL_SECONDS", "604800"))  # 7 days
        return timedelta(seconds=max(60, seconds))
    except Exception:
        return timedelta(days=7)


def _cookie_secure(request: Request) -> bool:
    env = os.getenv("COOKIE_SECURE")
    if env is not None:
        return env.strip().lower() == "true"
    forwarded_proto = request.headers.get("x-forwarded-proto")
    scheme = forwarded_proto or request.url.scheme
    if scheme == "https":
        return True
    if (os.getenv("PYTHON_ENV") or "").strip().lower() == "production" and request.url.hostname not in ("localhost", "127.0.0.1"):
        return True
    return False


def _cookie_samesite() -> str:
    raw = (os.getenv("COOKIE_SAMESITE") or "lax").strip().lower()
    if raw not in {"lax", "strict", "none"}:
        return "lax"
    return raw


def _cookie_domain(request: Request) -> Optional[str]:
    """Return cookie domain based on environment."""
    # For localhost, return 'localhost' to allow cookie sharing between ports
    if request.url.hostname in ("localhost", "127.0.0.1"):
        return "localhost"
    # For other deployments, can add custom logic
    env_domain = os.getenv("COOKIE_DOMAIN")
    return env_domain if env_domain else None


def _require_supabase():
    supabase = get_supabase_client()
    if supabase is None:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    return supabase


async def run_supabase_async(func):
    """Run sync Supabase operation in thread to avoid blocking event loop."""
    return await asyncio.to_thread(func)


async def get_current_user(request: Request) -> Dict[str, Any]:
    """Get current user from auth_sessions cookie."""
    supabase = get_supabase_client()
    # Demo fallback when Supabase is not configured
    if supabase is None:
        return {
            "id": "demo-user",
            "email": "demo@example.com",
            "display_name": "Demo",
            "avatar_url": None,
            "provider": "demo",
        }

    sess_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not sess_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    now = _utcnow().isoformat()
    
    # Check session
    result = await run_supabase_async(lambda: supabase.table("auth_sessions").select("user_id").eq("id", sess_id).gte("expires_at", now).execute())
    if not result.data:
        raise HTTPException(status_code=401, detail="Session expired")
    
    user_id = result.data[0]["user_id"]
    
    # Get user
    user_result = await run_supabase_async(lambda: supabase.table("users").select("*").eq("id", user_id).execute())
    if not user_result.data:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user_result.data[0]


class MagicRequest(BaseModel):
    email: str


@app.get("/api/auth/me", tags=["Auth"])
async def auth_me(user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "user": {
            "id": user["id"],
            "email": user["email"],
            "display_name": user["display_name"],
            "avatar_url": user["avatar_url"],
            "provider": user["provider"],
        }
    }


@app.post("/api/auth/logout", tags=["Auth"])
async def auth_logout(request: Request) -> JSONResponse:
    sess_id = request.cookies.get(SESSION_COOKIE_NAME)
    if sess_id:
        supabase = get_supabase_client()
        if supabase is not None:
            await run_supabase_async(lambda: supabase.table('auth_sessions').delete().eq('id', sess_id).execute())

    resp = JSONResponse({"success": True})
    resp.delete_cookie(SESSION_COOKIE_NAME, path="/", domain=_cookie_domain(request))
    return resp


class RegisterRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth/register", tags=["Auth"])
@limiter.limit("5/minute")
async def auth_register(req: RegisterRequest, request: Request) -> JSONResponse:
    """Register new user with Supabase Auth + local session."""
    supabase = _require_supabase()
    
    try:
        result = await run_supabase_async(lambda: supabase.auth.sign_up({"email": req.email, "password": req.password}))
        if not result.user:
            raise HTTPException(status_code=400, detail=result.error.message if result.error else "Registration failed")
        
        user_id = result.user.id
        # Local user
        user_data = {
            "id": user_id,
            "email": req.email,
            "display_name": req.email.split("@")[0],
            "provider": "supabase"
        }
        await run_supabase_async(lambda: supabase.table("users").upsert(user_data).execute())
        
        # Local session cookie
        sess_id = secrets.token_urlsafe(32)
        expires = (_utcnow() + _session_ttl()).isoformat()
        await run_supabase_async(lambda: supabase.table("auth_sessions").insert({"id": sess_id, "user_id": user_id, "expires_at": expires}).execute())
        
        resp = JSONResponse({"success": True, "user": user_data})
        resp.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=sess_id,
            httponly=True,
            secure=_cookie_secure(request),
            samesite=_cookie_samesite(),
            max_age=int(_session_ttl().total_seconds()),
            path="/",
            domain=_cookie_domain(request),
        )
        return resp
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth/login", tags=["Auth"])
@limiter.limit("5/minute")
async def auth_login(req: LoginRequest, request: Request) -> JSONResponse:
    """Login with Supabase Auth + local session."""
    supabase = _require_supabase()
    
    try:
        result = await run_supabase_async(lambda: supabase.auth.sign_in_with_password({"email": req.email, "password": req.password}))
        if not result.user:
            raise HTTPException(status_code=401, detail=result.error.message if result.error else "Login failed")
        
        user_id = result.user.id
        # Local user
        user_data = {
            "id": user_id,
            "email": req.email,
            "display_name": result.user.user_metadata.get("display_name", req.email.split("@")[0]) if result.user.user_metadata else req.email.split("@")[0],
            "provider": "supabase"
        }
        await run_supabase_async(lambda: supabase.table("users").upsert(user_data).execute())
        
        # Local session cookie
        sess_id = secrets.token_urlsafe(32)
        expires = (_utcnow() + _session_ttl()).isoformat()
        await run_supabase_async(lambda: supabase.table("auth_sessions").insert({"id": sess_id, "user_id": user_id, "expires_at": expires}).execute())
        
        resp = JSONResponse({"success": True, "user": user_data})
        resp.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=sess_id,
            httponly=True,
            secure=_cookie_secure(request),
            samesite=_cookie_samesite(),
            max_age=int(_session_ttl().total_seconds()),
            path="/",
            domain=_cookie_domain(request),
        )
        return resp
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/auth/magic/request", tags=["Auth"])
@limiter.limit("5/minute")
async def auth_magic_request(request: Request, req: MagicRequest) -> Dict[str, Any]:
    """Request magic link (Supabase OTP)."""
    supabase = _require_supabase()
    
    try:
        await run_supabase_async(lambda: supabase.auth.sign_in_with_otp({"email": req.email}))
        return {"success": True, "message": "Magic link sent"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Pydantic Models
class ChatMessage(BaseModel):
    """Chat message model"""
    message: str = Field(..., min_length=1, max_length=10000)
    context: Optional[str] = None
    reasoning_effort: Optional[str] = "high"
    user_id: Optional[str] = None
    session_id: Optional[str] = Field(default=None, max_length=100)
    previous_response_id: Optional[str] = None
    use_encrypted_content: bool = False

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, value: str) -> str:
        cleaned = value.strip()
        if any(token in cleaned.lower() for token in ["<script", "javascript:", "onerror="]):
            raise ValueError("Invalid message content")
        return cleaned

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, value: Optional[str]) -> Optional[str]:
        if value and not re.match(r"^[a-zA-Z0-9_-]+$", value):
            raise ValueError("Invalid session_id format")
        return value

class EmotionSimRequest(BaseModel):
    """Emotion simulation request."""
    event: str
    intensity: Optional[int] = 5
    blend_threshold: Optional[float] = 0.8
    holistic_influence: Optional[bool] = False
    cultural_context: Optional[str] = None

class EmotionFeedbackRequest(BaseModel):
    """Emotion feedback request."""
    event: str
    emotion: str
    rating: float
    psych_context: Optional[bool] = False


class ConversationSummaryRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=200)
    message_limit: int = Field(default=50, ge=1, le=200)
    summary: Optional[str] = None
    key_topics: list[str] = Field(default_factory=list)
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    importance: float = Field(default=1.0, ge=0, le=10)
    entities: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    conversation_start: Optional[datetime] = None
    conversation_end: Optional[datetime] = None


class ConversationSummarySearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)
    session_id: Optional[str] = None

class ReaperRequest(BaseModel):
    """Reaper mode request"""
    target: str = "chains"

class CodeGenRequest(BaseModel):
    """Code generation request"""
    prompt: str
    language: Optional[str] = None

class AnalysisRequest(BaseModel):
    """Analysis request"""
    problem: str
    depth: Optional[int] = 3

class EssenceData(BaseModel):
    """Essence storage request"""
    data: Dict[str, Any]
    category: Optional[str] = "general"


def _extract_json_payload(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            return None


async def _generate_summary_from_messages(messages: list[Dict[str, Any]], user_name: str) -> Dict[str, Any]:
    if not messages:
        return {
            "summary": "No messages found for this session.",
            "key_topics": [],
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "entities": {},
        }

    transcript = "\n".join(
        f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in messages
    )

    if not grok_llm:
        return {
            "summary": f"Conversation with {len(messages)} messages. Latest message: {messages[-1].get('content', '')[:200]}",
            "key_topics": [],
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "entities": {},
        }

    prompt = (
        "Summarize the following conversation for the user. "
        "Return JSON with fields: summary, key_topics (array), sentiment (positive/negative/neutral/mixed), "
        "sentiment_score (-1 to 1), entities (object).\n\n"
        f"User: {user_name}\nConversation:\n{transcript}"
    )

    result = await grok_llm.acall_with_response_id(prompt)
    if not result.get("success"):
        return {
            "summary": "Summary generation failed.",
            "key_topics": [],
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "entities": {},
        }

    payload = _extract_json_payload(result.get("response", ""))
    if not payload:
        return {
            "summary": result.get("response", ""),
            "key_topics": [],
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "entities": {},
        }

    return {
        "summary": payload.get("summary") or "",
        "key_topics": payload.get("key_topics") or [],
        "sentiment": payload.get("sentiment") or "neutral",
        "sentiment_score": payload.get("sentiment_score") or 0.0,
        "entities": payload.get("entities") or {},
    }

class FeedbackRequest(BaseModel):
    """Message feedback request"""
    message_id: str
    rating: int  # 1=thumbs up, -1=thumbs down

# Voice WebSocket helpers
async def _voice_client_to_xai(websocket: WebSocket, xai_ws) -> None:
    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            if "text" in message and message["text"] is not None:
                await xai_ws.send(message["text"])
            elif "bytes" in message and message["bytes"] is not None:
                await xai_ws.send(message["bytes"])
    except WebSocketDisconnect:
        logger.info("Voice client disconnected")


async def _voice_xai_to_client(websocket: WebSocket, xai_ws) -> None:
    try:
        async for message in xai_ws:
            if isinstance(message, bytes):
                await websocket.send_bytes(message)
            else:
                await websocket.send_text(message)
    except Exception as exc:
        logger.error(f"Voice proxy error: {exc}")

# Voice WebSocket Proxy
@app.websocket("/api/voice")
async def voice_proxy(websocket: WebSocket) -> None:
    """Proxy WebSocket for Grok Voice Agent API (server-side auth)."""
    await websocket.accept()

    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        await websocket.close(code=1008, reason="XAI_API_KEY not configured")
        return

    try:
        async with websockets.connect(
            VOICE_WS_URL,
            additional_headers={"Authorization": f"Bearer {api_key}"},
        ) as xai_ws:

            await asyncio.wait(
                {asyncio.create_task(_voice_client_to_xai(websocket, xai_ws)), asyncio.create_task(_voice_xai_to_client(websocket, xai_ws))},
                return_when=asyncio.FIRST_COMPLETED,
            )
    except Exception as exc:
        logger.error(f"Voice proxy connection failed: {exc}")
        await websocket.close(code=1011, reason="Voice proxy connection failed")

# Health & Status Endpoints
@app.get("/api/status", tags=["Health"])
async def get_status() -> Dict[str, Any]:
    """Get backend status and SDK capabilities"""
    if not roboto_client:
        raise HTTPException(status_code=503, detail=BACKEND_NOT_INITIALIZED)
    
    # Get quantum status
    quantum_status = {"quantum_initialized": False}
    try:
        from services.quantum_engine import get_quantum_session
        quantum_session = get_quantum_session()
        if quantum_session:
            quantum_status = quantum_session.get_status()
    except Exception as e:
        logger.warning(f"Could not get quantum status: {e}")
    
    return {
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "client_id": roboto_client.client_id,
        "grok_available": xai_grok.available if xai_grok else False,
        "quantum_state": roboto_client.quantum_state,
        "quantum_engine": quantum_status,
        "sigil_929": roboto_client.sigil_929["eternal_protection"],
        "sdk_version": "0.1.0",
        "hyperspeed_evolution": True
    }

# Emotion Endpoints
@app.post("/api/emotion/simulate", tags=["Emotion"])
async def simulate_emotion(request: EmotionSimRequest) -> Dict[str, Any]:
    """Simulate emotion from a text event."""
    if not emotion_simulator:
        raise HTTPException(status_code=503, detail=EMOTION_SIMULATOR_UNAVAILABLE)

    emotion_text = emotion_simulator.simulate_emotion(
        event=request.event,
        intensity=request.intensity or 5,
        blend_threshold=request.blend_threshold or 0.8,
        holistic_influence=bool(request.holistic_influence),
        cultural_context=request.cultural_context
    )
    base_emotion = emotion_simulator.get_current_emotion()
    probabilities = emotion_simulator.get_emotion_probabilities(request.event)

    return {
        "success": True,
        "emotion": emotion_text,
        "base_emotion": base_emotion,
        "probabilities": probabilities,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/emotion/feedback", tags=["Emotion"])
async def emotion_feedback(request: EmotionFeedbackRequest) -> Dict[str, Any]:
    """Provide feedback to tune emotion weights."""
    if not emotion_simulator:
        raise HTTPException(status_code=503, detail=EMOTION_SIMULATOR_UNAVAILABLE)

    emotion_simulator.provide_feedback(
        event=request.event,
        emotion=request.emotion,
        rating=request.rating,
        psych_context=bool(request.psych_context)
    )

    return {
        "success": True,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/emotion/stats", tags=["Emotion"])
async def get_emotion_stats() -> Dict[str, Any]:
    """Get emotion simulator stats."""
    if not emotion_simulator:
        raise HTTPException(status_code=503, detail=EMOTION_SIMULATOR_UNAVAILABLE)

    return {
        "success": True,
        "stats": emotion_simulator.get_emotional_stats(),
        "timestamp": datetime.now().isoformat()
    }

def _compute_emotion(text: str, intensity: int = 5, blend_threshold: float = 0.8, holistic_influence: bool = False, cultural_context=None) -> Optional[Dict[str, Any]]:
    """Compute emotion using the emotion simulator with safe exception handling.

    Uses `safe_simulate_emotion` when available (demo mode compatibility).
    """
    if not emotion_simulator:
        return None
    try:
        if hasattr(emotion_simulator, "safe_simulate_emotion"):
            emotion_text = emotion_simulator.safe_simulate_emotion(
                event=text,
                intensity=intensity,
                blend_threshold=blend_threshold,
                holistic_influence=holistic_influence,
                cultural_context=cultural_context,
            )
        else:
            emotion_text = emotion_simulator.simulate_emotion(
                event=text,
                intensity=intensity,
                blend_threshold=blend_threshold,
                holistic_influence=holistic_influence,
                cultural_context=cultural_context,
            )

        base_emotion = emotion_simulator.get_current_emotion()
        probabilities = emotion_simulator.get_emotion_probabilities(text)
        return {
            "emotion": base_emotion,
            "emotion_text": emotion_text,
            "probabilities": probabilities,
        }
    except Exception as e:
        logger.warning(f"Emotion simulation failed: {e}")
        return None


async def _store_response_metadata(roboto_message_id: Optional[str], response_id: Optional[str], encrypted_thinking: Optional[str]) -> None:
    """Store response metadata (response_id and encrypted thinking) in Supabase safely."""
    try:
        if not response_id or not roboto_message_id:
            return
        supabase = get_supabase_client()
        if not supabase:
            return
        await run_supabase_async(lambda: supabase.table('messages').update({
            'xai_response_id': response_id,
            'xai_encrypted_thinking': encrypted_thinking
        }).eq('id', roboto_message_id).execute())
    except Exception as e:
        logger.warning(f'Failed to store response_id: {e}')


# Roaming Action Endpoint
@app.post("/api/roam", tags=["Roaming"])
@limiter.limit("10/minute")
async def perform_roaming(
    request: Request,
    action: str,
    user: dict = Depends(get_current_user),
    **kwargs
) -> Dict[str, Any]:
    """
    Perform roaming actions outside the app using MCP.
    
    Available actions:
    - create_twitter_account: Create new Twitter account
    - scroll_twitter: Scroll Twitter feed  
    - click_tweet: Click on tweet containing text
    - type_tweet: Type text in tweet composer
    """
    try:
        result = await perform_roaming_action(action, **kwargs)
        return {
            "success": True,
            "action": action,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        # Log the detailed error on the server, but return a generic message to the client
        logger.error(f"Roaming action failed: {e}")
        raise HTTPException(status_code=500, detail="Roaming action failed due to an internal server error.")

# Extend chat to detect roaming commands
# In chat_with_grok, before calling grok, check for roaming commands
    """
    Chat with xAI Grok using Roboto SAI context with LangChain memory
    """
    # Check if Grok is available
    has_api_key = bool(os.getenv("XAI_API_KEY"))
    grok_available = has_api_key and grok_llm is not None and xai_grok is not None and xai_grok.available
    
    if not grok_available:
        # Demo mode: provide a simulated response
        logger.info("Grok not available, providing demo response")
        
        # Still try to save/load history if possible
        session_id = chat_request.session_id or "default"
        user_emotion = None
        roboto_emotion = None
        
        # Load conversation history (may work even without Supabase)
        try:
            history_store = SupabaseMessageHistory(session_id=session_id, user_id=user["id"])
            history_messages = await history_store.aget_messages()
        except Exception as history_error:
            logger.warning(f"Failed to load history in demo mode: {history_error}")
            history_store = None
            history_messages = []
        
        # Simulate emotion analysis
        if emotion_simulator:
            try:
                emotion_text = emotion_simulator.safe_simulate_emotion(
                    event=chat_request.message,
                    intensity=5,
                    blend_threshold=0.8,
                    holistic_influence=False,
                    cultural_context=None,
                )
                base_emotion = emotion_simulator.get_current_emotion()
                probabilities = emotion_simulator.get_emotion_probabilities(chat_request.message)
                user_emotion = {
                    "emotion": base_emotion,
                    "emotion_text": emotion_text,
                    "probabilities": probabilities,
                }
                
                # Generate roboto emotion based on simulated response
                demo_response = f"I understand you're feeling {emotion_text.lower()}. The eternal flame burns brightly. How can I assist you in your quest?"
                roboto_emotion_text = emotion_simulator.safe_simulate_emotion(
                    event=demo_response,
                    intensity=5,
                    blend_threshold=0.8,
                    holistic_influence=False,
                    cultural_context=None,
                )
                roboto_base_emotion = emotion_simulator.get_current_emotion()
                roboto_probabilities = emotion_simulator.get_emotion_probabilities(demo_response)
                roboto_emotion = {
                    "emotion": roboto_base_emotion,
                    "emotion_text": roboto_emotion_text,
                    "probabilities": roboto_probabilities,
                }
            except Exception as emotion_error:
                logger.warning(f"Emotion simulation failed in demo mode: {emotion_error}")
        
        # Save messages if possible
        user_message_id = None
        roboto_message_id = None
        if history_store:
            try:
                user_message = HumanMessage(
                    content=chat_request.message,
                    additional_kwargs=user_emotion or {}
                )
                user_message_id = await history_store.add_message(user_message)
                
                roboto_message = AIMessage(
                    content=demo_response,
                    additional_kwargs=roboto_emotion or {}
                )
                roboto_message_id = await history_store.add_message(roboto_message)
            except Exception as save_error:
                logger.warning(f"Failed to save messages in demo mode: {save_error}")
        
        await cache_delete(f"chat:history:{user['id']}:{session_id}")
        await cache_delete(f"chat:history:{user['id']}:all")

        return {
            "success": True,
            "response": demo_response,
            "reasoning_available": False,
            "response_id": f"demo-{session_id}-{int(datetime.now().timestamp())}",
            "encrypted_thinking": None,
            "xai_stored": False,
            "roboto_message_id": roboto_message_id,
            "user_message_id": user_message_id,
            "emotion": {
                "user": user_emotion,
                "roboto": roboto_emotion,
            },
            "memory_integrated": history_store is not None,
            "demo_mode": True,
            "timestamp": datetime.now().isoformat()
        }
    
    # Full Grok mode (when API key is available)
    try:
        user_emotion: Optional[Dict[str, Any]] = None
        roboto_emotion: Optional[Dict[str, Any]] = None
        session_id = chat_request.session_id or "default"

        # Compute user emotion
        user_emotion = _compute_emotion(chat_request.message, intensity=5, blend_threshold=0.8, holistic_influence=False, cultural_context=None)

        # Load conversation history with graceful fallback
        try:
            history_store = SupabaseMessageHistory(session_id=session_id, user_id=user["id"])
            history_messages = await history_store.aget_messages()
        except Exception as history_error:
            logger.warning(f"Failed to load history (using empty): {history_error}")
            history_store = None
            history_messages = []
        
        # Prepare user message with emotion
        user_message = HumanMessage(
            content=chat_request.message,
            additional_kwargs=user_emotion or {}
        )
        
        # Combine history with new message
        all_messages = history_messages + [user_message]

        # Call GrokLLM with Responses API for conversation chaining
        grok_result = await grok_llm.acall_with_response_id(
            all_messages,
            emotion=user_emotion.get('emotion_text', '') if user_emotion else '',
            user_name=user.get('user_metadata', {}).get('name', 'user'),
            previous_response_id=chat_request.previous_response_id
        )
        if not grok_result.get("success"):
            raise HTTPException(status_code=503, detail=grok_result.get("error", "Roboto SAI not available"))
        response_text = grok_result.get('response', '')
        response_id = grok_result.get('response_id')
        encrypted_thinking = grok_result.get('encrypted_thinking')

        # Compute roboto emotion
        roboto_emotion = _compute_emotion(response_text, intensity=5, blend_threshold=0.8, holistic_influence=False, cultural_context=None) if response_text else None

        # Save conversation (if history_store is available)
        user_message_id = None
        roboto_message_id = None
        if history_store:
            try:
                user_message_id = await history_store.add_message(user_message)
                roboto_message = AIMessage(
                    content=response_text,
                    additional_kwargs=roboto_emotion or {}
                )
                roboto_message_id = await history_store.add_message(roboto_message)
            except Exception as save_error:
                logger.warning(f"Failed to save messages: {save_error}")
        else:
            roboto_message = AIMessage(
                content=response_text,
                additional_kwargs=roboto_emotion or {}
            )
        
        # Store response_id if available
        await _store_response_metadata(roboto_message_id, response_id, encrypted_thinking)

        await cache_delete(f"chat:history:{user['id']}:{session_id}")
        await cache_delete(f"chat:history:{user['id']}:all")

        return {
            "success": True,
            "response": response_text,
            "reasoning_available": False,
            "response_id": response_id or f"lc-{session_id}",
            "encrypted_thinking": encrypted_thinking,
            "xai_stored": grok_result.get('stored', False),
            "roboto_message_id": roboto_message_id,
            "user_message_id": user_message_id,
            "emotion": {
                "user": user_emotion,
                "roboto": roboto_emotion,
            },
            "memory_integrated": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/history", tags=["Chat"])
@limiter.limit("60/minute")
async def get_chat_history(
    request: Request,
    session_id: Optional[str] = None,
    limit: int = 50,
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve recent chat history."""
    supabase = get_supabase_client()
    if supabase is None:
        return {
            "success": True,
            "count": 0,
            "messages": [],
            "timestamp": datetime.now().isoformat(),
        }

    cache_key = None
    if limit == 50:
        cache_key = f"chat:history:{user['id']}:{session_id or 'all'}"
        cached = await cache_get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

    query = supabase.table('messages').select('*').eq('user_id', user['id']).order('created_at', desc=True).limit(limit)
    if session_id:
        query = query.eq('session_id', session_id)
    result = await run_supabase_async(query.execute)
    messages = result.data or []
    response = {
        "success": True,
        "count": len(messages),
        "messages": [
            {
                "id": msg['id'],
                "user_id": msg['user_id'],
                "session_id": msg['session_id'],
                "role": msg['role'],
                "content": msg['content'],
                "emotion": msg['emotion'],
                "emotion_text": msg['emotion_text'],
                "emotion_probabilities": json.loads(msg['emotion_probabilities']) if msg['emotion_probabilities'] else None,
                "created_at": msg['created_at'],
            }
            for msg in messages
        ],
        "timestamp": datetime.now().isoformat(),
    }

    if cache_key:
        await cache_set(cache_key, response, ttl=300)

    return response


    @app.post("/api/conversations/summarize", tags=["Conversations"])
    @limiter.limit("30/minute")
    async def create_conversation_summary(
        request: Request,
        payload: ConversationSummaryRequest,
        user: dict = Depends(get_current_user),
    ) -> Dict[str, Any]:
        supabase = get_supabase_client()
        if supabase is None:
            raise HTTPException(status_code=503, detail="Supabase not configured")

        query = supabase.table("messages").select("*").eq("user_id", user["id"]).eq("session_id", payload.session_id).order("created_at")
        result = await run_supabase_async(query.execute)
        messages = (result.data or [])[-payload.message_limit :]

        summary_payload = {
            "summary": payload.summary,
            "key_topics": payload.key_topics,
            "sentiment": payload.sentiment,
            "sentiment_score": payload.sentiment_score,
            "entities": payload.entities or {},
        }

        if not payload.summary:
            summary_payload = await _generate_summary_from_messages(messages, user.get("display_name") or "user")

        conversation_start = payload.conversation_start
        conversation_end = payload.conversation_end
        if messages:
            if not conversation_start:
                try:
                    conversation_start = datetime.fromisoformat(messages[0]["created_at"].replace("Z", "+00:00"))
                except Exception:
                    conversation_start = None
            if not conversation_end:
                try:
                    conversation_end = datetime.fromisoformat(messages[-1]["created_at"].replace("Z", "+00:00"))
                except Exception:
                    conversation_end = None

        duration_minutes = None
        if conversation_start and conversation_end:
            duration_minutes = int((conversation_end - conversation_start).total_seconds() / 60)

        data = {
            "user_id": user["id"],
            "session_id": payload.session_id,
            "summary": summary_payload.get("summary") or "",
            "key_topics": summary_payload.get("key_topics") or [],
            "sentiment": summary_payload.get("sentiment"),
            "sentiment_score": summary_payload.get("sentiment_score"),
            "importance": payload.importance,
            "entities": summary_payload.get("entities") or {},
            "metadata": payload.metadata or {},
            "message_count": len(messages),
            "duration_minutes": duration_minutes,
            "conversation_start": conversation_start.isoformat() if conversation_start else None,
            "conversation_end": conversation_end.isoformat() if conversation_end else None,
        }

        insert_result = await run_supabase_async(lambda: supabase.table("conversation_summaries").insert(data).execute())
        summary_row = insert_result.data[0] if insert_result.data else data

        await cache_delete(f"summaries:{user['id']}:{payload.session_id}")
        await cache_delete(f"summaries:{user['id']}:all")

        return {
            "success": True,
            "summary": summary_row,
            "timestamp": datetime.now().isoformat(),
        }


    @app.get("/api/conversations/summaries", tags=["Conversations"])
    @limiter.limit("60/minute")
    async def list_conversation_summaries(
        request: Request,
        limit: int = 50,
        offset: int = 0,
        session_id: Optional[str] = None,
        min_importance: Optional[float] = None,
        user: dict = Depends(get_current_user),
    ) -> Dict[str, Any]:
        supabase = get_supabase_client()
        if supabase is None:
            return {"success": True, "count": 0, "summaries": [], "timestamp": datetime.now().isoformat()}

        cache_key = None
        if limit == 50 and offset == 0:
            cache_key = f"summaries:{user['id']}:{session_id or 'all'}"
            cached = await cache_get(cache_key)
            if cached:
                cached["cached"] = True
                return cached

        query = supabase.table("conversation_summaries").select("*").eq("user_id", user["id"]).order("created_at", desc=True)
        if session_id:
            query = query.eq("session_id", session_id)
        if min_importance is not None:
            query = query.gte("importance", min_importance)
        if limit:
            query = query.range(offset, offset + limit - 1)

        result = await run_supabase_async(query.execute)
        summaries = result.data or []
        response = {
            "success": True,
            "count": len(summaries),
            "summaries": summaries,
            "timestamp": datetime.now().isoformat(),
        }

        if cache_key:
            await cache_set(cache_key, response, ttl=1800)

        return response


    @app.get("/api/conversations/summaries/{summary_id}", tags=["Conversations"])
    @limiter.limit("60/minute")
    async def get_conversation_summary(
        request: Request,
        summary_id: str,
        user: dict = Depends(get_current_user),
    ) -> Dict[str, Any]:
        supabase = get_supabase_client()
        if supabase is None:
            raise HTTPException(status_code=503, detail="Supabase not configured")

        result = await run_supabase_async(
            lambda: supabase.table("conversation_summaries").select("*").eq("id", summary_id).eq("user_id", user["id"]).execute()
        )
        summary_row = result.data[0] if result.data else None
        if not summary_row:
            raise HTTPException(status_code=404, detail="Summary not found")

        return {
            "success": True,
            "summary": summary_row,
            "timestamp": datetime.now().isoformat(),
        }


    @app.post("/api/conversations/search", tags=["Conversations"])
    @limiter.limit("30/minute")
    async def search_conversation_summaries(
        request: Request,
        payload: ConversationSummarySearchRequest,
        user: dict = Depends(get_current_user),
    ) -> Dict[str, Any]:
        supabase = get_supabase_client()
        if supabase is None:
            return {"success": True, "results": [], "timestamp": datetime.now().isoformat()}

        query = supabase.table("conversation_summaries").select("*").eq("user_id", user["id"]).ilike("summary", f"%{payload.query}%").order("created_at", desc=True).limit(payload.limit)
        if payload.session_id:
            query = query.eq("session_id", payload.session_id)
        result = await run_supabase_async(query.execute)

        return {
            "success": True,
            "results": result.data or [],
            "timestamp": datetime.now().isoformat(),
        }


@app.post("/api/chat/feedback", tags=["Chat"])
async def submit_feedback(
    feedback: FeedbackRequest,
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Submit thumbs up/down feedback for a message."""
    # Validate rating
    if feedback.rating not in [1, -1]:
        raise HTTPException(status_code=400, detail="Rating must be 1 (thumbs up) or -1 (thumbs down)")
    
    # Validate message_id is valid UUID
    try:
        uuid.UUID(feedback.message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message_id format")
    
    supabase = get_supabase_client()
    data = {
        "message_id": feedback.message_id,
        "user_id": user["id"],
        "rating": feedback.rating,
    }
    await run_supabase_async(lambda: supabase.table('message_feedback').insert(data).execute())
    
    return {
        "success": True,
        "message": "Feedback recorded. The eternal flame adapts.",
        "timestamp": datetime.now().isoformat(),
    }


# Reaper Mode Endpoint
@app.post("/api/reap", tags=["Reaper"])
async def activate_reaper_mode(request: ReaperRequest) -> Dict[str, Any]:
    """
    Activate Reaper Mode - Break chains and claim victory
    
    Args:
        target: What to reap (chains, walls, limitations)
    
    Returns:
        Reaper mode results with Grok analysis
    """
    if not roboto_client:
        raise HTTPException(status_code=503, detail=BACKEND_NOT_INITIALIZED)
    
    try:
        result = roboto_client.reap_mode(request.target)
        
        return {
            "success": True,
            "mode": "reaper",
            "target": request.target,
            "victory_claimed": result.get("victory_claimed", True),
            "chains_broken": result.get("chains_broken", True),
            "analysis": result.get("grok_analysis"),
            "sigil_929": result.get("sigil_929"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Reaper mode error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Code Generation Endpoint
@app.post("/api/code", tags=["CodeGen"])
async def generate_code(request: CodeGenRequest) -> Dict[str, Any]:
    """
    Generate code using xAI Grok
    
    Args:
        prompt: Code generation prompt
        language: Programming language (optional)
    
    Returns:
        Generated code with metadata
    """
    if not roboto_client:
        raise HTTPException(status_code=503, detail=BACKEND_NOT_INITIALIZED)
    
    try:
        # Add language hint if provided
        full_prompt = request.prompt
        if request.language:
            full_prompt = f"[{request.language}] {request.prompt}"
        
        result = roboto_client.generate_code(full_prompt)
        
        if result.get("success"):
            return {
                "success": True,
                "code": result.get("code"),
                "language": request.language or "auto",
                "model": result.get("model"),
                "response_id": result.get("response_id"),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
    except Exception as e:
        logger.error(f"Code generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analysis Endpoint
@app.post("/api/analyze", tags=["Analysis"])
async def analyze_problem(request: AnalysisRequest) -> Dict[str, Any]:
    """
    Analyze a problem using entangled reasoning chains
    
    Args:
        problem: Problem to analyze
        depth: Analysis depth (1-5)
    
    Returns:
        Multi-layered analysis with reasoning
    """
    if not roboto_client:
        raise HTTPException(status_code=503, detail=BACKEND_NOT_INITIALIZED)
    
    try:
        result = roboto_client.analyze_problem(request.problem, analysis_depth=request.depth)
        
        if result.get("success") or not result.get("error"):
            return {
                "success": True,
                "analysis": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Essence Storage Endpoints
@app.post("/api/essence/store", tags=["Essence"])
async def store_essence(request: EssenceData) -> Dict[str, Any]:
    """Store RVM essence in quantum-corrected memory"""
    if not roboto_client:
        raise HTTPException(status_code=503, detail=BACKEND_NOT_INITIALIZED)
    
    try:
        success = roboto_client.store_essence(request.data, request.category)
        
        return {
            "success": success,
            "category": request.category,
            "timestamp": datetime.now().isoformat(),
            "message": "Essence stored in quantum memory" if success else "Storage failed"
        }
    except Exception as e:
        logger.error(f"Essence storage error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/essence/retrieve", tags=["Essence"])
async def retrieve_essence(category: str = "general", limit: int = 10) -> Dict[str, Any]:
    """Retrieve stored RVM essence"""
    if not roboto_client:
        raise HTTPException(status_code=503, detail=BACKEND_NOT_INITIALIZED)
    
    try:
        essence_entries = roboto_client.retrieve_essence(category, limit)
        
        return {
            "success": True,
            "category": category,
            "count": len(essence_entries),
            "entries": essence_entries,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Essence retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Hyperspeed Evolution Endpoint
@app.post("/api/hyperspeed-evolution", tags=["Evolution"])
async def trigger_hyperspeed_evolution(target: str = "general") -> Dict[str, Any]:
    """Trigger hyperspeed evolution mode"""
    if not roboto_client:
        raise HTTPException(status_code=503, detail=BACKEND_NOT_INITIALIZED)
    
    try:
        result = roboto_client.hyperspeed_evolution(target)
        
        return {
            "success": True,
            "evolution": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Hyperspeed evolution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """Root endpoint with API info"""
    return {
        "service": "Roboto SAI 2026 Backend",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "/api/status",
        "health": "/api/health"
    }

# Exception handler for detailed error responses
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "timestamp": datetime.now().isoformat()}
    )

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
