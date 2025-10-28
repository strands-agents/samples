import jwt
from jwt import PyJWKClient
import requests
import os
from typing import Dict, Optional
from functools import lru_cache
import json
from .ssm_utils import load_config

# Load configuration from SSM
try:
    config = load_config()
except Exception as e:
    print(f"❌ Error loading config in cognito_utils: {e}")
    config = {}


@lru_cache(maxsize=10)
def get_jwks(region: str, user_pool_id: str) -> Dict:
    """
    Fetch and cache the JSON Web Key Set (JWKS) from Cognito.
    
    Args:
        region (str): AWS region where the Cognito User Pool is located
        user_pool_id (str): Cognito User Pool ID
    
    Returns:
        Dict: The JWKS containing public keys for token verification
    """
    jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    
    try:
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching JWKS: {str(e)}")
        raise Exception(f"Failed to fetch JWKS: {str(e)}")


def get_public_key(token_header: Dict, region: str, user_pool_id: str):
    """
    Get the public key for token verification based on the token header.
    
    Args:
        token_header (Dict): The JWT token header containing key ID
        region (str): AWS region where the Cognito User Pool is located
        user_pool_id (str): Cognito User Pool ID
        
    Returns:
        The public key for verification
    """
    jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    
    try:
        # Use PyJWKClient for better compatibility
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token_header.get('kid'))
        return signing_key.key
    except Exception as e:
        # Fallback to manual JWKS parsing
        jwks = get_jwks(region, user_pool_id)
        
        # Find the key that matches the token's key ID
        for key in jwks.get('keys', []):
            if key.get('kid') == token_header.get('kid'):
                try:
                    # Try different methods based on PyJWT version
                    if hasattr(jwt.algorithms, 'RSAAlgorithm'):
                        return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                    else:
                        # For older PyJWT versions, use jwt.algorithms.get_default_algorithms()
                        from cryptography.hazmat.primitives import serialization
                        from cryptography.hazmat.primitives.asymmetric import rsa
                        import base64
                        
                        # Extract RSA components
                        n = base64.urlsafe_b64decode(key['n'] + '==')
                        e = base64.urlsafe_b64decode(key['e'] + '==')
                        
                        # Convert to integers
                        n_int = int.from_bytes(n, 'big')
                        e_int = int.from_bytes(e, 'big')
                        
                        # Create RSA public key
                        public_numbers = rsa.RSAPublicNumbers(e_int, n_int)
                        public_key = public_numbers.public_key()
                        
                        return public_key
                except Exception as key_error:
                    print(f"❌ Error converting JWK to key: {key_error}")
                    continue
        
        raise Exception("Public key not found in JWKS")


def validate_cognito_token(token: str, region: str, user_pool_id: str) -> Optional[Dict]:
    """
    Validate a Cognito JWT token.
    
    Args:
        token (str): The JWT token to validate
        region (str): AWS region where the Cognito User Pool is located
        user_pool_id (str): Cognito User Pool ID
        
    Returns:
        Optional[Dict]: The decoded token payload if valid, None if invalid
    """
    try:
        # Use PyJWKClient for simpler token validation
        jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
        jwks_client = PyJWKClient(jwks_url)
        
        # Get the signing key from the token
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Verify and decode the token
        decoded_token = jwt.decode(
            token,
            signing_key.key,
            algorithms=['RS256'],
            audience=None,  # We'll validate audience separately if needed
            options={"verify_aud": False}  # Disable automatic audience verification
        )
        
        # Validate token type (should be 'id' for ID tokens or 'access' for access tokens)
        token_use = decoded_token.get('token_use')
        if token_use not in ['id', 'access']:
            raise Exception(f"Invalid token use: {token_use}")
        
        # Validate issuer
        expected_iss = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        if decoded_token.get('iss') != expected_iss:
            raise Exception("Invalid token issuer")
        
        print(f"✅ Token validated successfully for user: {decoded_token.get('username', 'unknown')}")
        return decoded_token
        
    except jwt.ExpiredSignatureError:
        print("❌ Token validation error: Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"❌ Token validation error: Invalid token: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Token validation error: {str(e)}")
        return None


def validate_cognito_token_with_config(token: str) -> Optional[Dict]:
    """
    Validate a Cognito token using SSM configuration.
    
    Args:
        token (str): The JWT token to validate
        
    Returns:
        Optional[Dict]: The decoded token payload if valid, None if invalid
    """
    try:
        region, user_pool_id = get_cognito_config_from_ssm()
        return validate_cognito_token(token, region, user_pool_id)
    except Exception as e:
        print(f"❌ Token validation error: {str(e)}")
        return None


def extract_bearer_token(authorization_header: str) -> Optional[str]:
    """
    Extract the bearer token from an Authorization header.
    
    Args:
        authorization_header (str): The Authorization header value
        
    Returns:
        Optional[str]: The extracted token, or None if not found
    """
    if not authorization_header:
        return None
    
    # Check if it starts with "Bearer "
    if authorization_header.startswith("Bearer "):
        return authorization_header[7:]  # Remove "Bearer " prefix
    
    return None


def get_cognito_config_from_ssm() -> tuple[str, str]:
    """
    Get Cognito configuration from SSM and environment variables.
    
    Returns:
        tuple[str, str]: A tuple containing (region, user_pool_id)
        
    Raises:
        Exception: If required configuration values are not set or are "N/A"
    """
    import os
    
    region = config.get('AWS_REGION')
    user_pool_id = os.environ.get('COGNITO_USER_POOL_ID', 'N/A')
    
    if not region or region == "N/A":
        raise Exception("AWS_REGION SSM parameter not set or is N/A")
    
    if not user_pool_id or user_pool_id == "N/A":
        raise Exception("COGNITO_USER_POOL_ID environment variable not set or is N/A")
    
    return region, user_pool_id
