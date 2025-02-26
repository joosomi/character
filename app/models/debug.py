from typing import List, Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """문서 응답 모델"""

    content: str
    user_id: str
    source: Optional[str] = None
    similarity: Optional[str] = None


class DebugResponse(BaseModel):
    """디버그 응답 모델"""

    query: str
    results: List[DocumentResponse]
    success: bool
    message: str


class DebugRequest(BaseModel):
    """디버그 요청 모델"""

    query: str
    user_id: Optional[str] = None
    k: Optional[int] = 3
    reload: Optional[bool] = True
    score_threshold: Optional[float] = 0.3
