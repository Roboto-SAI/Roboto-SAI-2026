from typing import Dict, Any, Optional
import os
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage, AIMessage
from langchain_memory import SupabaseMessageHistory
from utils.supabase_client import get_supabase_client
from grok_llm import GrokLLM
from advanced_emotion_simulator import AdvancedEmotionSimulator

import logging
logger = logging.getLogger(__name__)

class GrokClient:
    def __init__(self):
        self.grok_llm = GrokLLM()
        self.emotion_simulator = AdvancedEmotionSimulator()

    async def chat(
        self,
        message: str,
        reasoning_effort: str = "medium",
        context: Dict[str, Any] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        previous_response_id: Optional[str] = None,
    ) -> tuple[str, Dict[str, Any]]:
        """
        Enhanced chat with memory integration
        """
        context = context or {}

        # Load conversation history
        history_store = SupabaseMessageHistory(session_id=session_id or "default", user_id=user_id)
        try:
            history_messages = await history_store.aget_messages()
        except Exception as e:
            logger.warning(f"Failed to load history: {e}")
            history_messages = []

        # Compute user emotion
        user_emotion = None
        if self.emotion_simulator:
            try:
                user_emotion = _compute_emotion(message, self.emotion_simulator)
            except Exception as e:
                logger.warning(f"Emotion computation failed: {e}")

        # Prepare user message with emotion
        user_message = HumanMessage(content=message, additional_kwargs=user_emotion or {})

        # Combine history with new message
        all_messages = history_messages + [user_message]

        # Call GrokLLM with Responses API for conversation chaining
        grok_available = True
        try:
            grok_result = await self.grok_llm.acall_with_response_id(
                all_messages,
                emotion=user_emotion.get('emotion_text', '') if user_emotion else '',
                user_name=context.get('user_name', 'user'),
                previous_response_id=previous_response_id
            )

            if not grok_result.get("success"):
                raise ValueError(grok_result.get("error", "Grok not available"))

            response_text = grok_result.get('response', '')
            response_id = grok_result.get('response_id')
            encrypted_thinking = grok_result.get('encrypted_thinking')
        except Exception as e:
            grok_available = False
            logger.warning(f"Grok unavailable, using demo response: {e}")
            response_text = "Warning: Grok is unavailable right now. The eternal flame persists - please try again shortly."
            response_id = None
            encrypted_thinking = None

        # Compute roboto emotion
        roboto_emotion = None
        if self.emotion_simulator and response_text:
            try:
                roboto_emotion = _compute_emotion(response_text, self.emotion_simulator)
            except Exception as e:
                logger.warning(f"Roboto emotion computation failed: {e}")

        # Save conversation
        user_message_id = None
        roboto_message_id = None
        try:
            user_message_id = await history_store.add_message(user_message)
            roboto_message = AIMessage(content=response_text, additional_kwargs=roboto_emotion or {})
            roboto_message_id = await history_store.add_message(roboto_message)
        except Exception as save_error:
            logger.warning(f"Failed to save messages: {save_error}")

        meta = {
            "trace_id": response_id,
            "tokens_used": grok_result.get("tokens_used") if grok_available else None,
            "mode": "entangled" if grok_available else "demo",
            "response_id": response_id,
            "encrypted_thinking": encrypted_thinking,
            "user_message_id": user_message_id,
            "roboto_message_id": roboto_message_id,
            "emotion": {
                "user": user_emotion,
                "roboto": roboto_emotion,
            },
            "memory_integrated": True,
        }

        return response_text, meta

def _compute_emotion(text: str, emotion_simulator: AdvancedEmotionSimulator) -> Optional[Dict[str, Any]]:
    """Compute emotion safely"""
    try:
        emotion_text = emotion_simulator.simulate_emotion(event=text, intensity=5, blend_threshold=0.8, holistic_influence=False)
        base_emotion = emotion_simulator.get_current_emotion()
        probabilities = emotion_simulator.get_emotion_probabilities(text)
        return {
            "emotion": base_emotion,
            "emotion_text": emotion_text,
            "probabilities": probabilities,
        }
    except Exception:
        return None

def get_grok_client() -> GrokClient:
    return GrokClient()