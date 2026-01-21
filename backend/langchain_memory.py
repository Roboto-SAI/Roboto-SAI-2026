"""
LangChain memory integration for Roboto SAI backend.
Custom SQL message history store using existing messages table.
"""

import json
from typing import List, Optional, Any, Dict
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.pydantic_v1 import BaseModel

from db import get_session
from models import Message


class SQLMessageHistory(BaseChatMessageHistory):
    """
    Custom chat message history store using Roboto SAI's messages table.
    Implements LangChain's BaseChatMessageHistory for async SQLAlchemy.
    """

    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id

    @property
    def messages(self) -> List[BaseMessage]:
        """Get all messages in conversation history."""
        # This is synchronous property, but we need async query
        # Use sync session for LangChain compatibility
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(self._get_messages_async())
            return result
        finally:
            loop.close()

    async def _get_messages_async(self) -> List[BaseMessage]:
        """Async method to fetch messages from database."""
        async for session in get_session():
            stmt = select(Message).where(Message.session_id == self.session_id)
            if self.user_id:
                stmt = stmt.where(Message.user_id == self.user_id)
            stmt = stmt.order_by(Message.created_at)

            result = await session.execute(stmt)
            messages = result.scalars().all()

            lc_messages = []
            for msg in messages:
                # Convert to LangChain message format
                content = msg.content
                additional_kwargs = {}

                # Add emotion data to additional_kwargs
                if msg.emotion:
                    additional_kwargs["emotion"] = msg.emotion
                if msg.emotion_text:
                    additional_kwargs["emotion_text"] = msg.emotion_text
                if msg.emotion_probabilities:
                    try:
                        additional_kwargs["emotion_probabilities"] = json.loads(msg.emotion_probabilities)
                    except (json.JSONDecodeError, TypeError):
                        additional_kwargs["emotion_probabilities"] = msg.emotion_probabilities

                # Create appropriate message type
                if msg.role == "user":
                    lc_message = HumanMessage(content=content, additional_kwargs=additional_kwargs)
                elif msg.role == "assistant":
                    lc_message = AIMessage(content=content, additional_kwargs=additional_kwargs)
                else:
                    # Skip system/other messages or handle as needed
                    continue

                lc_messages.append(lc_message)

            return lc_messages

    async def add_message(self, message: BaseMessage) -> None:
        """Add a message to the database."""
        async for session in get_session():
            # Extract role from message type
            if isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            else:
                return  # Skip unknown message types

            # Extract emotion data from additional_kwargs
            emotion = message.additional_kwargs.get("emotion")
            emotion_text = message.additional_kwargs.get("emotion_text")
            emotion_probabilities = message.additional_kwargs.get("emotion_probabilities")

            # Convert probabilities to JSON if dict
            if isinstance(emotion_probabilities, dict):
                emotion_probabilities = json.dumps(emotion_probabilities)

            # Create message record
            db_message = Message(
                user_id=self.user_id,
                session_id=self.session_id,
                role=role,
                content=message.content,
                emotion=emotion,
                emotion_text=emotion_text,
                emotion_probabilities=emotion_probabilities,
            )

            session.add(db_message)
            await session.commit()
            break  # Exit async generator

    async def clear(self) -> None:
        """Clear all messages for this session."""
        async for session in get_session():
            stmt = select(Message).where(Message.session_id == self.session_id)
            if self.user_id:
                stmt = stmt.where(Message.user_id == self.user_id)

            result = await session.execute(stmt)
            messages = result.scalars().all()

            for msg in messages:
                await session.delete(msg)
            await session.commit()
            break

    def __len__(self) -> int:
        """Return number of messages."""
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(self._len_async())
            return result
        finally:
            loop.close()

    async def _len_async(self) -> int:
        """Async length calculation."""
        async for session in get_session():
            stmt = select(Message).where(Message.session_id == self.session_id)
            if self.user_id:
                stmt = stmt.where(Message.user_id == self.user_id)

            result = await session.execute(stmt)
            count = len(result.scalars().all())
            return count