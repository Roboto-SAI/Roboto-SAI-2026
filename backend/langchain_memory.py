"""
LangChain memory integration for Roboto SAI backend.
Custom SQL message history store using existing messages table with async Supabase client.
"""

import json
from typing import List, Optional, Any, Dict

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from utils.supabase_client import get_async_supabase_client


# In-memory fallback when Supabase is not configured
_memory_store: dict[str, list[BaseMessage]] = {}


class SupabaseMessageHistory(BaseChatMessageHistory):
    """
    Supabase-based chat message history for LangChain using async client.
    """

    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id or "demo-user"
        self._supabase = None  # Will be initialized async
        self._key = f"{self.user_id}::{self.session_id}"
        self._initialized = False

    async def _ensure_client(self):
        """Lazy initialization of async Supabase client."""
        if not self._initialized:
            self._supabase = await get_async_supabase_client()
            self._initialized = True

    @property
    def messages(self) -> List[BaseMessage]:
        """Get messages (note: synchronous property, returns empty for async usage)."""
        # LangChain may call this property sync, but we use async methods in practice
        return _memory_store.get(self._key, []).copy()

    def _build_additional_kwargs(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Build additional_kwargs from message data."""
        additional_kwargs = {}
        if msg.get("emotion"):
            additional_kwargs["emotion"] = msg["emotion"]
        if msg.get("emotion_text"):
            additional_kwargs["emotion_text"] = msg["emotion_text"]
        if msg.get("emotion_probabilities"):
            try:
                additional_kwargs["emotion_probabilities"] = json.loads(msg["emotion_probabilities"])
            except:
                additional_kwargs["emotion_probabilities"] = msg["emotion_probabilities"]
        return additional_kwargs

    def _create_lc_message(self, msg: Dict[str, Any]) -> Optional[BaseMessage]:
        """Create a LangChain message from message data."""
        content = msg["content"]
        additional_kwargs = self._build_additional_kwargs(msg)
        
        if msg["role"] == "user":
            return HumanMessage(content=content, additional_kwargs=additional_kwargs)
        elif msg["role"] == "assistant":
            return AIMessage(content=content, additional_kwargs=additional_kwargs)
        return None

    async def aget_messages(self) -> List[BaseMessage]:
        """Async get messages (proper async implementation)."""
        await self._ensure_client()
        
        if self._supabase is None:
            return _memory_store.get(self._key, []).copy()

        try:
            query = self._supabase.table("messages").select("*").eq("session_id", self.session_id).order("created_at")
            if self.user_id:
                query = query.eq("user_id", self.user_id)
            
            resp = await query.execute()
            data = resp.data or []

            lc_messages = []
            for msg in data:
                lc_message = self._create_lc_message(msg)
                if lc_message:
                    lc_messages.append(lc_message)
            return lc_messages
        except Exception as e:
            return []

    async def add_message(self, message: BaseMessage) -> Optional[str]:
        """Async add message."""
        role = "user" if isinstance(message, HumanMessage) else "assistant" if isinstance(message, AIMessage) else None
        if not role:
            return None

        await self._ensure_client()
        
        if self._supabase is None:
            _memory_store.setdefault(self._key, []).append(message)
            return None

        data = {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "role": role,
            "content": message.content,
            "emotion": message.additional_kwargs.get("emotion"),
            "emotion_text": message.additional_kwargs.get("emotion_text"),
            "emotion_probabilities": json.dumps(message.additional_kwargs.get("emotion_probabilities", {})),
        }
        
        try:
            resp = await self._supabase.table("messages").insert(data).execute()
            if resp and resp.data and len(resp.data) > 0:
                return str(resp.data[0].get("id"))
        except Exception as e:
            return None

    async def clear(self) -> None:
        """Async clear messages."""
        await self._ensure_client()
        
        if self._supabase is None:
            _memory_store.pop(self._key, None)
            return

        try:
            query = self._supabase.table("messages").delete().eq("session_id", self.session_id)
            if self.user_id:
                query = query.eq("user_id", self.user_id)
            await query.execute()
        except Exception:
            pass

    def __len__(self) -> int:
        """Get message count (sync fallback to in-memory)."""
        return len(_memory_store.get(self._key, []))
