#!/usr/bin/env python3
import os
import sys
import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks, NagSuppressions
from aws_cdk import Aspects


from smart_building_analytics_agent.smart_building_analytics_agent_stack import BaseAgentStack


app = cdk.App()
BaseAgentStack(app, "BaseAgentStack",
                    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
                 )

app.synth()
