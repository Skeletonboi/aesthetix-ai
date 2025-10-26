import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime
from src.tests.conftest import SEED_WORKOUT_LOGS

# TBD Missing test_get_by_id because awkward to access ID

@pytest.mark.asyncio
async def test_get_logs_all(temp_client: AsyncClient, test_user_login):
    access_token = test_user_login["access_token"]

    res = await temp_client.get("/v1/workout_log/", 
                                headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_get_logs_by_date(temp_client: AsyncClient, test_user_login):
    access_token = test_user_login["access_token"]

    for log in SEED_WORKOUT_LOGS:
        res = await temp_client.get("/v1/workout_log/", 
                                    params={"query_date" : log["date_performed"]},
                                    headers={"Authorization" : f"Bearer {access_token}"})
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_get_logs_by_slug(temp_client: AsyncClient, test_user_login):
    access_token = test_user_login["access_token"]

    for log in SEED_WORKOUT_LOGS:
        res = await temp_client.get("/v1/workout_log/", 
                                    params={"slug" : log["exercise_slug"]},
                                    headers={"Authorization" : f"Bearer {access_token}"})
        assert res.status_code == 200

@pytest_asyncio.fixture()
async def test_get_logs_by_user(temp_client: AsyncClient, test_user_login):
    access_token = test_user_login["access_token"]

    res = await temp_client.get("/v1/workout_log/user_logs",
                                headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 200
    return res.json()
    

@pytest.mark.asyncio
async def test_create_log(temp_client: AsyncClient, test_user_login):
    access_token = test_user_login["access_token"]

    test_log = {
        "exercise_slug" : "bb-bench-press",
        "reps" : 8,
        "weight" : 225,
        "date_performed" : "2025-05-15",
        "created_at" : "2025-05-15T21:55:02.234150",
        "tag_slugs" : ["Push"]
    }
    res = await temp_client.post("/v1/workout_log/",
                                 json=test_log,
                                 headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 201

@pytest.mark.asyncio
async def test_update_log(temp_client: AsyncClient, test_user_login, test_get_logs_by_user):
    access_token = test_user_login["access_token"]
    test_wid = test_get_logs_by_user[0]["wid"]

    test_update_data = {
        "exercise_slug" : "bb-bench-press",
        "reps" : 10,
        "weight" : 315,
        "date_performed" : "2025-05-15",
        "tag_slugs" : ["Push"]
    }

    res = await temp_client.patch(f"/v1/workout_log/{test_wid}",
                                  json=test_update_data,
                                  headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_delete_log(temp_client: AsyncClient, test_user_login, test_get_logs_by_user):
    access_token = test_user_login["access_token"]
    test_wid = test_get_logs_by_user[0]["wid"]

    res = await temp_client.delete(f"/v1/workout_log/{test_wid}",
                                   headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 204

@pytest.mark.asyncio
async def test_delete_log_by_day(temp_client: AsyncClient, test_user_login, test_get_logs_by_user):
    access_token = test_user_login["access_token"]
    day = test_get_logs_by_user[0]["date_performed"]

    res = await temp_client.delete(f"/v1/workout_log/day/{day}",
                                   headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 204

@pytest.mark.asyncio
async def test_get_pr_log(temp_client: AsyncClient, test_user_login):
    access_token = test_user_login["access_token"]
    test_exercise_slug = "bb-bench-press"

    res = await temp_client.get(f"/v1/workout_log/pr/?exercise_slug={test_exercise_slug}",
                                headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 200