import React, { useState, useEffect, useRef } from 'react';
import DecisionTreeVisualization from './DecisionTreeVisualization';
import './LeftSidebar.css';

const LeftSidebar = ({ selectedModel, setSelectedModel, sessionId, onClose }) => {
  const [models, setModels] = useState([]);
  const [mcpServers, setMcpServers] = useState({});
  const [loading, setLoading] = useState(true);
  const [isTriageSectionOpen, setIsTriageSectionOpen] = useState(true);
  const [triageStatus, setTriageStatus] = useState({});
  const [currentSession, setCurrentSession] = useState(null);
  const currentNodeRef = useRef(null);
  const updateIntervalRef = useRef(null);

  useEffect(() => {
    fetchModels();
    fetchMcpServers();
    fetchTriageStatus();
    fetchCurrentSession();
  }, [selectedModel, sessionId]);
  
  // Separate effect for sessionId changes to force reload
  useEffect(() => {
    if (sessionId) {
      console.log('SessionId changed, reloading triage data:', sessionId);
      fetchCurrentSession();
      fetchTriageStatus();
    }
  }, [sessionId]);
  
  // Add event listener for triage status reload
  useEffect(() => {
    const handleTriageStatusReload = (event) => {
      console.log('Triage status reload event received:', event.detail);
      // Force reload with a small delay to ensure backend is updated
      setTimeout(() => {
        fetchCurrentSession();
        fetchTriageStatus();
      }, 100);
    };
    
    window.addEventListener('triageStatusReload', handleTriageStatusReload);
    
    return () => {
      window.removeEventListener('triageStatusReload', handleTriageStatusReload);
    };
  }, [sessionId]);

  const fetchCurrentSession = async () => {
    if (!sessionId) return;
    
    try {
      const apiBase = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
      const response = await fetch(`${apiBase}/api/triage/session/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.exists) {
          setCurrentSession(data);
          
          // Handle scroll focus when current node changes
          if (currentNodeRef.current && 
              data.current_node_id && 
              (!currentSession || currentSession.current_node_id !== data.current_node_id)) {
            setTimeout(() => {
              const nodeElement = document.querySelector('.current-node');
              if (nodeElement) {
                nodeElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
              }
            }, 100);
          }
        } else {
          setCurrentSession(null);
        }
      } else {
        setCurrentSession(null);
      }
    } catch (error) {
      console.error('Error fetching current session:', error);
      setCurrentSession(null);
    }
  };

  const fetchModels = async () => {
    try {
          const apiBase = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
    const response = await fetch(`${apiBase}/models`);
      const data = await response.json();
      setModels(data);
    } catch (error) {
      console.error('Error fetching models:', error);
    }
  };

  const fetchMcpServers = async () => {
    try {
          const apiBase = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
    const response = await fetch(`${apiBase}/mcp/servers`);
      const data = await response.json();
      const transformedData = Object.keys(data).reduce((acc, serverName) => {
        acc[serverName] = {
          ...data[serverName],
          enabled: data[serverName].enabled !== undefined ? data[serverName].enabled : false,
          status: data[serverName].enabled ? 'ready' : 'disabled'
        };
        return acc;
      }, {});
      setMcpServers(transformedData);
    } catch (error) {
      console.error('Error fetching MCP servers:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTriageStatus = async () => {
    try {
      const apiBase = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
      const response = await fetch(`${apiBase}/api/triage/status`);
      if (response.ok) {
        const data = await response.json();
        setTriageStatus(data);
      } else {
        setTriageStatus({ status: 'offline', nodes_loaded: 0, tree: null });
      }
    } catch (error) {
      console.error('Error fetching triage status:', error);
      setTriageStatus({ status: 'offline', nodes_loaded: 0, tree: null });
    }
  };

  const toggleServer = async (serverName, enabled) => {
    try {
          const apiBase = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
    const response = await fetch(`${apiBase}/mcp/servers/${serverName}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !enabled })
      });

      if (response.ok) {
        setMcpServers(prev => ({
          ...prev,
          [serverName]: {
            ...prev[serverName],
            enabled: !enabled,
            status: !enabled ? 'ready' : 'disabled'
          }
        }));
      }
    } catch (error) {
      console.error('Error toggling server:', error);
    }
  };

  const formatModelName = (model) => {
    return model.name || model.id
      .replace('us.amazon.', '')
      .replace('anthropic.', '')
      .replace('-v1:0', '')
      .replace('-v2:0', '')
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const handleResetSession = () => {
    // Implementation of handleResetSession function
  };

  return (
    <div className="left-sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">Configuration</div>
      </div>

      <div className="sidebar-content">
        {/* AI Models Section */}
        <div className="section">
          <div className="section-header">
            <span className="section-icon">🤖</span>
            <span className="section-title">AI Models</span>
          </div>

          <div className="model-selector">
            <label className="input-label">Current Model</label>
            <select 
              value={selectedModel} 
              onChange={(e) => setSelectedModel(e.target.value)}
              className="model-dropdown"
            >
              {models.map((model) => (
                <option key={model.id} value={model.id}>
                  {formatModelName(model)}
                </option>
              ))}
            </select>
          </div>

          {selectedModel && (
            <div className="model-info">
              <div className="model-details">
                {(() => {
                  const model = models.find(m => m.id === selectedModel);
                  return model ? (
                    <>
                      <div className="model-name">{formatModelName(model)}</div>
                      <div className="model-description">{model.description}</div>
                    </>
                  ) : null;
                })()}
              </div>
            </div>
          )}
        </div>

        {/* Medical Triage Section */}
        <div className="section">
          <div className="section-header">
            <span className="section-icon">🏥</span>
            <span className="section-title">Medical Triage System</span>
          </div>

          <div className="section-content triage-details">
            {!triageStatus.status ? (
              <div className="triage-loading">Loading triage status...</div>
            ) : triageStatus.status === 'online' ? (
              <>
                <div className="triage-status">
                  <div className="status-item">
                    <span className="status-label">Decision Tree Status</span>
                    <span className={`status-value ${triageStatus.status}`}>
                      <span className={`status-indicator ${triageStatus.status}`}></span>
                      Online
                    </span>
                  </div>
                  <div className="status-item">
                    <span className="status-label">Nodes Loaded</span>
                    <span className="status-value">{triageStatus.nodes_loaded || triageStatus.nodes_count || 0}</span>
                  </div>
                  <div className="status-item">
                    <span className="status-label">Chat Session</span>
                    <span className="status-value">{sessionId ? 'Active' : 'None'}</span>
                  </div>
                  {currentSession ? (
                    <div className="status-item current-session" ref={currentNodeRef}>
                      <span className="status-label">Current Position</span>
                      <span className="status-value current-node">
                        <span className="node-indicator">📍</span>
                        {currentSession.current_node?.topic || currentSession.current_node_id || 'Start'}
                      </span>
                    </div>
                  ) : (
                    <div className="status-item">
                      <span className="status-label">Triage Session</span>
                                                      <span className="status-value">Start conversation to begin</span>
                    </div>
                  )}
                </div>
                
                <div className="tree-view-container">
                   <DecisionTreeVisualization 
                     tree={triageStatus.tree} 
                     currentNodeId={currentSession?.current_node_id}
                     key={currentSession?.current_node_id} // Force re-render on node change
                   />
                </div>
              </>
            ) : (
              <div className="triage-offline">
                System is currently offline.
              </div>
            )}
          </div>
        </div>

        {/* MCP Servers Section */}
        <div className="section">
          <div className="section-header">
            <span className="section-icon">🔧</span>
            <span className="section-title">MCP Servers</span>
          </div>

          {loading ? (
            <div className="loading-state">Loading servers...</div>
          ) : (
            <div className="servers-list">
              {Object.entries(mcpServers).map(([serverName, server]) => (
                <div key={serverName} className="server-item">
                  <div className="server-info">
                    <div className="server-header">
                      <span className="server-name">{server.name}</span>
                      <span className={`server-status ${server.enabled ? 'enabled' : 'disabled'}`}>
                        {server.enabled ? '●' : '○'}
                      </span>
                    </div>
                    <div className="server-description">{server.description}</div>
                  </div>
                  
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={server.enabled}
                      onChange={() => toggleServer(serverName, server.enabled)}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      {/* Disclaimer */}
      <div className="sidebar-disclaimer">
        ⚠️ PoC Demo Only - Not Medical Advice
      </div>
    </div>
  );
};

export default LeftSidebar; 