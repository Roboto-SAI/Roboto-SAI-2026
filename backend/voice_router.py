"""
Voice Router for Roboto SAI
Handles WebSocket connections for real-time voice interaction.
"""

import os
import json
import logging
import asyncio
import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

router = APIRouter()

VOICE_WS_URL = "wss://api.x.ai/v1/realtime" # Or openai if fallback
SESSION_COOKIE_NAME = "roboto_session"

@router.websocket("/api/voice/ws")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()
    logger.info("Voice WebSocket connected")
    
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        await websocket.send_json({
            "type": "error",
            "error": {"message": "XAI_API_KEY not configured on backend"}
        })
        await websocket.close()
        return

    # Create upstream connection
    upstream_ws = None
    
    try:
        # Check if we should use OpenAI fallback
        use_openai = os.getenv("USE_OPENAI_VOICE", "false").lower() == "true"
        target_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01" if use_openai else VOICE_WS_URL
        
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY') if use_openai else api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        # Determine protocol (xAI might not support this yet, so we might need to mock or fail gracefully)
        # For now, we attempt connection.
        
        async with websockets.connect(target_url, additional_headers=headers) as upstream:
            upstream_ws = upstream
            logger.info(f"Connected to upstream voice API: {target_url}")
            
            # Pipe tasks
            async def client_to_upstream():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await upstream.send(data)
                except WebSocketDisconnect:
                    logger.info("Client disconnected")
                except Exception as e:
                    logger.error(f"Client read error: {e}")

            async def upstream_to_client():
                try:
                    async for message in upstream:
                        await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Upstream read error: {e}")

            await asyncio.gather(client_to_upstream(), upstream_to_client())

    except Exception as e:
        logger.error(f"Voice connection error: {e}")
        # Send error to client if possible
        try:
            await websocket.send_json({
                "type": "error",
                "error": {"message": f"Upstream connection failed: {str(e)}. Ensure Voice API is available."}
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
