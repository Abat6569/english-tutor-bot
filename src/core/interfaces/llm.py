from typing import Protocol

from src.core.entities.conversation import ConversationTurn


class ConversationProvider(Protocol):
    async def reply(self, history: list[ConversationTurn], user_message: str) -> str: ...
