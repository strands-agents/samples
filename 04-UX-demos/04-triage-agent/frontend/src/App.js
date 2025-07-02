// src/App.js
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

import React, { useState, useEffect, useRef } from 'react';
import ChatInterface from './components/ChatInterface';
import LeftSidebar from './components/LeftSidebar';
import RightSidebar from './components/RightSidebar';
import './App.css';

// Cookie utility functions
const setCookie = (name, value, days = 30) => {
  const expires = new Date();
  expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
  document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
};

const getCookie = (name) => {
  const nameEQ = name + "=";
  const ca = document.cookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
  }
  return null;
};

const App = () => {
  const [messages, setMessages] = useState([]);
  const [mcpLogs, setMcpLogs] = useState({});
  const [backendStatus, setBackendStatus] = useState('checking');
  const [mcpStatus, setMcpStatus] = useState('checking');

  const logoPath = './aws-logo.png';
  const homePath = '/';

  // UI state
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(true);
  const [leftSidebarWidth, setLeftSidebarWidth] = useState(320);
  const [rightSidebarWidth, setRightSidebarWidth] = useState(350);
  // Initialize selectedModel from cookie or use default
  const [selectedModel, setSelectedModel] = useState('us.anthropic.claude-3-7-sonnet-20250219-v1:0');
  const [tokenCount, setTokenCount] = useState(0);
  const [isResizing, setIsResizing] = useState(null);
  const [currentSessionId, setCurrentSessionId] = useState(null);

  const leftResizeRef = useRef(null);
  const rightResizeRef = useRef(null);

  // Save selectedModel to cookie whenever it changes
  useEffect(() => {
    setCookie('selectedModel', selectedModel);
    console.log(`Model selection saved to cookie: ${selectedModel}`);
  }, [selectedModel]);

  // Check backend health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch('/health');
        if (response.ok) {
          setBackendStatus('online');
        } else {
          setBackendStatus('offline');
        }
      } catch (error) {
        setBackendStatus('offline');
      }
    };

    checkHealth();
    const healthInterval = setInterval(checkHealth, 5000);
    return () => clearInterval(healthInterval);
  }, []);

  // Check MCP servers status
  useEffect(() => {
    const checkMcpStatus = async () => {
      try {
        const response = await fetch('/mcp/servers');
        if (response.ok) {
          setMcpStatus('online');
        } else {
          setMcpStatus('offline');
        }
      } catch (error) {
        setMcpStatus('offline');
      }
    };

    checkMcpStatus();
    const mcpInterval = setInterval(checkMcpStatus, 5000);
    return () => clearInterval(mcpInterval);
  }, []);

  // Remove duplicate log fetching - RightSidebar handles its own logs

  const clearLogs = () => {
    setMcpLogs({});
  };

  // Handle mouse down for resizing
  const handleMouseDown = (side) => (e) => {
    e.preventDefault();
    setIsResizing(side);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  };

  // Handle mouse move for resizing
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing) return;

      if (isResizing === 'left') {
        const newWidth = Math.max(250, Math.min(500, e.clientX));
        setLeftSidebarWidth(newWidth);
      } else if (isResizing === 'right') {
        const newWidth = Math.max(250, Math.min(500, window.innerWidth - e.clientX));
        setRightSidebarWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(null);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  const toggleLeftSidebar = () => {
    setLeftSidebarOpen(!leftSidebarOpen);
  };

  const toggleRightSidebar = () => {
    setRightSidebarOpen(!rightSidebarOpen);
  };

  // Register global functions for sidebar components
  useEffect(() => {
    window.toggleLeftSidebar = toggleLeftSidebar;
    window.toggleRightSidebar = toggleRightSidebar;

    return () => {
      delete window.toggleLeftSidebar;
      delete window.toggleRightSidebar;
    };
  }, [leftSidebarOpen, rightSidebarOpen]);

  return (
    <div className="app">
      {/* Simplified Header */}
      <header className="app-header">
        <div className="header-left">
          <button
            className="sidebar-toggle"
            onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
          >
            {leftSidebarOpen ? '◀' : '▶'}
          </button>
          <div
            className="app-logo"
            onClick={() => window.location.href = homePath}
            style={{ cursor: 'pointer' }}
          >
            {/* <img src={logoPath} alt="AWS" className="aws-logo" /> */}
            <span className="aws-logo" >🏥</span>
            <div className="app-title">
                              <span className="title-main">AI Triage Agent</span>
              <span className="title-sub">POWERED BY AWS & STRANDS</span>
            </div>
          </div>
        </div>

        <div className="header-right">
          <button
            className="sidebar-toggle"
            onClick={() => setRightSidebarOpen(!rightSidebarOpen)}
          >
            {rightSidebarOpen ? '▶' : '◀'}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="app-main">
        {/* Left Sidebar */}
        <div
          className={`sidebar-container left ${!leftSidebarOpen ? 'closed' : ''}`}
          style={{ width: leftSidebarOpen ? `${leftSidebarWidth}px` : '0' }}
        >
          <LeftSidebar
            isOpen={leftSidebarOpen}
            selectedModel={selectedModel}
            setSelectedModel={setSelectedModel}
            sessionId={currentSessionId}
          />
          {leftSidebarOpen && (
            <div
              className="resize-handle left"
              onMouseDown={handleMouseDown('left')}
              ref={leftResizeRef}
            />
          )}
        </div>

        {/* Chat Interface */}
        <div className="chat-container">
          <ChatInterface
            messages={messages}
            setMessages={setMessages}
            selectedModel={selectedModel}
            tokenCount={tokenCount}
            setTokenCount={setTokenCount}
            leftSidebarOpen={leftSidebarOpen}
            rightSidebarOpen={rightSidebarOpen}
            toggleLeftSidebar={toggleLeftSidebar}
            toggleRightSidebar={toggleRightSidebar}
            onSessionIdChange={(sessionId, triggerReload = false) => {
              setCurrentSessionId(sessionId);
              if (triggerReload) {
                // Trigger left sidebar reload by updating a key or calling a function
                window.dispatchEvent(new CustomEvent('triageStatusReload', { detail: { sessionId } }));
              }
            }}
          />
        </div>

        {/* Right Sidebar */}
        <div
          className={`sidebar-container right ${!rightSidebarOpen ? 'closed' : ''}`}
          style={{ width: rightSidebarOpen ? `${rightSidebarWidth}px` : '0' }}
        >
          {rightSidebarOpen && (
            <div
              className="resize-handle right"
              onMouseDown={handleMouseDown('right')}
              ref={rightResizeRef}
            />
          )}
          <RightSidebar
            isOpen={rightSidebarOpen}
          />
        </div>
      </main>
    </div>
  );
};

export default App;