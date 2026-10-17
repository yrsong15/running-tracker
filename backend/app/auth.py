"""Single-user password auth with a signed session cookie."""

import hashlib
import hmac
import secrets

from fastapi import HTTPException, Request, Response
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner

from app.config import APP_PASSWORD_HASH, IS_PRODUCTION, ON_VERCEL, SESSION_MAX_AGE_S, SESSION_SECRET

COOKIE = "rt_session"
_signer = TimestampSigner(SESSION_SECRET, salt="running-tracker-session")
_SCRYPT = {"n": 2**14, "r": 8, "p": 1}


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, **_SCRYPT)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        scheme, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), **_SCRYPT)
    return hmac.compare_digest(digest.hex(), digest_hex)


def start_session(response: Response) -> None:
    token = _signer.sign(b"owner").decode()
    response.set_cookie(
        COOKIE, token, max_age=SESSION_MAX_AGE_S, httponly=True, samesite="lax", secure=IS_PRODUCTION or ON_VERCEL
    )


def end_session(response: Response) -> None:
    response.delete_cookie(COOKIE)


def is_logged_in(request: Request) -> bool:
    token = request.cookies.get(COOKIE)
    if not token:
        return False
    try:
        _signer.unsign(token, max_age=SESSION_MAX_AGE_S)
        return True
    except (BadSignature, SignatureExpired):
        return False


def require_login(request: Request) -> None:
    if not is_logged_in(request):
        raise HTTPException(status_code=401, detail="Not logged in")


def password_configured() -> bool:
    return bool(APP_PASSWORD_HASH)


def check_password(password: str) -> bool:
    return verify_password(password, APP_PASSWORD_HASH)
