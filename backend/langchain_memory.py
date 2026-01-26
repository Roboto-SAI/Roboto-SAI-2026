"""
LangChain memory integration for Roboto SAI backend.
Custom SQL message history store using existing messages table.
"""

import asyncio
import json
from typing import List, Optional, Any, Dict
from datetime import datetime

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.pydantic_v1 import BaseModel

from db import get_supabase_client


# In-memory fallback when Supabase is not configured
_memory_store: dict[str, list[BaseMessage]] = {}


class SupabaseMessageHistory(BaseChatMessageHistory):
    """
    Supabase-based chat message history for LangChain.
    """

    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id or "demo-user"
        self._supabase = get_supabase_client()
        self._key = f"{self.user_id}::{self.session_id}"

    @property
    def messages(self) -> List[BaseMessage]:
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(self._get_messages_async())
            return result
        finally:
            loop.close()

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

    async def _get_messages_async(self) -> List[BaseMessage]:
        if self._supabase is None:
            return _memory_store.get(self._key, []).copy()

        query = self._supabase.table("messages").select("*").eq("session_id", self.session_id).order("created_at")
        if self.user_id:
            query = query.eq("user_id", self.user_id)
        
        result = await asyncio.to_thread(query.execute)
        data = result.data or []

        lc_messages = []
        for msg in data:
            lc_message = self._create_lc_message(msg)
            if lc_message:
                lc_messages.append(lc_message)

        return lc_messages

    async def add_message(self, message: BaseMessage) -> Optional[str]:
        role = "user" if isinstance(message, HumanMessage) else "assistant" if isinstance(message, AIMessage) else None
        if not role:
            return None

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
        # Return inserted row id if available
        def _insert():
            resp = self._supabase.table("messages").insert(data).execute()
            try:
                if resp and resp.data and len(resp.data) > 0:
                    return str(resp.data[0].get("id"))
            except Exception:
                pass
            return None

        return await asyncio.to_thread(_insert)

    async def clear(self) -> None:
        if self._supabase is None:
            _memory_store.pop(self._key, None)
            return

        query = self._supabase.table("messages").delete().eq("session_id", self.session_id)
        if self.user_id:
            query = query.eq("user_id", self.user_id)
        await asyncio.to_thread(query.execute)

    def __len__(self) -> int:
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._len_async())
        finally:
            loop.close()

    async def _len_async(self) -> int:
        if self._supabase is None:
            return len(_memory_store.get(self._key, []))

        query = self._supabase.table("messages").select("count", count="exact").eq("session_id", self.session_id)
        if self.user_id:
            query = query.eq("user_id", self.user_id)
        result = await asyncio.to_thread(query.execute)
        return result.count or 0
