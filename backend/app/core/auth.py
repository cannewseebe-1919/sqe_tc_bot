import json
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


# --- JWT helpers ---

def create_jwt_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_jwt_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return decode_jwt_token(credentials.credentials)


# --- SAML helpers ---

def _get_saml_settings_path() -> str:
    return os.path.join(os.path.dirname(__file__), "saml")


def get_saml_settings(request: Request) -> dict:
    """Build python3-saml settings dict from config files and request info."""
    saml_path = _get_saml_settings_path()
    settings_file = os.path.join(saml_path, "settings.json")

    if not os.path.exists(settings_file):
        raise HTTPException(status_code=500, detail="SAML settings not configured")

    with open(settings_file, encoding="utf-8") as f:
        saml_settings = json.load(f)

    return saml_settings


def prepare_saml_request(request: Request) -> dict:
    """Prepare request data dict for python3-saml from a FastAPI request."""
    return {
        "https": "on" if request.url.scheme == "https" else "off",
        "http_host": request.url.hostname or "localhost",
        "script_name": request.url.path,
        "get_data": dict(request.query_params),
        "post_data": {},
    }
