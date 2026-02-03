#This sample application is intended solely for educational and knowledge-sharing purposes. It is not designed to provide investment guidance or financial advice.

import logging
import sys
import html
import traceback
import os
from typing import Dict, List, Optional, Tuple

import streamlit as st

# Show loading indicator while schema is being loaded with streaming updates
if not hasattr(st.session_state, 'schema_loaded'):
    status_placeholder = st.empty()
    progress_placeholder = st.empty()
    
    status_placeholder.info('🔄 Loading database schema... Please wait.')
    
    # Import retrieve_schema to access schema loading functions
    from retrieve_schema import boto3_clients, get_database_tables_via_athena, describe_table_via_athena, DATABASE
    
    try:
        # Initialize Athena client
        athena_client, _ = boto3_clients()
        
        # Get list of tables
        status_placeholder.info('📋 Retrieving table list...')
        tables = get_database_tables_via_athena(athena_client, database=DATABASE)
        
        # Create schema dictionary
        schema = {}
        total_tables = len(tables)
        
        # Stream table information as it loads
        for idx, table in enumerate(tables, 1):
            status_placeholder.info(f'📊 Loading table {idx}/{total_tables}: **{table}**')
            progress_placeholder.progress(idx / total_tables)
            
            try:
                columns = describe_table_via_athena(athena_client, table, database=DATABASE)
                schema[table] = columns
                status_placeholder.success(f'✓ Loaded **{table}**: {len(columns)} columns')
            except Exception as e:
                schema[table] = {"error": str(e)}
                status_placeholder.warning(f'⚠️ Error loading **{table}**: {str(e)}')
        
        # Store schema in prompt module
        import prompt
        prompt.fa_db_schema = schema
        
        # Now import chat which will use the loaded schema
        import chat
        
        # Mark as loaded
        st.session_state.schema_loaded = True
        
        # Show final success message
        status_placeholder.success(f'✅ Database schema loaded successfully! ({total_tables} tables)')
        progress_placeholder.empty()
        
        # Small delay to show success message
        import time
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        status_placeholder.error(f'❌ Failed to load database schema: {str(e)}')
        st.stop()
else:
    import chat

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================
# Application constants
APP_TITLE = "Financial Advisor AI"
APP_VERSION = "1.0"
MAX_INPUT_LENGTH = 5000
DEFAULT_MODEL = "Claude 3.7 Sonnet"

# Available AI models
AVAILABLE_MODELS = [
    "Claude 4 Sonnet",
    "Claude 3.7 Sonnet",
]

# Models that support advanced reasoning
REASONING_SUPPORTED_MODELS = ["Claude 4 Sonnet","Claude 3.7 Sonnet"]

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s:%(lineno)d | %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("streamlit")

# Suppress OpenTelemetry context warnings (harmless warnings from async operations being cancelled by Streamlit reruns)
logging.getLogger("opentelemetry.context").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.trace").setLevel(logging.CRITICAL)

# Configure Streamlit page settings
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://github.com/strands-agents/samples',
        'About': f"# {APP_TITLE} v{APP_VERSION}\nAI-powered financial advisory assistant"
    }
)

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================
def render_sidebar() -> tuple[str, str]:
    """Render the sidebar with model selection and configuration options."""
    with st.sidebar:
        st.title("🔧 Configuration")

        # Model selection
        model_name = st.selectbox(
            "🤖 Foundation Model",
            options=AVAILABLE_MODELS,
            index=0,
            help="Select the AI model for processing your queries"
        )

        # Reasoning mode configuration
        enable_reasoning = st.checkbox(
            "Advanced Reasoning",
            value=False,
            help="Enhanced thinking capabilities (may increase response time)",
            disabled=model_name not in REASONING_SUPPORTED_MODELS
        )
        
        reasoning_mode = "Enable" if enable_reasoning and model_name in REASONING_SUPPORTED_MODELS else "Disable"
        
        logger.info(f"Model: {model_name}, Reasoning: {reasoning_mode}")
        chat.update(model_name, reasoning_mode)
        
        return model_name, reasoning_mode

# Render sidebar and get configuration
model_name, reasoning_mode = render_sidebar()

st.title("💼 Financial Advisor AI Assistant")

# ============================================================================
# SESSION STATE MANAGEMENT
# ============================================================================
def initialize_session_state() -> None:
    """Initialize session state variables if they don't exist."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "greetings" not in st.session_state:
        st.session_state.greetings = False
    if "example_query" not in st.session_state:
        st.session_state.example_query = ""
    if "chart_to_display" not in st.session_state:
        st.session_state.chart_to_display = []
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None

def display_chat_messages() -> None:
    """Display chat message history with HTML/CSS styling, images, and charts."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Handle image attachments
            if "images" in message:
                for image_url in message["images"]:
                    file_name = image_url[image_url.rfind("/") + 1:]
                    st.image(image_url, caption=file_name, use_container_width=True)
            
            # Process and display message content
            content = html.unescape(message["content"]) if "&lt;" in message["content"] else message["content"]
            st.markdown(content, unsafe_allow_html=True)
            
            # Display chart if available
            if (message["role"] == "assistant" and 
                "chart_path" in message and 
                message["chart_path"] and 
                os.path.exists(message["chart_path"])):
                
                chart_filename = os.path.basename(message["chart_path"])
                st.image(message["chart_path"], caption=f"📊 {chart_filename}", use_container_width=True)
                message["chart_path"] = None

# Initialize session state and display messages
initialize_session_state()
display_chat_messages()

# ============================================================================
# WELCOME MESSAGE
# ============================================================================
def display_welcome_message() -> None:
    """Display the initial welcome message to new users."""
    if not st.session_state.greetings:
        welcome_message = """
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; 
                    padding: 20px; border-radius: 12px; border-left: 5px solid #4CAF50; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);">
            <h3 style="margin: 0 0 12px 0; font-size: 18px;">🏦 Welcome to Financial Advisor AI</h3>
            <p style="margin: 0; font-size: 15px;">Your intelligent assistant for:</p>
            <ul style="margin: 10px 0 0 20px; font-size: 14px;">
                <li>Client meeting analysis and reporting</li>
                <li>Portfolio analysis and performance tracking</li>
                <li>Market research and investment insights</li>
                <li>Stock data and financial metrics</li>
            </ul>
            <p style="margin: 10px 0 0 0; font-size: 14px; font-style: italic;">
                Try the example queries below to get started!
            </p>
        </div>
        """
        with st.chat_message("assistant"):
            st.markdown(welcome_message, unsafe_allow_html=True)
        
        st.session_state.messages.append({"role": "assistant", "content": welcome_message})
        st.session_state.greetings = True

def display_example_buttons() -> None:
    """Display example query buttons."""
    is_disabled = st.session_state.get("is_processing", False)
    
    st.markdown('<div style="padding: 8px; background-color: #f8f9fa; border-radius: 8px; margin-bottom: 10px;">'
                '<h4 style="margin: 0; color: #495057; font-size: 16px;">📝 Example Queries</h4></div>', 
                unsafe_allow_html=True)
    
    if is_disabled:
        st.info("⏳ Processing your request...")
    
    col1, col2 = st.columns(2)
    
    examples = [
        ("📈 US Stock Market Prospects", "The prospects for the US stock market for remaining 2025", "example3"),
        ("💰 Amazon Stock Price", "The latest Amazon stock pricing", "example4"),
        ("🔍 Compare AMZN vs MSFT", "Compare Amazon and Microsoft stock performance over the last year", "example6"),
        ("📋 Complete Customer Report", f"Using knowledge base id {chat.get_kb_id_from_config()}, provide a complete customer report including meeting summary, action items, research answers for each action item, portfolio analysis, security performance, and market trend overview", "example8"),
    ]
    
    examples_col2 = [
        ("📊 Client Portfolio Summary", "Michael Chen's Portfolio Summary", "example1"),
        ("🏦 Knowledge Base List", "provide me knowledge base list", "example2"),
        ("📝 Client Meeting Analysis", f"client meeting analysis and summary using knowledge base id {chat.get_kb_id_from_config()}", "example5"),
        ("👨‍💼 Advisor Follow-up Analysis", f"Using knowledge base id {chat.get_kb_id_from_config()}, Identify specific action items to financial advisor discussed during the client meeting, for each identified action item, conduct a web search to find relevant and up-to-date information.", "example7"),
    ]
    
    with col1:
        for label, query, key in examples:
            if st.button(label, key=key, disabled=is_disabled, use_container_width=True):
                st.session_state.example_query = query
                st.session_state.is_processing = True
                st.rerun()
    
    with col2:
        for label, query, key in examples_col2:
            if st.button(label, key=key, disabled=is_disabled, use_container_width=True):
                st.session_state.example_query = query
                st.session_state.is_processing = True
                st.rerun()

display_welcome_message()
display_example_buttons()

# ============================================================================
# CHAT INPUT AND PROCESSING
# ============================================================================
def sanitize_user_input(user_input: str) -> str:
    """Sanitize user input to prevent issues with quote characters."""
    return user_input.replace('"', "").replace("'", "")

def process_user_input(user_prompt: str) -> str:
    """Process user input and generate AI response with error handling."""
    try:
        sanitized_prompt = sanitize_user_input(user_prompt)
        logger.info(f"Processing: {sanitized_prompt}")
        
        # Reset chat state
        if hasattr(chat, 'references'):
            chat.references = []
        if hasattr(chat, 'image_url'):
            chat.image_url = []
        
        
        # Generate response using the chat triage system
        with st.spinner("🤔 Analyzing your request..."):
            response = chat.triage_query(sanitized_prompt, "Enable", st)
                
        # Handle chart display
        chart_path = chat.get_chart_image_path()
        if chart_path and os.path.exists(chart_path):
            if "chart_to_display" not in st.session_state:
                st.session_state.chart_to_display = []
            st.session_state.chart_to_display.append(chart_path)
            chat.clear_chart_image_path()
        
        return response
        
    except Exception as e:
        logger.error(f"Error: {str(e)}\n{traceback.format_exc()}")
        return """
        <div style="background-color: #ffebee; border: 1px solid #f44336; border-radius: 8px; padding: 15px;">
            <h4 style="color: #d32f2f; margin: 0 0 10px 0;">⚠️ Processing Error</h4>
            <p style="margin: 0; color: #666;">
                I encountered an issue. Please try again or rephrase your question.
            </p>
        </div>
        """

def validate_user_input(user_input: str) -> Tuple[bool, str]:
    """Validate user input for basic requirements."""
    if not user_input or not user_input.strip():
        return False, "Please enter a question or request."
    
    if len(user_input.strip()) > MAX_INPUT_LENGTH:
        return False, f"Input too long. Limit to {MAX_INPUT_LENGTH} characters."
    
    suspicious_patterns = ['<script', 'javascript:', 'eval(', 'exec(']
    if any(pattern in user_input.lower() for pattern in suspicious_patterns):
        return False, "Input contains potentially harmful content."
    
    return True, ""

def handle_chat_interaction() -> None:
    """Handle the main chat interaction flow."""
    # Process pending prompt
    if st.session_state.pending_prompt:
        user_prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        
        # Validate input
        is_valid, error_message = validate_user_input(user_prompt)
        if not is_valid:
            st.error(error_message)
            st.session_state.is_processing = False
            return
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_prompt)
        
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        
        # Generate response
        try:
            response = process_user_input(user_prompt)
        except Exception as e:
            logger.error(f"Chat error: {e}")
            response = """
            <div style="background-color: #ffebee; border: 1px solid #f44336; border-radius: 8px; padding: 15px;">
                <h4 style="color: #d32f2f; margin: 0 0 10px 0;">⚠️ System Error</h4>
                <p style="margin: 0; color: #666;">An unexpected error occurred. Please try again.</p>
            </div>
            """
        finally:
            st.session_state.is_processing = False
        
        # Handle chart display
        chart_path = None
        if "chart_to_display" in st.session_state and st.session_state.chart_to_display:
            chart_path = st.session_state.chart_to_display.pop(0)
        
        message_data = {"role": "assistant", "content": response}
        if chart_path:
            message_data["chart_path"] = chart_path
        
        st.session_state.messages.append(message_data)
        st.rerun()
        return
    
    # Handle example query or chat input
    user_prompt = st.session_state.example_query if st.session_state.example_query else None
    if st.session_state.example_query:
        st.session_state.example_query = ""
    
    if not user_prompt:
        user_prompt = st.chat_input(
            "💬 Ask about portfolios, market trends, or client meetings...",
            key="chat_input",
            disabled=st.session_state.get("is_processing", False)
        )
    
    if user_prompt:
        st.session_state.pending_prompt = user_prompt
        st.session_state.is_processing = True
        st.rerun()

# ============================================================================
# MAIN APPLICATION EXECUTION
# ============================================================================
handle_chat_interaction()