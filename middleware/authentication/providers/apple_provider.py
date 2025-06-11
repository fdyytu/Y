"""
Apple ID authentication provider implementation.
Mengimplementasikan Sign in with Apple OAuth 2.0 flow.
"""
from typing import Optional, Dict, Any, List
import httpx
import jwt
import json
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import logging

logger = logging.getLogger(__name__)


class AppleProvider:
    """
    Apple ID OAuth 2.0 Provider.
    Mengimplementasikan Sign in with Apple authentication flow.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Apple provider.
        
        Args:
            config: Configuration dictionary berisi:
                - client_id: Apple service ID
                - team_id: Apple team ID
                - key_id: Apple key ID
                - private_key: Apple private key (PEM format)
                - scope: List of scopes
                - redirect_uri: Redirect URI
        """
        self.client_id = config.get('client_id')
        self.team_id = config.get('team_id')
        self.key_id = config.get('key_id')
        self.private_key = config.get('private_key')
        self.scope = config.get('scope', ['name', 'email'])
        self.redirect_uri = config.get('redirect_uri')
        
        # Apple URLs
        self.auth_url = 'https://appleid.apple.com/auth/authorize'
        self.token_url = 'https://appleid.apple.com/auth/token'
        self.keys_url = 'https://appleid.apple.com/auth/keys'
        
        # Validate required config
        if not all([self.client_id, self.team_id, self.key_id, self.private_key]):
            raise ValueError("Apple provider requires client_id, team_id, key_id, and private_key")
        
        # Parse private key
        try:
            self.private_key_obj = serialization.load_pem_private_key(
                self.private_key.encode() if isinstance(self.private_key, str) else self.private_key,
                password=None
            )
        except Exception as e:
            raise ValueError(f"Invalid Apple private key: {e}")
    
    def get_authorization_url(self, redirect_uri: str = None, state: str = None) -> str:
        """
        Generate authorization URL untuk Apple OAuth flow.
        
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
            'response_mode': 'form_post'  # Apple recommends form_post
        }
        
        if state:
            params['state'] = state
        
        # Build URL
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_url}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str = None) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code untuk access token.
        
        Args:
            code: Authorization code dari Apple
            redirect_uri: Redirect URI yang digunakan
            
        Returns:
            Token data atau None jika gagal
        """
        redirect_uri = redirect_uri or self.redirect_uri
        if not redirect_uri:
            raise ValueError("Redirect URI is required")
        
        try:
            # Generate client secret (JWT)
            client_secret = self._generate_client_secret()
            
            # Prepare token request
            data = {
                'client_id': self.client_id,
                'client_secret': client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri
            }
            
            # Make token request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data=data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                if response.status_code != 200:
                    logger.error(f"Apple token exchange failed: {response.status_code} - {response.text}")
                    return None
                
                token_data = response.json()
                
                # Validate and decode ID token
                id_token = token_data.get('id_token')
                if id_token:
                    user_info = await self._decode_id_token(id_token)
                    if user_info:
                        token_data['user_info'] = user_info
                
                return token_data
                
        except Exception as e:
            logger.error(f"Apple token exchange error: {e}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information dari Apple.
        
        Note: Apple tidak menyediakan user info endpoint.
        User info didapat dari ID token saat token exchange.
        
        Args:
            access_token: Access token (atau ID token)
            
        Returns:
            User information atau None jika gagal
        """
        try:
            # Jika access_token adalah ID token, decode langsung
            if access_token.count('.') == 2:  # JWT format
                return await self._decode_id_token(access_token)
            
            # Jika bukan ID token, tidak bisa mendapatkan user info
            logger.warning("Apple provider: Cannot get user info from access token. Use ID token instead.")
            return None
            
        except Exception as e:
            logger.error(f"Apple get user info error: {e}")
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh access token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New token data atau None jika gagal
        """
        try:
            client_secret = self._generate_client_secret()
            
            data = {
                'client_id': self.client_id,
                'client_secret': client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data=data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                if response.status_code != 200:
                    logger.error(f"Apple token refresh failed: {response.status_code} - {response.text}")
                    return None
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Apple token refresh error: {e}")
            return None
    
    async def revoke_token(self, token: str, token_type: str = 'access_token') -> bool:
        """
        Revoke Apple token.
        
        Args:
            token: Token to revoke
            token_type: Type of token ('access_token' or 'refresh_token')
            
        Returns:
            True jika berhasil
        """
        try:
            client_secret = self._generate_client_secret()
            
            data = {
                'client_id': self.client_id,
                'client_secret': client_secret,
                'token': token,
                'token_type_hint': token_type
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://appleid.apple.com/auth/revoke',
                    data=data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Apple token revoke error: {e}")
            return False
    
    def _generate_client_secret(self) -> str:
        """
        Generate client secret JWT untuk Apple.
        
        Returns:
            Client secret JWT
        """
        now = datetime.utcnow()
        
        payload = {
            'iss': self.team_id,
            'iat': now,
            'exp': now + timedelta(minutes=5),  # Apple recommends 5 minutes max
            'aud': 'https://appleid.apple.com',
            'sub': self.client_id
        }
        
        headers = {
            'kid': self.key_id,
            'alg': 'ES256'
        }
        
        return jwt.encode(
            payload,
            self.private_key_obj,
            algorithm='ES256',
            headers=headers
        )
    
    async def _decode_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """
        Decode dan validate Apple ID token.
        
        Args:
            id_token: Apple ID token
            
        Returns:
            User info dari ID token
        """
        try:
            # Get Apple public keys
            apple_keys = await self._get_apple_public_keys()
            if not apple_keys:
                logger.error("Failed to get Apple public keys")
                return None
            
            # Decode header untuk mendapatkan key ID
            header = jwt.get_unverified_header(id_token)
            kid = header.get('kid')
            
            if not kid or kid not in apple_keys:
                logger.error(f"Apple key ID {kid} not found in public keys")
                return None
            
            # Get public key
            public_key = apple_keys[kid]
            
            # Decode dan verify token
            payload = jwt.decode(
                id_token,
                public_key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer='https://appleid.apple.com'
            )
            
            # Extract user info
            user_info = {
                'id': payload.get('sub'),
                'email': payload.get('email'),
                'email_verified': payload.get('email_verified', False),
                'provider': 'apple',
                'provider_id': payload.get('sub')
            }
            
            # Apple hanya memberikan nama pada first sign-in
            if 'name' in payload:
                user_info['name'] = payload['name']
            
            return user_info
            
        except jwt.ExpiredSignatureError:
            logger.error("Apple ID token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"Apple ID token invalid: {e}")
            return None
        except Exception as e:
            logger.error(f"Apple ID token decode error: {e}")
            return None
    
    async def _get_apple_public_keys(self) -> Optional[Dict[str, Any]]:
        """
        Get Apple public keys untuk JWT verification.
        
        Returns:
            Dictionary mapping key ID ke public key
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.keys_url)
                
                if response.status_code != 200:
                    logger.error(f"Failed to get Apple public keys: {response.status_code}")
                    return None
                
                keys_data = response.json()
                keys = {}
                
                for key_data in keys_data.get('keys', []):
                    kid = key_data.get('kid')
                    if kid:
                        # Convert JWK ke PEM format
                        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key_data))
                        keys[kid] = public_key
                
                return keys
                
        except Exception as e:
            logger.error(f"Error getting Apple public keys: {e}")
            return None
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            'name': 'Apple ID',
            'type': 'oauth2',
            'auth_url': self.auth_url,
            'token_url': self.token_url,
            'scopes': self.scope,
            'supports_refresh': True,
            'supports_revoke': True
        }
