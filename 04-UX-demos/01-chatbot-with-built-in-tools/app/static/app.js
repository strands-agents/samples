document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const userIdInput = document.getElementById('userId');
    const setUserIdButton = document.getElementById('setUserId');
    const systemPromptInput = document.getElementById('systemPrompt');
    const setSystemPromptButton = document.getElementById('setSystemPrompt');
    const latencyDisplay = document.getElementById('latency');
    const tokensDisplay = document.getElementById('tokens');
    
    // API endpoints
    const API_BASE_URL = '';
    const GET_CONVERSATIONS_ENDPOINT = `${API_BASE_URL}/get_conversations`;
    const CS_AGENT_ENDPOINT = `${API_BASE_URL}/cs_agent`;
    const SYSTEM_PROMPT_ENDPOINT = `${API_BASE_URL}/system_prompt`;
    
    // State
    let userId = userIdInput.value || 'user1';
    let isProcessing = false;
    
    // Initialize chat and system prompt
    loadConversation();
    loadSystemPrompt();
    
    // Event Listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    setUserIdButton.addEventListener('click', () => {
        const newUserId = userIdInput.value.trim();
        if (newUserId) {
            userId = newUserId;
            loadConversation();
        } else {
            showError('Please enter a valid User ID');
        }
    });
    
    setSystemPromptButton.addEventListener('click', async () => {
        const systemPrompt = systemPromptInput.value.trim();
        if (systemPrompt) {
            try {
                const response = await fetch(SYSTEM_PROMPT_ENDPOINT, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        systemPrompt: systemPrompt
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                
                showSuccess('System prompt updated successfully');
            } catch (error) {
                console.error('Error setting system prompt:', error);
                showError('Failed to update system prompt. Please try again.');
            }
        } else {
            showError('Please enter a valid system prompt');
        }
    });
    
    // Functions
    async function loadConversation() {
        try {
            chatMessages.innerHTML = '<div class="loading"></div>';
            
            const response = await fetch(`${GET_CONVERSATIONS_ENDPOINT}?userId=${encodeURIComponent(userId)}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            displayConversation(data.messages);
        } catch (error) {
            console.error('Error loading conversation:', error);
            chatMessages.innerHTML = '';
            showError('Failed to load conversation. Please try again.');
        }
    }
    
    function displayConversation(messages) {
        chatMessages.innerHTML = '';
        
        if (!messages || messages.length === 0) {
            const welcomeMsg = document.createElement('div');
            welcomeMsg.className = 'message bot-message';
            welcomeMsg.textContent = 'Welcome! How can I help you today?';
            chatMessages.appendChild(welcomeMsg);
            return;
        }
        
        messages.forEach(msg => {
            if (msg.role === 'user' || msg.role === 'assistant') {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${msg.role === 'user' ? 'user-message' : 'bot-message'}`;
                messageDiv.textContent = msg.content[0].text;
                chatMessages.appendChild(messageDiv);
            }
        });
        
        scrollToBottom();
    }
    
    async function sendMessage() {
        const message = userInput.value.trim();
        
        if (!message || isProcessing) return;
        
        // Add user message to chat
        const userMessageDiv = document.createElement('div');
        userMessageDiv.className = 'message user-message';
        userMessageDiv.textContent = message;
        chatMessages.appendChild(userMessageDiv);
        
        // Clear input and scroll to bottom
        userInput.value = '';
        scrollToBottom();
        
        // Show loading indicator
        isProcessing = true;
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot-message';
        loadingDiv.innerHTML = '<div class="loading"></div>';
        chatMessages.appendChild(loadingDiv);
        
        try {
            const startTime = Date.now();
            
            const response = await fetch(CS_AGENT_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prompt: message,
                    userId: userId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Remove loading indicator
            chatMessages.removeChild(loadingDiv);
            
            // Add bot response
            const botMessageDiv = document.createElement('div');
            botMessageDiv.className = 'message bot-message';
            botMessageDiv.textContent = data.messages.content[0].text;
            chatMessages.appendChild(botMessageDiv);
            
            // Update metrics
            console.log(data)
            latencyDisplay.textContent = `${data.latencyMs || 0} ms`;
            tokensDisplay.textContent = data.totalTokens || 0;
            
            scrollToBottom();
        } catch (error) {
            console.error('Error sending message:', error);
            chatMessages.removeChild(loadingDiv);
            showError('Failed to send message. Please try again.');
        } finally {
            isProcessing = false;
        }
    }
    
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    async function loadSystemPrompt() {
        try {
            const response = await fetch(SYSTEM_PROMPT_ENDPOINT);
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            systemPromptInput.value = data.systemPrompt;
        } catch (error) {
            console.error('Error loading system prompt:', error);
            showError('Failed to load system prompt. Please try again.');
        }
    }
    
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        chatMessages.appendChild(errorDiv);
        
        setTimeout(() => {
            chatMessages.removeChild(errorDiv);
        }, 5000);
        
        scrollToBottom();
    }
    
    function showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.textContent = message;
        chatMessages.appendChild(successDiv);
        
        setTimeout(() => {
            chatMessages.removeChild(successDiv);
        }, 3000);
        
        scrollToBottom();
    }
});