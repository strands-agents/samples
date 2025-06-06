'''
MIT No Attribution

Copyright 2024 Amazon Web Services

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

'''
from __future__ import print_function
import os
import boto3
import json
import urllib3
import string
import random

SUCCESS = "SUCCESS"
FAILED = "FAILED"
CUSTOM_RESOURCE_PHYSICAL_ID = 'CloudEnvBootstrapPhysicalID'

http = urllib3.PoolManager()



# Source code from https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-lambda-function-code-cfnresponsemodule.html#cfn-lambda-function-code-cfnresponsemodule-source
def cfnresponse_send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False, reason=None):
    responseUrl = event['ResponseURL']

    print(responseUrl)

    responseBody = {
        'Status' : responseStatus,
        'Reason' : reason or "See the details in CloudWatch Log Stream: {}".format(context.log_stream_name),
        'PhysicalResourceId' : physicalResourceId or context.log_stream_name,
        'StackId' : event['StackId'],
        'RequestId' : event['RequestId'],
        'LogicalResourceId' : event['LogicalResourceId'],
        'NoEcho' : noEcho,
        'Data' : responseData
    }

    json_responseBody = json.dumps(responseBody)

    print("Response body:")
    print(json_responseBody)

    headers = {
        'content-type' : '',
        'content-length' : str(len(json_responseBody))
    }

    try:
        response = http.request('PUT', responseUrl, headers=headers, body=json_responseBody)
        print("Status code:", response.status)


    except Exception as e:

        print("send(..) failed executing http.request(..):", e)

#create initial admin user
def create_cognito_user(user_pool_id, username, password, email, name):
    client = boto3.client('cognito-idp')

    try:
        # Create the user
        client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'name', 'Value': name}
            ],
            MessageAction='SUPPRESS'
        )

        # Set the user's password
        client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,
            Password=password,
            Permanent=True
        )

        print(f"User {username} created successfully with the specified password.")
    except client.exceptions.UsernameExistsException:
        print(f"User {username} already exists.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def generate_random_password(length = 10):
    # Define the character sets
    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    digits = string.digits
    special = '!%&'

    # Ensure at least one character from each set is included
    password = [random.choice(upper), random.choice(lower), random.choice(digits), random.choice(special)]

    # Fill the rest of the password length with a mix of all characters
    all_characters = upper + lower + digits + special
    password += random.choices(all_characters, k=length-4)

    # Shuffle the resulting password list to ensure randomness
    random.shuffle(password)

    return ''.join(password)


def lambda_handler(event, context):
    print(f'event: {json.dumps(event)}')

    if event['RequestType'] == 'Create':
        print('Processing create request')

        response_data = {'Success': 'Created user'}
        user_pool_id = os.environ['USER_POOL_ID']
        webapp_username = 'admin@example.com'
        webapp_password = generate_random_password()
        create_cognito_user(user_pool_id, webapp_username, webapp_password, 'admin@example.com', 'Admin')
        response_data['Username'] = webapp_username
        response_data['Password'] = webapp_password
        cfnresponse_send(event, context, SUCCESS, response_data, CUSTOM_RESOURCE_PHYSICAL_ID)
        
   
    else:
        cfnresponse_send(event, context, SUCCESS, {}, CUSTOM_RESOURCE_PHYSICAL_ID)