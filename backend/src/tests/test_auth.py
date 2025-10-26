import pytest
import pytest_asyncio
from httpx import AsyncClient
from src.tests.conftest import SEED_USER
from datetime import datetime

@pytest.mark.asyncio
async def test_user_signup(temp_client: AsyncClient):
    test_user_data = {
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe",
        "email": "johndoe123@co.com",
        "password": "testpass123",
        "birth_month" : 1,
        "birth_year" : 2000,
        "height_raw" : 187,
        "height_unit" : "CENTIMETERS"
        }
    response = await temp_client.post("/v1/user/signup", json=test_user_data)
    user = response.json()

    seed_age = datetime.now().year - test_user_data['birth_year']
    if test_user_data['birth_month'] > datetime.now().month:
        seed_age -= 1

    assert user["age"] == seed_age
    assert user["full_name"] == " ".join([test_user_data['first_name'], test_user_data['last_name']])
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_user_refresh(temp_client: AsyncClient, test_user_login):
    refresh_token = test_user_login["refresh_token"]

    response = await temp_client.get("/v1/user/refresh_token", 
                                headers={"Authorization" : f"Bearer {refresh_token}"})
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_current_user(temp_client: AsyncClient, test_user_login):
    access_token = test_user_login["access_token"]

    response = await temp_client.get("v1/user/me", headers={"Authorization" : f"Bearer {access_token}"})
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_user_delete(temp_client: AsyncClient, test_user_login):
    access_token = test_user_login["access_token"]
    refresh_token = test_user_login["refresh_token"]

    response = await temp_client.delete(f"/v1/user/delete/{refresh_token}",
                                 headers = {"Authorization" : f"Bearer {access_token}"})
    assert response.status_code == 200

