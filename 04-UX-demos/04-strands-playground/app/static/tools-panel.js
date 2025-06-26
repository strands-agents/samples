// tools-panel.js - Manages the Strands tools selection side panel

// Initialize the tools panel
async function initToolsPanel() {
    const toolsPanel = document.getElementById('tools-panel');
    if (!toolsPanel) return;

    // Fetch current tools configuration
    try {
        const response = await fetch('/get_available_tools');
        const data = await response.json();
        
        if (data.available_tools && data.selected_tools) {
            renderToolsList(toolsPanel, data.available_tools, data.selected_tools, data.tool_descriptions || {});
        }
    } catch (error) {
        console.error('Error fetching tools:', error);
        toolsPanel.innerHTML = '<p class="error">Failed to load tools</p>';
    }
}

// Render the tools list with checkboxes
function renderToolsList(container, availableTools, selectedTools, toolDescriptions = {}) {
    container.innerHTML = `
        <div class="tools-panel-header">
            <h3>Strands Built-in Tools</h3>
            <button id="update-tools-btn">Update</button>
        </div>
        <div class="tools-info">
            <a href="https://strandsagents.com/0.1.x/user-guide/concepts/tools/example-tools-package/" target="_blank" rel="noopener noreferrer">
                Learn more about the built-in tools for Strands SDK
            </a>
        </div>
        <div class="tools-list">
            ${availableTools.map(tool => `
                <div class="tool-item">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" value="${tool}" 
                            id="tool-${tool}" ${selectedTools.includes(tool) ? 'checked' : ''}>
                        <label class="form-check-label" for="tool-${tool}">
                            ${tool}
                        </label>
                    </div>
                    <p class="tool-description">${toolDescriptions[tool] || 'No description available'}</p>
                </div>
            `).join('')}
        </div>
    `;

    // Add event listener to update button
    document.getElementById('update-tools-btn').addEventListener('click', updateSelectedTools);
}

// Update the selected tools
async function updateSelectedTools() {
    const selectedTools = [];
    document.querySelectorAll('.form-check-input:checked').forEach(checkbox => {
        selectedTools.push(checkbox.value);
    });

    try {
        const response = await fetch('/update_tools', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ tools: selectedTools }),
        });

        const result = await response.json();
        
        if (result.success) {
            showNotification('Tools updated successfully', 'success');
        } else {
            showNotification('Failed to update tools', 'error');
        }
    } catch (error) {
        console.error('Error updating tools:', error);
        showNotification('Error updating tools', 'error');
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }, 100);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initToolsPanel);