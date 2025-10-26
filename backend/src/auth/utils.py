import jwt
import logging
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from src.config import Config
import uuid
from src.db.redis_cache import add_jti_to_blocklist

pwd_context = CryptContext(schemes=["bcrypt"])

def generate_pwd_hash(pwd: str) -> str:
    return  pwd_context.hash(pwd)


def verify_pwd(pwd: str, hash: str) -> bool:
    return pwd_context.verify(pwd, hash)


def generate_jwt(user_data: dict, expiry: timedelta = timedelta(minutes=60), refresh: bool = False) -> str:
    payload = {
        "user": user_data,
        "exp": datetime.now(timezone.utc) + expiry,
        "jti": str(uuid.uuid4()),
        "refresh": refresh
    }

    token = jwt.encode(
        payload=payload,
        key=Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )

    return token

def decode_validate_jwt(token: str) -> dict:
    # jwt.decode method automatically checks for JWT integrity and exp expiry
    try:
        jwt_data = jwt.decode(
            jwt=token,
            key=Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM]
        )

        return jwt_data
    
    except jwt.PyJWTError as jwte:
        logging.exception(jwte)
        return None
        
    except Exception as e:
        logging.exception(e)
        return None

async def revoke_access_refresh(access_payload: dict, refresh_token: str) -> None:
    # Revoke access token
    await add_jti_to_blocklist(access_payload["jti"])
    # Parse refresh token
    refresh_payload = decode_validate_jwt(refresh_token)
    # Revoke refresh token
    await add_jti_to_blocklist(refresh_payload["jti"])

    return