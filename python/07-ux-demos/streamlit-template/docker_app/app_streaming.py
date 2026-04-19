import asyncio
import streamlit as st
from utils.auth import Auth
from config_file import Config

from strands import Agent
from strands.models import BedrockModel

import tools.list_appointments
import tools.update_appointment
import tools.create_appointment
from strands_tools import calculator, current_time

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

# ID of Secrets Manager containing cognito parameters
secrets_manager_id = Config.SECRETS_MANAGER_ID

# ID of the AWS region in which Secrets Manager is deployed
region = Config.DEPLOYMENT_REGION

if Config.ENABLE_AUTH:
    # Initialise CognitoAuthenticator
    authenticator = Auth.get_authenticator(secrets_manager_id, region)

    # Authenticate user, and stop here if not logged in
    is_logged_in = authenticator.login()
    if not is_logged_in:
        st.stop()

    def logout():
        authenticator.logout()

    with st.sidebar:
        st.text(f"Welcome,\n{authenticator.get_username()}")
        st.button("Logout", "logout_btn", on_click=logout)

# Add title on the page
st.title("Streamlit Strands Demo")
st.write("This demo shows how to use Strands to create a personal assistant that can manage appointments and calendar. It also has a calculator tool.")

# Define agent
system_prompt = """You are a helpful personal assistant that specializes in managing my appointments and calendar. 
You have access to appointment management tools, a calculator, and can check the current time to help me organize my schedule effectively. 
Always provide the appointment id so that I can update it if required. Format your results in markdown when needed."""

model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    max_tokens=64000,
    additional_request_fields={
        "thinking": {
            "type": "disabled",
        }
    },
)

# Initialize the agent
if "agent" not in st.session_state:
    st.session_state.agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            current_time,
            calculator,
            tools.create_appointment,
            tools.list_appointments,
            tools.update_appointment,
        ],
        callback_handler=None
    )

# Display old chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.empty()  # This forces the container to render without adding visible content (workaround for streamlit bug)
        if message.get("type") == "tool_use":
            st.code(message["content"])
        else:
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask your agent..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Clear previous tool usage details
    if "details_placeholder" in st.session_state:
        st.session_state.details_placeholder.empty()
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)

    # Async function to process streaming response
    async def process_streaming_response(prompt):
        output_buffer = []
        
        # Create container for real-time display
        with st.chat_message("assistant"):
            container = st.container()
            spinner_placeholder = st.empty()
            
            current_text = ""
            text_placeholder = None
            current_tool_id = None
            first_content_received = False
            
            # Show spinner initially
            with spinner_placeholder:
                with st.spinner("Thinking..."):
                    # Stream events from agent
                    async for event in st.session_state.agent.stream_async(prompt):
                
                        # Handle tool usage - create new placeholder for each tool
                        if "current_tool_use" in event and event["current_tool_use"].get("name"):
                            current_text = ""
                            # Remove spinner on first content
                            if not first_content_received:
                                spinner_placeholder.empty()
                                first_content_received = True
                            
                            tool_use_id = event["current_tool_use"].get("toolUseId")
                            tool_name = event["current_tool_use"]["name"]
                            tool_input = event["current_tool_use"].get("input", {})
                            tool_text = f"Using tool: {tool_name} with args: {str(tool_input)}"
                            
                            # Check if this is a new tool (different toolUseId)
                            if tool_use_id != current_tool_id:
                                current_tool_id = tool_use_id
                                # Reset text placeholder when new tool starts
                                text_placeholder = None
                                
                                # Create new placeholder for this tool
                                with container:
                                    tool_placeholder = st.empty()
                                    tool_placeholder.code(tool_text)
                                
                                # Add to buffer as new entry
                                output_buffer.append({"type": "tool_use", "content": tool_text})
                            else:
                                # Update existing tool placeholder
                                tool_placeholder.code(tool_text)
                                
                                # Update buffer
                                if output_buffer and output_buffer[-1]["type"] == "tool_use":
                                    output_buffer[-1]["content"] = tool_text
                        
                        # Handle text data streaming
                        if "data" in event:
                            # Remove spinner on first content
                            if not first_content_received:
                                spinner_placeholder.empty()
                                first_content_received = True
                            
                            current_text += event["data"]
                            
                            # Create text placeholder if it doesn't exist or was reset
                            if text_placeholder is None:
                                with container:
                                    text_placeholder = st.empty()
                            
                            text_placeholder.markdown(current_text)
                            
                            # Add to buffer
                            if len(output_buffer) == 0 or output_buffer[-1]["type"] != "data":
                                output_buffer.append({"type": "data", "content": event["data"]})
                            else:
                                output_buffer[-1]["content"] += event["data"]
                        
                        # Handle reasoning text
                        if "reasoningText" in event:
                            reasoning_text = event["reasoningText"]
                            
                            # Add to buffer
                            if len(output_buffer) == 0 or output_buffer[-1]["type"] != "reasoning":
                                output_buffer.append({"type": "reasoning", "content": reasoning_text})
                            else:
                                output_buffer[-1]["content"] += reasoning_text
        
        return output_buffer

    # Run the async streaming function
    output_buffer = asyncio.run(process_streaming_response(prompt))

    # When done, add assistant messages to chat history
    for output_item in output_buffer:
            st.session_state.messages.append({"role": "assistant", "type": output_item["type"] , "content": output_item["content"]})
