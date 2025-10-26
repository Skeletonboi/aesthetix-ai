from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from src.exercise.service import ExerciseService
from src.exercise.schemas import ExerciseBase, ExerciseCreate, ExerciseUpdate, ExerciseResponse
from src.db.db import get_session
from src.auth.dependencies import AccessTokenBearer, RoleChecker
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

exercise_router = APIRouter()
exercise_service = ExerciseService()
access_token_bearer = AccessTokenBearer()
role_checker = RoleChecker(["user", "admin"])


@exercise_router.get("/", response_model=ExerciseResponse, dependencies=[Depends(role_checker)])
async def get_exercise_by_slug(
    slug: str,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer)
):
    result = await exercise_service.get_exercise_by_slug(slug, session)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No exercise found.")
        
    return result


@exercise_router.get("/tag/", response_model=List[ExerciseResponse], dependencies=[Depends(role_checker)])
async def get_exercises_by_tag_id(
    tid: UUID,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer)
):
    result = await exercise_service.get_exercises_by_tag_id(tid, session)

    return result


@exercise_router.get("/all", response_model=List[ExerciseResponse], dependencies=[Depends(role_checker)])
async def get_all_exercises(
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer)
):
    result = await exercise_service.get_all_exercises(session)

    return result


@exercise_router.post("/", status_code=status.HTTP_201_CREATED, response_model=ExerciseBase, 
                      dependencies=[Depends(role_checker)])
async def create_exercise(
    exercise_data: ExerciseCreate, 
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer)
):
    new_exercise = await exercise_service.create_exercise(exercise_data, session)

    return new_exercise


@exercise_router.patch("/{exercise_slug}", response_model=ExerciseBase, 
                       dependencies=[Depends(role_checker)])
async def update_exercise(
    update_data: ExerciseUpdate,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer)
):
    updated_exercise = await exercise_service.update_exercise(update_data, session)

    return updated_exercise

@exercise_router.delete("/{exercise_slug}", status_code=status.HTTP_204_NO_CONTENT, 
                        dependencies=[Depends(role_checker)])
async def delete_exercise(
    exercise_slug: str, 
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer)
):
    # Query if exercise exists
    ex = await exercise_service.get_exercise_by_slug(exercise_slug, session)
    if not ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    _ = await exercise_service.delete_exercise(exercise_slug, session)

    return