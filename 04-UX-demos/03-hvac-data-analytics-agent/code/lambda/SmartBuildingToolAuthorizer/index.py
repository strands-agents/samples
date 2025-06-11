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

from jose import jwt
import requests
from jose import jwk
import json
import time
import boto3
import os


REGION = os.environ.get('AWS_REGION', '')
USER_POOL_ID = os.environ.get('USER_POOL_ID', '')
CLIENT_ID = os.environ.get('CLIENT_ID', '') 
    

def get_cognito_public_keys(region, user_pool_id):
    """Fetch public keys from Cognito"""
    
    keys_url = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json'
    try:
        response = requests.get(keys_url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()['keys']
    except Exception as e:
        raise Exception(f"Failed to fetch public keys: {str(e)}")

def get_public_key(token, region, user_pool_id):
    """Get the public key that matches the token's key ID"""
    # Get the key ID from the token header
    headers = jwt.get_unverified_header(token)
    kid = headers['kid']
    
    # Find the matching public key
    keys = get_cognito_public_keys(region, user_pool_id)
    key = next((k for k in keys if k['kid'] == kid), None)
    if not key:
        raise Exception('Public key not found')
    
    print(key)
    # Convert the public key to PEM format
    return json.dumps(key)

def verify_token(token, region, user_pool_id, client_id):
    """Verify the JWT token"""
    try:
        # Get the public key
        public_key = get_public_key(token, region, user_pool_id)
        
        # Decode and verify the token
        claims = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            options={
                'verify_exp': True,  # Verify expiration
                'verify_aud': True,  # Verify audience claim
                'verify_iss': True   # Verify issuer claim
            },
            audience=client_id,
            issuer=f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}'
        )
        
        return {
            'isValid': True,
            'claims': claims
        }
        
    
    except Exception as e:
        print(e)
        return {
            'isValid': False,
            'error': str(e)
        }

def generatePolicy(principalId, effect, resource, id_token):
    authResponse = {}
    authResponse['principalId'] = principalId
    if (effect and resource):
        policyDocument = {}
        policyDocument['Version'] = '2012-10-17'
        policyDocument['Statement'] = []
        statementOne = {}
        statementOne['Action'] = 'execute-api:Invoke'
        statementOne['Effect'] = effect
        statementOne['Resource'] = resource
        policyDocument['Statement'] = [statementOne]
        authResponse['policyDocument'] = policyDocument

    authResponse['context'] = {
        "id_token": id_token
    }

    return authResponse


def generateAllow(principalId, resource, id_token):
    return generatePolicy(principalId, 'Allow', resource, id_token)


def generateDeny(principalId, resource):
    return generatePolicy(principalId, 'Deny', resource, "")


def lambda_handler(event, context):
    
    id_token = ""
    if 'headers' in event and 'id_token' in event['headers']:
        id_token = event['headers']['id_token']
    else:
        response = generateDeny('me', event['routeArn'])
        print("No JWT token provided")
        return response

    try:
        # Verify the token
        result = verify_token(id_token, REGION, USER_POOL_ID, CLIENT_ID)
        
        if result['isValid']:
            response = generateAllow('me', event['routeArn'], id_token)
            return response
            
    except Exception as e:
        print(e)

    response = generateDeny('me', event['routeArn'])
    return response
  