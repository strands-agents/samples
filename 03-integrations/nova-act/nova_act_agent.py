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

    with NovaAct(
        starting_page=starting_url
    ) as browser:
        try:
            result = browser.act(instr, max_steps=15)
            return result.response
                
        except Exception as e:
            error_msg = f"Error processing instruction: {instr}. Error: {str(e)}"
            print(error_msg)
            return error_msg


