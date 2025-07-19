/*
 * AI Web Crawler Chat Widget
 * Embeddable chat widget for intelligent web crawling and Q&A
 */

(function() {
    'use strict';
    
    // Default configuration
    const defaultConfig = {
        apiUrl: 'http://localhost:8000/chat',
        urls: [],
        companyName: 'Assistant',
        position: 'bottom-right',
        theme: {
            primaryColor: '#667eea',
            secondaryColor: '#764ba2'
        },
        autoOpen: false,
        showWelcome: true
    };
    
    // Widget state
    let config = { ...defaultConfig };
    let isInitialized = false;
    
    // Load marked.js library for markdown rendering
    function loadMarkedLibrary() {
        return new Promise((resolve) => {
            if (window.marked) {
                resolve();
                return;
            }
            
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
            script.onload = resolve;
            document.head.appendChild(script);
        });
    }
    
    // Render markdown to HTML
    function renderMarkdown(text) {
        if (!text) return '';
        if (window.marked) {
            return window.marked.parse(text);
        }
        return text; // Fallback to plain text if marked isn't loaded
    }
    
    // Create widget HTML
    function createWidget() {
        // Widget container
        const widgetContainer = document.createElement('div');
        widgetContainer.id = 'ai-chat-widget';
        widgetContainer.innerHTML = `
            <!-- Floating Chat Button -->
            <div id="chat-button" style="
                position: fixed;
                bottom: 20px;
                ${config.position === 'bottom-left' ? 'left: 20px;' : 'right: 20px;'}
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, ${config.theme.primaryColor} 0%, ${config.theme.secondaryColor} 100%);
                color: white;
                border: none;
                cursor: pointer;
                box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                z-index: 10000;
                transition: all 0.3s ease;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            ">💬</div>
            
            <!-- Chat Modal -->
            <div id="chat-modal" style="
                position: fixed;
                bottom: 90px;
                ${config.position === 'bottom-left' ? 'left: 20px;' : 'right: 20px;'}
                width: 400px;
                height: 600px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                z-index: 9999;
                display: none;
                flex-direction: column;
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            ">
                <!-- Header -->
                <div style="
                    background: linear-gradient(135deg, ${config.theme.primaryColor} 0%, ${config.theme.secondaryColor} 100%);
                    color: white;
                    padding: 16px 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <h3 style="margin: 0; font-size: 18px; font-weight: 600;">
                        Chatbot Assistant
                    </h3>
                    <button id="close-chat" style="
                        background: none;
                        border: none;
                        color: white;
                        font-size: 20px;
                        cursor: pointer;
                        padding: 4px;
                        border-radius: 4px;
                    ">✕</button>
                </div>
                
                <!-- Messages Area -->
                <div id="messages-area" style="
                    flex: 1;
                    overflow-y: auto;
                    padding: 16px;
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                ">
                    <!-- Welcome Message -->
                    <div id="welcome-message" style="
                        text-align: center;
                        color: #6b7280;
                        margin-top: 40px;
                    ">
                        <div style="font-size: 48px; margin-bottom: 16px;">🤖</div>
                        <p>Hi! I'm here to help you with questions about our documentation and services.</p>
                        <p style="font-size: 14px;">Ask me anything!</p>
                    </div>
                </div>
                
                <!-- Input Area -->
                <div style="
                    border-top: 1px solid #e5e7eb;
                    padding: 16px;
                    background: #f9fafb;
                ">
                    <div id="error-message" style="
                        background: #fef2f2;
                        border: 1px solid #fca5a5;
                        border-radius: 6px;
                        padding: 8px 12px;
                        color: #dc2626;
                        font-size: 14px;
                        margin-bottom: 12px;
                        display: none;
                    "></div>
                    
                    <form id="chat-form" style="display: flex; gap: 8px;">
                        <input
                            type="text"
                            id="chat-input"
                            placeholder="Type your message..."
                            style="
                                flex: 1;
                                padding: 12px;
                                border: 1px solid #d1d5db;
                                border-radius: 8px;
                                font-size: 14px;
                                outline: none;
                                transition: border-color 0.2s;
                            "
                        />
                        <button
                            type="submit"
                            id="send-button"
                            style="
                                background: linear-gradient(135deg, ${config.theme.primaryColor} 0%, ${config.theme.secondaryColor} 100%);
                                color: white;
                                border: none;
                                border-radius: 8px;
                                padding: 12px 16px;
                                cursor: pointer;
                                font-size: 16px;
                            "
                        >➤</button>
                    </form>
                </div>
            </div>
        `;
        
        document.body.appendChild(widgetContainer);
        return widgetContainer;
    }
    
    // Add CSS styles
    function addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes chatWidgetBlink {
                0%, 50% { opacity: 1; }
                51%, 100% { opacity: 0; }
            }
            
            #chat-button:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6);
            }
            
            #chat-input:focus {
                border-color: ${config.theme.primaryColor} !important;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            
            .streaming-cursor {
                color: ${config.theme.primaryColor};
                font-weight: bold;
                animation: chatWidgetBlink 1s infinite;
            }
            
            .reasoning-section {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                overflow: hidden;
                margin-bottom: 12px;
            }
            
            .reasoning-header {
                width: 100%;
                background: none;
                border: none;
                padding: 12px 16px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                color: #1f2937;
            }
            
            .reasoning-step {
                background: rgba(59, 130, 246, 0.05);
                border: 1px solid #dbeafe;
                border-radius: 6px;
                padding: 12px;
                margin-bottom: 8px;
                font-size: 12px;
            }
            
            .step-title {
                font-weight: 500;
                color: #1f2937;
                margin-bottom: 4px;
            }
            
            .step-reasoning {
                color: #6b7280;
                line-height: 1.4;
            }
            
            .user-message {
                display: flex;
                justify-content: flex-end;
                gap: 8px;
                margin-bottom: 16px;
            }
            
            .user-bubble {
                background: ${config.theme.primaryColor};
                color: white;
                padding: 12px 16px;
                border-radius: 18px 18px 4px 18px;
                max-width: 80%;
                font-size: 14px;
                word-wrap: break-word;
            }
            
            .user-avatar {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: ${config.theme.primaryColor};
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                font-weight: bold;
                flex-shrink: 0;
            }
            
            .bot-message {
                display: flex;
                gap: 8px;
                align-items: flex-start;
                margin-bottom: 16px;
            }
            
            .bot-avatar {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: #1f2937;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                font-weight: bold;
                flex-shrink: 0;
            }
            
            .bot-response {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .response-bubble {
                background: #f3f4f6;
                padding: 12px 16px;
                border-radius: 18px 18px 18px 4px;
                font-size: 14px;
                line-height: 1.5;
                color: #1f2937;
                white-space: pre-wrap;
            }
            
            .sources-section {
                background: #fefce8;
                border: 1px solid #fde047;
                border-radius: 8px;
                padding: 12px;
            }
            
            .sources-title {
                font-size: 12px;
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 8px;
            }
            
            .source-item {
                font-size: 12px;
                color: #6b7280;
                margin-bottom: 4px;
                word-break: break-word;
            }
            
            @media (max-width: 480px) {
                #chat-modal {
                    width: calc(100vw - 40px) !important;
                    left: 20px !important;
                    right: 20px !important;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Widget functionality
    function initializeWidget() {
        const chatButton = document.getElementById('chat-button');
        const chatModal = document.getElementById('chat-modal');
        const closeButton = document.getElementById('close-chat');
        const chatForm = document.getElementById('chat-form');
        const chatInput = document.getElementById('chat-input');
        const messagesArea = document.getElementById('messages-area');
        const errorMessage = document.getElementById('error-message');
        const sendButton = document.getElementById('send-button');
        
        let isOpen = false;
        let isLoading = false;
        let messages = [];
        let currentStreamData = {
            reasoning: [],
            content: '',
            sources: [],
            isStreaming: false
        };
        
        // Toggle chat
        function toggleChat() {
            isOpen = !isOpen;
            chatModal.style.display = isOpen ? 'flex' : 'none';
            chatButton.innerHTML = isOpen ? '✕' : '💬';
            
            if (isOpen) {
                chatInput.focus();
            }
        }
        
        // Add message to UI
        function addMessage(message, streamData = null) {
            const messageDiv = document.createElement('div');
            
            if (message.role === 'user') {
                messageDiv.className = 'user-message';
                messageDiv.innerHTML = `
                    <div class="user-bubble">${message.content}</div>
                    <div class="user-avatar">Y</div>
                `;
            } else {
                messageDiv.className = 'bot-message';
                messageDiv.innerHTML = `
                    <div class="bot-avatar">B</div>
                    <div class="bot-response">
                        ${streamData && streamData.reasoning.length > 0 ? `
                            <div class="reasoning-section">
                                <button class="reasoning-header" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'">
                                    <span>Reasoning</span>
                                    <span>▼</span>
                                </button>
                                <div style="padding: 0 16px 16px;">
                                    ${streamData.reasoning.map(step => `
                                        <div class="reasoning-step">
                                            <div class="step-title">${step.title}</div>
                                            <div class="step-reasoning">${step.reasoning}</div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                        
                        <div class="response-bubble">
                            ${renderMarkdown(message.content || (streamData ? streamData.content : ''))}
                            ${streamData && streamData.isStreaming ? '<span class="streaming-cursor">|</span>' : ''}
                        </div>
                        
                        ${streamData && streamData.sources.length > 0 ? `
                            <div class="sources-section">
                                <div class="sources-title">Sources</div>
                                ${streamData.sources.map(source => `
                                    <div class="source-item">
                                        • <a href="${source.url}" target="_blank" rel="noopener noreferrer" style="color: #3b82f6; text-decoration: none;">${source.url}</a>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                    </div>
                `;
            }
            
            if (document.getElementById('welcome-message')) {
                document.getElementById('welcome-message').remove();
            }
            
            messagesArea.appendChild(messageDiv);
            messagesArea.scrollTop = messagesArea.scrollHeight;
            
            return messageDiv;
        }
        
        // Generate session ID
        function generateSessionId() {
            return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
        }
        
        // 🚀 ULTRA-FAST MESSAGE SENDING WITH SIMPLE CHUNK CONSUMPTION
        async function sendMessage(query) {
            if (!query.trim() || isLoading) return;
            
            isLoading = true;
            sendButton.innerHTML = '⏳';
            sendButton.disabled = true;
            chatInput.disabled = true;
            errorMessage.style.display = 'none';
            
            // Add user message
            const userMessage = { role: 'user', content: query };
            messages.push(userMessage);
            addMessage(userMessage);
            
            // Add placeholder bot message
            const botMessage = { role: 'assistant', content: '' };
            messages.push(botMessage);
            
            // State for real-time updates
            let streamData = {
                reasoning: [],
                content: '',
                sources: [],
                isStreaming: true
            };
            
            const botMessageDiv = addMessage(botMessage, streamData);
            
            try {
                const response = await fetch(config.apiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        urls: config.urls,
                        query: query,
                        session_id: generateSessionId(),
                        company_name: config.companyName
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                // 🔥 ULTRA-SIMPLE STREAM CONSUMPTION!
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const lines = decoder.decode(value).split('\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const chunk = JSON.parse(line.slice(6));
                                
                                // 🎯 DIRECT CHUNK PROCESSING - NO COMPLEX PARSING!
                                switch (chunk.type) {
                                    case 'content':
                                        streamData.content = chunk.full_content || chunk.text;
                                        streamData.isStreaming = true;
                                        updateBotMessage(botMessageDiv, streamData);
                                        break;
                                        
                                    case 'reasoning':
                                        if (chunk.step) {
                                            streamData.reasoning = chunk.all_steps || [chunk.step];
                                            updateBotMessage(botMessageDiv, streamData);
                                        }
                                        break;
                                        
                                    case 'crawling':
                                        // Show crawling status (optional UI feedback)
                                        console.log(`🔍 ${chunk.message}`, chunk.urls);
                                        break;
                                        
                                    case 'completion':
                                        streamData.content = chunk.final_content || streamData.content;
                                        streamData.sources = chunk.sources || [];
                                        streamData.reasoning = chunk.reasoning_steps || streamData.reasoning;
                                        streamData.isStreaming = false;
                                        updateBotMessage(botMessageDiv, streamData);
                                        break;
                                        
                                    case 'error':
                                        throw new Error(chunk.message);
                                }
                                
                            } catch (e) {
                                console.error('Chunk processing error:', e);
                            }
                        }
                    }
                }
                
                // Update final message
                botMessage.content = streamData.content;
                
            } catch (err) {
                console.error('Stream error:', err);
                errorMessage.textContent = err.message || 'Failed to connect to backend';
                errorMessage.style.display = 'block';
            } finally {
                isLoading = false;
                sendButton.innerHTML = '➤';
                sendButton.disabled = false;
                chatInput.disabled = false;
                chatInput.value = '';
            }
        }
        
        // 🔥 ULTRA-FAST UI UPDATE FUNCTION
        function updateBotMessage(messageDiv, streamData) {
            messageDiv.innerHTML = `
                <div class="bot-avatar">B</div>
                <div class="bot-response">
                    ${streamData.reasoning.length > 0 ? `
                        <div class="reasoning-section">
                            <button class="reasoning-header" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'">
                                <span>Reasoning</span>
                                <span>▼</span>
                            </button>
                            <div style="padding: 0 16px 16px;">
                                ${streamData.reasoning.map(step => `
                                    <div class="reasoning-step">
                                        <div class="step-title">${step.title}</div>
                                        <div class="step-reasoning">${step.thought || step.reasoning || ''}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    <div class="response-bubble">
                        ${renderMarkdown(streamData.content)}
                        ${streamData.isStreaming ? '<span class="streaming-cursor">|</span>' : ''}
                    </div>
                    
                    ${streamData.sources.length > 0 ? `
                        <div class="sources-section">
                            <div class="sources-title">Sources</div>
                            ${streamData.sources.map(source => `
                                <div class="source-item">
                                    • <a href="${source.url}" target="_blank" rel="noopener noreferrer" style="color: #3b82f6; text-decoration: none;">${source.url}</a>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
            
            messagesArea.scrollTop = messagesArea.scrollHeight;
        }
        
        // Event listeners
        chatButton.addEventListener('click', toggleChat);
        closeButton.addEventListener('click', toggleChat);
        
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            sendMessage(chatInput.value);
        });
        
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage(chatInput.value);
            }
            if (e.key === 'Escape') {
                toggleChat();
            }
        });
        
        // Auto-open if configured
        if (config.autoOpen) {
            setTimeout(toggleChat, 1000);
        }
    }
    
    // Public API
    window.ChatWidget = {
        init: function(userConfig = {}) {
            if (isInitialized) {
                console.warn('Chat widget is already initialized');
                return;
            }
            
            // Merge configuration
            config = { ...defaultConfig, ...userConfig };
            if (userConfig.theme) {
                config.theme = { ...defaultConfig.theme, ...userConfig.theme };
            }
            
        // Wait for DOM to be ready and load markdown library
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', async () => {
                await loadMarkedLibrary();
                addStyles();
                createWidget();
                initializeWidget();
                isInitialized = true;
            });
        } else {
            loadMarkedLibrary().then(() => {
                addStyles();
                createWidget();
                initializeWidget();
                isInitialized = true;
            });
        }
        },
        
        open: function() {
            const button = document.getElementById('chat-button');
            if (button && button.innerHTML === '💬') {
                button.click();
            }
        },
        
        close: function() {
            const button = document.getElementById('chat-button');
            if (button && button.innerHTML === '✕') {
                button.click();
            }
        },
        
        configure: function(newConfig) {
            config = { ...config, ...newConfig };
            if (newConfig.theme) {
                config.theme = { ...config.theme, ...newConfig.theme };
            }
        }
    };
    
})();
