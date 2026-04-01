"""OTP authentication service — email-based one-time passwords."""
import hashlib
import hmac
import secrets
from datetime import datetime, timezone, timedelta
from ..extensions import db

OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 5


def generate_otp(user):
    """Generate a 6-digit OTP, store hash on user, return plaintext code."""
    code = ''.join([str(secrets.randbelow(10)) for _ in range(OTP_LENGTH)])
    user.otp_code = _hash_otp(code)
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)
    user.otp_attempts = 0
    db.session.commit()
    return code


def verify_otp(user, code):
    """Verify OTP code against stored hash. Returns True/False."""
    if not user.otp_code or not user.otp_expires_at:
        return False
    expires = user.otp_expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires:
        user.otp_code = None
        user.otp_expires_at = None
        db.session.commit()
        return False
    if not hmac.compare_digest(user.otp_code, _hash_otp(code)):
        user.otp_attempts = (user.otp_attempts or 0) + 1
        if user.otp_attempts >= MAX_OTP_ATTEMPTS:
            user.otp_code = None
            user.otp_expires_at = None
        db.session.commit()
        return False
    # Success — clear OTP
    user.otp_code = None
    user.otp_expires_at = None
    user.otp_attempts = 0
    db.session.commit()
    return True


def _hash_otp(code):
    return hashlib.sha256(code.encode()).hexdigest()
