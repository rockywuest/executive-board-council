"""
Supabase Authentication Module for Executive Board Council.

Handles user authentication, JWT verification, and user management.
"""

import os
from datetime import datetime
from typing import Optional
from functools import lru_cache

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client


# ============================================================================
# Configuration
# ============================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

# JWT Configuration
JWT_ALGORITHM = "HS256"


# ============================================================================
# Pydantic Models
# ============================================================================

class UserCreate(BaseModel):
    """Request model for user registration."""
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Request model for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Response model for user data."""
    id: str
    email: str
    tier: str = "free"
    created_at: Optional[str] = None


class AuthResponse(BaseModel):
    """Response model for authentication."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # User ID
    email: Optional[str] = None
    exp: Optional[int] = None
    aud: Optional[str] = None


# ============================================================================
# User Tiers
# ============================================================================

class UserTier:
    """User tier definitions with request limits."""
    ANONYMOUS = "anonymous"
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

    LIMITS = {
        ANONYMOUS: {"daily": 2, "monthly": 2},      # 2 requests per day
        FREE: {"daily": 5, "monthly": 5},           # 5 requests per month
        PRO: {"daily": 50, "monthly": 50},          # 50 requests per month
        ENTERPRISE: {"daily": -1, "monthly": -1},   # Unlimited
    }

    @classmethod
    def get_limit(cls, tier: str, period: str = "monthly") -> int:
        """Get request limit for a tier. -1 means unlimited."""
        return cls.LIMITS.get(tier, cls.LIMITS[cls.FREE]).get(period, 5)


# ============================================================================
# Supabase Client
# ============================================================================

@lru_cache()
def get_supabase_client() -> Optional[Client]:
    """Get cached Supabase client instance."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        print(f"Failed to create Supabase client: {e}")
        return None


@lru_cache()
def get_supabase_admin_client() -> Optional[Client]:
    """Get cached Supabase admin client (service role) for backend operations."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    except Exception as e:
        print(f"Failed to create Supabase admin client: {e}")
        return None


# ============================================================================
# Security
# ============================================================================

security = HTTPBearer(auto_error=False)


def verify_jwt_token(token: str) -> Optional[TokenPayload]:
    """
    Verify a Supabase JWT token and extract payload.

    Args:
        token: The JWT token string

    Returns:
        TokenPayload if valid, None otherwise
    """
    if not SUPABASE_JWT_SECRET:
        return None

    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            audience="authenticated"
        )
        return TokenPayload(
            sub=payload.get("sub"),
            email=payload.get("email"),
            exp=payload.get("exp"),
            aud=payload.get("aud")
        )
    except JWTError as e:
        print(f"JWT verification failed: {e}")
        return None


# ============================================================================
# Authentication Functions
# ============================================================================

async def register_user(email: str, password: str) -> AuthResponse:
    """
    Register a new user with Supabase.

    Args:
        email: User's email address
        password: User's password

    Returns:
        AuthResponse with access token and user info

    Raises:
        HTTPException if registration fails
    """
    client = get_supabase_client()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentifizierungsdienst nicht konfiguriert"
        )

    try:
        response = client.auth.sign_up({
            "email": email,
            "password": password
        })

        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registrierung fehlgeschlagen. Bitte versuchen Sie es erneut."
            )

        # Note: Supabase may require email verification depending on settings
        if response.session is None:
            return AuthResponse(
                access_token="",
                user=UserResponse(
                    id=response.user.id,
                    email=response.user.email or email,
                    tier=UserTier.FREE,
                    created_at=str(response.user.created_at) if response.user.created_at else None
                )
            )

        return AuthResponse(
            access_token=response.session.access_token,
            user=UserResponse(
                id=response.user.id,
                email=response.user.email or email,
                tier=UserTier.FREE,
                created_at=str(response.user.created_at) if response.user.created_at else None
            )
        )
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-Mail bereits registriert"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registrierung fehlgeschlagen: {error_msg}"
        )


async def login_user(email: str, password: str) -> AuthResponse:
    """
    Authenticate user with Supabase.

    Args:
        email: User's email address
        password: User's password

    Returns:
        AuthResponse with access token and user info

    Raises:
        HTTPException if login fails
    """
    client = get_supabase_client()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentifizierungsdienst nicht konfiguriert"
        )

    try:
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user is None or response.session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ungültige E-Mail oder Passwort"
            )

        # Get user tier from metadata (default to free)
        user_tier = UserTier.FREE
        if response.user.user_metadata:
            user_tier = response.user.user_metadata.get("tier", UserTier.FREE)

        return AuthResponse(
            access_token=response.session.access_token,
            user=UserResponse(
                id=response.user.id,
                email=response.user.email or email,
                tier=user_tier,
                created_at=str(response.user.created_at) if response.user.created_at else None
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültige E-Mail oder Passwort"
        )


async def logout_user(token: str) -> bool:
    """
    Sign out user from Supabase.

    Args:
        token: The user's access token

    Returns:
        True if logout successful
    """
    client = get_supabase_client()
    if not client:
        return True  # No client, nothing to sign out

    try:
        client.auth.sign_out()
        return True
    except Exception:
        return True  # Sign out is best-effort


# ============================================================================
# FastAPI Dependencies
# ============================================================================

async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserResponse]:
    """
    Optional authentication dependency.

    Returns user if authenticated, None otherwise.
    Use this for endpoints that work for both anonymous and authenticated users.
    """
    if not credentials:
        return None

    token_payload = verify_jwt_token(credentials.credentials)
    if not token_payload:
        return None

    # Get user tier from Supabase if possible
    user_tier = UserTier.FREE
    client = get_supabase_admin_client()
    if client and token_payload.sub:
        try:
            user_data = client.auth.admin.get_user_by_id(token_payload.sub)
            if user_data and user_data.user and user_data.user.user_metadata:
                user_tier = user_data.user.user_metadata.get("tier", UserTier.FREE)
        except Exception:
            pass  # Use default tier

    return UserResponse(
        id=token_payload.sub,
        email=token_payload.email or "",
        tier=user_tier
    )


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
) -> UserResponse:
    """
    Required authentication dependency.

    Returns user if authenticated, raises 401 otherwise.
    Use this for endpoints that require authentication.
    """
    token_payload = verify_jwt_token(credentials.credentials)
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiges oder abgelaufenes Token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Get user tier from Supabase if possible
    user_tier = UserTier.FREE
    client = get_supabase_admin_client()
    if client and token_payload.sub:
        try:
            user_data = client.auth.admin.get_user_by_id(token_payload.sub)
            if user_data and user_data.user and user_data.user.user_metadata:
                user_tier = user_data.user.user_metadata.get("tier", UserTier.FREE)
        except Exception:
            pass  # Use default tier

    return UserResponse(
        id=token_payload.sub,
        email=token_payload.email or "",
        tier=user_tier
    )


# ============================================================================
# User Management (Admin)
# ============================================================================

async def update_user_tier(user_id: str, tier: str) -> bool:
    """
    Update a user's tier (admin function for after payment).

    Args:
        user_id: The Supabase user ID
        tier: The new tier (free, pro, enterprise)

    Returns:
        True if update successful
    """
    if tier not in [UserTier.FREE, UserTier.PRO, UserTier.ENTERPRISE]:
        return False

    client = get_supabase_admin_client()
    if not client:
        return False

    try:
        client.auth.admin.update_user_by_id(
            user_id,
            {"user_metadata": {"tier": tier}}
        )
        return True
    except Exception as e:
        print(f"Failed to update user tier: {e}")
        return False


def get_client_ip(request: Request) -> str:
    """
    Get the real client IP address from request.

    Handles X-Forwarded-For header for proxied requests.
    """
    # Check for forwarded header (when behind proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded.split(",")[0].strip()

    # Check for real IP header (Nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    return "unknown"
