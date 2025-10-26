import pytest
import pytest_asyncio
from src.tests.conftest import SEED_EXERCISES, SEED_TAGS
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_exercise_by_slug(temp_client: AsyncClient, test_user_login):
    access_token = test_user_login["access_token"]

    for ex in SEED_EXERCISES:
        res = await temp_client.get("/v1/exercise/", 
                              params={"slug" : ex["exercise_slug"]},
                              headers={"Authorization" : f"Bearer {access_token}"})
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_get_all_exercises(temp_client: AsyncClient, test_user_login):
    access_token = test_user_login["access_token"]
    
    res = await temp_client.get("/v1/exercise/all",
                                headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_create_exercise(temp_client: AsyncClient, test_user_login):
    access_token = test_user_login["access_token"]

    test_exercise_data = {"exercise_slug" : "db-pullups", 
                          "exercise_name" : "Dumbell Pullups",
                          "tag_slugs" : ["Pull"]}
    res = await temp_client.post("/v1/exercise/", 
                                 json=test_exercise_data,
                                 headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 201

@pytest.mark.asyncio
async def test_update_exercise(temp_client: AsyncClient, test_user_login):
    access_token = test_user_login["access_token"]

    test_update_data = {"exercise_slug" : "bb-squat", 
                        "exercise_name" : "BB Squat Variation",
                        "tag_slugs" : ["Legs", "Pull"],
                        "new_slug" : "bb-squat-variation"}

    SEED_EXERCISES[0]["exercise_slug"]
    res = await temp_client.patch("/v1/exercise/{seed_ex_slug}", 
                                 json=test_update_data,
                                 headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_delete_exercise(temp_client: AsyncClient, test_user_login):
    access_token = test_user_login["access_token"]

    seed_ex_slug = SEED_EXERCISES[1]["exercise_slug"]
    res = await temp_client.delete(f"/v1/exercise/{seed_ex_slug}",
                                   headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 204

@pytest.mark.asyncio
async def test_get_exercises_by_tag_id(temp_client: AsyncClient, test_user_login):
    access_token = test_user_login["access_token"]

    res = await temp_client.get("/v1/tag/all",
                                headers={"Authorization" : f"Bearer {access_token}"})
    tags = res.json()
    tid = tags[0]["tid"]
    res = await temp_client.get(f"/v1/exercise/tag/?tid={tid}",
                                headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 200
