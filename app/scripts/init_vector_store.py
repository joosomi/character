import logging
import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.core.config import OPENAI_API_KEY
from app.services.vector_store import VectorStoreService

# 벡터 저장소 경로 직접 정의
VECTOR_STORE_PATH = os.environ.get("VECTOR_STORE_PATH", "vector_store")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_vector_store():
    """벡터 저장소 초기화 스크립트"""
    logger.info("벡터 저장소 초기화 시작")

    # API 키 확인
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        return False

    # 벡터 저장소 서비스 인스턴스 생성
    vector_store_service = VectorStoreService(api_key=OPENAI_API_KEY)

    # 초기 데이터 추가
    initial_texts = [
        "안녕하세요, 저는 심리 상담 코치 세레니티입니다.",
        "마음 챙김과 명상은 스트레스 관리에 효과적입니다.",
        "불안감을 느낄 때는 깊은 호흡이 도움이 됩니다.",
        "자신의 감정을 인식하고 표현하는 것이 중요합니다.",
    ]

    # 벡터 저장소에 초기 데이터 추가
    success = vector_store_service.add_texts(initial_texts, user_id="system")

    if success:
        logger.info("초기 데이터 추가 성공")
    else:
        logger.error("초기 데이터 추가 실패")
        return False

    # 벡터 저장소 저장
    success = vector_store_service.save_local(VECTOR_STORE_PATH)

    if success:
        logger.info("벡터 저장소 저장 성공")
    else:
        logger.error("벡터 저장소 저장 실패")
        return False

    return True


if __name__ == "__main__":
    if initialize_vector_store():
        print("벡터 저장소가 성공적으로 초기화되었습니다.")
    else:
        print("벡터 저장소 초기화 실패")
