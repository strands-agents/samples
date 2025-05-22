from strands import Agent, tool
from nova_act import NovaAct

@tool
def browser_automation_tool(starting_url:str, instr: str) -> str:
    """
    With starting url, automates tasks in browser based on instructions provided. Can run multiple sessions in parallel. 
    The tool can do some reasoning of its own but can sometimes not give good results when you ask complex tasks. 

    Args:
        starting_url (str): The website url to perform actions on
        instr (str): the instruction in natural language to be sent to the browser for the task to be performed

    Returns:
        str: The result of the action performed. 
    """
    # Create a unique user data directory for each session
    user_data_dir = "./tmp/user-data-dir"
    
    with NovaAct(
        starting_page=starting_url, 
        #user_data_dir=user_data_dir, 
        #clone_user_data_dir=False 
    ) as browser:
        try:
            result = browser.act(instr, max_steps=10)
            return result.response
                
        except Exception as e:
            error_msg = f"Error processing instruction: {instr}. Error: {str(e)}"
            print(error_msg)
            return error_msg


