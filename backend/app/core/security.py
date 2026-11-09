import re
from datetime import datetime, timedelta
from typing import Any, Union, Optional
import bcrypt
import jwt
from app.core.config import settings

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except Exception:
        return None

# PHI De-identification & Redaction Utility for HIPAA Compliance
def sanitize_phi_text(text: str) -> str:
    """
    Scans and redacts common Protected Health Information (PHI) patterns
    such as Social Security Numbers, Phone Numbers, Emails, and Credit Cards
    prior to sending prompt payloads to external LLM providers.
    """
    if not text:
        return text
    
    # Redact SSN: 000-00-0000
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", text)
    # Redact Phone: (123) 456-7890 or 123-456-7890 or 10 digits
    text = re.sub(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[REDACTED_PHONE]", text)
    # Redact Email
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED_EMAIL]", text)
    # Redact Credit Card: 16 digits
    text = re.sub(r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "[REDACTED_CC]", text)
    
    return text

