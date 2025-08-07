// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Helper function to create element with text content
function createElement(tag, className, textContent) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (textContent) element.textContent = textContent;
    return element;
}

document.addEventListener('DOMContentLoaded', () => {
    // Create summary panel container
    const summaryPanelContainer = document.createElement('div');
    summaryPanelContainer.id = 'summary-panel-container';
    summaryPanelContainer.className = 'summary-panel-container';
    
    // Create summary panel header
    const summaryPanelHeader = document.createElement('div');
    summaryPanelHeader.className = 'summary-panel-header';
    const headerTitle = createElement('h3', null, 'Metrics Summary');
    summaryPanelHeader.appendChild(headerTitle);
    
    // Create summary panel content
    const summaryPanelContent = document.createElement('div');
    summaryPanelContent.id = 'summary-panel-content';
    summaryPanelContent.className = 'summary-panel-content';
    
    // Create metrics info section
    const metricsInfo = document.createElement('div');
    metricsInfo.className = 'metrics-info';
    const infoLink = document.createElement('a');
    infoLink.href = 'https://strandsagents.com/0.1.x/user-guide/observability-evaluation/metrics/';
    infoLink.target = '_blank';
    infoLink.rel = 'noopener noreferrer';
    infoLink.textContent = 'Strands SDK offers detailed metrics tracking to monitor your agent\'s performance';
    metricsInfo.appendChild(infoLink);
    
    // Append elements to container
    summaryPanelContainer.appendChild(summaryPanelHeader);
    summaryPanelContainer.appendChild(metricsInfo);
    summaryPanelContainer.appendChild(summaryPanelContent);
    
    // Add to DOM
    document.querySelector('.app-wrapper').appendChild(summaryPanelContainer);
    
    // Function to show loading state in summary panel
    window.showSummaryLoading = function() {
        const content = document.getElementById('summary-panel-content');
        content.textContent = '';
        const loadingDiv = createElement('div', 'loading');
        const loadingText = createElement('div', 'loading-text', 'Updating metrics...');
        content.appendChild(loadingDiv);
        content.appendChild(loadingText);
    };
    
    // Function to update summary panel with data
    window.updateSummaryPanel = function(summaryData) {
        console.log("Received summary data:", summaryData);
        if (!summaryData) return;
        
        const content = document.getElementById('summary-panel-content');
        
        // Clear previous content
        content.textContent = '';
        
        // Create sections for different parts of the summary
        const cycleStats = document.createElement('div');
        cycleStats.className = 'summary-section';
        
        const cycleTitle = createElement('h4', null, 'Cycle Statistics');
        cycleStats.appendChild(cycleTitle);
        
        // Total Cycles
        const totalCyclesItem = document.createElement('div');
        totalCyclesItem.className = 'summary-item';
        totalCyclesItem.appendChild(createElement('span', null, 'Total Cycles:'));
        totalCyclesItem.appendChild(createElement('span', null, String(summaryData.total_cycles)));
        cycleStats.appendChild(totalCyclesItem);
        
        // Total Duration
        const totalDurationItem = document.createElement('div');
        totalDurationItem.className = 'summary-item';
        totalDurationItem.appendChild(createElement('span', null, 'Total Duration:'));
        totalDurationItem.appendChild(createElement('span', null, summaryData.total_duration.toFixed(2) + 's'));
        cycleStats.appendChild(totalDurationItem);
        
        // Average Cycle Time
        const avgCycleItem = document.createElement('div');
        avgCycleItem.className = 'summary-item';
        avgCycleItem.appendChild(createElement('span', null, 'Average Cycle Time:'));
        avgCycleItem.appendChild(createElement('span', null, summaryData.average_cycle_time.toFixed(2) + 's'));
        cycleStats.appendChild(avgCycleItem);
        
        // Tool usage section
        const toolUsage = document.createElement('div');
        toolUsage.className = 'summary-section';
        const toolTitle = createElement('h4', null, 'Tool Usage');
        toolUsage.appendChild(toolTitle);
        
        const toolList = document.createElement('div');
        toolList.className = 'tool-usage-list';
        
        // Add each tool's metrics
        for (const [toolName, metrics] of Object.entries(summaryData.tool_usage)) {
            const toolItem = document.createElement('div');
            toolItem.className = 'tool-usage-item';
            
            const toolNameDiv = createElement('div', 'tool-name', toolName);
            toolItem.appendChild(toolNameDiv);
            
            const toolStats = document.createElement('div');
            toolStats.className = 'tool-stats';
            
            // Calls
            const callsItem = document.createElement('div');
            callsItem.className = 'summary-item';
            callsItem.appendChild(createElement('span', null, 'Calls:'));
            callsItem.appendChild(createElement('span', null, String(metrics.execution_stats.call_count)));
            toolStats.appendChild(callsItem);
            
            // Success Rate
            const successItem = document.createElement('div');
            successItem.className = 'summary-item';
            successItem.appendChild(createElement('span', null, 'Success Rate:'));
            successItem.appendChild(createElement('span', null, (metrics.execution_stats.success_rate * 100).toFixed(1) + '%'));
            toolStats.appendChild(successItem);
            
            // Average Time
            const avgTimeItem = document.createElement('div');
            avgTimeItem.className = 'summary-item';
            avgTimeItem.appendChild(createElement('span', null, 'Avg Time:'));
            avgTimeItem.appendChild(createElement('span', null, metrics.execution_stats.average_time.toFixed(2) + 's'));
            toolStats.appendChild(avgTimeItem);
            
            toolItem.appendChild(toolStats);
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
            
            const usageTitle = createElement('h4', null, 'Token Usage');
            usageSection.appendChild(usageTitle);
            
            // Total Tokens
            const totalTokensItem = document.createElement('div');
            totalTokensItem.className = 'summary-item';
            totalTokensItem.appendChild(createElement('span', null, 'Total Tokens:'));
            totalTokensItem.appendChild(createElement('span', null, String(summaryData.accumulated_usage.totalTokens || 0)));
            usageSection.appendChild(totalTokensItem);
            
            // Input Tokens
            const inputTokensItem = document.createElement('div');
            inputTokensItem.className = 'summary-item';
            inputTokensItem.appendChild(createElement('span', null, 'Input Tokens:'));
            inputTokensItem.appendChild(createElement('span', null, String(summaryData.accumulated_usage.inputTokens || 0)));
            usageSection.appendChild(inputTokensItem);
            
            // Output Tokens
            const outputTokensItem = document.createElement('div');
            outputTokensItem.className = 'summary-item';
            outputTokensItem.appendChild(createElement('span', null, 'Output Tokens:'));
            outputTokensItem.appendChild(createElement('span', null, String(summaryData.accumulated_usage.outputTokens || 0)));
            usageSection.appendChild(outputTokensItem);
            
            content.appendChild(usageSection);
        }
        
        // Add accumulated metrics section if available
        if (summaryData.accumulated_metrics) {
            const metricsSection = document.createElement('div');
            metricsSection.className = 'summary-section';
            
            const metricsTitle = createElement('h4', null, 'Accumulated Metrics');
            metricsSection.appendChild(metricsTitle);
            
            // Total Latency
            const latencyItem = document.createElement('div');
            latencyItem.className = 'summary-item';
            latencyItem.appendChild(createElement('span', null, 'Total latency:'));
            latencyItem.appendChild(createElement('span', null, String(summaryData.accumulated_metrics.latencyMs || 0) + ' ms'));
            metricsSection.appendChild(latencyItem);
            
            content.appendChild(metricsSection);
        }
    };
});