import streamlit as st
import json
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
Always provide the appointment id so that I can update it if required"""

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
    )

# Keep track of the number of previous messages in the agent flow
if "start_index" not in st.session_state:
    st.session_state.start_index = 0

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.empty()  # This forces the container to render without adding visible content (workaround for streamlit bug)
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
    
    # Get response from agent
    with st.spinner("Thinking..."):
        response = st.session_state.agent(prompt)
    
    # Extract the assistant's response text
    assistant_response = ""
    for m in st.session_state.agent.messages:
        if m.get("role") == "assistant" and m.get("content"):
            for content_item in m.get("content", []):
                if "text" in content_item:
                    # We keep only the last response of the assistant
                    assistant_response = content_item["text"]
                    break
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    
    # Display assistant response
    with st.chat_message("assistant"):
        
        start_index = st.session_state.start_index      

        # Display last messages from agent, with tool usage detail if any
        st.session_state.details_placeholder = st.empty()  # Create a new placeholder
        with st.session_state.details_placeholder.container():
            for m in st.session_state.agent.messages[start_index:]:
                if m.get("role") == "assistant":
                    for content_item in m.get("content", []):
                        if "text" in content_item:
                            st.write(content_item["text"])
                        elif "toolUse" in content_item:
                            tool_use = content_item["toolUse"]
                            tool_name = tool_use.get("name", "")
                            tool_input = tool_use.get("input", {})
                            st.info(f"Using tool: {tool_name}")
                            st.code(json.dumps(tool_input, indent=2))
            
                elif m.get("role") == "user":
                    for content_item in m.get("content", []):
                        if "toolResult" in content_item:
                            tool_result = content_item["toolResult"]
                            st.info(f"Tool Result: {tool_result.get('status', '')}")
                            for result_content in tool_result.get("content", []):
                                if "text" in result_content:
                                    st.code(result_content["text"])

        # Update the number of previous messages
        st.session_state.start_index = len(st.session_state.agent.messages)
    

