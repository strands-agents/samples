#!/usr/bin/env python3
import os
import sys
import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks, NagSuppressions
from aws_cdk import Aspects


from smart_building_analytics_agent.smart_building_analytics_agent_stack import BaseAgentStack


app = cdk.App()
stack = BaseAgentStack(app, "BIAgent",
                    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
                 )



# Add CDK-nag to check for best practices AFTER adding suppressions
#Aspects.of(app).add(AwsSolutionsChecks(verbose=True))

app.synth()
