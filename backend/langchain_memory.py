"""
LangChain memory integration for Roboto SAI backend.
Custom SQL message history store using existing messages table.
"""

import json
from typing import List, Optional, Any, Dict
from datetime import datetime
from typing import List, Optional, Any, Dict
from datetime import datetime
import json

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.pydantic_v1 import BaseModel

from db import get_supabase_client


class SupabaseMessageHistory(BaseChatMessageHistory):
    """
    Supabase-based chat message history for LangChain.
    """

    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id

    @property
    def messages(self) -> List[BaseMessage]:
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(self._get_messages_async())
            return result
        finally:
            loop.close()

    async def _get_messages_async(self) -> List[BaseMessage]:
        supabase = get_supabase_client()
        query = supabase.table("messages").select("*").eq("session_id", self.session_id).order("created_at")
        if self.user_id:
            query = query.eq("user_id", self.user_id)
        
        result = query.execute()
        data = result.data or []

        lc_messages = []
        for msg in data:
            content = msg["content"]
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

            if msg["role"] == "user":
                lc_message = HumanMessage(content=content, additional_kwargs=additional_kwargs)
            elif msg["role"] == "assistant":
                lc_message = AIMessage(content=content, additional_kwargs=additional_kwargs)
            else:
                continue

            lc_messages.append(lc_message)

        return lc_messages

    async def add_message(self, message: BaseMessage) -> None:
        supabase = get_supabase_client()
        role = "user" if isinstance(message, HumanMessage) else "assistant" if isinstance(message, AIMessage) else None
        if not role:
            return

        data = {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "role": role,
            "content": message.content,
            "emotion": message.additional_kwargs.get("emotion"),
            "emotion_text": message.additional_kwargs.get("emotion_text"),
            "emotion_probabilities": json.dumps(message.additional_kwargs.get("emotion_probabilities", {})),
        }

        supabase.table("messages").insert(data).execute()

    async def clear(self) -> None:
        supabase = get_supabase_client()
        query = supabase.table("messages").delete().eq("session_id", self.session_id)
        if self.user_id:
            query = query.eq("user_id", self.user_id)
        query.execute()

    def __len__(self) -> int:
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._len_async())
        finally:
            loop.close()

    async def _len_async(self) -> int:
        supabase = get_supabase_client()
        query = supabase.table("messages").select("count", count="exact").eq("session_id", self.session_id)
        if self.user_id:
            query = query.eq("user_id", self.user_id)
        result = query.execute()
        return result.count or 0