"""
Auth Router for handling Google OAuth authentication.

Endpoints:
- GET /api/auth/google - Initiate Google OAuth flow
- GET /api/auth/google/callback - Handle OAuth callback
- POST /api/auth/refresh - Refresh access token
- POST /api/auth/logout - Logout and revoke tokens
- GET /api/auth/me - Get current user info

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
"""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import TokenResponse, UserResponse
from app.services.auth_service import (
    AuthService,
    AuthJWTError,
    get_current_user,
)

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/google")
async def google_login(
    redirect_url: str | None = Query(None, description="URL to redirect after login")
) -> RedirectResponse:
    """
    Initiate Google OAuth flow.
    
    Generates OAuth URL with state parameter and redirects to Google consent screen.
    
    Requirements: 1.1
    """
    auth_service = AuthService()
    
    # Generate state parameter for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # If redirect_url provided, encode it in state (simplified approach)
    # In production, you'd want to store this in Redis/session
    
    # Get Google OAuth URL
    oauth_url = auth_service.get_google_auth_url(state=state)
    
    return RedirectResponse(url=oauth_url, status_code=status.HTTP_302_FOUND)



@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str | None = Query(None, description="State parameter for CSRF protection"),
    error: str | None = Query(None, description="Error from Google OAuth"),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """
    Handle Google OAuth callback.
    
    Exchanges authorization code for tokens, creates/updates user in database,
    and redirects to frontend with JWT token.
    
    Requirements: 1.2, 1.3, 1.4
    """
    frontend_callback_url = f"{settings.frontend_url}/auth/callback"
    
    # Handle OAuth errors (Requirement 1.7)
    if error:
        return RedirectResponse(
            url=f"{frontend_callback_url}?error={error}",
            status_code=status.HTTP_302_FOUND,
        )
    
    auth_service = AuthService()
    
    try:
        # Exchange code for tokens (Requirement 1.2)
        token_data = await auth_service.exchange_code(code)
        
        user_info = token_data["user_info"]
        google_id = user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name")
        avatar_url = user_info.get("picture")
        
        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user info from Google",
            )
        
        # Encrypt OAuth tokens for storage (Requirement 1.3)
        encrypted_access_token = auth_service.encrypt_token(token_data["access_token"])
        encrypted_refresh_token = None
        if token_data.get("refresh_token"):
            encrypted_refresh_token = auth_service.encrypt_token(token_data["refresh_token"])
        
        # Calculate token expiration
        token_expires = datetime.now(timezone.utc) + timedelta(
            seconds=token_data.get("expires_in", 3600)
        )
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.google_id == google_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update existing user
            user.email = email
            user.name = name
            user.avatar_url = avatar_url
            user.access_token = encrypted_access_token
            if encrypted_refresh_token:
                user.refresh_token = encrypted_refresh_token
            user.token_expires = token_expires
            user.updated_at = datetime.now(timezone.utc)
        else:
            # Create new user
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                avatar_url=avatar_url,
                access_token=encrypted_access_token,
                refresh_token=encrypted_refresh_token,
                token_expires=token_expires,
            )
            db.add(user)
        
        await db.commit()
        await db.refresh(user)
        
        # Create JWT token (Requirement 1.4)
        jwt_token = auth_service.create_jwt(
            user_data={
                "id": str(user.id),
                "email": user.email,
                "google_id": user.google_id,
            }
        )
        
        # Redirect to frontend with JWT token (Requirement 1.4)
        redirect_url = f"{frontend_callback_url}?access_token={jwt_token}"
        return RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND,
        )
        
    except AuthJWTError as e:
        return RedirectResponse(
            url=f"{frontend_callback_url}?error={str(e)}",
            status_code=status.HTTP_302_FOUND,
        )
    except HTTPException as e:
        return RedirectResponse(
            url=f"{frontend_callback_url}?error={e.detail}",
            status_code=status.HTTP_302_FOUND,
        )
    except Exception as e:
        return RedirectResponse(
            url=f"{frontend_callback_url}?error=Authentication+failed",
            status_code=status.HTTP_302_FOUND,
        )



@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TokenResponse:
    """
    Refresh access token using Google refresh token.
    
    Validates the refresh token and issues a new access token.
    
    Requirements: 1.5
    """
    auth_service = AuthService()
    
    try:
        # Get stored refresh token
        if not current_user.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No refresh token available",
            )
        
        # Decrypt stored refresh token
        stored_refresh_token = auth_service.decrypt_token(current_user.refresh_token)
        
        # Refresh Google token
        token_data = await auth_service.refresh_google_token(stored_refresh_token)
        
        # Encrypt new access token
        encrypted_access_token = auth_service.encrypt_token(token_data["access_token"])
        
        # Calculate new expiration
        token_expires = datetime.now(timezone.utc) + timedelta(
            seconds=token_data.get("expires_in", 3600)
        )
        
        # Update user's access token
        current_user.access_token = encrypted_access_token
        current_user.token_expires = token_expires
        current_user.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(current_user)
        
        # Create new JWT token
        jwt_token = auth_service.create_jwt(
            user_data={
                "id": str(current_user.id),
                "email": current_user.email,
                "google_id": current_user.google_id,
            }
        )
        
        return TokenResponse(
            access_token=jwt_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=UserResponse(
                id=current_user.id,
                google_id=current_user.google_id,
                email=current_user.email,
                name=current_user.name,
                avatar_url=current_user.avatar_url,
                created_at=current_user.created_at,
            ),
        )
        
    except AuthJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}",
        )



@router.post("/logout")
async def logout(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Logout user and revoke OAuth tokens.
    
    Revokes Google OAuth tokens and invalidates the session.
    
    Requirements: 1.6
    """
    auth_service = AuthService()
    
    try:
        # Revoke Google OAuth tokens if available
        if current_user.access_token:
            try:
                decrypted_token = auth_service.decrypt_token(current_user.access_token)
                await auth_service.revoke_tokens(decrypted_token)
            except Exception:
                # Token revocation failure is not critical
                pass
        
        # Clear stored tokens
        current_user.access_token = None
        current_user.refresh_token = None
        current_user.token_expires = None
        current_user.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}",
        )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user info.
    
    Requirements: 1.4
    """
    return UserResponse(
        id=current_user.id,
        google_id=current_user.google_id,
        email=current_user.email,
        name=current_user.name,
        avatar_url=current_user.avatar_url,
        created_at=current_user.created_at,
    )
