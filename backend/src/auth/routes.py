from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.schemas import UserCreate, UserBase, UserLogin, UserLogout, UserUpdate
from src.auth.service import UserService
from src.auth.utils import decode_validate_jwt
from src.db.db import get_session
from src.auth.utils import verify_pwd, generate_jwt, revoke_access_refresh
from datetime import datetime, timedelta
from src.config import Config
from src.auth.dependencies import AccessTokenBearer, RefreshTokenBearer, get_current_user, RoleChecker
from uuid import UUID

auth_router = APIRouter()
user_service = UserService()
@auth_router.patch("/update", response_model=UserBase, status_code=status.HTTP_200_OK)
async def update_user(
    user_update_data: UserUpdate,  
    payload: dict = Depends(AccessTokenBearer()), 
    session: AsyncSession = Depends(get_session)
    ):
    updated_user = await user_service.update_user(UUID(payload["user"]["uid"]), user_update_data, session)
    return UserBase.model_validate(updated_user)


@auth_router.post("/signup", response_model=UserBase, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    # Check if user exists
    user = await user_service.get_user_by_email(user_data.email, session)
    if user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email address is already in use.")
    
    # Create user
    new_user = await user_service.create_user(user_data, session)

    return UserBase.model_validate(new_user)


@auth_router.post("/login")
async def login_user(login_data: UserLogin, session: AsyncSession = Depends(get_session)):
    # Perform user authentication
    user = await user_service.get_user_by_email(login_data.email, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No account under this email.")
    elif not verify_pwd(login_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect password")
    
    # Generate JWT
    user_data = {"email": user.email, "uid": str(user.uid)}
    access_token = generate_jwt(user_data)
    refresh_token = generate_jwt(user_data, expiry=timedelta(days=Config.REFRESH_TOKEN_EXPIRY), refresh=True)
    
    return JSONResponse(
        content={
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user_data
        } # this doesn't need to be a JSONResponse
    )


@auth_router.get("/refresh_token")
async def get_new_access_token(payload: dict = Depends(RefreshTokenBearer())):
    # I've found that this is redundant, exp is checked in the Depends() at jwt decoding
    # if datetime.now() > datetime.fromtimestamp(payload["exp"]):
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expired token.")
    
    new_access_token = generate_jwt(payload)
    
    return JSONResponse(content={"access_token": new_access_token}) # nor this

# Revokes both access token (auth header) and refresh token (request body)
@auth_router.post("/logout")
async def logout_user(logout_data: UserLogout, payload: dict = Depends(AccessTokenBearer())):
    _ = await revoke_access_refresh(access_token_payload = payload, 
                                    refresh_token = logout_data.refresh_token)
                                    
    return JSONResponse(content={"message": "Logged out successfully"}, # nor this
                        status_code=status.HTTP_200_OK)


@auth_router.get("/me", response_model=UserBase)
async def get_user(user: UserBase = Depends(get_current_user),
                   has_role: bool = Depends(RoleChecker(["admin", "user"]))):
    return user

# TBD Requires cascading otherwise this is broken
@auth_router.delete("/delete/{refresh_token}")
async def remove_user(
    refresh_token: str, 
    payload: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session)
    ):
    _ = await revoke_access_refresh(access_payload = payload, 
                                    refresh_token = refresh_token)
    await user_service.delete_user(UUID(payload["user"]["uid"]), session)

    return
    
