from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.schemas import ExchangeData, UserCreate, UserBase, UserLogin, UserLogout, UserUpdate
from src.auth.service import UserService
from src.auth.utils import decode_validate_jwt
from src.db.db import get_session
from src.db.redis_cache import add_temp_login_response, delete_temp_login_response, get_temp_login_response, delete_temp_login_response
from src.auth.utils import verify_pwd, generate_jwt, revoke_access_refresh
from datetime import datetime, timedelta
from src.config import Config
from src.auth.dependencies import AccessTokenBearer, RefreshTokenBearer, get_current_user, RoleChecker
from uuid import UUID, uuid4
from authlib.integrations.starlette_client import OAuth
import secrets
import json

oauth = OAuth()
oauth.register(
    name="google",
    client_id=Config.GOOGLE_CLIENT_ID,
    client_secret=Config.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
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

# Frontend doesn't call this API, it directly navigates to this oauth2 endpoint to initiate login    
@auth_router.get("/login/google")
async def google_oauth_login(
    request: Request,
    frontend_auth_callback_route: str = "/auth/callback"
):
    request.session["frontend_auth_callback_route"] = frontend_auth_callback_route

    redirect_uri = request.url_for("google_oauth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@auth_router.get("/auth/google")
async def google_oauth_callback(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"OAuth2 Google Error: {e}")

    user_info = await oauth.google.userinfo(token=token)

    email = user_info.get("email", None)
    # google_id = user_info.get("sub") # Google's account ID not used for now
    full_name = user_info.get("name", None)
    
    first_name = user_info.get("given_name", None)
    last_name = user_info.get("family_name", None)
    
    if full_name:
        if not first_name:
            first_name = full_name.split()[0]
        if not last_name:
            if len(full_name) > 1:
                last_name = full_name.split()[-1]
            else:
                last_name = full_name

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Google Account has no email!")
    # Check if user with email exists
    user = await user_service.get_user_by_email(email, session)

    if not user:
        user_data = UserCreate(
            username=email,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password="",
            account_creation_type="GOOGLE"
        )
        user = await user_service.create_user(user_data, session)
        
    # Generate login data and access tokens
    user_data = {"email": user.email, "uid": str(user.uid)}
    access_token = generate_jwt(user_data)
    refresh_token = generate_jwt(user_data, expiry=timedelta(days=Config.REFRESH_TOKEN_EXPIRY), refresh=True)
    # Generate temporary code that will allow client to exchange for access tokens (because it can/should not be sent with the RedirectResponse)
    temp_auth_code = secrets.token_urlsafe(32)
    await add_temp_login_response(temp_auth_code, json.dumps({
        'user_data' : user_data,
        'access_token' : access_token,
        'refresh_token' : refresh_token
    }))
    # Need to redirect browser from OAuth2 backend login endpoint to frontend 
    frontend_auth_callback_route = request.session.get("frontend_auth_callback_route", "/auth/callback")
    return RedirectResponse(
        url = f"{Config.FRONTEND_URL}{frontend_auth_callback_route}?code={temp_auth_code}"
    )

@auth_router.post("/exchange_code")
async def exchange_code_for_login_response(
    exchange_data: ExchangeData
):
    login_res = await get_temp_login_response(exchange_data.code)
    if not login_res:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code for exchange!")
    
    await delete_temp_login_response(exchange_data.code)
    return json.loads(login_res)