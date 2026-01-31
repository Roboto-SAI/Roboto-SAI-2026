"""
Grok LLM wrapper for LangChain integration.
Adapts Roboto SAI SDK to LangChain's LLM interface.
"""

import asyncio
import os
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
        # Check if we're already in an async context
        try:
            loop = asyncio.get_running_loop()
            logger.warning("Nested async detected in _call(), delegating to executor")
            # Delegate to executor (isolates new loop)
            def safe_acall():
                sub_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(sub_loop)
                try:
                    return sub_loop.run_until_complete(self._acall(prompt, stop, run_manager, **kwargs))
                finally:
                    sub_loop.close()
            return asyncio.get_event_loop().run_in_executor(None, safe_acall())
        except RuntimeError as e:
            if "no running event loop" not in str(e).lower():
                raise
        
        # No running loop - safe to create new one
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
        if result.get("success") and not result.get("response_id"):
            result["success"] = False
            result["error"] = "Roboto SAI not available: XAI connection failed"
        return result

    def _invoke_grok_client(
        self,
        user_message: str,
        roboto_context: Optional[str],
        previous_response_id: Optional[str],
        emotion: str,
        user_name: str,
    ) -> Dict[str, Any]:
        """Invoke Grok client with fallback to direct API call"""
        
        # Check for API key
        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            return {"success": False, "error": "Roboto SAI not available: XAI_API_KEY not configured"}
        
        client = self.client
        
        # Try SDK methods if client is available
        if client:
            if hasattr(client, "available") and not getattr(client, "available"):
                logger.warning("Grok client available=False, falling back to direct API")
            elif hasattr(client, "roboto_grok_chat"):
                try:
                    result = client.roboto_grok_chat(
                        user_message=user_message,
                        roboto_context=roboto_context,
                        previous_response_id=previous_response_id,
                    )
                    return self._normalize_grok_result(result)
                except Exception as e:
                    logger.warning(f"roboto_grok_chat failed: {e}, trying fallback")
            
            elif hasattr(client, "chat"):
                try:
                    result = client.chat(
                        message=user_message,
                        emotion=emotion,
                        user_name=user_name,
                        previous_response_id=previous_response_id,
                        use_encrypted_content=self.use_encrypted_content,
                        store_messages=self.store_messages,
                    )
                    return self._normalize_grok_result(result)
                except Exception as e:
                    logger.warning(f"chat method failed: {e}, trying fallback")
            
            elif hasattr(client, "grok_chat"):
                try:
                    result = client.grok_chat(
                        user_message,
                        roboto_context=roboto_context,
                        previous_response_id=previous_response_id,
                    )
                    return self._normalize_grok_result(result)
                except Exception as e:
                    logger.warning(f"grok_chat failed: {e}, trying fallback")
            
            elif hasattr(client, "create_chat_with_system_prompt") and hasattr(client, "send_message"):
                try:
                    system_prompt = "You are Roboto SAI." if not roboto_context else f"Roboto SAI Context: {roboto_context}"
                    chat = client.create_chat_with_system_prompt(
                        system_prompt,
                        reasoning_effort=self.reasoning_effort,
                    )
                    result = client.send_message(chat, user_message, previous_response_id=previous_response_id)
                    return self._normalize_grok_result(result)
                except Exception as e:
                    logger.warning(f"create_chat/send_message failed: {e}, trying fallback")
        
        # Fallback to direct API call using httpx
        logger.info("Using direct Grok API call as fallback")
        return self._direct_grok_api_call(user_message, roboto_context, previous_response_id)
    
    def _get_xai_base_url(self) -> str:
        base = (os.getenv("XAI_API_BASE_URL") or "https://api.x.ai").rstrip("/")
        return base

    def _get_xai_chat_paths(self) -> list[str]:
        custom_path = os.getenv("XAI_API_CHAT_PATH")
        if custom_path:
            return [custom_path.lstrip("/")]
        return [
            "v1/responses",
            "v1/chat/completions",
            "v1/messages",
            "chat/completions",
            "responses",
        ]

    def _build_xai_messages(
        self,
        user_message: str,
        roboto_context: Optional[str],
    ) -> list[dict[str, str]]:
        system_content = (
            f"You are Roboto SAI, an AI companion created by Roberto Villarreal Martinez. Context: {roboto_context}"
            if roboto_context
            else "You are Roboto SAI, an AI companion powered by Grok, created by Roberto Villarreal Martinez."
        )
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_message},
        ]

    def _extract_response_text(self, data: Dict[str, Any]) -> Optional[str]:
        if not isinstance(data, dict):
            return None
        if "choices" in data:
            return data.get("choices", [{}])[0].get("message", {}).get("content")
        if "output" in data and isinstance(data["output"], list):
            for output_item in data["output"]:
                content = output_item.get("content") if isinstance(output_item, dict) else None
                if isinstance(content, list) and content:
                    text = content[0].get("text") if isinstance(content[0], dict) else None
                    if text:
                        return text
        content = data.get("content")
        if isinstance(content, list) and content:
            text = content[0].get("text") if isinstance(content[0], dict) else None
            if text:
                return text
        if isinstance(content, str) and content:
            return content
        response_text = data.get("response")
        if isinstance(response_text, str) and response_text:
            return response_text
        return None

    def _direct_grok_api_call(
        self,
        user_message: str,
        roboto_context: Optional[str],
        previous_response_id: Optional[str]
    ) -> Dict[str, Any]:
        """Direct API call to Grok as fallback"""
        import httpx
        
        api_key = os.getenv("XAI_API_KEY")
        
        base_url = self._get_xai_base_url()
        url = f"{base_url}/v1/responses"
        
        messages = self._build_xai_messages(user_message, roboto_context)
        
        payload = {
            "model": os.getenv("XAI_MODEL", "grok-4-1-fast-reasoning"),
            "input": messages,
            "stream": False,
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Calling Grok API: {url}")
            # Increased timeout to 120s to handle slow responses or cold starts
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, json=payload, headers=headers)
                
                # Log response for debugging
                logger.info(f"Grok API response status: {response.status_code}")
                
                if response.status_code == 404:
                    # Try alternate endpoint structure
                    logger.warning("404 on standard endpoint, trying alternate...")
                    return self._try_alternate_grok_endpoint(user_message, roboto_context, api_key)
                
                response.raise_for_status()
                
                data = response.json()
                logger.debug(f"Grok API response: {data}")
                
                # Extract content from response
                content = self._extract_response_text(data)
                if content:
                    return {
                        "success": True,
                        "response": content,
                        "response_id": data.get("id"),
                    }
                
                return {"success": False, "error": "Empty response from Grok API"}
                    
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.json()
            except:  # noqa: E722
                error_detail = e.response.text

            # Log full details server-side, but return a generic message to the client
            logger.error(f"Grok API HTTP error {e.response.status_code}: {error_detail}", exc_info=True)
            return {
                "success": False,
                "error": "Grok service returned an error. Please try again later.",
            }
        except httpx.ReadTimeout:
            logger.error("Grok API request timed out", exc_info=True)
            return {
                "success": False,
                "error": "Grok service is taking too long to respond. Please try again later.",
            }
        except httpx.HTTPError as e:
            # Connection and protocol-related errors
            logger.error(f"Grok API connection error: {e}", exc_info=True)
            return {
                "success": False,
                "error": "Unable to reach Grok service at the moment. Please try again later.",
            }
        except Exception as e:
            # Catch-all for any other unexpected errors
            logger.error(f"Grok API unexpected error: {e}", exc_info=True)
            return {
                "success": False,
                "error": "Failed to call Grok service due to an unexpected error.",
            }
    
    def _try_alternate_grok_endpoint(
        self,
        user_message: str,
        roboto_context: Optional[str],
        api_key: str
    ) -> Dict[str, Any]:
        """Try alternate Grok API endpoint structures"""
        import httpx
        
        base_url = self._get_xai_base_url()
        alternate_urls = [f"{base_url}/{path}" for path in self._get_xai_chat_paths()]
        
        for url in alternate_urls:
            try:
                logger.info(f"Trying alternate endpoint: {url}")
                
                if url.endswith("/responses"):
                    payload = {
                        "model": os.getenv("XAI_MODEL", "grok-4-1-fast-reasoning"),
                        "input": self._build_xai_messages(user_message, roboto_context),
                        "stream": False,
                    }
                # Try Anthropic-style format for /v1/messages
                elif url.endswith("/messages"):
                    payload = {
                        "model": os.getenv("XAI_MODEL", "grok-4-1-fast-reasoning"),
                        "messages": [{"role": "user", "content": user_message}],
                        "system": roboto_context or "You are Roboto SAI.",
                        "max_tokens": 1024,
                    }
                else:
                    payload = {
                        "model": os.getenv("XAI_MODEL", "grok-4-1-fast-reasoning"),
                        "messages": [
                            {"role": "system", "content": roboto_context or "You are Roboto SAI."},
                            {"role": "user", "content": user_message}
                        ],
                        "stream": False,
                    }
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",  # Try with Anthropic header
                }
                
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(url, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        logger.info(f"Success with alternate endpoint: {url}")
                        data = response.json()
                        
                        # Handle different response formats
                        content = self._extract_response_text(data)
                        
                        if content:
                            return {
                                "success": True,
                                "response": content,
                                "response_id": data.get("id"),
                            }
                    
            except Exception as e:
                logger.debug(f"Alternate endpoint {url} failed: {e}")
                continue
        
        # All endpoints failed - try OpenAI fallback if configured
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            logger.warning("Grok API unavailable, attempting OpenAI fallback")
            return self._try_openai_fallback(user_message, roboto_context, openai_key)

        return {
            "success": False, 
            "error": "Could not connect to Grok API. Please verify your XAI_API_KEY is valid and has access to the Grok API. Set XAI_API_BASE_URL/XAI_API_CHAT_PATH if endpoints changed, or configure OPENAI_API_KEY for fallback. Visit https://console.x.ai for API documentation."
        }

    def _try_openai_fallback(
        self,
        user_message: str,
        roboto_context: Optional[str],
        api_key: str,
    ) -> Dict[str, Any]:
        import httpx

        url = (os.getenv("OPENAI_API_BASE_URL") or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        messages = []
        if roboto_context:
            messages.append({"role": "system", "content": f"You are Roboto SAI. Context: {roboto_context}"})
        else:
            messages.append({"role": "system", "content": "You are Roboto SAI, an AI companion."})
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    return {"success": True, "response": content, "response_id": data.get("id")}
        except Exception as e:
            logger.error(f"OpenAI fallback failed: {e}")

        return {"success": False, "error": "OpenAI fallback failed. Verify OPENAI_API_KEY and model access."}

    def _build_from_messages(self, messages: List[BaseMessage]) -> tuple[str, str, Optional[str]]:
        # Performance: Use list comprehension generator
        context_parts = (
            f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}" 
            for msg in messages[:-1]
        )
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