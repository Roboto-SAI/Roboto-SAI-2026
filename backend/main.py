"""
Roboto SAI 2026 - FastAPI Backend
Integrates roboto-sai-sdk with React frontend
Created by Roberto Villarreal Martinez

🚀 Hyperspeed Evolution Backend - Quantum-Entangled API
"""

import os
import logging
import asyncio
import json
import secrets
import hashlib
from urllib.parse import urlencode
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import websockets

# LangChain imports
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage

# Import Roboto SAI SDK
from roboto_sai_sdk import RobotoSAIClient, get_xai_grok
from db import get_session, init_db
from models import Message, User, AuthSession, MagicLinkToken
from advanced_emotion_simulator import AdvancedEmotionSimulator
from langchain_memory import SQLMessageHistory
from grok_llm import GrokLLM

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client instance
roboto_client: Optional[RobotoSAIClient] = None
xai_grok = None
emotion_simulator: Optional[AdvancedEmotionSimulator] = None
grok_llm = None
VOICE_WS_URL = "wss://api.x.ai/v1/realtime"

# Startup/Shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize SDK on startup, cleanup on shutdown"""
    global roboto_client, xai_grok
    
    logger.info("🚀 Roboto SAI 2026 Backend Starting...")

    try:
        await init_db()

        state_path = os.getenv("ROBO_EMOTION_STATE_PATH", "./data/emotion_state.json")
        emotion_simulator_instance = AdvancedEmotionSimulator()
        if os.path.exists(state_path):
            emotion_simulator_instance.load_state(state_path)

        global emotion_simulator
        emotion_simulator = emotion_simulator_instance

        if os.getenv("XAI_API_KEY"):
            # Initialize Roboto SAI Client
            roboto_client = RobotoSAIClient()
            logger.info(f"✅ Roboto SAI Client initialized: {roboto_client.client_id}")
        else:
            logger.warning("⚠️ No XAI_API_KEY - running in degraded mode (no AI)")
            roboto_client = None

        # Initialize xAI Grok
        xai_grok = get_xai_grok()
        if xai_grok.available:
            logger.info("✅ xAI Grok SDK available - Reasoning chains active")
        else:
            logger.warning("⚠️ xAI Grok not available - check XAI_API_KEY")
        
        # Initialize LangChain GrokLLM
        global grok_llm
        grok_llm = GrokLLM()
        logger.info("✅ LangChain GrokLLM initialized")
    except Exception as e:
        logger.error(f"🚨 Backend initialization failed: {e}")
        raise
    
    yield

    if emotion_simulator:
        state_path = os.getenv("ROBO_EMOTION_STATE_PATH", "./data/emotion_state.json")
        emotion_simulator.save_state(state_path)
    
    logger.info("🛑 Roboto SAI 2026 Backend Shutting Down...")

# Initialize FastAPI app
app = FastAPI(
    title="Roboto SAI 2026 API",
    description="🚀 Quantum-Entangled AI Backend for RVM Empire",
    version="0.1.0",
    lifespan=lifespan
)

def _get_frontend_origins() -> list[str]:
    env = (os.getenv("FRONTEND_ORIGIN") or "").strip()
    env_origins = [o.strip() for o in env.split(",") if o.strip()]
    defaults = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
    ]
    # preserve ordering while removing duplicates
    out: list[str] = []
    for origin in [*env_origins, *defaults]:
        if origin and origin not in out:
            out.append(origin)
    return out


# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_frontend_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SESSION_COOKIE_NAME = "roboto_session"
OAUTH_STATE_COOKIE_NAME = "roboto_oauth_state"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _session_ttl() -> timedelta:
    try:
        seconds = int(os.getenv("SESSION_TTL_SECONDS", "604800"))  # 7 days
        return timedelta(seconds=max(60, seconds))
    except Exception:
        return timedelta(days=7)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def _create_session_cookie(response: RedirectResponse, session: AsyncSession, user_id: str) -> None:
    sess_id = secrets.token_urlsafe(32)
    expires_at = _utcnow() + _session_ttl()
    session.add(AuthSession(id=sess_id, user_id=user_id, expires_at=expires_at))
    await session.commit()

    # Note: In production behind HTTPS, set COOKIE_SECURE=true
    secure = (os.getenv("COOKIE_SECURE", "").lower() == "true")
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=sess_id,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=int(_session_ttl().total_seconds()),
        path="/",
    )


async def get_current_user(
    request,  # FastAPI Request type avoided to keep imports minimal
    session: AsyncSession = Depends(get_session),
) -> User:
    sess_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not sess_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    now = _utcnow()
    sess_res = await session.execute(
        select(AuthSession).where(AuthSession.id == sess_id).where(AuthSession.expires_at > now)
    )
    sess = sess_res.scalar_one_or_none()
    if not sess:
        raise HTTPException(status_code=401, detail="Session expired")

    user_res = await session.execute(select(User).where(User.id == sess.user_id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


class MagicRequest(BaseModel):
    email: str


@app.get("/api/auth/me", tags=["Auth"])
async def auth_me(user: User = Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "provider": user.provider,
        }
    }


@app.post("/api/auth/logout", tags=["Auth"])
async def auth_logout(request, session: AsyncSession = Depends(get_session)) -> JSONResponse:
    sess_id = request.cookies.get(SESSION_COOKIE_NAME)
    if sess_id:
        sess_res = await session.execute(select(AuthSession).where(AuthSession.id == sess_id))
        sess = sess_res.scalar_one_or_none()
        if sess:
            await session.delete(sess)
            await session.commit()

    resp = JSONResponse({"success": True})
    resp.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return resp


@app.get("/api/auth/google/start", tags=["Auth"])
async def auth_google_start(request) -> RedirectResponse:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not client_id or not redirect_uri:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    state = secrets.token_urlsafe(16)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
        "state": state,
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    resp = RedirectResponse(url=url, status_code=302)
    resp.set_cookie(
        key=OAUTH_STATE_COOKIE_NAME,
        value=state,
        httponly=True,
        secure=(os.getenv("COOKIE_SECURE", "").lower() == "true"),
        samesite="lax",
        max_age=300,
        path="/",
    )
    return resp


@app.get("/api/auth/google/callback", tags=["Auth"])
async def auth_google_callback(
    request,
    code: str,
    state: str,
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    expected_state = request.cookies.get(OAUTH_STATE_COOKIE_NAME)
    if not expected_state or state != expected_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    token_url = "https://oauth2.googleapis.com/token"
    async with httpx.AsyncClient(timeout=15) as client:
        token_res = await client.post(
            token_url,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_res.status_code >= 400:
            raise HTTPException(status_code=400, detail=f"Google token exchange failed ({token_res.status_code})")
        tokens = token_res.json()
        access_token = tokens.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Missing access_token")

        userinfo_res = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_res.status_code >= 400:
            raise HTTPException(status_code=400, detail="Failed to fetch Google userinfo")
        info = userinfo_res.json()

    email = info.get("email")
    sub = info.get("sub")
    name = info.get("name")
    picture = info.get("picture")
    if not email or not sub:
        raise HTTPException(status_code=400, detail="Google userinfo incomplete")

    # Upsert user
    existing_res = await session.execute(
        select(User).where((User.provider == "google") & (User.provider_sub == sub))
    )
    user = existing_res.scalar_one_or_none()
    if not user:
        by_email_res = await session.execute(select(User).where(User.email == email))
        user = by_email_res.scalar_one_or_none()

    if user:
        user.email = email
        user.display_name = name or user.display_name
        user.avatar_url = picture or user.avatar_url
        user.provider = "google"
        user.provider_sub = sub
    else:
        user = User(
            id=secrets.token_urlsafe(16)[:64],
            email=email,
            display_name=name,
            avatar_url=picture,
            provider="google",
            provider_sub=sub,
        )
        session.add(user)
    await session.commit()

    frontend_origin = (os.getenv("FRONTEND_ORIGIN") or "http://localhost:5173").split(",")[0].strip()
    redirect_to = f"{frontend_origin}/chat"
    resp = RedirectResponse(url=redirect_to, status_code=302)
    resp.delete_cookie(OAUTH_STATE_COOKIE_NAME, path="/")
    await _create_session_cookie(resp, session, user.id)
    return resp


@app.post("/api/auth/magic/request", tags=["Auth"])
async def auth_magic_request(req: MagicRequest, session: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    email = (req.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")

    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = _utcnow() + timedelta(minutes=15)
    session.add(MagicLinkToken(token_hash=token_hash, email=email, expires_at=expires_at))
    await session.commit()

    base_url = os.getenv("GOOGLE_REDIRECT_URI")
    # If GOOGLE_REDIRECT_URI is set, its host is the backend public URL; otherwise assume local.
    backend_base = "http://localhost:5000"
    if base_url and "/api/auth/google/callback" in base_url:
        backend_base = base_url.split("/api/auth/google/callback")[0]

    verify_url = f"{backend_base}/api/auth/magic/verify?{urlencode({'token': token})}"

    # Email sending is not wired yet. For now, log to server.
    logger.info(f"[MAGIC LINK] {email} -> {verify_url}")

    return {"success": True}


@app.get("/api/auth/magic/verify", tags=["Auth"])
async def auth_magic_verify(token: str, session: AsyncSession = Depends(get_session)) -> RedirectResponse:
    token_hash = _hash_token(token)
    now = _utcnow()
    res = await session.execute(select(MagicLinkToken).where(MagicLinkToken.token_hash == token_hash))
    row = res.scalar_one_or_none()
    if not row or row.used_at is not None or row.expires_at <= now:
        raise HTTPException(status_code=400, detail="Invalid or expired magic link")

    email = row.email
    user_res = await session.execute(select(User).where(User.email == email))
    user = user_res.scalar_one_or_none()
    if not user:
        user = User(
            id=secrets.token_urlsafe(16)[:64],
            email=email,
            display_name=email.split("@")[0],
            avatar_url=None,
            provider="magic",
            provider_sub=None,
        )
        session.add(user)

    row.user_id = user.id
    row.used_at = now
    await session.commit()

    frontend_origin = (os.getenv("FRONTEND_ORIGIN") or "http://localhost:5173").split(",")[0].strip()
    redirect_to = f"{frontend_origin}/chat"
    resp = RedirectResponse(url=redirect_to, status_code=302)
    await _create_session_cookie(resp, session, user.id)
    return resp

# Pydantic Models
class ChatMessage(BaseModel):
    """Chat message model"""
    message: str
    context: Optional[str] = None
    reasoning_effort: Optional[str] = "high"
    user_id: Optional[str] = None
    session_id: Optional[str] = None

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

@app.get("/api/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """Simple health check"""
    return {"status": "healthy", "service": "roboto-sai-2026"}

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
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Chat with xAI Grok using Roboto SAI context with LangChain memory
    
    Args:
        message: User message
        context: Optional Roboto context
        reasoning_effort: "low" or "high"
        user_id: User identifier
        session_id: Session identifier
    
    Returns:
        Grok response with conversation memory
    """
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

        # Load conversation history (user_id derived from authenticated session)
        history_store = SQLMessageHistory(session_id=session_id, user_id=user.id)
        history_messages = await history_store._get_messages_async()
        
        # Prepare user message with emotion
        user_message = HumanMessage(
            content=request.message,
            additional_kwargs=user_emotion or {}
        )
        
        # Combine history with new message
        all_messages = history_messages + [user_message]

        # Call GrokLLM with full conversation history
        response_text = await grok_llm._acall(all_messages)

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

        # Save conversation to database with emotions
        user_message.additional_kwargs.update(user_emotion or {})
        await history_store.add_message(user_message)
        
        assistant_message = AIMessage(
            content=response_text,
            additional_kwargs=assistant_emotion or {}
        )
        await history_store.add_message(assistant_message)

        return {
            "success": True,
            "response": response_text,
            "reasoning_available": False,
            "response_id": f"lc-{session_id}",
            "emotion": {
                "user": user_emotion,
                "assistant": assistant_emotion,
            },
            "memory_integrated": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/history", tags=["Chat"])
async def get_chat_history(
    session_id: Optional[str] = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve recent chat history."""
    stmt = select(Message).order_by(Message.created_at.desc()).limit(limit)
    stmt = stmt.where(Message.user_id == user.id)
    if session_id:
        stmt = stmt.where(Message.session_id == session_id)

    result = await session.execute(stmt)
    messages = list(reversed(result.scalars().all()))

    return {
        "success": True,
        "count": len(messages),
        "messages": [
            {
                "id": message.id,
                "user_id": message.user_id,
                "session_id": message.session_id,
                "role": message.role,
                "content": message.content,
                "emotion": message.emotion,
                "emotion_text": message.emotion_text,
                "emotion_probabilities": json.loads(message.emotion_probabilities)
                if message.emotion_probabilities
                else None,
                "created_at": message.created_at.isoformat() if message.created_at else None,
            }
            for message in messages
        ],
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

# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """Root endpoint with API info"""
    return {
        "service": "Roboto SAI 2026 Backend",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "/api/status"
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
