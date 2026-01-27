"""
Grok LLM wrapper for LangChain integration.
Adapts Roboto SAI SDK to LangChain's LLM interface.
"""

import asyncio
from typing import Any, List, Optional, Dict
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import LLM
from langchain_core.outputs import Generation, LLMResult
from langchain_core.messages import BaseMessage, HumanMessage
import logging

logger = logging.getLogger(__name__)

# Import Roboto SAI SDK (optional)
try:
    from roboto_sai_sdk import get_xai_grok
    HAS_SDK = True
except ImportError:
    logger.warning("roboto_sai_sdk not available in grok_llm")
    HAS_SDK = False
    get_xai_grok = None


class GrokLLM(LLM):
    """
    LangChain LLM wrapper for xAI Grok via Roboto SAI SDK.
    Supports Responses API for stateful conversation chaining.
    """
    
    model_name: str = "grok"
    reasoning_effort: Optional[str] = "high"
    previous_response_id: Optional[str] = None
    use_encrypted_content: bool = False
    store_messages: bool = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Only initialize client if SDK is available
        if HAS_SDK and get_xai_grok is not None:
            try:
                object.__setattr__(self, 'client', get_xai_grok())
            except Exception as e:
                logger.warning(f"Failed to initialize Grok client: {e}")
                object.__setattr__(self, 'client', None)
        else:
            object.__setattr__(self, 'client', None)
        # Extract Responses API params if provided
        if 'previous_response_id' in kwargs:
            self.previous_response_id = kwargs.pop('previous_response_id')
        if 'use_encrypted_content' in kwargs:
            self.use_encrypted_content = kwargs.pop('use_encrypted_content')
        if 'store_messages' in kwargs:
            self.store_messages = kwargs.pop('store_messages')

    @property
    def _llm_type(self) -> str:
        return "grok"

    def _call(
        self,
        prompt: str | List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Synchronous call to Grok.
        """
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(self._acall(prompt, stop, run_manager, **kwargs))
            return result
        finally:
            loop.close()

    def _normalize_grok_result(self, result: Any) -> Dict[str, Any]:
        if not isinstance(result, dict):
            return {"success": False, "error": "Invalid Grok response"}
        if "success" not in result:
            result["success"] = bool(result.get("response"))
        if "response_id" not in result and "id" in result:
            result["response_id"] = result["id"]
        return result

    def _invoke_grok_client(
        self,
        user_message: str,
        roboto_context: Optional[str],
        previous_response_id: Optional[str],
        emotion: str,
        user_name: str,
    ) -> Dict[str, Any]:
        client = self.client
        if hasattr(client, "roboto_grok_chat"):
            result = client.roboto_grok_chat(
                user_message=user_message,
                roboto_context=roboto_context,
                previous_response_id=previous_response_id,
            )
            return self._normalize_grok_result(result)

        if hasattr(client, "chat"):
            result = client.chat(
                message=user_message,
                emotion=emotion,
                user_name=user_name,
                previous_response_id=previous_response_id,
                use_encrypted_content=self.use_encrypted_content,
                store_messages=self.store_messages,
            )
            return self._normalize_grok_result(result)

        if hasattr(client, "grok_chat"):
            result = client.grok_chat(
                user_message,
                roboto_context=roboto_context,
                previous_response_id=previous_response_id,
            )
            return self._normalize_grok_result(result)

        if hasattr(client, "create_chat_with_system_prompt") and hasattr(client, "send_message"):
            system_prompt = "You are Roboto SAI." if not roboto_context else f"Roboto SAI Context: {roboto_context}"
            chat = client.create_chat_with_system_prompt(
                system_prompt,
                reasoning_effort=self.reasoning_effort,
            )
            result = client.send_message(chat, user_message, previous_response_id=previous_response_id)
            return self._normalize_grok_result(result)

        return {"success": False, "error": "Grok client does not support chat"}

    def _build_from_messages(self, messages: List[BaseMessage]) -> tuple[str, str, Optional[str]]:
        context_parts = []
        for msg in messages[:-1]:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            context_parts.append(f"{role}: {msg.content}")
        context = "\n".join(context_parts)
        last_msg = messages[-1]
        user_message = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

        emotion: Optional[str] = None
        if hasattr(last_msg, "additional_kwargs"):
            emotion = last_msg.additional_kwargs.get("emotion_text", "") or None
            if emotion:
                context = f"{context}\nUser Emotion: {emotion}" if context else f"User Emotion: {emotion}"

        return user_message, context, emotion

    def _build_prompt_context(
        self,
        prompt: str | List[BaseMessage],
        context_override: Optional[str] = None,
    ) -> tuple[str, str, Optional[str]]:
        if isinstance(prompt, list):
            return self._build_from_messages(prompt)
        if isinstance(prompt, str):
            return prompt, context_override or "", None
        return str(prompt), context_override or "", None

    def _apply_stop_sequences(self, response: str, stop: Optional[List[str]]) -> str:
        if not stop:
            return response
        for stop_seq in stop:
            if stop_seq in response:
                return response.split(stop_seq)[0]
        return response

    def _handle_grok_result(self, result: Dict[str, Any], stop: Optional[List[str]]) -> str:
        if result.get("success"):
            response = result.get("response", "")
            return self._apply_stop_sequences(response, stop)
        error = result.get("error", "Unknown error")
        raise RuntimeError(f"Grok API error: {error}")

    async def acall_with_response_id(
        self,
        prompt: str | List[BaseMessage],
        emotion: str = "neutral",
        user_name: str = "user",
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Async call to Grok using Responses API with stateful conversation chaining.
        Returns response dict with response_id and encrypted_thinking.
        """
        if not self.client:
            raise ValueError("Grok client not initialized")
        if not hasattr(self.client, 'available') or not self.client.available:
            raise ValueError("Grok client not available")

        # Handle input
        if isinstance(prompt, str):
            user_message = prompt
            context = kwargs.get("context", "")
        elif isinstance(prompt, list):
            messages = prompt
            context_parts = []
            for msg in messages[:-1]:  # All except last
                role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                context_parts.append(f"{role}: {msg.content}")
            context = "\n".join(context_parts)
            last_msg = messages[-1]
            user_message = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
        else:
            user_message = str(prompt)
            context = kwargs.get("context", "")

        # Use SDK roboto_grok_chat (wraps Responses API)
        roboto_context = f"Emotion: {emotion}. User: {user_name}. History: {context}."
        
        # Truncate extremely large contexts to prevent API limits (Grok 4.1: 1M+ tokens ~4M chars, but safe cap at 200k chars)
        if len(roboto_context) > 200000:
            logger.warning(f"Context too large ({len(roboto_context)} chars), truncating to 200k")
            roboto_context = roboto_context[:200000] + "... (truncated)"
        
        result = self._invoke_grok_client(
            user_message=user_message,
            roboto_context=roboto_context,
            previous_response_id=kwargs.get("previous_response_id"),
            emotion=emotion,
            user_name=user_name,
        )

        logger.info(f"Grok response ID: {result.get('response_id')}")
        return result

    async def _acall(
        self,
        prompt: str | List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:  # pylint: disable=too-many-branches
        """
        Async call to Grok for better performance.
        """
        if not self.client:
            raise ValueError("Grok client not initialized")
        if not hasattr(self.client, 'available') or not self.client.available:
            raise ValueError("Grok client not available")

        user_message, context, emotion = self._build_prompt_context(prompt, kwargs.get("context"))

        # Prepare roboto context
        roboto_context = context if context else None

        try:
            # roboto_grok_chat is sync, not async
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._invoke_grok_client(
                    user_message=user_message,
                    roboto_context=roboto_context,
                    previous_response_id=kwargs.get("previous_response_id"),
                    emotion=emotion if "emotion" in locals() else "neutral",
                    user_name=kwargs.get("user_name", "user"),
                )
            )

            return self._handle_grok_result(result, stop)

        except Exception as e:
            raise RuntimeError(f"Grok call failed: {e}")

    @property
    def _identifying_params(self) -> dict:
        return {
            "model_name": self.model_name,
            "reasoning_effort": self.reasoning_effort,
        }

    def _generate(
        self,
        prompts: List[str] | List[List[BaseMessage]],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Generate completions for multiple prompts."""
        generations = []
        for prompt in prompts:
            response = self._call(prompt, stop=stop, run_manager=run_manager, **kwargs)
            generations.append([Generation(text=response)])

        return LLMResult(generations=generations)