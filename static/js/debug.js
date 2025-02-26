document.addEventListener('DOMContentLoaded', function() {
    const searchBtn = document.getElementById('search-btn');
    const resultsDiv = document.getElementById('results');
    
    searchBtn.addEventListener('click', async () => {
        const query = document.getElementById('query').value;
        const userId = document.getElementById('user-id').value;
        const k = document.getElementById('k').value;
        const threshold = document.getElementById('threshold').value;
        const reload = document.getElementById('reload').checked;
        
        if (!query) {
            alert('검색 쿼리를 입력하세요');
            return;
        }
        
        resultsDiv.innerHTML = '<p>검색 중...</p>';
        
        try {
            const response = await fetch('/debug/rag', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    user_id: userId || null,
                    k: parseInt(k),
                    reload: reload,
                    score_threshold: parseFloat(threshold)
                })
            });
            
            const data = await response.json();
            displayResults(data, resultsDiv);
        } catch (error) {
            resultsDiv.innerHTML = `<p class="error">오류 발생: ${error.message}</p>`;
        }
    });
    
    function displayResults(data, resultsDiv) {
        let html = '';
        if (data.success) {
            html += `<p class="success">${data.message}</p>`;
            
            if (data.results.length === 0) {
                html += '<p>검색 결과가 없습니다.</p>';
            } else {
                data.results.forEach((result, index) => {
                    html += `
                        <div class="result-item">
                            <h3>결과 ${index + 1}</h3>
                            <p><strong>내용:</strong> ${result.content}</p>
                            <p><strong>사용자:</strong> ${result.user_id}</p>
                            <p><strong>출처:</strong> ${result.source || '없음'}</p>
                            <p><strong>유사도:</strong> ${result.similarity || 'N/A'}</p>
                        </div>
                    `;
                });
            }
        } else {
            html += `<p class="error">${data.message}</p>`;
        }
        
        resultsDiv.innerHTML = html;
    }
}); 