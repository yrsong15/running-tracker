"""Garmin session handling.

The server never logs in with a password. `cli login` runs on your Mac, and the
resulting OAuth tokens are encrypted into the garmin_auth row. Everywhere else
we restore a session from those tokens and write refreshed tokens back.
"""

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectTooManyRequestsError,
)
from sqlmodel import Session

from app.crypto import decrypt, encrypt
from app.models import GarminAuth, utcnow


class GarminNotConnected(RuntimeError):
    pass


def get_auth(session: Session) -> GarminAuth:
    auth = session.get(GarminAuth, 1)
    if auth is None:
        auth = GarminAuth()
        session.add(auth)
        session.commit()
        session.refresh(auth)
    return auth


def store_tokens(session: Session, garmin: Garmin) -> None:
    auth = get_auth(session)
    auth.tokens_encrypted = encrypt(garmin.client.dumps())
    auth.status = "ok"
    auth.last_error = None
    auth.updated_at = utcnow()
    session.add(auth)
    session.commit()


def mark_needs_reconnect(session: Session, error: str) -> None:
    auth = get_auth(session)
    auth.status = "needs_reconnect"
    auth.last_error = error[:500]
    auth.updated_at = utcnow()
    session.add(auth)
    session.commit()


def restore_client(session: Session) -> Garmin:
    """A logged-in Garmin client built from stored tokens (no credentials)."""
    auth = get_auth(session)
    if not auth.tokens_encrypted:
        raise GarminNotConnected("Garmin isn't connected yet. Run `cli login` on your Mac.")
    garmin = Garmin()
    try:
        garmin.login(tokenstore=decrypt(auth.tokens_encrypted))
    except GarminConnectAuthenticationError as exc:
        mark_needs_reconnect(session, f"Stored Garmin tokens were rejected: {exc}")
        raise GarminNotConnected("Garmin tokens expired. Run `cli login` on your Mac to reconnect.") from exc
    except GarminConnectTooManyRequestsError:
        raise
    # login() may have refreshed the access token; persist whatever it holds now.
    store_tokens(session, garmin)
    return garmin


def interactive_login(email: str, password: str, prompt_mfa) -> Garmin:
    garmin = Garmin(email=email, password=password, prompt_mfa=prompt_mfa)
    garmin.login()
    return garmin
