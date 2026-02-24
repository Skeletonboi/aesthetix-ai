import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.db import Session, get_session, async_engine
from src.main import app
from httpx import ASGITransport, AsyncClient
import os
import json

base_dir = os.path.dirname(os.path.abspath(__file__))
SEED_DATA_PATH = os.path.join(base_dir, "seed_data.json")

with open(SEED_DATA_PATH, "r") as f:
    seed_data = json.load(f)

SEED_USER = seed_data["seed_users"][0]
SEED_EXERCISES = seed_data["seed_exercises"]
SEED_WORKOUT_LOGS = seed_data["seed_workout_logs"]
SEED_TAGS = seed_data["seed_tags"]

async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_engine.connect() as conn:
        trans = await conn.begin()
        async with Session(bind=conn) as session:
            yield session
            await session.close()
        await trans.rollback()

@pytest.fixture()
def temp_app():
    app.dependency_overrides[get_session] = get_test_session
    return app 

@pytest_asyncio.fixture()
async def temp_client(temp_app):
    transport = ASGITransport(app=temp_app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        yield ac

@pytest_asyncio.fixture
async def test_user_login(temp_client: AsyncClient):
    response = await temp_client.post("/v1/user/login",
                                 json = {
                                     "email" : SEED_USER["email"],
                                     "password" : SEED_USER["password"]
                                 })
    assert response.status_code == 200
    response_json = response.json()

    return {
        "access_token" : response_json["access_token"],
        "refresh_token" : response_json["refresh_token"]
    }
