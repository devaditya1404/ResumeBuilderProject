import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_empty_candidates_list(client: AsyncClient):
    response = await client.get("/api/candidates")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_create_candidate_with_nullable_fields_preserved(client: AsyncClient):
    # Candidate payload omitting notice_period, expected_salary, preferred_location
    payload = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "phone": "+1 555 0199",
        "current_company": "Tech Corp",
        "current_designation": "Software Engineer",
        "experience_years": 4.5,
        "professional_summary": "Experienced full-stack engineer.",
        "skills": ["Python", "FastAPI", "React"],
        "experiences": [
            {
                "company": "Tech Corp",
                "designation": "Software Engineer",
                "start_date": "2022-01",
                "end_date": "Present",
                "is_current": True,
                "responsibilities": ["Built scalable backend APIs"],
                "clients": ["Client A", "Client B"]
            }
        ]
    }

    response = await client.post("/api/candidates", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane.doe@example.com"

    # STRICT CHECK: Missing fields MUST remain null!
    assert data["notice_period"] is None
    assert data["expected_salary"] is None
    assert data["preferred_location"] is None

    # Check relationships
    assert len(data["skills"]) == 3
    assert len(data["experiences"]) == 1
    assert data["experiences"][0]["clients"] == ["Client A", "Client B"]

    cand_id = data["id"]

    # Verify retrieval GET /api/candidates/{id}
    get_res = await client.get(f"/api/candidates/{cand_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["notice_period"] is None

    # Clean up test candidate
    del_res = await client.delete(f"/api/candidates/{cand_id}")
    assert del_res.status_code == 204

    # Verify DB is empty again
    empty_res = await client.get("/api/candidates")
    assert empty_res.json() == []
