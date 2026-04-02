import logging
from requests_oauthlib import OAuth2Session
from urllib.parse import urlparse, parse_qs
import argparse
import json
from time import time
import colors

AUTHORIZATION_BASE_URL = "https://api.digikey.com/v1/oauth2/authorize"
TOKEN_URL = "https://api.digikey.com/v1/oauth2/token"
REDIRECT_URI = "https://localhost:8000/oauth2/callback"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_auth_code(client_id: str, client_secret: str) -> str:
    """Get authorization code from Digi-Key

    Args:
        client_id (str): Digikey Client ID
        client_secret (str): Digikey Client Secret
    Returns:
        str: Authorization code
    """
    try:
        digikey = OAuth2Session(client_id, redirect_uri=REDIRECT_URI)
        authorization_url, _ = digikey.authorization_url(AUTHORIZATION_BASE_URL)
        
        colors.print_info("Please copy and paste URL to your browser. Make sure you have logged in Digikey:")
        print(f"  {colors.Colors.CYAN}{authorization_url}{colors.Colors.RESET}")
        redirect_response = input(colors.question("Please copy and paste the redirect URL here: "))
        
        # Parse authorization code from redirect URL
        parsed = urlparse(redirect_response)
        query_params = parse_qs(parsed.query)
        return query_params['code'][0]
    
    except Exception as e:
        colors.print_error(f"Error getting authorization code: {str(e)}")
        raise

def get_access_token(auth_code: str, client_id: str, client_secret: str) -> tuple[str, str, int, int]:
    """Get access token and refresh token from Digi-Key
    
    Args:
        auth_code (str): Authorization code
        client_id (str): Digikey Client ID
        client_secret (str): Digikey Client Secret
    
    Returns:
        tuple: a tuple contains:
            access_token (str): access token
            refresh_token (str): refresh token
            expires_in (int): access token expires in seconds
            refresh_token_expires_in (int): refresh token expires in seconds
    """
    try:
        digikey = OAuth2Session(client_id, redirect_uri=REDIRECT_URI)
        token = digikey.fetch_token(
            TOKEN_URL,
            client_secret=client_secret,
            code=auth_code,
            include_client_id=True
        )
        return token['access_token'], token['refresh_token'], token['expires_in'], token['refresh_token_expires_in']
    
    except Exception as e:
        colors.print_error(f"Error getting access token: {str(e)}")
        raise

def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> tuple[str, str, int, int]:
    """Refresh access token using refresh token

    Args:
        client_id (str): Digikey Client ID
        client_secret (str): Digikey Client Secret
        refresh_token (str): Refresh token 
    
    Returns:
        tuple: a tuple contains:
            access_token (str): access token
            refresh_token (str): refresh token
            expires_in (int): access token expires in seconds
            refresh_token_expires_in (int): refresh token expires in seconds
    """
    try:
        digikey = OAuth2Session(client_id)
        token = digikey.refresh_token(
            TOKEN_URL,
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token
        )
        return token['access_token'], token['refresh_token'], token['expires_in'], token['refresh_token_expires_in']
    
    except Exception as e:
        colors.print_error(f"Error refreshing access token: {str(e)}")
        raise

# Command line interface
# Get access token and save it to .token (default output)
# translate expire in seconds to expire by in seconds
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Request a new Digikey access token and output to .token file')
    parser.add_argument('--user', '-u', type=str, required=True, help='Digikey Client ID')
    parser.add_argument('--secret', '-s', type=str, required=True, help='Digikey Client Secret')
    parser.add_argument('--output', '-o', type=str, default='.token', help='Token Output FileName')

    args = parser.parse_args()
    client_id = args.user
    client_secret = args.secret
    output = args.output
    
    # # Get authorization code
    colors.print_header("DigiKey Authentication")
    auth_code = get_auth_code(client_id, client_secret)
    colors.print_success(f"Authorization code received: {colors.highlight(auth_code[:20] + '...')}")
    
    # # Get access tokens
    access_token, refresh_token, expires_in, refresh_token_expires_in = get_access_token(auth_code, client_id, client_secret)
    colors.print_success(f"Access token request done! Writing tokens to {colors.highlight(output)}")
    print(f"  {colors.Colors.DIM}access_token={colors.Colors.RESET}{colors.Colors.GREEN}{access_token[:20]}...{colors.Colors.RESET}")
    print(f"  {colors.Colors.DIM}refresh_token={colors.Colors.RESET}{colors.Colors.GREEN}{refresh_token[:20]}...{colors.Colors.RESET}")
    print(f"  {colors.Colors.DIM}expires_in={colors.Colors.RESET}{colors.Colors.CYAN}{expires_in}{colors.Colors.RESET}")
    print(f"  {colors.Colors.DIM}refresh_token_expires_in={colors.Colors.RESET}{colors.Colors.CYAN}{refresh_token_expires_in}{colors.Colors.RESET}")

    time_now = int(time()) 
    tokens = {
        'client_id': client_id,
        'client_secret': client_secret,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_by': expires_in + time_now,
        'refresh_token_expires_by': refresh_token_expires_in + time_now
    }
    with open(output, 'w') as file:
        json.dump(tokens, file)