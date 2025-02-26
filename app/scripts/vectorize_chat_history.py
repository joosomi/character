import logging
import os
import sys

from dotenv import load_dotenv
from pymongo import MongoClient

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.services.vector_store import VectorStoreService

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def vectorize_chat_history():
    """MongoDB에 저장된 채팅 기록을 벡터화하여 벡터 저장소에 저장"""
    logger.info("채팅 기록 벡터화 시작")

    # MongoDB 연결
    mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.environ.get("MONGODB_DATABASE", "serenity")
    collection_name = os.environ.get("MONGODB_COLLECTION", "chat_history")

    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    # 벡터 저장소 서비스 초기화
    vector_store_service = VectorStoreService()

    # 기존 벡터 저장소 로드 시도
    try:
        vector_store_service.load_local(allow_dangerous_deserialization=True)
    except:
        logger.info("기존 벡터 저장소 로드 실패, 새로 생성합니다")

    # 사용자별 채팅 기록 가져오기
    user_ids = collection.distinct("user_id")
    logger.info(f"총 {len(user_ids)}명의 사용자 데이터 처리 중")

    for user_id in user_ids:
        # 사용자 메시지 가져오기
        messages = list(collection.find({"user_id": user_id}).sort("timestamp", 1))
        logger.info(f"사용자 '{user_id}'의 메시지 {len(messages)}개 처리 중")

        # 메시지 내용 추출
        texts = []
        for msg in messages:
            # 메시지 내용이 있고 길이가 충분한 경우만 처리
            if msg.get("content") and len(msg.get("content", "")) > 10:
                texts.append(msg["content"])

        if not texts:
            logger.warning(f"사용자 '{user_id}'의 처리할 메시지가 없습니다")
            continue

        # 벡터 저장소에 추가
        success = vector_store_service.add_texts(texts, user_id=user_id)

        if success:
            logger.info(
                f"사용자 '{user_id}'의 메시지 {len(texts)}개가 벡터 저장소에 추가됨"
            )
        else:
            logger.error(f"사용자 '{user_id}'의 메시지 추가 실패")

    # 벡터 저장소 저장
    success = vector_store_service.save_local()

    if success:
        logger.info("벡터 저장소 저장 성공")
    else:
        logger.error("벡터 저장소 저장 실패")
        return False

    return True


if __name__ == "__main__":
    if vectorize_chat_history():
        print("채팅 기록 벡터화 완료")
    else:
        print("채팅 기록 벡터화 실패")
