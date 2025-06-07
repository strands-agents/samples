document.addEventListener('DOMContentLoaded', () => {
    // Create summary panel container
    const summaryPanelContainer = document.createElement('div');
    summaryPanelContainer.id = 'summary-panel-container';
    summaryPanelContainer.className = 'summary-panel-container';
    
    // Create summary panel header
    const summaryPanelHeader = document.createElement('div');
    summaryPanelHeader.className = 'summary-panel-header';
    summaryPanelHeader.innerHTML = '<h3>Metrics Summary</h3>';
    
    // Create summary panel content
    const summaryPanelContent = document.createElement('div');
    summaryPanelContent.id = 'summary-panel-content';
    summaryPanelContent.className = 'summary-panel-content';
    
    // Append elements to container
    summaryPanelContainer.appendChild(summaryPanelHeader);
    summaryPanelContainer.appendChild(summaryPanelContent);
    
    // Add to DOM
    document.querySelector('.app-wrapper').appendChild(summaryPanelContainer);
    
    // Function to show loading state in summary panel
    window.showSummaryLoading = function() {
        const content = document.getElementById('summary-panel-content');
        content.innerHTML = '<div class="loading"></div><div class="loading-text">Updating metrics...</div>';
    };
    
    // Function to update summary panel with data
    window.updateSummaryPanel = function(summaryData) {
        if (!summaryData) return;
        
        const content = document.getElementById('summary-panel-content');
        
        // Clear previous content
        content.innerHTML = '';
        
        // Create sections for different parts of the summary
        const cycleStats = document.createElement('div');
        cycleStats.className = 'summary-section';
        cycleStats.innerHTML = `
            <h4>Cycle Statistics</h4>
            <div class="summary-item">
                <span>Total Cycles:</span>
                <span>${summaryData.total_cycles}</span>
            </div>
            <div class="summary-item">
                <span>Total Duration:</span>
                <span>${summaryData.total_duration.toFixed(2)}s</span>
            </div>
            <div class="summary-item">
                <span>Average Cycle Time:</span>
                <span>${summaryData.average_cycle_time.toFixed(2)}s</span>
            </div>
        `;
        
        // Tool usage section
        const toolUsage = document.createElement('div');
        toolUsage.className = 'summary-section';
        toolUsage.innerHTML = '<h4>Tool Usage</h4>';
        
        const toolList = document.createElement('div');
        toolList.className = 'tool-usage-list';
        
        // Add each tool's metrics
        for (const [toolName, metrics] of Object.entries(summaryData.tool_usage)) {
            const toolItem = document.createElement('div');
            toolItem.className = 'tool-usage-item';
            toolItem.innerHTML = `
                <div class="tool-name">${toolName}</div>
                <div class="tool-stats">
                    <div class="summary-item">
                        <span>Calls:</span>
                        <span>${metrics.execution_stats.call_count}</span>
                    </div>
                    <div class="summary-item">
                        <span>Success Rate:</span>
                        <span>${(metrics.execution_stats.success_rate * 100).toFixed(1)}%</span>
                    </div>
                    <div class="summary-item">
                        <span>Avg Time:</span>
                        <span>${metrics.execution_stats.average_time.toFixed(2)}s</span>
                    </div>
                </div>
            `;
            toolList.appendChild(toolItem);
        }
        
        toolUsage.appendChild(toolList);
        
        // Add sections to content
        content.appendChild(cycleStats);
        content.appendChild(toolUsage);
        
        // Add accumulated usage section if available
        if (summaryData.accumulated_usage) {
            const usageSection = document.createElement('div');
            usageSection.className = 'summary-section';
            usageSection.innerHTML = `
                <h4>Token Usage</h4>
                <div class="summary-item">
                    <span>Total Tokens:</span>
                    <span>${summaryData.accumulated_usage.totalTokens || 0}</span>
                </div>
                <div class="summary-item">
                    <span>Input Tokens:</span>
                    <span>${summaryData.accumulated_usage.inputTokens || 0}</span>
                </div>
                <div class="summary-item">
                    <span>Output Tokens:</span>
                    <span>${summaryData.accumulated_usage.outputTokens || 0}</span>
                </div>
            `;
            content.appendChild(usageSection);
        }
        // Add accumulated usage section if available
        if (summaryData.accumulated_metrics) {
            const usageSection = document.createElement('div');
            usageSection.className = 'summary-section';
            usageSection.innerHTML = `
                <h4>Accumulated Metrics</h4>
                <div class="summary-item">
                    <span>Total latency :</span>
                    <span>${summaryData.accumulated_metrics.latencyMs || 0} ms</span>
                </div>
            `;
            content.appendChild(usageSection);
        }
    };
});