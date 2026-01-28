"""
Roboto SAI 2026 - FastAPI Backend
Integrates roboto-sai-sdk with React frontend
Created by Roberto Villarreal Martinez

🚀 Hyperspeed Evolution Backend - Quantum-Entangled API
"""

print("DEBUG: main.py module loading started")

import os
print("DEBUG: os imported")

import logging
print("DEBUG: logging imported")

import asyncio
print("DEBUG: asyncio imported")

import json
print("DEBUG: json imported")

import secrets
print("DEBUG: secrets imported")

import hashlib
print("DEBUG: hashlib imported")

from urllib.parse import urlencode
print("DEBUG: urlencode imported")

from typing import Dict, Any, Optional
print("DEBUG: typing imported")

from datetime import datetime, timedelta, timezone
print("DEBUG: datetime imported")

from contextlib import asynccontextmanager
print("DEBUG: asynccontextmanager imported")

# Configure logging EARLY
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
print("DEBUG: logging configured")

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends, Request
print("DEBUG: fastapi imported")

from fastapi.responses import JSONResponse, RedirectResponse
print("DEBUG: fastapi responses imported")

from fastapi.middleware.cors import CORSMiddleware
print("DEBUG: cors middleware imported")

from pydantic import BaseModel
print("DEBUG: pydantic imported")

# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession  # Deprecated
import httpx
print("DEBUG: httpx imported")

import websockets
print("DEBUG: websockets imported")

from dotenv import load_dotenv
print("DEBUG: dotenv imported")

import uuid
print("DEBUG: uuid imported")

# LangChain imports
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
print("DEBUG: langchain_core imported")

from langchain_core.messages import HumanMessage, AIMessage
print("DEBUG: langchain messages imported")

from dotenv import load_dotenv
print("DEBUG: dotenv re-imported")

import os
print("DEBUG: os re-imported")

# Load local .env when running outside Docker
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
print("DEBUG: dotenv loaded")

# Import Roboto SAI SDK (optional) - updated for proper package structure
try:
    from roboto_sai_sdk import RobotoSAIClient, get_xai_grok
    HAS_SDK = True
    print("DEBUG: SDK imported successfully")
except ImportError as e:
    print(f"DEBUG: SDK import failed: {e}")
    logger.warning("roboto_sai_sdk not available, using fallback implementations")
    HAS_SDK = False
    RobotoSAIClient = None
    get_xai_grok = None

print("DEBUG: Starting local module imports")

# Import local modules
from advanced_emotion_simulator import AdvancedEmotionSimulator
print("DEBUG: AdvancedEmotionSimulator imported")

from grok_llm import GrokLLM
print("DEBUG: GrokLLM imported")

# Use langchain_memory which has in-memory fallback when Supabase unavailable
from langchain_memory import SupabaseMessageHistory
print("DEBUG: SupabaseMessageHistory imported (with fallback support)")

from utils.supabase_client import get_supabase_client
print("DEBUG: get_supabase_client imported")

from db import init_db
print("DEBUG: init_db imported")

print("DEBUG: All imports completed, starting FastAPI app creation")

# Global client instance
roboto_client: Optional[Any] = None  # Optional[RobotoSAIClient]
xai_grok = None
emotion_simulator: Optional[AdvancedEmotionSimulator] = None
grok_llm = None
VOICE_WS_URL = "wss://api.x.ai/v1/realtime"

# Startup/Shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize SDK on startup, cleanup on shutdown"""
    global roboto_client, xai_grok
    
    print("DEBUG: Lifespan startup beginning...")
    
    logger.info("🚀 Roboto SAI 2026 Backend Starting...")
    logger.info("📍 Phase 1: Database initialization")

    try:
        # Initialize database (graceful fallback if Supabase unavailable)
        try:
            init_db()
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.warning(f"⚠️ Database initialization failed (running in demo mode): {e}")

        logger.info("📍 Phase 2: Emotion simulator initialization")
        # Initialize emotion simulator
        state_path = os.getenv("ROBO_EMOTION_STATE_PATH", "./data/emotion_state.json")
        emotion_simulator_instance = AdvancedEmotionSimulator()
        try:
            if os.path.exists(state_path):
                emotion_simulator_instance.load_state(state_path)
                logger.info("✅ Emotion state loaded")
        except Exception as e:
            logger.warning(f"⚠️ Could not load emotion state: {e}")

        global emotion_simulator
        emotion_simulator = emotion_simulator_instance

        logger.info("📍 Phase 3: SDK client initialization")
        # Initialize Roboto SAI Client (optional)
        if HAS_SDK and os.getenv("XAI_API_KEY"):
            try:
                roboto_client = RobotoSAIClient()
                logger.info(f"✅ Roboto SAI Client initialized: {roboto_client.client_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Roboto SAI Client: {e}")
                roboto_client = None
        else:
            logger.warning("⚠️ SDK not available or XAI_API_KEY not set - running in degraded mode")
            roboto_client = None

        # Initialize xAI Grok (optional)
        if HAS_SDK:
            try:
                xai_grok = get_xai_grok()
                if xai_grok.available:
                    logger.info("✅ xAI Grok SDK available - Reasoning chains active")
                else:
                    logger.warning("⚠️ xAI Grok not available - check XAI_API_KEY")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize xAI Grok: {e}")
                xai_grok = None
        else:
            logger.warning("⚠️ SDK not available - xAI Grok not initialized")
        
        logger.info("📍 Phase 4: LangChain GrokLLM initialization")
        # Initialize LangChain GrokLLM (graceful fallback)
        global grok_llm
        try:
            grok_llm = GrokLLM()
            logger.info("✅ LangChain GrokLLM initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize GrokLLM: {e}")
            grok_llm = None
            
        logger.info("📍 Phase 5: Startup complete")
        logger.info("🚀 Backend initialization complete (may be in degraded mode)")
        logger.info(f"📊 Status: SDK={'available' if HAS_SDK else 'unavailable'}, Grok={xai_grok is not None and xai_grok.available if xai_grok else False}, GrokLLM={grok_llm is not None}")
    except Exception as e:
        logger.error(f"🚨 Unexpected backend initialization error: {e}")
        # Still allow the app to start - don't crash
        logger.info("Starting app in minimal/demo mode...")
        import traceback
        traceback.print_exc()
    
    yield

    if emotion_simulator:
        state_path = os.getenv("ROBO_EMOTION_STATE_PATH", "./data/emotion_state.json")
        emotion_simulator.save_state(state_path)
    
    logger.info("🛑 Roboto SAI 2026 Backend Shutting Down...")

# Initialize FastAPI app
try:
    print("DEBUG: Creating FastAPI app...")
    app = FastAPI(
        title="Roboto SAI 2026 API",
        description="🚀 Quantum-Entangled AI Backend for RVM Empire",
        version="0.1.0",
        lifespan=lifespan
    )
    print("DEBUG: FastAPI app created successfully")
except Exception as e:
    print(f"CRITICAL: FastAPI app creation failed: {e}")
    import traceback
    traceback.print_exc()
    raise

@app.on_event("startup")
async def startup_debug():
    logger.debug("Startup event triggered - beginning initialization")
    try:
        logger.debug("Startup logic will be handled by lifespan context manager")
        logger.debug("Startup event completed successfully")
    except Exception as e:
        logger.exception(f"Startup failure: {e}")
        raise  # let it crash so Render logs it
    logger.debug("Startup event completed successfully")


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
    # For localhost, return None (browser uses current domain)
    if request.url.hostname in ("localhost", "127.0.0.1"):
        return None
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
async def auth_magic_request(req: MagicRequest) -> Dict[str, Any]:
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
    message: str
    context: Optional[str] = None
    reasoning_effort: Optional[str] = "high"
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    previous_response_id: Optional[str] = None
    use_encrypted_content: bool = False

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

class FeedbackRequest(BaseModel):
    """Message feedback request"""
    message_id: str
    rating: int  # 1=thumbs up, -1=thumbs down

# Voice WebSocket Proxy
@app.websocket("/api/voice/ws")
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

            async def client_to_xai() -> None:
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

            async def xai_to_client() -> None:
                try:
                    async for message in xai_ws:
                        if isinstance(message, bytes):
                            await websocket.send_bytes(message)
                        else:
                            await websocket.send_text(message)
                except Exception as exc:
                    logger.error(f"Voice proxy error: {exc}")

            await asyncio.wait(
                {asyncio.create_task(client_to_xai()), asyncio.create_task(xai_to_client())},
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
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
    return {
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "client_id": roboto_client.client_id,
        "grok_available": xai_grok.available if xai_grok else False,
        "quantum_state": roboto_client.quantum_state,
        "sigil_929": roboto_client.sigil_929["eternal_protection"],
        "sdk_version": "0.1.0",
        "hyperspeed_evolution": True
    }

# Emotion Endpoints
@app.post("/api/emotion/simulate", tags=["Emotion"])
async def simulate_emotion(request: EmotionSimRequest) -> Dict[str, Any]:
    """Simulate emotion from a text event."""
    if not emotion_simulator:
        raise HTTPException(status_code=503, detail="Emotion simulator not available")

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
        raise HTTPException(status_code=503, detail="Emotion simulator not available")

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
        raise HTTPException(status_code=503, detail="Emotion simulator not available")

    return {
        "success": True,
        "stats": emotion_simulator.get_emotional_stats(),
        "timestamp": datetime.now().isoformat()
    }

# Chat Endpoints
@app.post("/api/chat", tags=["Chat"])
async def chat_with_grok(
    request: ChatMessage,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Chat with xAI Grok using Roboto SAI context with LangChain memory
    """
    if not os.getenv("XAI_API_KEY"):
        raise HTTPException(status_code=503, detail="Roboto SAI not available: XAI_API_KEY not configured")
    if not grok_llm or not xai_grok or not xai_grok.available:
        raise HTTPException(status_code=503, detail="Grok not available")
    
    try:
        user_emotion: Optional[Dict[str, Any]] = None
        assistant_emotion: Optional[Dict[str, Any]] = None
        session_id = request.session_id or "default"

        # Compute user emotion
        if emotion_simulator:
            try:
                emotion_text = emotion_simulator.simulate_emotion(
                    event=request.message,
                    intensity=5,
                    blend_threshold=0.8,
                    holistic_influence=False,
                    cultural_context=None,
                )
                base_emotion = emotion_simulator.get_current_emotion()
                probabilities = emotion_simulator.get_emotion_probabilities(request.message)
                user_emotion = {
                    "emotion": base_emotion,
                    "emotion_text": emotion_text,
                    "probabilities": probabilities,
                }
            except Exception as emotion_error:
                logger.warning(f"Emotion simulation (user) failed: {emotion_error}")

        # Load conversation history with graceful fallback
        try:
            history_store = SupabaseMessageHistory(session_id=session_id, user_id=user["id"])
            history_messages = await history_store._get_messages_async()
        except Exception as history_error:
            logger.warning(f"Failed to load history (using empty): {history_error}")
            history_store = None
            history_messages = []
        
        # Prepare user message with emotion
        user_message = HumanMessage(
            content=request.message,
            additional_kwargs=user_emotion or {}
        )
        
        # Combine history with new message
        all_messages = history_messages + [user_message]

        # Call GrokLLM with Responses API for conversation chaining
        grok_result = await grok_llm.acall_with_response_id(
            all_messages,
            emotion=user_emotion.get('emotion_text', '') if user_emotion else '',
            user_name=user.get('user_metadata', {}).get('name', 'user'),
            previous_response_id=request.previous_response_id
        )
        if not grok_result.get("success"):
            raise HTTPException(status_code=503, detail=grok_result.get("error", "Roboto SAI not available"))
        response_text = grok_result.get('response', '')
        response_id = grok_result.get('response_id')
        encrypted_thinking = grok_result.get('encrypted_thinking')

        # Compute assistant emotion
        if emotion_simulator and response_text:
            try:
                assistant_emotion_text = emotion_simulator.simulate_emotion(
                    event=response_text,
                    intensity=5,
                    blend_threshold=0.8,
                    holistic_influence=False,
                    cultural_context=None,
                )
                assistant_base_emotion = emotion_simulator.get_current_emotion()
                assistant_probabilities = emotion_simulator.get_emotion_probabilities(response_text)
                assistant_emotion = {
                    "emotion": assistant_base_emotion,
                    "emotion_text": assistant_emotion_text,
                    "probabilities": assistant_probabilities,
                }
            except Exception as emotion_error:
                logger.warning(f"Emotion simulation (assistant) failed: {emotion_error}")

        # Save conversation (if history_store is available)
        user_message_id = None
        assistant_message_id = None
        if history_store:
            try:
                user_message_id = await history_store.add_message(user_message)
                assistant_message = AIMessage(
                    content=response_text,
                    additional_kwargs=assistant_emotion or {}
                )
                assistant_message_id = await history_store.add_message(assistant_message)
            except Exception as save_error:
                logger.warning(f"Failed to save messages: {save_error}")
        else:
            assistant_message = AIMessage(
                content=response_text,
                additional_kwargs=assistant_emotion or {}
            )
        
        # Store response_id if available
        if response_id and assistant_message_id:
            try:
                supabase = get_supabase_client()
                if supabase:
                    await run_supabase_async(
                        supabase.table('messages').update({
                            'xai_response_id': response_id,
                            'xai_encrypted_thinking': encrypted_thinking
                        }).eq('id', assistant_message_id).execute
                    )
            except Exception as e:
                logger.warning(f'Failed to store response_id: {e}')

        return {
            "success": True,
            "response": response_text,
            "reasoning_available": False,
            "response_id": response_id or f"lc-{session_id}",
            "encrypted_thinking": encrypted_thinking,
            "xai_stored": grok_result.get('stored', False),
            "assistant_message_id": assistant_message_id,
            "user_message_id": user_message_id,
            "emotion": {
                "user": user_emotion,
                "assistant": assistant_emotion,
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
async def get_chat_history(
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

  query = supabase.table('messages').select('*').eq('user_id', user['id']).order('created_at', desc=True).limit(limit)
  if session_id:
    query = query.eq('session_id', session_id)
  result = await run_supabase_async(query.execute)
  messages = result.data or []
  return {
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
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
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
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
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
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
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
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
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
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
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
        raise HTTPException(status_code=503, detail="Backend not initialized")
    
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
