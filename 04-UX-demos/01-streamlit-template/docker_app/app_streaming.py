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

    # Prepare containers for response
    with st.chat_message("assistant"):
        st.session_state.details_placeholder = st.empty()  # Create a new placeholder
    
    # Initialize strings to store streaming of model output
    st.session_state.output = []

    # Create the callback handler to display streaming responses
    def custom_callback_handler(**kwargs):
        def add_to_output(output_type, content, append = True):
            if len(st.session_state.output) == 0:
                st.session_state.output.append({"type": output_type, "content": content})
            else:
                last_item = st.session_state.output[-1]
                if last_item["type"] == output_type:
                    if append:
                        st.session_state.output[-1]["content"] += content
                    else:
                        st.session_state.output[-1]["content"] = content
                else:
                    st.session_state.output.append({"type": output_type, "content": content})

        with st.session_state.details_placeholder.container():
            current_streaming_tool_use = ""
            # Process stream data
            if "data" in kwargs:
                add_to_output("data", kwargs["data"])
            elif "current_tool_use" in kwargs and kwargs["current_tool_use"].get("name"):
                tool_use_id = kwargs["current_tool_use"].get("toolUseId")
                current_streaming_tool_use = "Using tool: " + kwargs["current_tool_use"]["name"] + " with args: " + str(kwargs["current_tool_use"]["input"])
                add_to_output("tool_use", current_streaming_tool_use, append = False)
            elif "reasoningText" in kwargs:
                add_to_output("reasoning", kwargs["reasoningText"])

            # Display output
            for output_item in st.session_state.output:
                if output_item["type"] == "data":
                    st.markdown(output_item["content"])
                elif output_item["type"] == "tool_use":
                    st.code(output_item["content"])
                elif output_item["type"] == "reasoning":
                    st.markdown(output_item["content"])
    
    # Set callback handler into the agent
    st.session_state.agent.callback_handler = custom_callback_handler
    
    # Get response from agent
    response = st.session_state.agent(prompt)

    # When done, add assistant messages to chat history
    for output_item in st.session_state.output:
            st.session_state.messages.append({"role": "assistant", "type": output_item["type"] , "content": output_item["content"]})
