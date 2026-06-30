from passlib.context import CryptContext
from fastapi import HTTPException
from jose import jwt
from jose import JWTError
from datetime import datetime
from datetime import timedelta

from app.core.config import settings


def create_access_token(
    data: dict
):

    payload = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload["exp"] = expire

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def decode_access_token(token: str):

    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def validate_password_policy(password: str):

    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long"
        )

    checks = [
        (any(char.isupper() for char in password), "uppercase letter"),
        (any(char.islower() for char in password), "lowercase letter"),
        (any(char.isdigit() for char in password), "number"),
        (
            any(not char.isalnum() for char in password),
            "special character"
        ),
    ]

    for passed, label in checks:
        if not passed:
            raise HTTPException(
                status_code=400,
                detail=f"Password must contain at least one {label}"
            )
