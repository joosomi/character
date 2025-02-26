import logging
from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.models.debug import DebugRequest, DebugResponse, DocumentResponse
from app.services.vector_store import VectorStoreService

router = APIRouter()
logger = logging.getLogger(__name__)

# 벡터 저장소 서비스 인스턴스
vector_store_service = VectorStoreService()


@router.get("/debug")
async def debug_page():
    """디버그 페이지로 리디렉션"""
    return RedirectResponse(url="/static/debug.html")


@router.post("/debug/rag", response_model=DebugResponse)
async def debug_rag(request: DebugRequest):
    """RAG 디버깅 엔드포인트"""
    logger.info(
        f"RAG 디버그 요청: 쿼리='{request.query}', k={request.k}, 임계값={request.score_threshold}"
    )

    try:
        # 벡터 저장소 로드 확인
        if request.reload or not vector_store_service.vector_store:
            success = vector_store_service.load_local()
            if not success:
                return DebugResponse(
                    query=request.query,
                    results=[],
                    success=False,
                    message="벡터 저장소 로드 실패",
                )

        # 관련 문서 검색
        docs = vector_store_service.search(
            request.query,
            user_id=request.user_id,
            k=request.k,
            score_threshold=request.score_threshold,
        )

        # 결과 변환
        results = [
            DocumentResponse(
                content=doc.page_content,
                user_id=doc.metadata.get("user_id", "unknown"),
                source=doc.metadata.get("source"),
                similarity=doc.metadata.get("similarity", "N/A"),
            )
            for doc in docs
        ]

        return DebugResponse(
            query=request.query,
            results=results,
            success=True,
            message=f"{len(results)}개의 관련 문서 검색됨",
        )
    except Exception as e:
        logger.error(f"RAG 디버그 중 오류 발생: {str(e)}")
        return DebugResponse(
            query=request.query,
            results=[],
            success=False,
            message=f"오류 발생: {str(e)}",
        )
