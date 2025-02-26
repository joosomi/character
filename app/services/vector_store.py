import logging
import os
from typing import List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)


class VectorStoreService:
    def __init__(self, api_key=None, vector_store_path: str = "vector_store"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.vector_store_path = vector_store_path
        try:
            self.embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
            self.vector_store = None
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            )
            logger.info("벡터 저장소 서비스 초기화 성공")
        except Exception as e:
            logger.error(f"벡터 저장소 초기화 실패: {str(e)}")
            self.embeddings = None

    def add_texts(self, texts, user_id):
        """텍스트를 벡터 저장소에 추가"""
        if not self.embeddings:
            logger.warning("임베딩 모델이 초기화되지 않았습니다")
            return False

        try:
            # 메타데이터 추가
            metadatas = [{"user_id": user_id} for _ in texts]

            # 문서 분할
            docs = self.text_splitter.create_documents(texts, metadatas=metadatas)

            # 벡터 저장소에 추가
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(docs, self.embeddings)
                logger.info(f"새 벡터 저장소 생성: {len(docs)}개 문서 추가")
            else:
                self.vector_store.add_documents(docs)
                logger.info(f"기존 벡터 저장소에 {len(docs)}개 문서 추가")

            return True
        except Exception as e:
            logger.error(f"텍스트 추가 실패: {str(e)}")
            return False

    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        k: int = 3,
        score_threshold: float = 0.3,
    ):
        """쿼리와 관련된 문서 검색"""
        try:
            if not self.vector_store:
                logger.warning("벡터 저장소가 로드되지 않았습니다")
                return []

            # 필터 설정
            filter_dict = None
            if user_id:
                filter_dict = {"user_id": user_id}

            # 검색 실행
            docs_with_scores = self.vector_store.similarity_search_with_score(
                query, k=k, filter=filter_dict, score_threshold=score_threshold
            )

            # 유사도 점수 메타데이터에 추가
            docs = []
            for doc, score in docs_with_scores:
                doc.metadata["similarity"] = f"{score:.4f}"
                docs.append(doc)

            logger.info(f"쿼리 '{query}'에 대해 {len(docs)}개 문서 검색됨")
            return docs
        except Exception as e:
            logger.error(f"검색 실패: {str(e)}")
            return []

    def save_local(self, path: Optional[str] = None) -> bool:
        """벡터 저장소를 로컬에 저장"""
        try:
            if not self.vector_store:
                logger.warning("저장할 벡터 저장소가 없습니다")
                return False

            store_path = path or self.vector_store_path
            logger.info(f"벡터 저장소 저장 중: {store_path}")

            self.vector_store.save_local(store_path)

            logger.info(f"벡터 저장소 저장 완료: {store_path}")
            return True
        except Exception as e:
            logger.error(f"벡터 저장소 저장 실패: {str(e)}")
            return False

    def load_local(self, path: Optional[str] = None) -> bool:
        """로컬에서 벡터 저장소 로드"""
        try:
            store_path = path or self.vector_store_path
            index_path = os.path.join(store_path, "index.faiss")
            pkl_path = os.path.join(store_path, "index.pkl")

            if not os.path.exists(index_path) or not os.path.exists(pkl_path):
                logger.warning(f"벡터 저장소 파일이 '{store_path}'에 존재하지 않습니다")
                return False

            logger.info(f"벡터 저장소 로드 중: {store_path}")

            # 보안 경고를 무시하고 pickle 파일 로드 허용
            self.vector_store = FAISS.load_local(
                store_path, self.embeddings, allow_dangerous_deserialization=True
            )

            logger.info(f"벡터 저장소 로드 완료: {store_path}")
            return True
        except Exception as e:
            logger.error(f"벡터 저장소 로드 실패: {str(e)}")
            return False
