from strands import Agent
import logging
from config_file import app_config
import streamlit as st
from strands.models import BedrockModel
from botocore.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 
sys_prompt=(
        "You are an AI assistant helping answer user questions as accurately as possible"
        "Always explain your reasoning and cite sources when possible. Ask questions to clarify understanding."
    )

# Create a BedrockModel with default values
bedrock_model = BedrockModel(
model_id=app_config.AMZ_BEDROCK_CLAUDE_MODEL_ID,
region_name=app_config.BEDROCK_REGION,
temperature=0.1,
top_p= 0.0,
profile_name='default' #AWS CLI profile to be used having access to Bedrock LLMs
)

# Create an agent with default settings
strand_agent = Agent(system_prompt = sys_prompt,model=bedrock_model)

# Async function that iterators over streamed agent events
async def process_streaming_response(prompt):
    try:
        async for event in strand_agent.stream_async(prompt):
            if "data" in event:
                # Only stream text chunks to the client
                yield event["data"]
                #st.write(event["data"])
    except Exception as e:
        yield f"Error: {str(e)}"

#Set page configuration
st.set_page_config(
    page_title="AI Assistant", 
    page_icon=":robot_face:",
    layout="wide",
    initial_sidebar_state="expanded"
)


#Initialize chat history in session state
if "history" not in st.session_state:
    #st.session_state["chat_history"] = []
    st.session_state.history = []


# Add title on the page
st.title("AI Assistant :sunglasses:")
st.subheader("🤖 Powered by Strands Agents", divider="rainbow")


# Model options mapping
model_options = {
    "Claude 3.7 Sonnet": app_config.AMZ_BEDROCK_CLAUDE_MODEL_ID, 
    "Amazon Nova Pro": app_config.AMZ_BEDROCK_NOVA_PRO_MODEL_ID,
    "Amazon Nova Lite": app_config.AMZ_BEDROCK_NOVE_LITE_MODEL_ID
}

#Update agent configuration based on UI changes
def update_agent():
    bedrock_model.update_config(
    temperature=st.session_state.temp,
    top_p=st.session_state.topP,
    model_id = model_options[st.session_state.select_model]
    )

#side bar UI
with st.sidebar:
     st.subheader("Configuration")
     st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.1, step=0.1,on_change=update_agent,key="temp")
     st.slider("Top P", min_value=0.0, max_value=1.0, value=0.0, step=0.1,on_change=update_agent,key="topP")
     st.sidebar.selectbox("Select LLM",list(model_options.keys()),on_change=update_agent,key="select_model")

     
#display chat history
for i, message in enumerate(st.session_state.history):
    with st.chat_message(message["role"]):
        st.write(message["content"])


#display initial prompt
prompt = st.chat_input("What would you like to ask AI Assistant today?")

if prompt:
    try:   
        # Display #user message
        with st.chat_message("user"):
            st.markdown(prompt)
            # Add user message to chat history
        st.session_state.history.append({"role": "user", "content": prompt})


    #Process user prompt and generate streaming output
        with st.spinner("Generating Output..."):
            response = ""
            with st.chat_message("assistant"):
                response = st.write_stream(process_streaming_response(prompt))

            st.session_state.history.append({"role": "assistant", "content": response})
    except Exception as e:
        st.write(f"Error: {str(e)}")