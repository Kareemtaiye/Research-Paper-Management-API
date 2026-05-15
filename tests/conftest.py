import os

import asyncpg
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from app.main import app
from dotenv import load_dotenv

load_dotenv("/.env.test")
db_url = os.getenv("DATABASE_URL")

# Pure asyncpg connection string targeting the docker service name
# TEST_DATABASE_URL = "postgresql://test_user:password_test@db_test:5432/test_app_db"
print(db_url)


# Asynchronous client
@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Synchronous client
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def db_conn():
    # Connect directly to the isolated docker test database
    async with asyncpg.connect(db_url) as conn:
        # conn = await asyncpg.connect(TEST_DATABASE_URL)
        yield conn
    # await conn.close()
