import sys
import os
from aws_cdk import (
    # Duration,
    Stack,
    Fn,
    aws_ec2 as ec2,
    aws_secretsmanager as secretsmanager,
    aws_rds as rds
)
from constructs import Construct


from smart_building_analytics_agent.cognito import CognitoStack
from smart_building_analytics_agent.agent_api import AgentApiStack
from smart_building_analytics_agent.webapp import WebAppStack
from smart_building_analytics_agent.agent_main import AgentStack
from smart_building_analytics_agent.tool_api import ToolApiStack

class BaseAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

      
        # Create Cognito stack
        cognito_stack = CognitoStack(self, "CognitoStack")
        
        agent_main_function_name = Stack.of(self).stack_name + "-MainFunction"
        
        # Create API stack
        agent_api_stack = AgentApiStack(self, "ApiStack", 
                                            cognito_stack.user_pool_id, 
                                            cognito_stack.user_pool_client_id,
                                            agent_main_function_name
                                        )
        
        # Add dependency
        agent_api_stack.add_dependency(cognito_stack)
        
        # Create Tool API stack
        tool_api_stack = ToolApiStack(self, "ToolApiStack", 
                                            cognito_stack.user_pool_id, 
                                            cognito_stack.user_pool_client_id
                                        )
        
        # Create Agent Main stack
        agent_main_stack = AgentStack(self, "MainStack",
                                    websocket_api = agent_api_stack.websocket_api,
                                    agent_main_function_name = agent_main_function_name,
                                    tool_api_endpoint = tool_api_stack.api_endpoint
                                )

        agent_main_stack.add_dependency(tool_api_stack)

        # Create WebApp stack with the necessary parameters
        webapp_stack = WebAppStack(self, "WebAppStack", 
                                  webapp_dir="code/webapp/",
                                  cognito_user_pool_client_id=cognito_stack.user_pool_client_id,
                                  websocket_api=agent_api_stack.websocket_api)
