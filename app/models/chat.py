from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """채팅 메시지 모델"""

    is_user: bool  # True면 사용자, False면 어시스턴트
    content: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """채팅 요청 모델"""

    user_id: str
    message: str
    offline_mode: Optional[bool] = False
    use_rag: Optional[bool] = True
    chat_history: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    """채팅 응답 모델"""

    user_id: str
    message: str
    response: str
    emotion_analysis: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatHistoryResponse(BaseModel):
    """채팅 기록 응답 모델"""

    user_id: str
    messages: List[Message]
    total_messages: int
