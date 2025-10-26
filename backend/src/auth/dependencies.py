from fastapi import status, Request, Depends
from src.db.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from fastapi.exceptions import HTTPException
from src.auth.utils import decode_validate_jwt
from src.auth.schemas import UserBase
from src.db.redis_cache import token_in_blocklist
from src.auth.service import UserService
from typing import List


user_service = UserService()

class TokenBearer(HTTPBearer):
    def __init__(self, auto_error=True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> dict:
        # Get Bearer credentials from JWT payload data in request  
        creds : HTTPAuthorizationCredentials = await super().__call__(request)

        token = creds.credentials

        payload = decode_validate_jwt(token)

        if not payload:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={
                "error": "Invalid or expired token.",
                "resolution": "Please get a new token."
            })
        elif await token_in_blocklist(payload["jti"]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={
                "error": "Token is revoked.",
                "resolution": "Please get a new token."
            })
        
        self.verify_payload(payload)

        return payload
    
    def verify_payload(self, payload: dict):
        raise NotImplementedError("Please override method in child classes")
    

class AccessTokenBearer(TokenBearer):
    def verify_payload(self, payload) -> None:
        if payload["refresh"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Please provide an access token instead of refresh token.")

class RefreshTokenBearer(TokenBearer):
    def verify_payload(self, payload) -> None:
        if not payload["refresh"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Please provide refresh token.")
        
async def get_current_user(
        payload: dict = Depends(AccessTokenBearer()),
        session: AsyncSession = Depends(get_session)
) -> UserBase:
    user_email = payload["user"]["email"]
    user = await user_service.get_user_by_email(user_email, session)

    return UserBase.model_validate(user)

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: UserBase = Depends(get_current_user)):
        if current_user.role in self.allowed_roles:
            return True
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="You are not allowed to perform this action.")