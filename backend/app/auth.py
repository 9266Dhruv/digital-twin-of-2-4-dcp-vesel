"""
JWT Authentication & Role-Based Access Control (RBAC)
Implements WORKER / OWNER / VIEWER roles with HS256 JWT tokens.

Usage:
  - POST /api/auth/login with {"username": "...", "password": "..."}
  - Returns {"access_token": "...", "token_type": "bearer"}
  - Include header: Authorization: Bearer <token> on all requests
  - WebSocket: pass ?token=<jwt> query parameter
"""

import os
import time
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta, timezone

# Use try/except for optional dependencies
try:
    from jose import JWTError, jwt
    HAS_JOSE = True
except ImportError:
    HAS_JOSE = False

try:
    from passlib.context import CryptContext
    HAS_PASSLIB = True
except ImportError:
    HAS_PASSLIB = False

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel


# ─── Configuration ───

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dcp-twin-dev-secret-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "30"))
AUTH_ENABLED = os.environ.get("AUTH_ENABLED", "true").lower() == "true"


# ─── Roles ───

class Role(str, Enum):
    WORKER = "WORKER"
    OWNER = "OWNER"
    VIEWER = "VIEWER"


# Role hierarchy: OWNER > WORKER > VIEWER
ROLE_HIERARCHY = {
    Role.VIEWER: 0,
    Role.WORKER: 1,
    Role.OWNER: 2,
}


# ─── Password Hashing ───

if HAS_PASSLIB:
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
else:
    # Fallback: plain comparison (dev only)
    class _FallbackContext:
        def verify(self, plain, hashed):
            return plain == hashed
        def hash(self, password):
            return password
    pwd_context = _FallbackContext()


# ─── User Database (hardcoded for now) ───

class UserInDB(BaseModel):
    username: str
    hashed_password: str
    role: Role
    full_name: str = ""


def _hash_pw(pw: str) -> str:
    """Hash a password (uses bcrypt if available, else plaintext)."""
    return pwd_context.hash(pw)


# Pre-hash passwords at module load
_USERS_DB = {}

def _init_users():
    global _USERS_DB
    _USERS_DB = {
        "worker1": UserInDB(
            username="worker1",
            hashed_password=_hash_pw("worker123"),
            role=Role.WORKER,
            full_name="Plant Operator 1",
        ),
        "worker": UserInDB(
            username="worker",
            hashed_password=_hash_pw("dcp2026"),
            role=Role.WORKER,
            full_name="Operator",
        ),
        "owner1": UserInDB(
            username="owner1",
            hashed_password=_hash_pw("owner456"),
            role=Role.OWNER,
            full_name="Plant Engineer",
        ),
        "owner": UserInDB(
            username="owner",
            hashed_password=_hash_pw("admin"),
            role=Role.OWNER,
            full_name="Himanshu Patel",
        ),
        "viewer1": UserInDB(
            username="viewer1",
            hashed_password=_hash_pw("view789"),
            role=Role.VIEWER,
            full_name="Remote Viewer",
        ),
    }

_init_users()


# ─── Token Models ───

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = ""
    username: str = ""
    expires_in: int = 0


class TokenData(BaseModel):
    username: str
    role: Role


class UserInfo(BaseModel):
    username: str
    role: str
    full_name: str


# ─── OAuth2 Scheme ───

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ─── Core Functions ───

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Verify username and password against the user database."""
    user = _USERS_DB.get(username)
    if not user:
        return None
    if not pwd_context.verify(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a signed JWT token."""
    if not HAS_JOSE:
        # Fallback: return a simple token string
        return f"dev-token-{data.get('sub', 'unknown')}-{data.get('role', 'VIEWER')}"

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token."""
    if not HAS_JOSE:
        # Fallback for dev mode without jose
        if token and token.startswith("dev-token-"):
            parts = token.split("-")
            if len(parts) >= 4:
                username = parts[2]
                role_str = parts[3]
                try:
                    return TokenData(username=username, role=Role(role_str))
                except ValueError:
                    return None
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role_str: str = payload.get("role")
        if username is None or role_str is None:
            return None
        return TokenData(username=username, role=Role(role_str))
    except (JWTError, ValueError):
        return None


# ─── FastAPI Dependencies ───

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[TokenData]:
    """
    Extract current user from JWT token.
    If AUTH_ENABLED is False, returns a default OWNER user.
    """
    if not AUTH_ENABLED:
        # Auth disabled — allow all access
        return TokenData(username="dev-user", role=Role.OWNER)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = decode_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


def require_role(minimum_role: Role):
    """
    Dependency factory that enforces a minimum role level.

    Usage:
        @app.get("/api/secret", dependencies=[Depends(require_role(Role.OWNER))])
        async def secret_endpoint():
            ...
    """
    async def role_checker(user: TokenData = Depends(get_current_user)):
        if not AUTH_ENABLED:
            return user
        if ROLE_HIERARCHY.get(user.role, -1) < ROLE_HIERARCHY.get(minimum_role, 99):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {minimum_role.value}, Your role: {user.role.value}",
            )
        return user
    return role_checker


async def get_ws_user(token: Optional[str] = None) -> Optional[TokenData]:
    """
    Authenticate WebSocket connections via query parameter token.
    Returns None if auth is disabled (allows all connections).
    """
    if not AUTH_ENABLED:
        return TokenData(username="dev-user", role=Role.OWNER)

    if not token:
        return None

    return decode_token(token)
