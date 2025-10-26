import pytest
import pytest_asyncio
from httpx import AsyncClient

@pytest_asyncio.fixture()
async def test_get_all_tags(temp_client: AsyncClient, test_user_login):
    access_token = test_user_login["access_token"]

    res = await temp_client.get("/v1/tag/all",
                                headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 200

    return res.json()

@pytest.mark.asyncio
async def test_get_tag_by_id(temp_client: AsyncClient, test_user_login, test_get_all_tags):
    access_token = test_user_login["access_token"]
    tag_id = test_get_all_tags[0]["tid"]

    res = await temp_client.get(f"/v1/tag/{tag_id}",
                                headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_create_tag(temp_client: AsyncClient, test_user_login):
    access_token = test_user_login["access_token"]
    test_tag = {
        "tag_name" : "test_bodypart",
        "tag_color" : "#000000"
    }

    res = await temp_client.post("/v1/tag/",
                                 json=test_tag,
                                 headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 201

@pytest.mark.asyncio
async def test_update_tag(temp_client: AsyncClient, test_user_login, test_get_all_tags):
    access_token = test_user_login["access_token"]
    tag_id = test_get_all_tags[0]["tid"]
    test_tag = {
        "tag_name" : "test_update_bodypart",
        "tag_color" : "#000000"
    }

    res = await temp_client.patch(f"/v1/tag/{tag_id}",
                                 json=test_tag,
                                 headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_delete_tag(temp_client: AsyncClient, test_user_login, test_get_all_tags):
    access_token = test_user_login["access_token"]
    tag_id = test_get_all_tags[0]["tid"]

    res = await temp_client.delete(f"/v1/tag/{tag_id}",
                                 headers={"Authorization" : f"Bearer {access_token}"})
    assert res.status_code == 204