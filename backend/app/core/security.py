# 비밀번호 해시(가입·로그인 공용)와 인증번호·가입 토큰 해시

import hashlib
import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings

# RFC 9106 두 번째 권고값: 64MiB, 3회, 병렬 4
_hasher = PasswordHasher(time_cost=3, memory_cost=64 * 1024, parallelism=4)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def check_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def new_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def new_signup_token() -> str:
    return secrets.token_urlsafe(32)


def digest(purpose: str, email: str, value: str) -> str:
    """6자리 코드는 해시만 저장하면 DB 유출 시 바로 풀리므로 서버 비밀키로 HMAC 한다."""
    message = f"{purpose}:{email}:{value}".encode()
    return hmac.new(settings.secret_key.encode(), message, hashlib.sha256).hexdigest()


def same(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)
