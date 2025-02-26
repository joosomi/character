document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    
    // 초기 메시지 추가
    addMessage('안녕하세요! 저는 심리 상담 코치 세레니티입니다. 오늘 어떤 이야기를 나누고 싶으신가요?', 'assistant');
    
    // 메시지 전송 이벤트 리스너
    sendButton.addEventListener('click', streamChat);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            streamChat();
        }
    });
    
    // 텍스트 영역 자동 높이 조절
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.scrollHeight > 150) {
            this.style.height = '150px';
            this.style.overflowY = 'auto';
        }
    });
    
    // 채팅 기록 저장
    let chatHistory = [];
    
    // 스트리밍 채팅 함수
    function streamChat() {
        const userInput = document.getElementById('user-input');
        const message = userInput.value.trim();
        
        if (message === '') return;
        
        // 사용자 메시지 표시
        addMessage(message, 'user');
        userInput.value = '';
        
        // 로딩 표시
        const messagesContainer = document.getElementById('chat-messages');
        const loadingElement = document.createElement('div');
        loadingElement.classList.add('message', 'assistant', 'loading');
        loadingElement.textContent = '...';
        messagesContainer.appendChild(loadingElement);
        
        // 스트리밍 요청
        fetch('/chat-stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: 'user_' + Date.now(),
                message: message
            })
        }).then(response => {
            // 로딩 표시 제거
            messagesContainer.removeChild(loadingElement);
            
            // 새 메시지 요소 생성
            const messageElement = document.createElement('div');
            messageElement.classList.add('message', 'assistant');
            messagesContainer.appendChild(messageElement);
            
            // 응답 텍스트를 저장할 변수
            let fullResponse = '';
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            function readStream() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        console.log("스트림 완료, 최종 응답:", fullResponse);
                        
                        // 스트림이 완료되면 전체 응답을 마크다운으로 변환
                        try {
                            // marked 라이브러리가 있는지 확인
                            if (typeof marked !== 'undefined') {
                                console.log("marked 라이브러리 사용");
                                messageElement.innerHTML = marked.parse(fullResponse);
                            } else {
                                console.error("marked 라이브러리를 찾을 수 없습니다");
                                // 대체 방법: 간단한 마크다운 변환
                                messageElement.innerHTML = simpleMarkdownToHtml(fullResponse);
                            }
                        } catch (e) {
                            console.error("마크다운 변환 오류:", e);
                            messageElement.textContent = fullResponse;
                        }
                        
                        // 시간 추가
                        const timeElement = document.createElement('div');
                        timeElement.className = 'message-time';
                        const now = new Date();
                        timeElement.textContent = `${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}`;
                        messageElement.appendChild(timeElement);
                        
                        return;
                    }
                    
                    const text = decoder.decode(value);
                    const lines = text.split('\n\n');
                    
                    lines.forEach(line => {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.substring(6));
                                
                                if (data.error) {
                                    messageElement.textContent = '오류가 발생했습니다: ' + data.error;
                                } else if (data.chunk) {
                                    // 응답 텍스트 누적
                                    fullResponse += data.response;
                                    
                                    // 임시로 일반 텍스트로 표시 (스트리밍 중)
                                    messageElement.textContent = fullResponse;
                                } else if (data.done) {
                                    console.log("done 신호 수신, 최종 응답:", fullResponse);
                                    
                                    // 스트림 완료 시 마크다운 변환
                                    try {
                                        if (typeof marked !== 'undefined') {
                                            messageElement.innerHTML = marked.parse(fullResponse);
                                        } else {
                                            messageElement.innerHTML = simpleMarkdownToHtml(fullResponse);
                                        }
                                    } catch (e) {
                                        console.error("마크다운 변환 오류:", e);
                                        messageElement.textContent = fullResponse;
                                    }
                                    
                                    // 시간 추가
                                    const timeElement = document.createElement('div');
                                    timeElement.className = 'message-time';
                                    const now = new Date();
                                    timeElement.textContent = `${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}`;
                                    messageElement.appendChild(timeElement);
                                }
                            } catch (e) {
                                console.error('JSON 파싱 오류:', e, line);
                            }
                        }
                    });
                    
                    // 스크롤을 최신 메시지로 이동
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                    
                    readStream();
                }).catch(error => {
                    console.error('스트림 읽기 오류:', error);
                    messageElement.textContent = '오류가 발생했습니다: ' + error.message;
                });
            }
            
            readStream();
        }).catch(error => {
            console.error('Error:', error);
            // 로딩 표시 제거
            if (messagesContainer.contains(loadingElement)) {
                messagesContainer.removeChild(loadingElement);
            }
            addMessage('오류가 발생했습니다: ' + error.message, 'assistant');
        });
    }
    
    // 간단한 마크다운 변환 함수 (marked 라이브러리가 없을 경우 대체용)
    function simpleMarkdownToHtml(text) {
        // 볼드체 변환
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // 이탤릭체 변환
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // 순서 있는 목록 변환
        text = text.replace(/^\d+\.\s+(.*?)$/gm, '<li>$1</li>');
        text = text.replace(/<li>.*?<\/li>(\n<li>.*?<\/li>)+/g, function(match) {
            return '<ol>' + match + '</ol>';
        });
        
        // 순서 없는 목록 변환
        text = text.replace(/^-\s+(.*?)$/gm, '<li>$1</li>');
        text = text.replace(/<li>.*?<\/li>(\n<li>.*?<\/li>)+/g, function(match) {
            return '<ul>' + match + '</ul>';
        });
        
        // 줄바꿈 변환
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }
    
    // 메시지 추가 함수
    function addMessage(text, sender) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}`;
        
        console.log(`메시지 추가: ${sender}, 내용: ${text.substring(0, 50)}...`);
        
        // 메시지 텍스트 추가 (마크다운 변환)
        if (sender === 'assistant') {
            try {
                // marked 라이브러리가 있는지 확인
                if (typeof marked !== 'undefined') {
                    console.log("marked 라이브러리로 변환");
                    messageElement.innerHTML = marked.parse(text);
                } else {
                    console.error("marked 라이브러리를 찾을 수 없습니다");
                    // 대체 방법: 간단한 마크다운 변환
                    messageElement.innerHTML = simpleMarkdownToHtml(text);
                }
            } catch (e) {
                console.error("마크다운 변환 오류:", e);
                messageElement.textContent = text;
            }
        } else {
            // 사용자 메시지는 일반 텍스트로 표시
            messageElement.textContent = text;
        }
        
        // 시간 추가
        const timeElement = document.createElement('div');
        timeElement.className = 'message-time';
        const now = new Date();
        timeElement.textContent = `${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}`;
        messageElement.appendChild(timeElement);
        
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // 간단한 응답 생성 함수 (실제로는 AI 모델 사용)
    function generateResponse(message) {
        // 키워드 기반 간단한 응답 로직
        message = message.toLowerCase();
        
        if (message.includes('안녕') || message.includes('반가워')) {
            return '안녕하세요! 오늘 기분이 어떠신가요? 편안한 마음으로 이야기해 주세요.';
        } else if (message.includes('불안') || message.includes('걱정')) {
            return '불안감을 느끼고 계시는군요. 그런 감정은 자연스러운 것입니다. 깊은 호흡을 천천히 5번 해보시겠어요? 호흡에 집중하는 것이 현재 순간으로 돌아오는 데 도움이 될 수 있습니다. 어떤 상황에서 특히 불안함을 느끼시나요?';
        } else if (message.includes('우울') || message.includes('슬픔') || message.includes('의욕')) {
            return '그런 감정을 느끼시는 것이 많이 힘드실 것 같아요. 우울한 기분이 들 때는 작은 활동부터 시작하는 것이 도움이 될 수 있어요. 오늘 햇빛을 잠시라도 쬐어보거나, 좋아하는 음악을 들어보는 건 어떨까요? 언제부터 이런 감정을 느끼기 시작하셨나요?';
        } else if (message.includes('화') || message.includes('분노') || message.includes('짜증')) {
            return '화가 나는 감정을 느끼고 계시는군요. 그런 감정도 중요하고 들어줄 가치가 있습니다. 잠시 그 감정을 알아차리고, 깊게 숨을 들이마시고 내쉬어보세요. 어떤 상황이 이런 감정을 불러일으켰는지 더 이야기해주실 수 있을까요?';
        } else if (message.includes('잠') || message.includes('수면')) {
            return '수면에 어려움을 겪고 계시는군요. 규칙적인 수면 습관이 중요합니다. 잠들기 전 1시간은 블루라이트를 피하고, 따뜻한 차를 마시거나 가벼운 스트레칭을 해보세요. 취침 전 명상도 도움이 될 수 있어요. 평소 수면 패턴은 어떠신가요?';
        } else {
            return '말씀해주셔서 감사합니다. 그런 경험이 있으셨군요. 더 구체적으로 어떤 감정을 느끼셨는지, 그리고 그 상황에서 어떤 생각이 드셨는지 이야기해주실 수 있을까요? 함께 이야기하면서 도움이 될 수 있는 방법을 찾아보고 싶습니다.';
        }
    }
}); 