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
import os
import boto3
import json
import sys

lambda_client = boto3.client('lambda')

def lambda_handler(event, context):

    #connection id of the websocket
    connection_id = event['requestContext']['connectionId']
    #jwt from the user 
    id_token = event['requestContext']['authorizer']['id_token']
    payload = {}
    if 'body' in event:
        payload = json.loads(event['body'])
    
    route_key = event['requestContext']['routeKey']

        
    status_code = 500

    #do nothing on connect. Connection has already been AuthN by the Lambda
    if route_key == "$connect":
        
        status_code = 200

    #all inbound messages from websocket
    elif route_key == "$default":
       
        if 'human_message' in payload:
            
            #invoke the agent lambda asynchronously
            lambda_client.invoke(
                FunctionName = os.environ['AGENT_LAMBDA_ARN'],
                InvocationType = 'Event',
                Payload = json.dumps({
                    'connection_id': connection_id,
                    'id_token': id_token,
                    'body': payload
                })
            )
            status_code = 200

    #final clean up on disconnect
    elif route_key == "$disconnect":
        status_code = 200
        
    else:
        status_code = 404
      
    return {
        'statusCode': status_code
    }