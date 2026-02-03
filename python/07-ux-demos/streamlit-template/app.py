#!/usr/bin/env python3
import os

from aws_cdk import App, Environment

from cdk.cdk_stack import CdkStack
from docker_app.config_file import Config


app = App()
CdkStack(app, Config.STACK_NAME,
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html

    env=Environment(region=Config.DEPLOYMENT_REGION)
    )

app.synth()
