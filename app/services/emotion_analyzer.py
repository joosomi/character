def analyze_emotion(query):
    """사용자 질문에서 감정 상태를 분석하는 함수"""
    # 간단한 키워드 기반 감정 분석
    anxiety_keywords = ["불안", "걱정", "두려움", "긴장"]
    depression_keywords = ["우울", "슬픔", "의욕", "무기력"]
    anger_keywords = ["화", "분노", "짜증", "답답"]
    joy_keywords = ["행복", "기쁨", "즐거움", "좋아"]

    emotions = {
        "anxiety": 0,
        "depression": 0,
        "anger": 0,
        "joy": 0,
        "neutral": 1,  # 기본값
    }

    for keyword in anxiety_keywords:
        if keyword in query:
            emotions["anxiety"] += 1
            emotions["neutral"] = 0

    for keyword in depression_keywords:
        if keyword in query:
            emotions["depression"] += 1
            emotions["neutral"] = 0

    for keyword in anger_keywords:
        if keyword in query:
            emotions["anger"] += 1
            emotions["neutral"] = 0

    for keyword in joy_keywords:
        if keyword in query:
            emotions["joy"] += 1
            emotions["neutral"] = 0

    # 가장 높은 점수의 감정 반환
    dominant_emotion = max(emotions, key=emotions.get)
    return {"dominant_emotion": dominant_emotion, "emotion_scores": emotions}


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
