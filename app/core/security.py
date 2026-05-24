import hashlib
from typing import Any

import jwt
import secrets
from datetime import datetime, timezone, timedelta
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

DUMMY_HASH = PasswordHash.recommended().hash("dummy_hasg")


def hash_password(password: str):
    password_hash = PasswordHash.recommended()
    return password_hash.hash(password)


def hash_token(token: str):
    return hashlib.sha256(token.encode()).hexdigest()


def verify_password(password: str, hash_str: str):
    password_hash = PasswordHash.recommended()
    return password_hash.verify(password, hash=hash_str)


def generate_access_token(data: Any):
    expiry_time = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {"sub": data, "exp": expiry_time}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def generate_refresh_token():
    return secrets.token_hex(32)


def verify_jwt(token: str):
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])


def verify_websocket_token(token: str, user_id: str):
    """
    Validates JWT token for WebSocket connection.
    Returns True if valid and belongs to user_id.
    Returns False otherwise.
    """

    try:
        payload = verify_jwt(token)
        token_user_id = payload.get("sub")
        return token_user_id == user_id
    except Exception:
        return False  # Might be invalid token or jwt exp err
