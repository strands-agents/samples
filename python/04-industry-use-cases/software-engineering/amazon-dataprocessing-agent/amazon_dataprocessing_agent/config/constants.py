# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Constants and configuration values for the DataProcessing Agent."""

# Maximum number of messages to keep in context
MAX_CONTEXT_MESSAGES = 10

# Page styling CSS
PAGE_STYLE = """
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Header */
    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 2.5rem;
        background: linear-gradient(135deg, #6366F1, #2DD4BF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.1);
        letter-spacing: -0.5px;
        padding: 1rem 0;
    }
    /* Chat Messages */
    .chat-message {
        padding: 1.2rem;
        border-radius: 12px;
        margin: 0.8rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        animation: fadeIn 0.4s ease-out;
        transition: all 0.3s ease;
    }
    
    .chat-message:hover {
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message {
        background-color: #f8f9ff;
        border-left: 5px solid #dfe0fc;
        border-top-left-radius: 0;
    }
    
    .assistant-message {
        background-color: #fdfcff;
        border-left: 5px solid #8B5CF6;
        border-top-left-radius: 0;
    }
    
    .streaming-message {
        background-color: #F5F3FF;
        border-left: 5px solid #8B5CF6;
        border-right: 4px solid #2DD4BF;
        animation: pulse 1.8s infinite;
    }
    
    @keyframes pulse {
        0% { border-right-color: #2DD4BF; }
        50% { border-right-color: #6366F1; }
        100% { border-right-color: #2DD4BF; }
    }
    .thinking-message {
        background-color: #fffdf7;
        border-left: 5px solid #fdebce;
        font-family: 'JetBrains Mono', monospace;
        white-space: pre-wrap;
        font-size: 0.9em;
        line-height: 1.5;
        padding: 1.5rem;
        margin-top: 0.5rem;
        border-radius: 8px;
    }
    
    .tool-status {
        background-color: #f3f6f4;
        border-left: 5px solid #10B981;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        font-size: 0.9em;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    /* Containers */
    .chat-container {
        max-height: 650px;
        overflow-y: auto;
        padding: 1.5rem;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        background-color: #FFFFFF;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
        scrollbar-width: thin;
        scrollbar-color: #CBD5E1 #F1F5F9;
    }
    
    .chat-container::-webkit-scrollbar {
        width: 8px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: #F1F5F9;
        border-radius: 10px;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background-color: #CBD5E1;
        border-radius: 10px;
        border: 2px solid #F1F5F9;
    }
    
    .input-container {
        position: sticky;
        bottom: 0;
        background-color: white;
        padding: 1.2rem;
        border-top: 1px solid #E5E7EB;
        margin-top: 1.5rem;
        border-radius: 0 0 16px 16px;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.03);
    }
    
    .context-info {
        background-color: #EEF2FF;
        border: 1px solid #6366F1;
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.8rem 0;
        font-size: 0.85em;
        color: #4F46E5;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    /* Buttons and Controls */
    button.primary-button {
        background: linear-gradient(135deg, #6366F1, #4F46E5);
        color: white;
        border: none;
        padding: 0.6rem 1.2rem;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(79, 70, 229, 0.3);
    }
    
    button.primary-button:hover {
        background: linear-gradient(135deg, #4F46E5, #4338CA);
        box-shadow: 0 4px 8px rgba(79, 70, 229, 0.4);
        transform: translateY(-1px);
    }
    
    button.secondary-button {
        background-color: #F3F4F6;
        color: #4B5563;
        border: 1px solid #E5E7EB;
        padding: 0.6rem 1.2rem;
        border-radius: 8px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    button.secondary-button:hover {
        background-color: #E5E7EB;
        color: #374151;
    }
    
    /* Sidebar Styling */
    .sidebar .block-container {
        padding: 1.5rem;
        background-color: #F8FAFC;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    }
    
    .sidebar h1, .sidebar h2, .sidebar h3 {
        color: #1E293B;
        margin-bottom: 1rem;
    }
    
    /* Status Indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-weight: 500;
        font-size: 0.9em;
    }
    
    .status-success {
        background-color: #ECFDF5;
        color: #059669;
    }
    
    .status-warning {
        background-color: #FFFBEB;
        color: #D97706;
    }
    
    .status-error {
        background-color: #FEF2F2;
        color: #DC2626;
    }
    
    /* Metrics Display */
    .metrics-container {
        background-color: #F8FAFC;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #E2E8F0;
    }
    
    .metric-item {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px dashed #E2E8F0;
    }
    
    .metric-item:last-child {
        border-bottom: none;
    }
    
    .metric-label {
        color: #64748B;
        font-weight: 500;
    }
    
    .metric-value {
        color: #0F172A;
        font-weight: 600;
    }
</style>
"""
