import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .models import SessionToken, User


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"pbkdf2_sha256$310000${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        calculated = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds))
        return hmac.compare_digest(calculated.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def create_session(db: Session, user: User) -> str:
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    db.add(
        SessionToken(
            token_hash=token_hash,
            user_id=user.id,
            expires_at=datetime.now(UTC) + timedelta(minutes=get_settings().access_token_ttl_minutes),
        )
    )
    db.commit()
    return raw_token


def get_user_for_token(db: Session, token: str | None) -> User | None:
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = db.scalar(select(SessionToken).where(SessionToken.token_hash == token_hash))
    if not session:
        return None
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC):
        return None
    return db.get(User, session.user_id)
