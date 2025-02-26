import logging
import os
import re
from typing import Any, Dict

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

api_key = os.environ.get("OPENAI_API_KEY")
emotion_client = AsyncOpenAI(api_key=api_key)


async def analyze_emotion(message: str) -> Dict[str, Any]:
    """사용자 메시지의 감정 분석"""
    try:
        # 로그 추가
        logger.info(f"감정 분석 시작: '{message[:30]}...'")

        # 메시지 길이 계산
        words = message.split()
        message_length = len(words)

        # # 짧은 메시지(5단어 이하)는 중립으로 처리
        # if message_length <= 5:
        #     logger.info(f"짧은 메시지({message_length}단어)는 중립으로 처리합니다.")
        #     return {
        #         "emotion": "중립",
        #         "intensity": 2,
        #         "raw_analysis": "짧은 메시지는 중립으로 처리",
        #         "message_length": message_length,
        #     }

        if not emotion_client:
            logger.error("감정 분석용 OpenAI 클라이언트가 초기화되지 않았습니다.")
            return {
                "emotion": "중립",
                "intensity": 3,
                "raw_analysis": "OpenAI 클라이언트 없음",
                "message_length": message_length,
            }

        # 감정 분석 요청
        response = await emotion_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """
사용자의 메시지에서 감정을 분석해주세요. 다음 감정 중 하나를 선택하고 강도를 1-10 사이로 평가해주세요: 기쁨, 슬픔, 분노, 불안, 중립.

중요한 지침:
1. 일상적인 표현이나 단순한 상태 표현("배고파", "피곤해" 등)은 감정이 아닙니다. 이런 경우 "중립"으로 분류하고 강도를 2-3으로 낮게 평가하세요.
2. 확실하지 않은 경우 항상 "중립"으로 분류하고 강도를 낮게(1-3) 평가하세요.
3. 짧은 메시지는 대부분 "중립"으로 분류하세요.
4. 감정이 명확하게 표현된 경우에만 해당 감정으로 분류하세요.
5. 인사말, 질문, 일상적인 대화는 "중립"으로 분류하세요.

응답 형식:
감정: [감정]
강도: [1-10]
""",
                },
                {"role": "user", "content": message},
            ],
            temperature=0.3,
            max_tokens=100,
        )

        result = response.choices[0].message.content
        logger.info(f"감정 분석 원본 결과: {result}")

        # 감정 파싱
        emotion = "중립"
        intensity = 3

        if "기쁨" in result.lower():
            emotion = "기쁨"
        elif "슬픔" in result.lower():
            emotion = "슬픔"
        elif "분노" in result.lower() or "짜증" in result.lower():
            emotion = "분노"
        elif "불안" in result.lower():
            emotion = "불안"

        # 강도 추출
        numbers = re.findall(r"\d+", result)
        if numbers:
            # 첫 번째 숫자를 강도로 사용
            raw_intensity = int(numbers[0])

            # 메시지 길이에 따라 강도 조정
            if message_length <= 5:
                # 짧은 메시지는 강도를 30%로 줄임
                intensity = max(2, int(raw_intensity * 0.3))
            elif message_length <= 10:
                # 중간 길이 메시지는 강도를 50%로 줄임
                intensity = max(2, int(raw_intensity * 0.5))
            else:
                # 긴 메시지도 80%로 줄임
                intensity = max(3, int(raw_intensity * 0.8))

        analysis_result = {
            "emotion": emotion,
            "intensity": intensity,
            "raw_analysis": result,
            "message_length": message_length,
        }

        logger.info(f"감정 분석 최종 결과: {analysis_result}")

        return analysis_result
    except Exception as e:
        error_msg = f"감정 분석 중 오류: {str(e)}"
        logger.error(error_msg)

        return {
            "emotion": "중립",
            "intensity": 3,
            "raw_analysis": "분석 실패",
            "error": str(e),
            "message_length": len(message.split()),
        }


def generate_offline_response(message):
    """오프라인 모드용 응답 생성 함수"""
    message = message.lower()

    if "안녕" in message or "반가워" in message:
        return "안녕하세요! 오늘 기분이 어떠신가요? 편안한 마음으로 이야기해 주세요."
    elif "불안" in message or "걱정" in message:
        return "불안감을 느끼고 계시는군요. 그런 감정은 자연스러운 것입니다. 깊은 호흡을 천천히 5번 해보시겠어요? 호흡에 집중하는 것이 현재 순간으로 돌아오는 데 도움이 될 수 있습니다. 어떤 상황에서 특히 불안함을 느끼시나요?"
    elif "우울" in message or "슬픔" in message or "의욕" in message:
        return "그런 감정을 느끼시는 것이 많이 힘드실 것 같아요. 우울한 기분이 들 때는 작은 활동부터 시작하는 것이 도움이 될 수 있어요. 오늘 햇빛을 잠시라도 쬐어보거나, 좋아하는 음악을 들어보는 건 어떨까요? 언제부터 이런 감정을 느끼기 시작하셨나요?"
    elif "화" in message or "분노" in message or "짜증" in message:
        return "화가 나는 감정을 느끼고 계시는군요. 그런 감정도 중요하고 들어줄 가치가 있습니다. 잠시 그 감정을 알아차리고, 깊게 숨을 들이마시고 내쉬어보세요. 어떤 상황이 이런 감정을 불러일으켰는지 더 이야기해주실 수 있을까요?"
    else:
        return "말씀해주셔서 감사합니다. 더 구체적으로 어떤 감정을 느끼셨는지, 그리고 그 상황에서 어떤 생각이 드셨는지 이야기해주실 수 있을까요? 함께 이야기하면서 도움이 될 수 있는 방법을 찾아보고 싶습니다."
