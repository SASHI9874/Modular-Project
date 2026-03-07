# from datetime import datetime, timedelta, timezone
# from typing import Any, Union
# from jose import jwt
# from passlib.context import CryptContext
# from app.core.config import settings

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ALGORITHM = "HS256"

# def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
#     if expires_delta:
#         expire = datetime.now(timezone.utc) + expires_delta
#     else:
#         expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    
#     to_encode = {"exp": expire, "sub": str(subject)}
#     encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password[:72], hashed_password)

# def get_password_hash(password: str) -> str:
#     return pwd_context.hash(password[:72])   

from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Use Argon2 instead of bcrypt
# pwd_context = CryptContext(
#     schemes=["argon2"],
#     deprecated="auto"
# )

pwd_context = CryptContext(
    schemes=["argon2"],
    argon2__memory_cost=102400,   # 100 MB
    argon2__time_cost=3,
    argon2__parallelism=4,
    deprecated="auto"
)

ALGORITHM = "HS256"


def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)