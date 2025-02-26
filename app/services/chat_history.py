import datetime
import logging

from pymongo import MongoClient

from app.core.config import MONGODB_URI
from app.models import Message

logger = logging.getLogger(__name__)


class ChatHistoryService:
    def __init__(self, connection_string=MONGODB_URI):
        try:
            self.client = MongoClient(connection_string)
            self.db = self.client.get_database()
            self.collection = self.db["chat_history"]
            logger.info("MongoDB 연결 성공")
        except Exception as e:
            logger.error(f"MongoDB 연결 실패: {str(e)}")
            raise

    def add_message(self, user_id, message):
        """메시지 추가"""
        try:
            self.collection.insert_one(
                {
                    "user_id": user_id,
                    "timestamp": datetime.datetime.now(),
                    "is_user": message.is_user,
                    "content": message.content,
                }
            )
            return True
        except Exception as e:
            logger.error(f"메시지 추가 실패: {str(e)}")
            return False

    def get_history(self, user_id, limit=20):
        """사용자 대화 기록 가져오기"""
        try:
            cursor = self.collection.find(
                {"user_id": user_id}, sort=[("timestamp", 1)], limit=limit
            )
            return [
                Message(is_user=doc["is_user"], content=doc["content"])
                for doc in cursor
            ]
        except Exception as e:
            logger.error(f"대화 기록 조회 실패: {str(e)}")
            return []

    def get_message_count(self, user_id):
        """사용자의 메시지 수 반환"""
        try:
            # MongoDB에서 사용자 메시지 수 조회
            count = self.collection.count_documents({"user_id": user_id})
            return count
        except Exception as e:
            logger.error(f"메시지 수 조회 실패: {str(e)}")
            return 0
