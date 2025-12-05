"""
Authentication service for handling OAuth, JWT, and token encryption.

This service provides:
- Token encryption/decryption using Fernet symmetric encryption
- JWT creation and verification
- Google OAuth flow helpers
- FastAPI dependency for authentication

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 10.1, 11.1, 11.2, 11.3
"""

import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from jose import jwt
from jose.exceptions import JWTError as JoseJWTError, ExpiredSignatureError

from app.config import get_settings

settings = get_settings()


class TokenEncryptionError(Exception):
    """Raised when token encryption/decryption fails."""
    pass


class AuthJWTError(Exception):
    """Raised when JWT operations fail."""
    pass


class JWTExpiredError(AuthJWTError):
    """Raised when JWT token is expired."""
    pass


class JWTInvalidError(AuthJWTError):
    """Raised when JWT token is invalid."""
    pass


class AuthService:
    """
    Authentication service for handling OAuth, JWT, and token encryption.
    
    Implements:
    - Fernet symmetric encryption for OAuth tokens (Requirements 1.3, 10.1, 11.3)
    - JWT creation and verification (Requirements 1.4, 11.1, 11.2)
    - Google OAuth flow helpers (Requirements 1.1, 1.2, 1.5)
    """

    def __init__(self):
        """Initialize the auth service with encryption key from settings."""
        self._fernet = self._create_fernet(settings.encryption_key)
        self._jwt_secret = settings.jwt_secret_key
        self._jwt_algorithm = settings.jwt_algorithm
        self._access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self._refresh_token_expire_days = settings.jwt_refresh_token_expire_days

    @staticmethod
    def _create_fernet(key: str) -> Fernet:
        """
        Create a Fernet instance from a string key.
        
        The key is hashed to ensure it's the correct length for Fernet (32 bytes).
        """
        # Hash the key to get a consistent 32-byte key
        key_bytes = hashlib.sha256(key.encode()).digest()
        # Fernet requires base64-encoded 32-byte key
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        return Fernet(fernet_key)

    def encrypt_token(self, token: str) -> str:
        """
        Encrypt an OAuth token for secure storage.
        
        Uses Fernet symmetric encryption (AES-128-CBC with HMAC).
        
        Args:
            token: The plaintext OAuth token to encrypt
            
        Returns:
            The encrypted token as a base64-encoded string
            
        Raises:
            TokenEncryptionError: If encryption fails
            
        Requirements: 1.3, 10.1, 11.3
        """
        if not token:
            raise TokenEncryptionError("Cannot encrypt empty token")
        
        try:
            encrypted = self._fernet.encrypt(token.encode())
            return encrypted.decode()
        except Exception as e:
            raise TokenEncryptionError(f"Failed to encrypt token: {e}") from e

    def decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt an encrypted OAuth token.
        
        Args:
            encrypted_token: The encrypted token string
            
        Returns:
            The decrypted plaintext token
            
        Raises:
            TokenEncryptionError: If decryption fails (invalid token or key)
            
        Requirements: 1.3, 10.1, 11.3
        """
        if not encrypted_token:
            raise TokenEncryptionError("Cannot decrypt empty token")
        
        try:
            decrypted = self._fernet.decrypt(encrypted_token.encode())
            return decrypted.decode()
        except InvalidToken as e:
            raise TokenEncryptionError("Invalid or corrupted token") from e
        except Exception as e:
            raise TokenEncryptionError(f"Failed to decrypt token: {e}") from e

    def create_jwt(
        self,
        user_data: dict[str, Any],
        expires_delta: timedelta | None = None,
        token_type: str = "access"
    ) -> str:
        """
        Create a JWT token with user payload and expiration.
        
        Args:
            user_data: Dictionary containing user information (id, email, google_id)
            expires_delta: Optional custom expiration time
            token_type: Type of token ("access" or "refresh")
            
        Returns:
            Encoded JWT token string
            
        Raises:
            AuthJWTError: If token creation fails
            
        Requirements: 1.4, 11.1, 11.2
        """
        try:
            # Set expiration based on token type
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            elif token_type == "refresh":
                expire = datetime.now(timezone.utc) + timedelta(
                    days=self._refresh_token_expire_days
                )
            else:
                expire = datetime.now(timezone.utc) + timedelta(
                    minutes=self._access_token_expire_minutes
                )
            
            # Build payload
            payload = {
                "sub": str(user_data.get("id", "")),
                "email": user_data.get("email", ""),
                "google_id": user_data.get("google_id", ""),
                "type": token_type,
                "exp": expire,
                "iat": datetime.now(timezone.utc),
            }
            
            # Encode token
            token = jwt.encode(
                payload,
                self._jwt_secret,
                algorithm=self._jwt_algorithm
            )
            
            return token
            
        except Exception as e:
            raise AuthJWTError(f"Failed to create JWT: {e}") from e

    def verify_jwt(self, token: str) -> dict[str, Any]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: The JWT token string to verify
            
        Returns:
            Dictionary containing decoded payload with user information
            
        Raises:
            JWTExpiredError: If the token has expired
            JWTInvalidError: If the token is invalid or malformed
            
        Requirements: 1.4, 11.1, 11.2
        """
        if not token:
            raise JWTInvalidError("Token is required")
        
        try:
            payload = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=[self._jwt_algorithm]
            )
            
            # Extract user data from payload
            return {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "google_id": payload.get("google_id"),
                "type": payload.get("type"),
                "exp": payload.get("exp"),
                "iat": payload.get("iat"),
            }
            
        except ExpiredSignatureError as e:
            raise JWTExpiredError("Token has expired") from e
        except JoseJWTError as e:
            raise JWTInvalidError(f"Invalid token: {e}") from e
        except Exception as e:
            raise JWTInvalidError(f"Token verification failed: {e}") from e

    # Google OAuth Scopes required for YouTube API access
    GOOGLE_OAUTH_SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ]

    def get_google_auth_url(self, state: str | None = None) -> str:
        """
        Generate Google OAuth authorization URL with required scopes.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            The Google OAuth consent screen URL
            
        Requirements: 1.1
        """
        import urllib.parse
        
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.GOOGLE_OAUTH_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        }
        
        if state:
            params["state"] = state
        
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        query_string = urllib.parse.urlencode(params)
        
        return f"{base_url}?{query_string}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        """
        Exchange authorization code for OAuth tokens.
        
        Args:
            code: The authorization code from Google OAuth callback
            
        Returns:
            Dictionary containing access_token, refresh_token, expires_in, and user_info
            
        Raises:
            AuthJWTError: If token exchange fails
            
        Requirements: 1.2
        """
        import httpx
        
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.google_redirect_uri,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # Exchange code for tokens
                token_response = await client.post(token_url, data=data)
                
                if token_response.status_code != 200:
                    error_data = token_response.json()
                    raise AuthJWTError(
                        f"Token exchange failed: {error_data.get('error_description', 'Unknown error')}"
                    )
                
                tokens = token_response.json()
                
                # Get user info using the access token
                user_info = await self._get_google_user_info(
                    client, tokens["access_token"]
                )
                
                return {
                    "access_token": tokens["access_token"],
                    "refresh_token": tokens.get("refresh_token"),
                    "expires_in": tokens.get("expires_in", 3600),
                    "token_type": tokens.get("token_type", "Bearer"),
                    "user_info": user_info,
                }
                
        except httpx.HTTPError as e:
            raise AuthJWTError(f"HTTP error during token exchange: {e}") from e
        except Exception as e:
            if isinstance(e, AuthJWTError):
                raise
            raise AuthJWTError(f"Token exchange failed: {e}") from e

    async def _get_google_user_info(
        self, client: "httpx.AsyncClient", access_token: str
    ) -> dict[str, Any]:
        """
        Fetch user information from Google using access token.
        
        Args:
            client: HTTP client instance
            access_token: Valid Google OAuth access token
            
        Returns:
            Dictionary containing user profile information
        """
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(user_info_url, headers=headers)
        
        if response.status_code != 200:
            raise AuthJWTError("Failed to fetch user info from Google")
        
        return response.json()

    async def refresh_google_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh an expired Google OAuth access token.
        
        Args:
            refresh_token: The refresh token from initial OAuth flow
            
        Returns:
            Dictionary containing new access_token and expires_in
            
        Raises:
            AuthJWTError: If token refresh fails
            
        Requirements: 1.5
        """
        import httpx
        
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                
                if response.status_code != 200:
                    error_data = response.json()
                    raise AuthJWTError(
                        f"Token refresh failed: {error_data.get('error_description', 'Unknown error')}"
                    )
                
                tokens = response.json()
                
                return {
                    "access_token": tokens["access_token"],
                    "expires_in": tokens.get("expires_in", 3600),
                    "token_type": tokens.get("token_type", "Bearer"),
                }
                
        except httpx.HTTPError as e:
            raise AuthJWTError(f"HTTP error during token refresh: {e}") from e
        except Exception as e:
            if isinstance(e, AuthJWTError):
                raise
            raise AuthJWTError(f"Token refresh failed: {e}") from e

    async def revoke_tokens(self, access_token: str) -> bool:
        """
        Revoke Google OAuth tokens.
        
        Args:
            access_token: The access token to revoke
            
        Returns:
            True if revocation was successful
            
        Requirements: 1.6
        """
        import httpx
        
        revoke_url = "https://oauth2.googleapis.com/revoke"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    revoke_url,
                    params={"token": access_token}
                )
                
                # Google returns 200 on success
                return response.status_code == 200
                
        except Exception:
            # Revocation failure is not critical
            return False



# FastAPI Dependencies for Authentication

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User

# HTTP Bearer token security scheme
oauth2_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency for JWT validation and user retrieval.
    
    Extracts the JWT token from the Authorization header, validates it,
    and returns the corresponding User from the database.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session
        
    Returns:
        The authenticated User object
        
    Raises:
        HTTPException 401: If token is missing, invalid, or expired
        HTTPException 401: If user not found in database
        
    Requirements: 11.1, 11.2
    """
    # Check if credentials are provided
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    auth_service = AuthService()
    
    try:
        # Verify and decode the JWT
        payload = auth_service.verify_jwt(token)
        
        user_id = payload.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Fetch user from database
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except JWTExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
            # Include error code for frontend handling
        )
    except JWTInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Optional authentication dependency.
    
    Returns the user if authenticated, None otherwise.
    Useful for endpoints that work differently for authenticated vs anonymous users.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session
        
    Returns:
        The authenticated User object or None
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
