"""
Roboto SAI 2026 - FastAPI Backend
Integrates roboto-sai-sdk with React frontend
Created by Roberto Villarreal Martinez

🚀 Hyperspeed Evolution Backend - Quantum-Entangled API
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import websockets

# Import Roboto SAI SDK
from roboto_sai_sdk import RobotoSAIClient, get_xai_grok

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client instance
roboto_client: Optional[RobotoSAIClient] = None
xai_grok = None
VOICE_WS_URL = "wss://api.x.ai/v1/realtime"

# Startup/Shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize SDK on startup, cleanup on shutdown"""
    global roboto_client, xai_grok
    
    logger.info("🚀 Roboto SAI 2026 Backend Starting...")

    try:
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
    except Exception as e:
        logger.error(f"🚨 Backend initialization failed: {e}")
        raise
    
    yield
    
    logger.info("🛑 Roboto SAI 2026 Backend Shutting Down...")

# Initialize FastAPI app
app = FastAPI(
    title="Roboto SAI 2026 API",
    description="🚀 Quantum-Entangled AI Backend for RVM Empire",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class ChatMessage(BaseModel):
    """Chat message model"""
    message: str
    context: Optional[str] = None
    reasoning_effort: Optional[str] = "high"

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

# Chat Endpoints
@app.post("/api/chat", tags=["Chat"])
async def chat_with_grok(request: ChatMessage) -> Dict[str, Any]:
    """
    Chat with xAI Grok using Roboto SAI context
    
    Args:
        message: User message
        context: Optional Roboto context
        reasoning_effort: "low" or "high"
    
    Returns:
        Grok response with reasoning traces
    """
    if not roboto_client or not xai_grok or not xai_grok.available:
        raise HTTPException(status_code=503, detail="Grok not available")
    
    try:
        result = roboto_client.chat_with_grok(
            request.message,
            roboto_context=request.context,
            reasoning_effort=request.reasoning_effort
        )
        
        if result.get("success"):
            return {
                "success": True,
                "response": result.get("response"),
                "reasoning_available": result.get("reasoning_available", False),
                "response_id": result.get("response_id"),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
