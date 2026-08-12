from collections import defaultdict

from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory

_sessions: dict[str, BaseChatMessageHistory] = defaultdict(InMemoryChatMessageHistory)


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    return _sessions[session_id]
