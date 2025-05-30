import json
import boto3
from datetime import datetime

cloudformation = boto3.client('cloudformation')
dynamodb_resource = boto3.resource('dynamodb')

def create_base_infrastructure(solution_id):
    # Read the YAML template file
    with open('utils/base-infra.yaml', 'r') as f:
        template_body = f.read()

    # Define the stack parameters
    stack_parameters = [
        {
            'ParameterKey': 'SolutionId',
            'ParameterValue': solution_id
        }
    ]

    # Create the CloudFormation stack
    stack_name = solution_id
    response = cloudformation.create_stack(
        StackName=stack_name,
        TemplateBody=template_body,
        Parameters=stack_parameters,
        Capabilities=['CAPABILITY_NAMED_IAM']  # Required if your template creates IAM resources
    )

    stack_id = response['StackId']
    print(f'Creating stack {stack_name} ({stack_id})')

    # Wait for the stack to be created
    waiter = cloudformation.get_waiter('stack_create_complete')
    waiter.wait(StackName=stack_id)

    # Get the stack outputs
    stack_outputs = cloudformation.describe_stacks(StackName=stack_id)['Stacks'][0]['Outputs']

    # Extract the output values into variables
    dynamo_table = next((output['OutputValue'] for output in stack_outputs if output['OutputKey'] == 'DynamoDBTableName'), None)
    sns_topic = next((output['OutputValue'] for output in stack_outputs if output['OutputKey'] == 'SNSTopicArn'), None)

    print('Stack outputs:')
    print(f'DynamoDB Table: {dynamo_table}')
    print(f'SNS Topic Arn: {sns_topic}')
   
    return dynamo_table, sns_topic


def create_onboarding_record(table_name: str, employee_id: str) -> str:
    """
    Create a new onboarding record in a DynamoDB table for an employee.

    Args:
        table_name (str): The name of the DynamoDB table.
        employee_id (str): The ID of the employee.

    Returns:
        str: Success or error message.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    # Default onboarding steps (3 only)
    onboarding_steps = {
        'form_submission': False,
        'benefits_enrollment': False,
        'security_training': False,
        'approval_status': 'pending'
    }

    item = {'employee_id': employee_id, **onboarding_steps}

    try:
        table.put_item(Item=item)
        return f"✅ Onboarding record created for employee ID '{employee_id}' with default steps."
    except Exception as e:
        return f"❌ Failed to create onboarding record for '{employee_id}': {e}"
