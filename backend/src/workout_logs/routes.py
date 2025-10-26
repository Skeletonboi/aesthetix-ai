from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from typing import List
from datetime import date
from src.workout_logs.schemas import WorkoutLogCreate, WorkoutLogResponse, WorkoutLogUpdate
from src.workout_logs.service import WorkoutLogService
from src.auth.dependencies import AccessTokenBearer, RoleChecker
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from src.db.db import get_session

workout_logs_router = APIRouter()
workout_logs_service = WorkoutLogService()
access_token_bearer = AccessTokenBearer()
role_checker = RoleChecker(["user", "admin"])

@workout_logs_router.get("/", response_model=List[WorkoutLogResponse], dependencies=[Depends(role_checker)])
async def get_logs(
    query_date: date | None = None, 
    slug: str | None = None,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer)
):
    if query_date:
        result = await workout_logs_service.get_logs_by_day(query_date, session)
    elif slug:
        result = await workout_logs_service.get_logs_by_exercise(slug, session)
    else:
        result = await workout_logs_service.get_logs_all(session)
        
    return result


# This API only exposes user logs of the user in the beared credential
@workout_logs_router.get("/user_logs", response_model=List[WorkoutLogResponse], dependencies=[Depends(role_checker)])
async def get_logs_by_user(
    session: AsyncSession = Depends(get_session), 
    token_details: dict = Depends(access_token_bearer)
):
    result = await workout_logs_service.get_logs_by_user(
        UUID(token_details["user"]["uid"]), 
        session)
    
    return result


@workout_logs_router.get("/{log_id}", response_model=WorkoutLogResponse, dependencies=[Depends(role_checker)])
async def get_log_by_id(
    log_id: UUID, 
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer)
):
    result = await workout_logs_service.get_log_by_id(log_id, session)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return result


@workout_logs_router.get("/pr/", response_model=WorkoutLogResponse, dependencies=[Depends(role_checker)])
async def get_pr_log_by_ex(
    exercise_slug: str,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer)
):
    uid = UUID(token_details["user"]["uid"])
    result = await workout_logs_service.get_pr_log_by_ex(exercise_slug, uid, session)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No personal record found for this exercise")

    return result

@workout_logs_router.post("/", status_code=status.HTTP_201_CREATED, response_model=WorkoutLogResponse, 
                          dependencies=[Depends(role_checker)])
async def create_log(
    log_data: WorkoutLogCreate,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer)
):
    uid = UUID(token_details["user"]["uid"])
    new_log = await workout_logs_service.create_log(log_data,
                                                    uid,
                                                    session)
    return new_log


@workout_logs_router.patch("/{wid}", response_model=WorkoutLogResponse, dependencies=[Depends(role_checker)])
async def update_log(
    wid: UUID, 
    update_data: WorkoutLogUpdate,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer)
):
    old_log = await workout_logs_service.get_log_by_id(wid, session)
    
    if not old_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    new_log = await workout_logs_service.update_log(wid, 
                                                    update_data,
                                                    session)
    return new_log


@workout_logs_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, 
                            dependencies=[Depends(role_checker)])
async def delete_log(
    id: UUID, 
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer)
):    
    _ = await workout_logs_service.delete_log(id, session)
        
    return

@workout_logs_router.delete("/day/{date}", status_code=status.HTTP_204_NO_CONTENT, 
                            dependencies=[Depends(role_checker)])
async def delete_logs_by_day(
    date: date,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer)
):
    uid = UUID(token_details["user"]["uid"])
    _ = await workout_logs_service.delete_logs_by_day(date, uid, session)

    return
# @workout_logs_router.post("/", response_model=WorkoutLogBase)
# async def upsert_log(log_data: WorkoutLogBase, session: AsyncSession = Depends(get_session)):
#     # This route is (currently) only used to upsert seed test data
#     new_log = await workout_logs_service.upsert_log(log_data, session)

#     return new_log