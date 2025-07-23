document.addEventListener('DOMContentLoaded', () => {

    // DOM Elements
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const userIdInput = document.getElementById('userId');
    const setUserIdButton = document.getElementById('setUserId');
    const systemPromptInput = document.getElementById('systemPrompt');
    const setSystemPromptButton = document.getElementById('setSystemPrompt');
    const modelIdInput = document.getElementById('modelId');
    const regionInput = document.getElementById('region');
    const maxTokensInput = document.getElementById('maxTokens');
    const temperatureInput = document.getElementById('temperature');
    const topPInput = document.getElementById('topP');
    const updateModelSettingsButton = document.getElementById('updateModelSettings');
    
    // API endpoints
    const API_BASE_URL = '';
    const GET_CONVERSATIONS_ENDPOINT = `${API_BASE_URL}/get_conversations`;
    const CS_AGENT_ENDPOINT = `${API_BASE_URL}/strandsplayground_agent`;
    const SYSTEM_PROMPT_ENDPOINT = `${API_BASE_URL}/system_prompt`;
    const MODEL_SETTINGS_ENDPOINT = `${API_BASE_URL}/model_settings`;
    
    // State
    let userId = userIdInput.value || 'user1';
    let isProcessing = false;
    
    // Initialize chat, system prompt, and model settings
    loadConversation();
    loadSystemPrompt();
    loadModelSettings();
    
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
    
    updateModelSettingsButton.addEventListener('click', async () => {
        const modelId = modelIdInput.value.trim();
        const region = regionInput.value.trim();
        
        // Check if optional fields are enabled
        const maxTokensEnabled = document.getElementById('enableMaxTokens').checked;
        const temperatureEnabled = document.getElementById('enableTemperature').checked;
        const topPEnabled = document.getElementById('enableTopP').checked;
        
        // Get values only from enabled fields
        const maxTokens = maxTokensEnabled ? parseInt(maxTokensInput.value.trim()) : null;
        const temperature = temperatureEnabled ? parseFloat(temperatureInput.value.trim()) : null;
        const topP = topPEnabled ? parseFloat(topPInput.value.trim()) : null;
        
        if (!modelId || !region) {
            showError('Model ID and Region are required');
            return;
        }
        
        try {
            const response = await fetch(MODEL_SETTINGS_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    modelId,
                    region,
                    maxTokens: maxTokensEnabled ? (isNaN(maxTokens) ? null : maxTokens) : null,
                    temperature: temperatureEnabled ? (isNaN(temperature) ? null : temperature) : null,
                    topP: topPEnabled ? (isNaN(topP) ? null : topP) : null
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            showSuccess('Model settings updated successfully');
        } catch (error) {
            console.error('Error updating model settings:', error);
            showError('Failed to update model settings. Please try again.');
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
            welcomeMsg.textContent = "Welcome to Strands Playground, let's get started!";
            chatMessages.appendChild(welcomeMsg);
            
            // Add note about file access
            return;
        }
        
        messages.forEach(msg => {
            if (msg.role === 'user' || msg.role === 'assistant') {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${msg.role === 'user' ? 'user-message' : 'bot-message'}`;
                
                const responseText = msg.content[0].text;
                messageDiv.textContent = responseText;
                
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
        
        // Show loading indicator in chat
        isProcessing = true;
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot-message';
        loadingDiv.innerHTML = '<div class="loading"></div>';
        chatMessages.appendChild(loadingDiv);
        
        // Show loading indicator in summary panel
        if (window.showSummaryLoading) {
            window.showSummaryLoading();
        }
        
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
            
            const responseText = data.messages.content[0].text;
            botMessageDiv.textContent = responseText;
            
            chatMessages.appendChild(botMessageDiv);
            
            // Update summary panel if available
            if (data.summary && window.updateSummaryPanel) {
                console.log(data.summary);
                window.updateSummaryPanel(data.summary);
            }
            
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
    
    async function loadModelSettings() {
        try {
            const response = await fetch(MODEL_SETTINGS_ENDPOINT);
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            modelIdInput.value = data.modelId || '';
            regionInput.value = data.region || '';
            
            // Set values and toggle states for optional fields
            if (data.maxTokens !== null && data.maxTokens !== undefined) {
                maxTokensInput.value = data.maxTokens;
                document.getElementById('enableMaxTokens').checked = true;
                maxTokensInput.disabled = false;
            } else {
                document.getElementById('enableMaxTokens').checked = false;
                maxTokensInput.disabled = true;
            }
            
            if (data.temperature !== null && data.temperature !== undefined) {
                temperatureInput.value = data.temperature;
                document.getElementById('enableTemperature').checked = true;
                temperatureInput.disabled = false;
            } else {
                document.getElementById('enableTemperature').checked = false;
                temperatureInput.disabled = true;
            }
            
            if (data.topP !== null && data.topP !== undefined) {
                topPInput.value = data.topP;
                document.getElementById('enableTopP').checked = true;
                topPInput.disabled = false;
            } else {
                document.getElementById('enableTopP').checked = false;
                topPInput.disabled = true;
            }
        } catch (error) {
            console.error('Error loading model settings:', error);
            showError('Failed to load model settings. Please try again.');
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