import React, { useState, useEffect, useRef } from 'react';
import './RightSidebar.css';

const RightSidebar = ({ onClose }) => {
  const [logs, setLogs] = useState({});
  const [selectedServer, setSelectedServer] = useState('All Servers');
  const [selectedLevel, setSelectedLevel] = useState('All Levels');
  const [autoScroll, setAutoScroll] = useState(true);
  const [expandedLog, setExpandedLog] = useState(null);
  const logsListRef = useRef(null);
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const scrollTimeoutRef = useRef(null);

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 3000); // Increased to 3 seconds
    return () => clearInterval(interval);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

    // CloudWatch-style tail to bottom
  const tailToBottom = () => {
    if (logsListRef.current) {
      const container = logsListRef.current;
      const oldScrollTop = container.scrollTop;
      const maxScrollTop = container.scrollHeight - container.clientHeight;
      
      console.log('tailToBottom called:', {
        oldScrollTop,
        maxScrollTop,
        scrollHeight: container.scrollHeight,
        clientHeight: container.clientHeight
      });
      
      // Force immediate scroll without smooth behavior for better responsiveness
      container.scrollTop = container.scrollHeight;
    } else {
      console.log('tailToBottom called but logsListRef.current is null');
    }
  };

  // Check if user is at the bottom
  const isAtBottom = () => {
    if (!logsListRef.current) return false;
    const container = logsListRef.current;
    const threshold = 5; // 5px tolerance
    return Math.abs(container.scrollHeight - container.scrollTop - container.clientHeight) < threshold;
  };

  // Handle user scroll detection - CloudWatch style
  const handleScroll = () => {
    if (!autoScroll) return;
    
    // Check if we're at the bottom
    const atBottom = isAtBottom();
    
    if (atBottom) {
      // If at bottom, allow auto-scroll
      setIsUserScrolling(false);
    } else {
      // If not at bottom, user is scrolling
      setIsUserScrolling(true);
      
      // Clear existing timeout
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
      
      // Reset user scrolling after 2 seconds of no scrolling
      scrollTimeoutRef.current = setTimeout(() => {
        if (isAtBottom()) {
          setIsUserScrolling(false);
        }
      }, 2000);
    }
  };

  const fetchLogs = async () => {
    try {
      const apiBase = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
      const response = await fetch(`${apiBase}/mcp/logs`);
      if (response.ok) {
        const data = await response.json();
        
        // Only update if logs have actually changed
        const currentLogsString = JSON.stringify(logs);
        const newLogsString = JSON.stringify(data);
        
        if (currentLogsString !== newLogsString) {
          setLogs(data);
        }
      }
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  const clearLogs = async () => {
    try {
          const apiBase = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
    const response = await fetch(`${apiBase}/mcp/logs`, {
        method: 'DELETE'
      });
      if (response.ok) {
        setLogs({});
      }
    } catch (error) {
      console.error('Error clearing logs:', error);
    }
  };

  const formatTimestamp = (logEntry) => {
    try {
      // Handle both old string format and new structured format
      if (typeof logEntry === 'object' && logEntry.timestamp) {
        const timestamp = new Date(logEntry.timestamp);
        return timestamp.toLocaleTimeString('en-US', { 
          hour12: false, 
          hour: '2-digit', 
          minute: '2-digit', 
          second: '2-digit' 
        });
      } else if (typeof logEntry === 'string') {
        const match = logEntry.match(/\[(.*?)\]/);
        if (match) {
          const timestamp = new Date(match[1]);
          return timestamp.toLocaleTimeString('en-US', { 
            hour12: false, 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
          });
        }
      }
    } catch (e) {
      // Ignore parsing errors
    }
    return '';
  };

  const formatLogMessage = (logEntry) => {
    try {
      // Handle structured format
      if (typeof logEntry === 'object' && logEntry.message) {
        return logEntry.message;
      }
      // Handle old string format
      else if (typeof logEntry === 'string') {
        const match = logEntry.match(/\[.*?\] (.*)/);
        return match ? match[1] : logEntry;
      }
    } catch (e) {
      return typeof logEntry === 'string' ? logEntry : JSON.stringify(logEntry);
    }
    return '';
  };

  const getLogLevel = (logEntry) => {
    // Handle structured format
    if (typeof logEntry === 'object' && logEntry.level) {
      return logEntry.level;
    }
    // Handle old string format
    const message = typeof logEntry === 'string' ? logEntry : logEntry.message || '';
    if (message.toLowerCase().includes('error')) return 'error';
    if (message.toLowerCase().includes('warning')) return 'warning';
    if (message.toLowerCase().includes('creating') || message.toLowerCase().includes('loading')) return 'info';
    return 'default';
  };

  const getLogDetails = (logEntry) => {
    if (typeof logEntry === 'object' && logEntry.details) {
      const details = logEntry.details;
      if (Object.keys(details).length === 0) return null;
      
      // Only show actual tool parameters - nothing else
      const filteredDetails = {};
      
      if (details.parameters && typeof details.parameters === 'object' && details.parameters !== null && Object.keys(details.parameters).length > 0) {
        filteredDetails.parameters = details.parameters;
      }
      
      return Object.keys(filteredDetails).length > 0 ? filteredDetails : null;
    }
    return null;
  };

  const formatLogDetails = (details) => {
    if (!details || Object.keys(details).length === 0) return null;
    
    return Object.entries(details).map(([key, value]) => {
      // Format different types of values
      let formattedValue = value;
      let valueType = 'text';
      
      // Special handling for parameters
      if (key === 'parameters' || key === 'input_parameters') {
        if (typeof value === 'object' && value !== null) {
          // If parameters object is empty, show that explicitly
          if (Object.keys(value).length === 0) {
            formattedValue = '(no parameters)';
            valueType = 'empty';
          } else {
            formattedValue = JSON.stringify(value, null, 2);
            valueType = 'parameters';
          }
        } else {
          formattedValue = value || '(no parameters)';
          valueType = 'parameters';
        }
      } else if (typeof value === 'object' && value !== null) {
        formattedValue = JSON.stringify(value, null, 2);
        valueType = 'json';
      } else if (Array.isArray(value)) {
        formattedValue = value.join(', ');
        valueType = 'array';
      } else if (typeof value === 'string' && value.length > 100) {
        valueType = 'long-text';
      } else if (typeof value === 'number') {
        valueType = 'number';
      }
      
      return { 
        key: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()), // Format key names
        value: formattedValue,
        originalKey: key,
        valueType
      };
    });
  };

  const getServerTag = (serverName) => {
    return serverName.toUpperCase();
  };

  const getLevelTag = (level) => {
    return level.toUpperCase();
  };

  const getAllLogs = () => {
    const allLogs = [];
    Object.entries(logs).forEach(([serverName, serverLogs]) => {
      serverLogs.forEach((logEntry, index) => {
        // Create a unique ID combining server name, timestamp, and index
        const timestamp = formatTimestamp(logEntry);
        const message = formatLogMessage(logEntry);
        const messagePreview = typeof message === 'string' ? message.slice(0, 20) : String(message).slice(0, 20);
        const uniqueId = `${serverName}-${timestamp || '00:00:00'}-${index}-${messagePreview}`;
        
        allLogs.push({
          id: uniqueId,
          server: serverName,
          message: message,
          timestamp: timestamp,
          level: getLogLevel(logEntry),
          details: getLogDetails(logEntry),
          raw: logEntry
        });
      });
    });
    
    // Sort by timestamp and server (oldest first)
    return allLogs.sort((a, b) => {
      const timeA = a.timestamp || '00:00:00';
      const timeB = b.timestamp || '00:00:00';
      const timeCompare = timeA.localeCompare(timeB);
      if (timeCompare !== 0) return timeCompare;
      // If timestamps are equal, sort by server name
      return a.server.localeCompare(b.server);
    });
  };

  const filteredLogs = getAllLogs().filter(log => {
    const serverMatch = selectedServer === 'All Servers' || log.server === selectedServer;
    const levelMatch = selectedLevel === 'All Levels' || log.level === selectedLevel.toLowerCase();
    return serverMatch && levelMatch;
  });

  const totalLogCount = getAllLogs().length;
  const serverNames = ['All Servers', ...Object.keys(logs)];
  const logLevels = ['All Levels', 'Info', 'Warning', 'Error'];

  // Auto-scroll when logs change - use logs object directly
  useEffect(() => {
    if (autoScroll && !isUserScrolling) {
      console.log('Auto-scrolling triggered, logs changed:', Object.keys(logs).length, 'servers');
      // Use requestAnimationFrame for better DOM sync
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          tailToBottom();
        });
      });
    }
  }, [logs, autoScroll, isUserScrolling]); // Watch logs object directly

  // Force scroll to bottom on mount if auto-scroll is enabled
  useEffect(() => {
    if (autoScroll) {
      setTimeout(() => {
        tailToBottom();
      }, 500); // Give time for initial render
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="right-sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">
          Server Logs
        </div>
        <div className="sidebar-subtitle">Real-time MCP server monitoring</div>
      </div>

      <div className="logs-controls">
        <div className="filter-row">
          <div className="filter-group">
            <label className="filter-label">Server</label>
            <select 
              value={selectedServer} 
              onChange={(e) => {
                setSelectedServer(e.target.value);
                setIsUserScrolling(false);
                // Auto-scroll after filter change
                if (autoScroll) {
                  setTimeout(() => tailToBottom(), 150);
                }
              }}
              className="filter-select"
            >
              {serverNames.map(name => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>
          
          <div className="filter-group">
            <label className="filter-label">Level</label>
            <select 
              value={selectedLevel} 
              onChange={(e) => {
                setSelectedLevel(e.target.value);
                setIsUserScrolling(false);
                // Auto-scroll after filter change
                if (autoScroll) {
                  setTimeout(() => tailToBottom(), 150);
                }
              }}
              className="filter-select"
            >
              {logLevels.map(level => (
                <option key={level} value={level}>{level}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="controls-row">
          <div className="auto-scroll-toggle">
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => {
                  const enabled = e.target.checked;
                  setAutoScroll(enabled);
                  setIsUserScrolling(false);
                  
                  // Immediately scroll to bottom when enabling
                  if (enabled) {
                    setTimeout(() => tailToBottom(), 100);
                  }
                }}
              />
              <span className="toggle-slider"></span>
            </label>
            <span className="toggle-label">Auto-scroll</span>
          </div>
          
          <button 
            onClick={clearLogs}
            className="clear-logs-btn"
            title="Clear all logs"
          >
            🗑️ Clear
          </button>
        </div>
      </div>

      <div className="logs-content">
        {filteredLogs.length === 0 ? (
          <div className="empty-logs">
            <div className="empty-icon">📝</div>
            <div className="empty-title">No logs available</div>
            <div className="empty-description">
              Server logs will appear here in real-time
            </div>
          </div>
        ) : (
          <div className="logs-list" ref={logsListRef} onScroll={handleScroll}>
                        {filteredLogs.map((log) => {
              const hasDetails = log.details && formatLogDetails(log.details) && formatLogDetails(log.details).length > 0;
              
              return (
                <div key={log.id} className={`log-entry ${log.level} ${hasDetails ? 'has-details' : ''}`}>
                  <div className="log-line expandable" onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}>
                    <div className="log-left">
                      <span className="log-timestamp">{log.timestamp}</span>
                      <span className="log-level-tag">
                        {getLevelTag(log.level)}
                      </span>
                      <span className="log-server-tag">
                        {getServerTag(log.server)}
                      </span>
                    </div>
                    <div className="log-message-content">
                      {log.message}
                    </div>
                  </div>
                  
                  {expandedLog === log.id && (
                    <div className="log-details-expanded">
                      <div className="details-content">
                        <div className="full-message">
                          <div className="message-text">{log.message}</div>
                        </div>
                        {hasDetails && formatLogDetails(log.details)?.map(({ key, value, originalKey, valueType }) => (
                          <div key={originalKey} className="param-detail">
                            <span className="param-key">{originalKey}:</span>
                            <span className="param-value">
                              {typeof value === 'object' ? 
                                JSON.stringify(value, null, 2) :
                                String(value)
                              }
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="logs-footer">
        <div className="logs-status">
          <div className="status-indicator">
            <span className="status-dot"></span>
            <span className="status-text">Live monitoring active</span>
          </div>
          <div className="status-info">
            <span className="log-count">
              {filteredLogs.length} / {totalLogCount} logs
            </span>
            <span className="update-info">Updates every 3s</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RightSidebar; 