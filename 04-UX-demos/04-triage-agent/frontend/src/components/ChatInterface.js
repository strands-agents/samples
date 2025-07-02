/*
⚠️ IMPORTANT DISCLAIMER:
This is a Proof of Concept (PoC) demonstration only. This application is designed for 
educational and demonstration purposes to showcase AI integration capabilities and productivity 
tool orchestration. It is not intended to provide medical advice, professional consultation, 
or replace qualified professional judgment in any domain.

The AI responses and any data generated are produced by artificial intelligence models and 
should be treated as mock/demo content only. Use this application at your own risk. The 
developers and contributors are not responsible for any decisions made based on the output 
from this system.

For any medical, legal, financial, or other professional advice, please consult with 
qualified professionals in the respective fields.
*/

import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './ChatInterface.css';

const ChatInterface = ({ 
  messages, 
  setMessages, 
  selectedModel, 
  tokenCount, 
  setTokenCount,
  leftSidebarOpen,
  rightSidebarOpen,
  toggleLeftSidebar,
  toggleRightSidebar,
  onSessionIdChange
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [abortController, setAbortController] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);
  const [totalTokens, setTotalTokens] = useState({ input: 0, output: 0, total: 0 });
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [selectedImages, setSelectedImages] = useState([]);
  const [quickOptions, setQuickOptions] = useState([]);
  const [isFirstInteraction, setIsFirstInteraction] = useState(true);
  const [decisionTreeOptions, setDecisionTreeOptions] = useState([]);
  
  // Generate or get session ID
  const [sessionId] = useState(() => {
    let id = localStorage.getItem('chat_session_id');
    if (!id) {
      id = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('chat_session_id', id);
    }
    return id;
  });

  // Notify parent component about sessionId
  useEffect(() => {
    if (onSessionIdChange) {
      onSessionIdChange(sessionId);
    }
  }, [sessionId, onSessionIdChange]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus input after sending message
  const focusInput = () => {
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }, 100);
  };

  // Auto-resize textarea function
  const autoResizeTextarea = (textarea) => {
    if (!textarea) return;
    
    // Reset height to calculate new height
    textarea.style.height = 'auto';
    
    // Set new height based on scroll height
    const newHeight = Math.min(textarea.scrollHeight, 200); // Max 200px
    textarea.style.height = newHeight + 'px';
  };

  // Parse XML options from assistant response - streaming version
  const parseQuickOptionsStreaming = (content) => {
    const options = [];
    try {
      // Look for any <option tags, even incomplete ones
      const optionMatches = content.matchAll(/<option[^>]*urgency="([^"]*)"[^>]*>([^<]*)/g);
      
      for (const match of optionMatches) {
        const urgency = match[1];
        let text = match[2].trim();
        
        if (text && text.length > 2) {
          options.push({ text, urgency });
        }
      }
    } catch (error) {
      console.error('Error parsing streaming options:', error);
    }
    return options;
  };

  // Parse XML options from completed response
  const parseQuickOptionsRealTime = (content) => {
    const options = [];
    try {
      // Look for <available_options> block
      const optionsMatch = content.match(/<available_options>([\s\S]*?)<\/available_options>/);
      if (optionsMatch) {
        const optionsContent = optionsMatch[1];
        
        // Split by <option and process each piece
        const optionParts = optionsContent.split(/<option/);
        
        for (let i = 1; i < optionParts.length; i++) {
          const part = optionParts[i];
          
          // Extract urgency
          const urgencyMatch = part.match(/urgency="([^"]*)"/); 
          const urgency = urgencyMatch ? urgencyMatch[1] : 'normal';
          
          // Extract text between > and next < or end
          const textMatch = part.match(/>([^<]+)/);
          if (textMatch) {
            let text = textMatch[1].trim();
            if (text && text.length > 2) {
              options.push({ text, urgency });
            }
          }
        }
      }
    } catch (error) {
      console.error('Error parsing quick options:', error);
    }
    return options;
  };

  // Load decision tree options on mount
  useEffect(() => {
    const loadDecisionTreeOptions = async () => {
      try {
        const apiBase = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
        const response = await fetch(`${apiBase}/api/decision-tree`);
        if (response.ok) {
          const treeData = await response.json();
          const startNode = treeData.nodes?.start;
          if (startNode && startNode.response_options) {
            // "Other" 옵션을 하나로 통합하고 명확하게 변경
            const options = [...startNode.response_options.filter(o => !o.toLowerCase().includes('other')), "Other - Describe your concern"];
            setDecisionTreeOptions(options);
          }
        }
      } catch (error) {
        console.error('Error loading decision tree:', error);
        // Fallback options
        setDecisionTreeOptions([
          "Emergency or life-threatening situation",
          "Pain or injury", 
          "Feeling sick or unwell",
          "Mental health concerns",
          "Digestive issues",
          "Heart or chest symptoms",
          "Breathing difficulties",
          "Other health concern"
        ]);
      }
    };

    loadDecisionTreeOptions();
  }, []);

  // Handle image file selection
  const handleImageSelect = (files) => {
    const imageFiles = Array.from(files).filter(file => 
      file.type.startsWith('image/') && file.size <= 10 * 1024 * 1024 // 10MB limit
    );
    
    imageFiles.forEach(file => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const imageData = {
          id: Date.now() + Math.random(),
          file: file,
          url: e.target.result,
          name: file.name
        };
        setSelectedImages(prev => [...prev, imageData]);
      };
      reader.readAsDataURL(file);
    });
  };

  // Handle file input change
  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      handleImageSelect(e.target.files);
      e.target.value = ''; // Reset file input
    }
  };

  // Handle paste event for images
  const handlePaste = (e) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.type.startsWith('image/')) {
        e.preventDefault();
        const file = item.getAsFile();
        if (file) {
          handleImageSelect([file]);
        }
        break;
      }
    }
  };

  // Remove selected image
  const removeImage = (imageId) => {
    setSelectedImages(prev => prev.filter(img => img.id !== imageId));
  };

  // Load session history on mount
  useEffect(() => {
    const loadSessionHistory = async () => {
      setIsLoadingHistory(true);
      console.log(`Loading session history for: ${sessionId} with model: ${selectedModel}`);
      
      try {
        const apiBase = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
        const url = `${apiBase}/sessions/${sessionId}/history?model_id=${selectedModel}`;
        console.log(`Fetching from: ${url}`);
        
        const response = await fetch(url);
        console.log(`Response status: ${response.status}`);
        
        if (response.ok) {
          const data = await response.json();
          console.log('Session history response:', data);
          
          if (data.exists && data.messages && data.messages.length > 0) {
            console.log(`Setting ${data.messages.length} messages to UI`);
            setMessages(data.messages);
            setIsFirstInteraction(false);
            
            // Check last assistant message for quick options
            const lastAssistantMessage = data.messages
              .filter(msg => msg.role === 'assistant')
              .pop();
            
            if (lastAssistantMessage && lastAssistantMessage.content) {
              const options = parseQuickOptionsRealTime(lastAssistantMessage.content);
              setQuickOptions(options);
            }
          } else {
            console.log('No messages found or session does not exist - showing initial triage options');
            setIsFirstInteraction(true);
          }
        } else {
          console.error(`Failed to fetch session history: ${response.status} ${response.statusText}`);
          setIsFirstInteraction(true);
        }
      } catch (error) {
        console.error('Error loading session history:', error);
        setIsFirstInteraction(true);
      } finally {
        // Ensure loading is visible for at least 500ms
        setTimeout(() => {
          setIsLoadingHistory(false);
        }, 500);
      }
    };

    loadSessionHistory();
    focusInput();
  }, [sessionId, selectedModel, setMessages]);

  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      // Focus input on any key press (except when modal/sidebar interactions)
      if (e.target.tagName !== 'INPUT' && 
          e.target.tagName !== 'TEXTAREA' && 
          !e.target.closest('.sidebar') &&
          !e.ctrlKey && !e.metaKey && !e.altKey &&
          e.key.length === 1) {
        focusInput();
      }
    };

    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  const stopGeneration = () => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
      setIsLoading(false);
      
      // Update the last streaming message to indicate it was stopped
      setMessages(prev => prev.map((msg, index) => 
        index === prev.length - 1 && msg.isStreaming
          ? { ...msg, content: msg.content + '\n\n*Generation stopped by user*', isStreaming: false }
          : msg
      ));
    }
  };

  const sendMessage = async (messageText = null, isQuickResponse = false) => {
    const messageToSend = messageText || inputMessage;
    
    if ((!messageToSend.trim() && selectedImages.length === 0) || isLoading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: messageToSend,
      images: selectedImages.map(img => ({
        url: img.url,
        name: img.name
      })),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsFirstInteraction(false); // User has interacted
    
    if (!isQuickResponse) {
      setInputMessage('');
      setSelectedImages([]);
      
      // Reset textarea height
      if (inputRef.current) {
        inputRef.current.style.height = 'auto';
      }
    }
    
    // Clear quick options when sending new message
    setQuickOptions([]);
    setIsLoading(true);

    // Create initial AI message for streaming
    const aiMessageId = Date.now() + 1;
    const aiMessage = {
      id: aiMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      model: selectedModel,
      isStreaming: true
    };

    setMessages(prev => [...prev, aiMessage]);

    // Create abort controller
    const controller = new AbortController();
    setAbortController(controller);

    try {
      const apiBase = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
      
      // Prepare request body with images
      const requestBody = {
        message: messageToSend,
        model_id: selectedModel,
        session_id: sessionId,
        history: messages.filter(m => m.id !== userMessage.id) // Exclude current user message
      };

      // Add images if any
      if (selectedImages.length > 0) {
        requestBody.images = selectedImages.map(img => ({
          data: img.url,
          name: img.name
        }));
      }

      const response = await fetch(`${apiBase}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(requestBody),
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';
      let messageTokens = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              break;
            }

            try {
              const parsed = JSON.parse(data);
              
              if (parsed.type === 'content') {
                accumulatedContent += parsed.content;
                // Update UI immediately for each chunk, preserving formatting
                setMessages(prev => prev.map(msg => 
                  msg.id === aiMessageId 
                    ? { ...msg, content: accumulatedContent }
                    : msg
                ));
                
                // Real-time option parsing during streaming
                const currentOptions = parseQuickOptionsStreaming(accumulatedContent);
                if (currentOptions.length > 0) {
                  setQuickOptions(currentOptions);
                }
                
              } else if (parsed.type === 'tool_use') {
                // Show tool usage with input details
                const toolInfo = parsed.input ? ` (${JSON.stringify(parsed.input).slice(0, 50)}...)` : '';
                accumulatedContent += `\n`;
                setMessages(prev => prev.map(msg => 
                  msg.id === aiMessageId 
                    ? { ...msg, content: accumulatedContent + `\n\nUsing tool: ${parsed.tool_name}${toolInfo}` }
                    : msg
                ));
              } else if (parsed.type === 'tool_result') {
                // Tool result received with details
                const resultInfo = parsed.result;
                console.log(`${resultInfo}`)
                accumulatedContent += `${resultInfo}\n\n`;
                setMessages(prev => prev.map(msg => 
                  msg.id === aiMessageId 
                    ? { ...msg, content: accumulatedContent }
                    : msg
                ));
              } else if (parsed.type === 'image') {
                // Handle image from event_loop_metrics
                setMessages(prev => prev.map(msg => 
                  msg.id === aiMessageId 
                    ? { 
                        ...msg, 
                        content: accumulatedContent + `\n\n![Generated Image](${parsed.url})`,
                        images: [...(msg.images || []), { url: parsed.url, filename: parsed.filename }]
                      }
                    : msg
                ));
              } else if (parsed.type === 'metrics') {
                // Handle metrics information
                console.log('Received metrics:', parsed.data);
              } else if (parsed.type === 'tokens') {
                messageTokens = parsed;
                setTotalTokens(prev => ({
                  input: prev.input + parsed.input,
                  output: prev.output + parsed.output,
                  total: prev.total + parsed.total
                }));
                setTokenCount(prev => prev + parsed.total);
              } else if (parsed.type === 'session_started' || parsed.type === 'node_changed') {
                // Handle left sidebar reload events
                if (parsed.reload_left_ui && parsed.call_status_api && onSessionIdChange) {
                  onSessionIdChange(sessionId, true); // true = trigger status reload
                }
              }
            } catch (e) {
              // Ignore JSON parse errors for partial chunks
            }
          }
        }
      }

      // Mark streaming as complete and ensure final options are parsed
      setMessages(prev => prev.map(msg => 
        msg.id === aiMessageId 
          ? { ...msg, isStreaming: false, tokens: messageTokens }
          : msg
      ));
      
      // Final parse of quick options from completed content
      const finalOptions = parseQuickOptionsRealTime(accumulatedContent);
      setQuickOptions(finalOptions);

    } catch (error) {
      const aistMessageId = aiMessage.id;
      if (error.name === 'AbortError') {
        console.log('Request aborted');
        return;
      }
      
      let errorMessage = "An unexpected error occurred. Please try again.";
      if (error instanceof TypeError) { // Network error
        errorMessage = "Could not connect to the server. Please check your connection and try again.";
      } else if (error.message.includes('400')) {
        errorMessage = "There was a problem with the request. The selected AI model might not be available or the input was invalid.";
      } else if (error.message.includes('500')) {
        errorMessage = "The server encountered an internal error. Please try again later or contact support.";
      }

      setMessages(prev => prev.map(msg => 
        msg.id === aistMessageId 
          ? { 
              ...msg, 
              content: `System Error: ${errorMessage}`, 
              isStreaming: false,
              isError: true 
            }
          : msg
      ));
    } finally {
      setIsLoading(false);
      setAbortController(null);
      focusInput();
      
      // Always trigger left sidebar reload after each message
      if (onSessionIdChange) {
        onSessionIdChange(sessionId, true); // true = trigger status reload
      }
    }
  };

  const handleQuickOptionClick = (option) => {
    if (option.urgency === 'other' || option.text.includes('Other')) {
      // Focus input for "Other" option
      focusInput();
    } else if (option.text === "Start over") {
      newSession();
    } else if (option.text === "Emergency - Call 911") {
      sendMessage("This is an emergency situation", true);
    } else {
      // Send the option text as a message
      sendMessage(option.text, true);
    }
  };

  const handleDecisionTreeOptionClick = (optionText) => {
    sendMessage(optionText, true);
  };

  const handleKeyDown = (e) => {
    // Enter without Shift - send message
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading && inputMessage.trim()) {
        sendMessage();
      }
    }
    // Escape - clear input or focus
    else if (e.key === 'Escape') {
      e.preventDefault();
      if (inputMessage.trim()) {
        setInputMessage('');
        // Reset textarea height
        if (e.target) {
          e.target.style.height = 'auto';
        }
      }
      // Keep focus on input
      e.target.blur();
      setTimeout(() => e.target.focus(), 0);
    }
  };

  const clearMessages = async () => {
    // Clear current session on backend
    try {
      const apiBase = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
      await fetch(`${apiBase}/sessions/${sessionId}`, {
        method: 'DELETE'
      });
      console.log(`Cleared session ${sessionId} from backend`);
    } catch (error) {
      console.error('Error clearing session:', error);
    }
    
    // Clear UI
    setMessages([]);
    setQuickOptions([]);
    setTotalTokens({ input: 0, output: 0, total: 0 });
    setTokenCount(0);
    focusInput();
  };

  const newSession = async () => {
    // Clear current session on backend
    try {
      const apiBase = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
      await fetch(`${apiBase}/sessions/${sessionId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error('Error clearing session:', error);
    }
    
    // Clear messages
    setMessages([]);
    setQuickOptions([]);
    setTotalTokens({ input: 0, output: 0, total: 0 });
    setTokenCount(0);
    
    // Generate new session ID
    const newId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('chat_session_id', newId);
    
    // Force re-render with new session (would need to lift state up to parent)
    window.location.reload();
  };

  const formatModelName = (modelId) => {
    // Define custom names for specific models
    const modelNames = {
      'us.anthropic.claude-3-7-sonnet-20250219-v1:0': 'Claude 3.7 Sonnet',
      'us.anthropic.claude-sonnet-4-20250514-v1:0': 'Claude Sonnet 4',
      'anthropic.claude-3-5-sonnet-20241022-v2:0': 'Claude 3.5 Sonnet',
      'anthropic.claude-3-haiku-20240307-v1:0': 'Claude 3 Haiku',
      'us.amazon.nova-pro-v1:0': 'Nova Pro',
      'us.amazon.nova-lite-v1:0': 'Nova Lite',
      'us.amazon.nova-micro-v1:0': 'Nova Micro'
    };

    // Return custom name if available
    if (modelNames[modelId]) {
      return modelNames[modelId];
    }

    // Fallback to formatted version
    return modelId
      .replace('us.amazon.', '')
      .replace('us.anthropic.', '')
      .replace('anthropic.', '')
      .replace('-v1:0', '')
      .replace('-v2:0', '')
      .replace('-20250219', '')
      .replace('-20250514', '')
      .replace('-20241022', '')
      .replace('-20240307', '')
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <div className="chat-interface">
      {/* Chat Header */}
      <div className="chat-header">
        <div className="chat-header-left">
          {!leftSidebarOpen && (
            <button 
              className="expand-sidebar-btn" 
              onClick={toggleLeftSidebar}
              title="Open configuration"
            >
              ⚙️
            </button>
          )}
          <div className="chat-info">
            <div className="chat-title">AI Assistant</div>
            <div className="chat-subtitle">
              {formatModelName(selectedModel)} • {messages.length} messages
            </div>
          </div>
        </div>
        
        <div className="chat-header-right">
          {totalTokens.total > 0 && (
            <div className="token-display">
              <div className="token-stats">
                <span className="token-stat">
                  <span className="token-label">IN</span>
                  <span className="token-value">{totalTokens.input}</span>
                </span>
                <span className="token-stat">
                  <span className="token-label">OUT</span>
                  <span className="token-value">{totalTokens.output}</span>
                </span>
              </div>
              <div className="total-tokens">{totalTokens.total} tokens</div>
            </div>
          )}
          
          <button 
            className="clear-chat-btn"
            onClick={clearMessages}
            title="Clear conversation"
          >
            🗑️
          </button>
          
          <button 
            className="new-session-btn"
            onClick={newSession}
            title="Start new session"
          >
            ➕
          </button>
          
          {!rightSidebarOpen && (
            <button 
              className="expand-sidebar-btn" 
              onClick={toggleRightSidebar}
              title="Open server logs"
            >
              📋
            </button>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="messages-container">
        {isLoadingHistory ? (
          <div className="loading-history">
            <div className="loading-spinner"></div>
            <div>Loading conversation history...</div>
          </div>
        ) : messages.length === 0 || isFirstInteraction ? (
          <div className="empty-chat">
            <div className="empty-icon">🏥</div>
            <div className="empty-title">Medical AI Triage Assistant</div>
            <div className="empty-description">
              Welcome to your AI-powered medical triage assistant. I'll help assess your health concerns and guide you to appropriate care. 
              Please select your main health concern or describe it in your own words.
            </div>
            <div className="triage-options">
              <div className="triage-options-title">What's your main health concern today?</div>
              <div className="decision-tree-options">
                {decisionTreeOptions.map((option, index) => (
                  <button 
                    key={index}
                    className={`triage-option ${option.includes('Emergency') ? 'urgent' : 'routine'}`}
                    onClick={() => handleDecisionTreeOptionClick(option)}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="messages-list">
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.role}`}>
                <div className="message-header">
                  <div className="message-role">
                    {message.role === 'user' ? '👤 You' : '🤖 Assistant'}
                  </div>
                  <div className="message-meta">
                    {message.model && (
                      <span className="message-model">{formatModelName(message.model)}</span>
                    )}
                    <span className="message-time">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
                <div className={`message-content ${message.isError ? 'error' : ''}`}>
                  {/* Display images if present */}
                  {message.images && message.images.length > 0 && (
                    <div className="message-images">
                      {message.images.map((image, index) => (
                        <img 
                          key={index} 
                          src={image.url} 
                          alt={image.name || `Image ${index + 1}`}
                          className="message-image"
                        />
                      ))}
                    </div>
                  )}
                  
                  {message.role === 'assistant' ? (
                    <>
                      <ReactMarkdown>
                        {message.content
                          .replace(/<decision_tree_status[^>]*\/?>/g, '')
                          .replace(/<available_options>[\s\S]*?<\/available_options>/g, '')
                        }
                      </ReactMarkdown>
                      
                      {/* Show quick options only if message is complete (not streaming) and has available_options */}
                      {!message.isStreaming && message.content.includes('<available_options>') && (
                        <>
                          <hr className="message-divider" />
                          <div className="quick-options-label">Quick Options:</div>
                          <div className="message-quick-options">
                            {parseQuickOptionsRealTime(message.content).map((option, index) => (
                              <button
                                key={index}
                                className={`message-quick-btn urgency-${option.urgency}`}
                                onClick={() => handleQuickOptionClick(option)}
                              >
                                <span className="option-text">{option.text}</span>
                              </button>
                            ))}
                          </div>
                        </>
                      )}
                    </>
                  ) : (
                    message.content
                  )}
                  {message.isStreaming && (
                    <span className="streaming-cursor">▋</span>
                  )}
                </div>
                {message.tokens && (
                  <div className="message-tokens">
                    <span className="token-info">
                      {message.tokens.input}→{message.tokens.output} ({message.tokens.total} tokens)
                    </span>
                  </div>
                )}
              </div>
            )            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="input-container">
        <div className="input-wrapper">
          {/* Image preview section - Top */}
          {selectedImages.length > 0 && (
            <div className="image-preview-container">
              {selectedImages.map((image) => (
                <div key={image.id} className="image-preview">
                  <img src={image.url} alt={image.name} />
                  <button
                    className="image-preview-remove"
                    onClick={() => removeImage(image.id)}
                    title="Remove image"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
          
          {/* Input section - Bottom */}
          <div className="input-section">
            <div className="input-actions">
              <button
                className="attach-button"
                onClick={() => fileInputRef.current?.click()}
                title="Attach image"
              >
                📎
              </button>
            </div>
            
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => {
                setInputMessage(e.target.value);
                autoResizeTextarea(e.target);
              }}
              onKeyDown={handleKeyDown}
              placeholder="Describe your health concern or select an option above..."
              className="message-input"
              rows={1}
              disabled={isLoading}
            />
            
            <button
              onClick={isLoading ? stopGeneration : sendMessage}
              disabled={!isLoading && !inputMessage.trim() && selectedImages.length === 0}
              className="send-button"
            >
              {isLoading ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor"/>
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M7 11L12 6L17 11M12 18V7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              )}
            </button>
          </div>
        </div>
        
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileChange}
          className="file-input"
        />
      </div>
    </div>
  );
};

export default ChatInterface;