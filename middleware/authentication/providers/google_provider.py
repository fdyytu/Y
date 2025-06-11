"""
Google OAuth 2.0 authentication provider implementation.
Mengimplementasikan Google OAuth 2.0 flow.
"""
from typing import Optional, Dict, Any, List
import httpx
import jwt
import json
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class GoogleProvider:
    """
    Google OAuth 2.0 Provider.
    Mengimplementasikan Google OAuth 2.0 authentication flow.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Google provider.
        
        Args:
            config: Configuration dictionary berisi:
                - client_id: Google OAuth client ID
                - client_secret: Google OAuth client secret
                - scope: List of OAuth scopes
                - redirect_uri: Redirect URI
        """
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.scope = config.get('scope', ['openid', 'email', 'profile'])
        self.redirect_uri = config.get('redirect_uri')
        
        # Google OAuth URLs
        self.auth_url = 'https://accounts.google.com/o/oauth2/auth'
        self.token_url = 'https://oauth2.googleapis.com/token'
        self.user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        self.revoke_url = 'https://oauth2.googleapis.com/revoke'
        self.certs_url = 'https://www.googleapis.com/oauth2/v1/certs'
        
        # Validate required config
        if not all([self.client_id, self.client_secret]):
            raise ValueError("Google provider requires client_id and client_secret")
    
    def get_authorization_url(self, redirect_uri: str = None, state: str = None) -> str:
        """
        Generate authorization URL untuk Google OAuth flow.
        
        Args:
            redirect_uri: Redirect URI (optional, uses config default)
            state: State parameter untuk security
            
        Returns:
            Authorization URL
        """
        redirect_uri = redirect_uri or self.redirect_uri
        if not redirect_uri:
            raise ValueError("Redirect URI is required")
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.scope),
            'access_type': 'offline',  # To get refresh token
            'prompt': 'consent'  # Force consent screen untuk refresh token
        }
        
        if state:
            params['state'] = state
        
        return f"{self.auth_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str = None) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code untuk access token.
        
        Args:
            code: Authorization code dari Google
            redirect_uri: Redirect URI yang digunakan
            
        Returns:
            Token data atau None jika gagal
        """
        redirect_uri = redirect_uri or self.redirect_uri
        if not redirect_uri:
            raise ValueError("Redirect URI is required")
        
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data=data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                if response.status_code != 200:
                    logger.error(f"Google token exchange failed: {response.status_code} - {response.text}")
                    return None
                
                token_data = response.json()
                
                # Decode ID token jika ada
                id_token = token_data.get('id_token')
                if id_token:
                    user_info = await self._decode_id_token(id_token)
                    if user_info:
                        token_data['user_info'] = user_info
                
                return token_data
                
        except Exception as e:
            logger.error(f"Google token exchange error: {e}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information dari Google API.
        
        Args:
            access_token: Google access token
            
        Returns:
            User information atau None jika gagal
        """
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.user_info_url, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"Google user info failed: {response.status_code} - {response.text}")
                    return None
                
                user_data = response.json()
                
                # Normalize user info
                user_info = {
                    'id': user_data.get('id'),
                    'username': user_data.get('email', '').split('@')[0],
                    'email': user_data.get('email'),
                    'name': user_data.get('name'),
                    'first_name': user_data.get('given_name'),
                    'last_name': user_data.get('family_name'),
                    'picture_url': user_data.get('picture'),
                    'verified_email': user_data.get('verified_email', False),
                    'locale': user_data.get('locale'),
                    'provider': 'google',
                    'provider_id': user_data.get('id')
                }
                
                return user_info
                
        except Exception as e:
            logger.error(f"Google get user info error: {e}")
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh access token menggunakan refresh token.
        
        Args:
            refresh_token: Google refresh token
            
        Returns:
            New token data atau None jika gagal
        """
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data=data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                if response.status_code != 200:
                    logger.error(f"Google token refresh failed: {response.status_code} - {response.text}")
                    return None
                
                token_data = response.json()
                
                # Add refresh token back (Google doesn't return it in refresh response)
                token_data['refresh_token'] = refresh_token
                
                return token_data
                
        except Exception as e:
            logger.error(f"Google token refresh error: {e}")
            return None
    
    async def revoke_token(self, token: str) -> bool:
        """
        Revoke Google access atau refresh token.
        
        Args:
            token: Access token atau refresh token
            
        Returns:
            True jika berhasil
        """
        try:
            params = {'token': token}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.revoke_url, params=params)
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Google token revoke error: {e}")
            return False
    
    async def validate_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate Google access token.
        
        Args:
            access_token: Access token to validate
            
        Returns:
            Token info atau None jika invalid
        """
        try:
            # Use tokeninfo endpoint untuk validation
            url = f'https://oauth2.googleapis.com/tokeninfo?access_token={access_token}'
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    logger.error(f"Google token validation failed: {response.status_code}")
                    return None
                
                token_info = response.json()
                
                # Check if token is for our client
                if token_info.get('aud') != self.client_id:
                    logger.warning("Google token audience mismatch")
                    return None
                
                return token_info
                
        except Exception as e:
            logger.error(f"Google token validation error: {e}")
            return None
    
    async def _decode_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """
        Decode dan validate Google ID token.
        
        Args:
            id_token: Google ID token
            
        Returns:
            User info dari ID token
        """
        try:
            # Get Google public keys
            google_certs = await self._get_google_certs()
            if not google_certs:
                logger.error("Failed to get Google certificates")
                return None
            
            # Decode header untuk mendapatkan key ID
            header = jwt.get_unverified_header(id_token)
            kid = header.get('kid')
            
            if not kid or kid not in google_certs:
                logger.error(f"Google key ID {kid} not found in certificates")
                return None
            
            # Get public key
            public_key = google_certs[kid]
            
            # Decode dan verify token
            payload = jwt.decode(
                id_token,
                public_key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer='https://accounts.google.com'
            )
            
            # Extract user info
            user_info = {
                'id': payload.get('sub'),
                'email': payload.get('email'),
                'email_verified': payload.get('email_verified', False),
                'name': payload.get('name'),
                'first_name': payload.get('given_name'),
                'last_name': payload.get('family_name'),
                'picture_url': payload.get('picture'),
                'locale': payload.get('locale'),
                'provider': 'google',
                'provider_id': payload.get('sub')
            }
            
            return user_info
            
        except jwt.ExpiredSignatureError:
            logger.error("Google ID token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"Google ID token invalid: {e}")
            return None
        except Exception as e:
            logger.error(f"Google ID token decode error: {e}")
            return None
    
    async def _get_google_certs(self) -> Optional[Dict[str, Any]]:
        """
        Get Google public certificates untuk JWT verification.
        
        Returns:
            Dictionary mapping key ID ke public key
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.certs_url)
                
                if response.status_code != 200:
                    logger.error(f"Failed to get Google certificates: {response.status_code}")
                    return None
                
                certs_data = response.json()
                certs = {}
                
                for kid, cert_pem in certs_data.items():
                    # Convert PEM certificate ke public key
                    from cryptography import x509
                    from cryptography.hazmat.backends import default_backend
                    
                    cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())
                    public_key = cert.public_key()
                    certs[kid] = public_key
                
                return certs
                
        except Exception as e:
            logger.error(f"Error getting Google certificates: {e}")
            return None
    
    async def get_user_profile(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed user profile dari Google People API.
        
        Args:
            access_token: Google access token dengan people scope
            
        Returns:
            Detailed user profile atau None jika gagal
        """
        try:
            url = 'https://people.googleapis.com/v1/people/me'
            params = {
                'personFields': 'names,emailAddresses,photos,phoneNumbers,addresses,birthdays'
            }
            headers = {'Authorization': f'Bearer {access_token}'}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"Google People API failed: {response.status_code}")
                    return None
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Google People API error: {e}")
            return None
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            'name': 'Google',
            'type': 'oauth2',
            'auth_url': self.auth_url,
            'token_url': self.token_url,
            'user_info_url': self.user_info_url,
            'scopes': self.scope,
            'supports_refresh': True,
            'supports_revoke': True,
            'supports_id_token': True,
            'supports_people_api': True
        }
