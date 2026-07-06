document.addEventListener('DOMContentLoaded', () => {
    const chatOutput = document.getElementById('chat-output');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');

    // Auto-resize textarea
    userInput.addEventListener('input', function() {
        this.style.height = '60px';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
    });

    // Handle Enter key (Shift+Enter for new line)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        userInput.value = '';
        userInput.style.height = '60px';

        addMessage(text, 'user-message');
        scrollToBottom();

        const loadingEl = addLoadingMessage();
        scrollToBottom();

        setInputEnabled(false);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();
            loadingEl.remove();

            if (!response.ok) {
                addMessage('❌ Error: ' + (data.detail || 'Something went wrong.'), 'system-message');
            } else {
                // Support both 'reply' (new) and 'report' (legacy) keys
                const replyText = data.reply || data.report || '(No response returned.)';
                addMarkdownMessage(replyText);
            }
        } catch (error) {
            loadingEl.remove();
            addMessage('❌ Could not connect to the server. Please try again.', 'system-message');
            console.error(error);
        } finally {
            setInputEnabled(true);
            userInput.focus();
            scrollToBottom();
        }
    }

    function setInputEnabled(enabled) {
        userInput.disabled = !enabled;
        sendBtn.disabled = !enabled;
        sendBtn.querySelector('.btn-text').textContent = enabled ? 'Send' : 'Thinking...';
    }

    function addMessage(text, className) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${className}`;
        msgDiv.textContent = text;
        chatOutput.appendChild(msgDiv);
        return msgDiv;
    }

    function addMarkdownMessage(markdown) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message agent-message';
        msgDiv.innerHTML = marked.parse(markdown, { breaks: true });
        chatOutput.appendChild(msgDiv);
        return msgDiv;
    }

    function addLoadingMessage() {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message agent-message loading-message';
        msgDiv.innerHTML = `
            <div class="spinner"></div>
            <span>BizPilot is thinking…</span>
        `;
        chatOutput.appendChild(msgDiv);
        return msgDiv;
    }

    function scrollToBottom() {
        chatOutput.scrollTop = chatOutput.scrollHeight;
    }
});
