function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function initWatchProgress(animeId, savedProgress) {
    const iframes = document.querySelectorAll('.player iframe');
    
    if (iframes.length === 0) return;
    
    const csrftoken = getCookie('csrftoken');
    let saveTimeout;
    
    iframes.forEach(iframe => {
        iframe.addEventListener('load', function() {
            try {
                const iframeWindow = iframe.contentWindow;
                
                if (savedProgress && savedProgress > 10) {
                    setTimeout(() => {
                        const shouldResume = confirm(`Продолжить просмотр с ${formatTime(savedProgress)}?`);
                        if (shouldResume && iframeWindow.postMessage) {
                            iframeWindow.postMessage({
                                action: 'seek',
                                time: savedProgress
                            }, '*');
                        }
                    }, 1000);
                }
                
                window.addEventListener('message', function(event) {
                    if (event.data && event.data.currentTime !== undefined) {
                        const currentTime = event.data.currentTime;
                        const duration = event.data.duration || 0;
                        
                        clearTimeout(saveTimeout);
                        saveTimeout = setTimeout(() => {
                            saveProgress(animeId, currentTime, duration, csrftoken);
                        }, 5000);
                    }
                });
                
                setInterval(() => {
                    if (iframeWindow.postMessage) {
                        iframeWindow.postMessage({ action: 'getTime' }, '*');
                    }
                }, 10000);
                
            } catch (e) {
            }
        });
    });
}

function saveProgress(animeId, currentTime, duration, csrftoken) {
    if (currentTime < 10) return;
    
    fetch(`/anime/${animeId}/progress/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken
        },
        body: `current_time=${currentTime}&duration=${duration}`
    })
    .catch(error => console.error('Error:', error));
}

function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}
