import boto3
import json
from streamlit_cognito_auth import CognitoAuthenticator

class Auth:

    @staticmethod
    def get_authenticator(secret_id, region):
        """
        Get Cognito parameters from Secrets Manager and
        returns a CognitoAuthenticator object.
        """
        # Get Cognito parameters from Secrets Manager
        secretsmanager_client = boto3.client(
            "secretsmanager",
            region_name=region
        )
        response = secretsmanager_client.get_secret_value(
            SecretId=secret_id,
        )
        secret_string = json.loads(response['SecretString'])
        pool_id = secret_string['pool_id']
        app_client_id = secret_string['app_client_id']
        app_client_secret = secret_string['app_client_secret']

        # Initialise CognitoAuthenticator
        authenticator = CognitoAuthenticator(
            pool_id=pool_id,
            app_client_id=app_client_id,
            app_client_secret=app_client_secret,
        )

        return authenticator
