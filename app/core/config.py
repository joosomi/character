import logging
import os

from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 로깅 설정
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# MongoDB 설정
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
MONGODB_HOST = os.getenv("MONGODB_HOST")
MONGODB_PORT = os.getenv("MONGODB_PORT")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")

# MongoDB 연결 문자열 생성
MONGODB_URI = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}?authSource=admin"

# OpenAI API 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 벡터 저장소 경로
VECTOR_STORE_PATH = os.environ.get("VECTOR_STORE_PATH")

# 애플리케이션 설정
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

# 설정 로깅
logger.info(f"MongoDB 호스트: {MONGODB_HOST}")
logger.info(f"MongoDB 포트: {MONGODB_PORT}")
logger.info(f"MongoDB 데이터베이스: {MONGODB_DATABASE}")
logger.info(f"OpenAI API 키 설정됨: {bool(OPENAI_API_KEY)}")
logger.info(f"벡터 저장소 경로: {VECTOR_STORE_PATH}")
