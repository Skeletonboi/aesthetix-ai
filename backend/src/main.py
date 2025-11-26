from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from src.workout_logs.routes import workout_logs_router
from src.exercise.routes import exercise_router
from src.auth.routes import auth_router
from src.tags.routes import tag_router
from src.rag.routes import rag_router
from src.db.db import init_db, get_session_context
from src.exercise.service import ExerciseService
from src.workout_logs.service import WorkoutLogService
from src.auth.service import UserService
from src.tags.service import TagService
from src.exercise.schemas import ExerciseCreate
from src.workout_logs.schemas import WorkoutLogCreate, WorkoutLogUpdate
from src.auth.schemas import UserCreate
from src.tags.schemas import TagCreate
from src.config import Config
from contextlib import asynccontextmanager
import json
import os

version = 1
description = """
REST API backend application built using FastAPI for a gym exercise tracker.

Includes ability to: 
TBD
"""
version_prefix = f"/v{version}"

async def load_seed_data(seed_file: str):
    with open(seed_file, 'r') as f:
        seed_dict = json.load(f)
    
    exc_service = ExerciseService()
    log_service = WorkoutLogService()
    user_service = UserService()
    tag_service = TagService()
    
    async with get_session_context() as session:
        # Attempt seed user data insertion
        for user in seed_dict["seed_users"]:
            if not await user_service.get_user_by_email(user["email"], session):
                res = await user_service.create_user(UserCreate(**user), session)
        
        # Attempt seed tag insertion
        for tag in seed_dict["seed_tags"]:
            if not await tag_service.get_tag_by_slug(tag["tag_name"], session):
                res = await tag_service.create_tag(TagCreate(**tag), session)

        # Attempt seed exercise insertion
        for exercise in seed_dict["seed_exercises"]:
            if not await exc_service.get_exercise_by_slug(exercise["exercise_slug"], session):
                res = await exc_service.create_exercise(ExerciseCreate(**exercise), session)

        # Attempt seed log insertion
        # Normally uid is collected from credentials, here we search manually
        seed_user = await user_service.get_user_by_email(user["email"], session)
        seed_user_uid = seed_user.uid
        
        for log in seed_dict["seed_workout_logs"]:
            await log_service.upsert_log(WorkoutLogUpdate(**log), 
                                         seed_user_uid,
                                         session)
    return


@asynccontextmanager
async def startup(app: FastAPI):
    dev = True

    await init_db()
    if dev:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        seed_data_path = os.path.join(current_dir, "tests", "seed_data.json")
        await load_seed_data(seed_data_path)
    yield

app = FastAPI(
    lifespan=startup,
    title = "Gym Tracker",
    description = description
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:5173"],  # Frontend development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=Config.SESSION_SECRET_KEY
)

app.include_router(workout_logs_router, prefix=f"{version_prefix}/workout_log", tags=['workout_logs'])
app.include_router(exercise_router, prefix=f"{version_prefix}/exercise", tags=['exercises'])
app.include_router(auth_router, prefix=f"{version_prefix}/user", tags=['users'])
app.include_router(tag_router, prefix=f"{version_prefix}/tag", tags=["tags"])
app.include_router(rag_router, prefix=f"{version_prefix}/rag", tags=["rag"])