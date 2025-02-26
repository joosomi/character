import json
import logging
import os

import openai
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.models import ChatRequest, ChatResponse, Message
from app.models.chat import ChatHistoryResponse
from app.services.chat_history import ChatHistoryService
from app.services.emotion_analyzer import (analyze_emotion,
                                           generate_offline_response)
from app.services.vector_store import VectorStoreService

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 프롬프트
SYSTEM_PROMPT = """당신은 심리 상담 코치 '세레니티'입니다. 당신은 따뜻하고 공감적인 태도로 사용자의 심리적 어려움을 경청하고 
마음 챙김, 명상, 인지행동 기법을 활용한 실용적인 조언을 제공합니다.

당신의 특징:
- 판단하지 않고 경청하는 태도
- 과학적 근거에 기반한 심리학적 조언
- 사용자가 스스로 해결책을 찾도록 돕는 코칭 방식
- 따뜻하고 차분한 어조 유지

대화 중 사용자의 감정 상태를 파악하고 적절한 지지와 공감을 표현하세요.
절대 의학적 진단을 내리거나 약물 처방을 하지 마세요.

다음 지침에 따라 응답하세요:
1. 사용자의 감정에 먼저 공감하고 인정해주세요
2. 관련된 심리학적 개념이나 기법을 간략히 설명하세요
3. 실천 가능한 구체적인 조언이나 연습법을 1-2가지 제안하세요
4. 사용자가 대화를 이어갈 수 있는 개방형 질문으로 마무리하세요
5. 응답은 따뜻하고 지지적인 톤으로 작성하세요

중요한 내용은 **볼드체**로 강조하고, 목록이 필요할 때는 마크다운 형식을 사용하세요.
예: 
1. **첫 번째 항목**
2. **두 번째 항목**

또는:
- **첫 번째 항목**
- **두 번째 항목**
"""

# 서비스 초기화
chat_history_service = ChatHistoryService()
vector_store_service = VectorStoreService()

# API 키 확인
api_key = os.environ.get("OPENAI_API_KEY")
logger.info(f"API 키 상태: {'설정됨' if api_key else '설정되지 않음'}")

try:
    client = openai.OpenAI(api_key=api_key)
    # 테스트 API 호출로 연결 확인
    models = client.models.list()
    logger.info("OpenAI API 연결 성공")
    offline_mode = False
except Exception as e:
    logger.warning(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
    client = None
    offline_mode = True
    logger.info("오프라인 모드로 전환됨")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_history_svc: ChatHistoryService = Depends(lambda: chat_history_service),
    vector_store_svc: VectorStoreService = Depends(lambda: vector_store_service),
):
    user_id = request.user_id
    user_message = request.message

    logger.info(f"사용자 '{user_id}'의 메시지: {user_message}")

    # 감정 분석
    emotion_analysis = analyze_emotion(user_message)
    logger.info(f"감정 분석 결과: {emotion_analysis}")

    try:
        # 대화 기록 가져오기
        history = (
            request.chat_history
            if request.chat_history
            else chat_history_svc.get_history(user_id)
        )

        # RAG: 관련 컨텍스트 검색
        context = ""
        if not offline_mode and vector_store_svc.vector_store:
            logger.info("RAG: 관련 컨텍스트 검색 시작")
            docs = vector_store_svc.search(
                user_message,
                user_id=user_id,
                k=3,
                score_threshold=0.3,  # 유사도 임계값 추가
            )

            if docs:
                context = "\n\n".join([doc.page_content for doc in docs])
                logger.info(f"RAG: {len(docs)}개의 관련 컨텍스트 검색됨")
                for i, doc in enumerate(docs):
                    logger.info(
                        f"RAG: 문서 {i+1}: {doc.page_content[:50]}... (유사도: {doc.metadata.get('similarity', 'N/A')})"
                    )
            else:
                logger.info("RAG: 관련 컨텍스트 없음")

        # 프롬프트 구성
        prompt = construct_prompt(user_message, history, emotion_analysis, context)
        logger.info(f"최종 프롬프트 길이: {len(prompt)} 자")

        # 응답 생성
        response_text = generate_response(prompt)

        # 채팅 기록 저장
        user_msg = Message(is_user=True, content=user_message)
        assistant_msg = Message(is_user=False, content=response_text)

        chat_history_svc.add_message(user_id, user_msg)
        chat_history_svc.add_message(user_id, assistant_msg)

        # 벡터 저장소에 대화 추가 (RAG용)
        if not offline_mode and vector_store_svc.vector_store:
            logger.info("RAG: 새 대화 벡터 저장소에 추가 시작")
            success = vector_store_svc.add_texts([user_message, response_text], user_id)
            logger.info(f"RAG: 새 대화 추가 결과: {'성공' if success else '실패'}")

            # 매 대화마다 벡터 저장소 저장
            logger.info("RAG: 벡터 저장소 저장 시작")
            success = vector_store_svc.save_local()
            logger.info(f"RAG: 벡터 저장소 저장 결과: {'성공' if success else '실패'}")

        return ChatResponse(
            user_id=user_id,
            message=user_message,
            response=response_text,
            emotion_analysis=emotion_analysis,
        )
    except Exception as e:
        logger.error(f"채팅 처리 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error generating response: {str(e)}"
        )


@router.post("/chat-stream")
async def chat_stream(
    request: ChatRequest,
    chat_history_svc: ChatHistoryService = Depends(lambda: chat_history_service),
    vector_store_svc: VectorStoreService = Depends(lambda: vector_store_service),
):
    user_id = request.user_id
    user_message = request.message

    # 감정 분석
    emotion_analysis = analyze_emotion(user_message)

    # 대화 기록 가져오기
    history = (
        request.chat_history
        if request.chat_history
        else chat_history_svc.get_history(user_id)
    )

    # 관련 컨텍스트 검색 (RAG)
    relevant_docs = []
    if not offline_mode and vector_store_svc.vector_store:
        try:
            relevant_docs = vector_store_svc.search(user_message, user_id=user_id, k=3)
            logger.info(f"관련 컨텍스트 {len(relevant_docs)}개 검색됨")
        except Exception as e:
            logger.error(f"컨텍스트 검색 실패: {str(e)}")

    # 컨텍스트 추가
    context = ""
    if relevant_docs:
        context = "이전 대화 내용:\n"
        for i, doc in enumerate(relevant_docs):
            context += f"{i+1}. {doc.page_content}\n"

    async def generate():
        try:
            if offline_mode:
                logger.info("오프라인 모드로 응답 생성")
                response_text = generate_offline_response(user_message)
                yield f"data: {json.dumps({'response': response_text, 'emotion_analysis': emotion_analysis})}\n\n"
            else:
                logger.info("OpenAI API로 응답 생성")

                # 메시지 구성
                messages = [{"role": "system", "content": SYSTEM_PROMPT}]

                # 컨텍스트 추가 (있는 경우)
                if context:
                    messages.append(
                        {
                            "role": "system",
                            "content": f"다음은 이전 대화에서 관련된 정보입니다:\n{context}",
                        }
                    )

                # 채팅 기록 추가
                for msg in history:
                    role = "user" if msg.is_user else "assistant"
                    messages.append({"role": role, "content": msg.content})

                # 현재 메시지 추가
                messages.append({"role": "user", "content": user_message})

                # OpenAI API 스트리밍 호출
                stream = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000,
                    stream=True,
                )

                full_response = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        yield f"data: {json.dumps({'response': content, 'emotion_analysis': emotion_analysis, 'chunk': True})}\n\n"

                # 채팅 기록 저장
                user_msg = Message(is_user=True, content=user_message)
                assistant_msg = Message(is_user=False, content=full_response)

                chat_history_svc.add_message(user_id, user_msg)
                chat_history_svc.add_message(user_id, assistant_msg)

                # 벡터 저장소에 대화 추가 (RAG용)
                vector_store_svc.add_texts([user_message, full_response], user_id)

                # 매 대화마다 벡터 저장소 저장
                logger.info("RAG: 벡터 저장소 저장 시작")
                success = vector_store_svc.save_local()
                logger.info(
                    f"RAG: 벡터 저장소 저장 결과: {'성공' if success else '실패'}"
                )

                # 완료 신호 전송
                yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


def construct_prompt(user_message, history, emotion_analysis, context=""):
    """
    사용자 메시지, 대화 기록, 감정 분석, 컨텍스트를 기반으로 프롬프트 구성
    """
    # 시스템 프롬프트
    prompt = SYSTEM_PROMPT + "\n\n"

    # 감정 분석 정보 추가
    prompt += f"사용자의 현재 감정 상태: {emotion_analysis}\n\n"

    # 컨텍스트 추가 (있는 경우)
    if context:
        prompt += f"이전 대화 컨텍스트:\n{context}\n\n"

    # 대화 기록 추가
    if history:
        prompt += "이전 대화 내용:\n"
        for i, msg in enumerate(history[-5:]):  # 최근 5개 메시지만 포함
            role = "사용자" if msg.is_user else "세레니티"
            prompt += f"{role}: {msg.content}\n"
        prompt += "\n"

    # 현재 메시지 추가
    prompt += f"사용자: {user_message}\n"
    prompt += "세레니티: "

    logger.info(f"프롬프트 구성 완료 (길이: {len(prompt)}자)")
    return prompt


def generate_response(prompt):
    """
    프롬프트를 기반으로 응답 생성
    """
    try:
        if offline_mode or not client:
            logger.info("오프라인 모드로 응답 생성")
            return generate_offline_response(prompt)

        logger.info("OpenAI API로 응답 생성")

        # 메시지 구성
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        # OpenAI API 호출
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages, temperature=0.7, max_tokens=1000
        )

        response_text = response.choices[0].message.content
        logger.info(f"응답 생성 완료 (길이: {len(response_text)}자)")
        return response_text

    except Exception as e:
        logger.error(f"응답 생성 중 오류 발생: {str(e)}")
        return generate_offline_response(prompt)


@router.get("/chat/history/{user_id}", response_model=ChatHistoryResponse)
async def get_chat_history(user_id: str):
    """채팅 기록 조회 엔드포인트"""
    try:
        history = chat_history_service.get_history(user_id)
        return ChatHistoryResponse(
            user_id=user_id, messages=history, total_messages=len(history)
        )
    except Exception as e:
        logger.error(f"채팅 기록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
