"""
Facebook OAuth 2.0 authentication provider implementation.
Mengimplementasikan Facebook Login OAuth 2.0 flow.
"""
from typing import Optional, Dict, Any, List
import httpx
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class FacebookProvider:
    """
    Facebook OAuth 2.0 Provider.
    Mengimplementasikan Facebook Login authentication flow.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Facebook provider.
        
        Args:
            config: Configuration dictionary berisi:
                - client_id: Facebook App ID
                - client_secret: Facebook App Secret
                - scope: List of permissions
                - redirect_uri: Redirect URI
                - api_version: Facebook API version (default: v18.0)
        """
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.scope = config.get('scope', ['email', 'public_profile'])
        self.redirect_uri = config.get('redirect_uri')
        self.api_version = config.get('api_version', 'v18.0')
        
        # Facebook URLs
        self.auth_url = f'https://www.facebook.com/{self.api_version}/dialog/oauth'
        self.token_url = f'https://graph.facebook.com/{self.api_version}/oauth/access_token'
        self.user_info_url = f'https://graph.facebook.com/{self.api_version}/me'
        self.debug_token_url = f'https://graph.facebook.com/{self.api_version}/debug_token'
        
        # Validate required config
        if not all([self.client_id, self.client_secret]):
            raise ValueError("Facebook provider requires client_id and client_secret")
    
    def get_authorization_url(self, redirect_uri: str = None, state: str = None) -> str:
        """
        Generate authorization URL untuk Facebook OAuth flow.
        
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
            'scope': ','.join(self.scope)
        }
        
        if state:
            params['state'] = state
        
        return f"{self.auth_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str = None) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code untuk access token.
        
        Args:
            code: Authorization code dari Facebook
            redirect_uri: Redirect URI yang digunakan
            
        Returns:
            Token data atau None jika gagal
        """
        redirect_uri = redirect_uri or self.redirect_uri
        if not redirect_uri:
            raise ValueError("Redirect URI is required")
        
        try:
            params = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'redirect_uri': redirect_uri
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.token_url, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Facebook token exchange failed: {response.status_code} - {response.text}")
                    return None
                
                token_data = response.json()
                
                # Get user info dengan access token
                access_token = token_data.get('access_token')
                if access_token:
                    user_info = await self.get_user_info(access_token)
                    if user_info:
                        token_data['user_info'] = user_info
                
                return token_data
                
        except Exception as e:
            logger.error(f"Facebook token exchange error: {e}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information dari Facebook Graph API.
        
        Args:
            access_token: Facebook access token
            
        Returns:
            User information atau None jika gagal
        """
        try:
            # Fields yang akan diambil dari Facebook
            fields = [
                'id', 'name', 'email', 'first_name', 'last_name',
                'picture.type(large)', 'verified', 'locale', 'timezone'
            ]
            
            params = {
                'access_token': access_token,
                'fields': ','.join(fields)
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.user_info_url, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Facebook user info failed: {response.status_code} - {response.text}")
                    return None
                
                user_data = response.json()
                
                # Normalize user info
                user_info = {
                    'id': user_data.get('id'),
                    'username': user_data.get('name', '').replace(' ', '_').lower(),
                    'email': user_data.get('email'),
                    'name': user_data.get('name'),
                    'first_name': user_data.get('first_name'),
                    'last_name': user_data.get('last_name'),
                    'verified': user_data.get('verified', False),
                    'locale': user_data.get('locale'),
                    'timezone': user_data.get('timezone'),
                    'provider': 'facebook',
                    'provider_id': user_data.get('id')
                }
                
                # Extract profile picture
                picture = user_data.get('picture', {}).get('data', {})
                if picture:
                    user_info['picture_url'] = picture.get('url')
                    user_info['picture_is_silhouette'] = picture.get('is_silhouette', True)
                
                return user_info
                
        except Exception as e:
            logger.error(f"Facebook get user info error: {e}")
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh access token.
        
        Note: Facebook access tokens biasanya long-lived dan tidak perlu refresh.
        Method ini untuk extend token lifetime.
        
        Args:
            refresh_token: Current access token
            
        Returns:
            New token data atau None jika gagal
        """
        try:
            params = {
                'grant_type': 'fb_exchange_token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'fb_exchange_token': refresh_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.token_url, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Facebook token refresh failed: {response.status_code} - {response.text}")
                    return None
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Facebook token refresh error: {e}")
            return None
    
    async def validate_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate Facebook access token.
        
        Args:
            access_token: Access token to validate
            
        Returns:
            Token info atau None jika invalid
        """
        try:
            params = {
                'input_token': access_token,
                'access_token': f"{self.client_id}|{self.client_secret}"  # App token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.debug_token_url, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Facebook token validation failed: {response.status_code}")
                    return None
                
                result = response.json()
                token_data = result.get('data', {})
                
                # Check if token is valid
                if not token_data.get('is_valid', False):
                    logger.warning("Facebook token is not valid")
                    return None
                
                return token_data
                
        except Exception as e:
            logger.error(f"Facebook token validation error: {e}")
            return None
    
    async def revoke_token(self, access_token: str) -> bool:
        """
        Revoke Facebook access token.
        
        Args:
            access_token: Access token to revoke
            
        Returns:
            True jika berhasil
        """
        try:
            # Facebook menggunakan DELETE request ke /me/permissions
            url = f"https://graph.facebook.com/{self.api_version}/me/permissions"
            params = {'access_token': access_token}
            
            async with httpx.AsyncClient() as client:
                response = await client.delete(url, params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('success', False)
                
                logger.error(f"Facebook token revoke failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Facebook token revoke error: {e}")
            return False
    
    async def get_user_permissions(self, access_token: str) -> Optional[List[str]]:
        """
        Get user permissions untuk access token.
        
        Args:
            access_token: Facebook access token
            
        Returns:
            List of permissions atau None jika gagal
        """
        try:
            url = f"https://graph.facebook.com/{self.api_version}/me/permissions"
            params = {'access_token': access_token}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Facebook permissions check failed: {response.status_code}")
                    return None
                
                result = response.json()
                permissions = []
                
                for perm in result.get('data', []):
                    if perm.get('status') == 'granted':
                        permissions.append(perm.get('permission'))
                
                return permissions
                
        except Exception as e:
            logger.error(f"Facebook get permissions error: {e}")
            return None
    
    async def get_long_lived_token(self, short_lived_token: str) -> Optional[Dict[str, Any]]:
        """
        Exchange short-lived token untuk long-lived token.
        
        Args:
            short_lived_token: Short-lived access token
            
        Returns:
            Long-lived token data atau None jika gagal
        """
        try:
            params = {
                'grant_type': 'fb_exchange_token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'fb_exchange_token': short_lived_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.token_url, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Facebook long-lived token exchange failed: {response.status_code}")
                    return None
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Facebook long-lived token error: {e}")
            return None
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            'name': 'Facebook',
            'type': 'oauth2',
            'auth_url': self.auth_url,
            'token_url': self.token_url,
            'user_info_url': self.user_info_url,
            'scopes': self.scope,
            'api_version': self.api_version,
            'supports_refresh': True,
            'supports_revoke': True,
            'supports_long_lived_tokens': True
        }
