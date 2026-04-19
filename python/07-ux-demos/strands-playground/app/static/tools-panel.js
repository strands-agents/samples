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
        const errorP = document.createElement('p');
        errorP.className = 'error';
        errorP.textContent = 'Failed to load tools';
        toolsPanel.appendChild(errorP);
    }
}

// Render the tools list with checkboxes
function renderToolsList(container, availableTools, selectedTools, toolDescriptions = {}) {
    container.textContent = '';
    
    // Create header
    const header = document.createElement('div');
    header.className = 'tools-panel-header';
    const h3 = document.createElement('h3');
    h3.textContent = 'Strands Built-in Tools';
    const updateBtn = document.createElement('button');
    updateBtn.id = 'update-tools-btn';
    updateBtn.textContent = 'Update';
    header.appendChild(h3);
    header.appendChild(updateBtn);
    
    // Create info section
    const info = document.createElement('div');
    info.className = 'tools-info';
    const link = document.createElement('a');
    link.href = 'https://strandsagents.com/0.1.x/user-guide/concepts/tools/example-tools-package/';
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = 'Learn more about the built-in tools for Strands SDK';
    info.appendChild(link);
    
    // Create tools list
    const toolsList = document.createElement('div');
    toolsList.className = 'tools-list';
    
    availableTools.forEach(tool => {
        const toolItem = document.createElement('div');
        toolItem.className = 'tool-item';
        
        const formCheck = document.createElement('div');
        formCheck.className = 'form-check';
        
        const checkbox = document.createElement('input');
        checkbox.className = 'form-check-input';
        checkbox.type = 'checkbox';
        checkbox.value = tool;
        checkbox.id = `tool-${tool}`;
        checkbox.checked = selectedTools.includes(tool);
        
        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.setAttribute('for', `tool-${tool}`);
        label.textContent = tool;
        
        const description = document.createElement('p');
        description.className = 'tool-description';
        description.textContent = toolDescriptions[tool] || 'No description available';
        
        formCheck.appendChild(checkbox);
        formCheck.appendChild(label);
        toolItem.appendChild(formCheck);
        toolItem.appendChild(description);
        toolsList.appendChild(toolItem);
    });
    
    container.appendChild(header);
    container.appendChild(info);
    container.appendChild(toolsList);
    
    // Add event listener to update button
    updateBtn.addEventListener('click', updateSelectedTools);
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