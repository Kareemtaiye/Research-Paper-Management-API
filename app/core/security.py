from datetime import datetime, timezone, timedelta
import secrets
from pwdlib import PasswordHash

import jwt
from app.core.config import settings


def hash_password(password: str):
    password_hash = PasswordHash.recommended()
    return password_hash.hash(password)


def verify_password(password: str, hash_str: str):
    password_hash = PasswordHash.recommended()
    return password_hash.verify(password, hash=hash_str)


def generate_access_token(data):
    expiry_time = datetime.now(timezone.utc) + timedelta(
        days=settings.access_token_expire_minutes
    )

    payload = {"sub": data, "exp": expiry_time}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def generate_refresh_token():
    return secrets.token_hex(32)
