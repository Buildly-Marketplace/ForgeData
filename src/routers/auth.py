"""
Authentication router
Provides OAuth2 authentication and user management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
import requests
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str
    user_data: dict


class UserData(BaseModel):
    username: str
    email: str
    organization_id: str
    organization_name: str


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserData:
    """
    Validate token and get current user information
    """
    if not settings.AUTH_API_URL:
        # Development mode - return mock user
        return UserData(
            username="dev_user",
            email="dev@example.com",
            organization_id="dev_org_1",
            organization_name="Development Organization"
        )
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{settings.AUTH_API_URL}/coreuser/me",
            headers=headers
        )
        response.raise_for_status()
        user_info = response.json()
        
        return UserData(
            username=user_info.get("username"),
            email=user_info.get("email"),
            organization_id=user_info.get("organization", {}).get("organization_uuid"),
            organization_name=user_info.get("organization", {}).get("name", "")
        )
    except Exception as e:
        logger.error(f"Failed to validate token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint - authenticates with configured auth provider
    """
    if not settings.AUTH_API_URL:
        # Development mode
        return Token(
            access_token="dev_token_12345",
            token_type="bearer",
            user_data={
                "username": "dev_user",
                "email": "dev@example.com",
                "organization_id": "dev_org_1"
            }
        )
    
    try:
        # Authenticate with auth provider
        response = requests.post(
            f"{settings.AUTH_API_URL}/oauth/token/",
            data={
                "username": form_data.username,
                "password": form_data.password,
                "grant_type": "password",
                "client_id": settings.AUTH_CLIENT_ID,
                "client_secret": settings.AUTH_CLIENT_SECRET
            }
        )
        response.raise_for_status()
        token_data = response.json()
        
        # Get user info
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        user_response = requests.get(
            f"{settings.AUTH_API_URL}/coreuser/me",
            headers=headers
        )
        user_response.raise_for_status()
        user_info = user_response.json()
        
        return Token(
            access_token=token_data["access_token"],
            token_type="bearer",
            user_data=user_info
        )
    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )


@router.get("/me", response_model=UserData)
async def get_me(current_user: UserData = Depends(get_current_user)):
    """Get current user information"""
    return current_user
