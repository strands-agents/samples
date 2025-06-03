# Streamlit UI Demo of Strands Agents

## Getting Started  


1. Clone the repo locally  

    `git clone <path to repo>`

2. ensure that you have Python 3.10+ installed.

3. We'll create a **virtual environment**  

    `python -m venv .venv`

4. **Activate the virtual environment:**   
    -> macOS / Linux: `source .venv/bin/activate`   
    -> Windows (CMD): `.venv\Scripts\activate.bat`     
    -> Windows (PowerShell): `.venv\Scripts\Activate.ps1`  

5. **Install required Python packages**  

    `cd <into the download folder>`  

    `pip install -r requirements.txt`  

6. Open file config_file.py in editor of your choice, update the variables based on your local environment and save & close 

    `BEDROCK_REGION = AWS Region based on your deployment`

    `AMZ_BEDROCK_CLAUDE_MODEL_ID = <Claude model id>`  

    `AMZ_BEDROCK_NOVA_PRO_MODEL_ID = <Amazon Nova Pro model id>`  

    `AMZ_BEDROCK_NOVE_LITE_MODEL_ID = <Amazon Nova Lite model id>`  

    `AWS_PROFILE_NAME = 'default' AWS profile that has access to your AWS account and permissions to run model inference in Amazon Bedrock` 


7. **Go back to Terminal**  

    `streamlit run streamlit_app.py`