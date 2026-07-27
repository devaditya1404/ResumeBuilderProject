import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_root_healthcheck(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "SQLite" in data["database"]
