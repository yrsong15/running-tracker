from cryptography.fernet import Fernet

from app.config import GARMIN_TOKEN_KEY


class MissingKeyError(RuntimeError):
    pass


def _fernet() -> Fernet:
    if not GARMIN_TOKEN_KEY:
        raise MissingKeyError("GARMIN_TOKEN_KEY is not set")
    return Fernet(GARMIN_TOKEN_KEY.encode())


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode()).decode()
