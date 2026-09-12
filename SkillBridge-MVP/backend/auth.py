# backend/auth.py
#
# WHAT THIS FILE DOES:
# This is the security center for SkillBridge Stage 3.
# It handles:
#   1. Secure password hashing and verification using bcrypt
#   2. Generating and validating signed JSON Web Tokens (JWT)
#   3. The FastAPI dependency `get_current_user` to protect private endpoints
#
# SECURITY RULES ENFORCED HERE:
#   - We NEVER store plain-text passwords in SQLite.
#   - We NEVER send password_hash back to the client in API responses.
#   - We verify tokens on every protected request.

import os
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.database import get_user_by_id

# ---------------------------------------------------------
# LOAD CONFIGURATION FROM ENVIRONMENT VARIABLES
# ---------------------------------------------------------
# Load settings from .env file if present
load_dotenv()

# SECRET_KEY: Used to cryptographically sign tokens so hackers cannot tamper with them.
# In production, this must be a long random string kept in an environment variable.
SECRET_KEY = os.getenv(
    "SECRET_KEY"
) or os.getenv(
    "SESSION_SECRET"
) or "skillbridge-dev-secret-key-change-in-production-123456789"

# ALGORITHM: The cryptographic algorithm used for signing (HS256 = HMAC with SHA-256)
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# How long a login session stays valid before requiring login again (default 60 minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# HTTPBearer security scheme: looks for "Authorization: Bearer <token>" in request headers
security_bearer = HTTPBearer(auto_error=False)


# =========================================================
# 1. PASSWORD HASHING (bcrypt)
# =========================================================
# WHAT IS A "PASSWORD HASH"?
# Hashing is a one-way mathematical transformation.
# "password123" -> "$2b$12$e8kP...random-looking-scramble"
#
# It is IMPOSSIBLE to reverse the hash back into the password.
# When a user logs in, we hash their entered password and check
# if the resulting hash matches what is stored in the database.
#
# WHAT IS A "SALT"?
# bcrypt automatically generates a random "salt" for each password.
# This ensures that even if two users have the exact same password,
# their hashes in the database look completely different!
# =========================================================

def hash_password(plain_password: str) -> str:
    """
    Takes a plain-text password, hashes it securely with bcrypt + random salt,
    and returns the hash as a string for safe database storage.
    """
    # bcrypt operates on raw bytes, so we encode string to utf-8 bytes
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain-text password matches the stored bcrypt hash.
    Returns True if valid, False if incorrect.
    """
    try:
        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        # bcrypt.checkpw handles timing-safe comparison to prevent timing attacks
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


# =========================================================
# 2. JSON WEB TOKENS (JWT)
# =========================================================
# WHAT IS A "JWT"?
# A JSON Web Token is like a digital ID card stamped with a digital wax seal.
# When a user logs in successfully, the server gives them a token containing:
#   - sub: User ID
#   - email: User email
#   - role: User role (student, industry, academician, institution)
#   - exp: Expiration date/time
#
# The server signs this token with SECRET_KEY.
# Whenever the user visits a protected page, their browser sends this token.
# The server verifies the signature to know: "Yes, I issued this, and it hasn't expired."
# =========================================================

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Creates a signed JWT access token containing the provided data dictionary
    plus an expiration timestamp ('exp').
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decodes and validates a JWT token.
    Returns the payload dictionary if valid.
    Raises HTTPException 401 if invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =========================================================
# 3. FASTAPI AUTHENTICATION DEPENDENCY
# =========================================================
# WHAT IS A "DEPENDENCY" IN FASTAPI?
# It is a helper function that FastAPI automatically calls BEFORE running
# an endpoint function.
#
# If an endpoint has: `current_user = Depends(get_current_user)`:
#   1. FastAPI intercepts the request
#   2. Checks for "Authorization: Bearer <token>"
#   3. Decodes the token
#   4. Looks up the user in SQLite
#   5. Passes the clean user dict into your endpoint function
#   6. If anything fails (no token, expired token, fake token),
#      FastAPI immediately stops and returns HTTP 401 Unauthorized!
# =========================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer)
) -> dict:
    """
    Extracts the Bearer token from the HTTP Authorization header,
    decodes it, verifies the user exists, and returns the sanitized user dict
    (WITHOUT password_hash).
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing user identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier in token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from SQLite using the configured database path
    user = get_user_by_id(user_id_int)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Sanitize: NEVER return password_hash to endpoints
    clean_user = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "age": user.get("age"),
        "gender": user.get("gender"),
        "created_at": user.get("created_at")
    }
    return clean_user
