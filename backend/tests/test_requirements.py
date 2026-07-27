import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_requirement_crud_and_dashboard_stats(client: AsyncClient):
    # Check empty dashboard stats
    dash_res = await client.get("/api/dashboard/stats")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["total_candidates"] == 0
    assert dash_data["active_requirements"] == 0
    assert dash_data["average_match_score"] == 0.0

    # Create Requirement
    req_payload = {
        "job_title": "Backend Architect",
        "job_description": "Design distributed microservices",
        "minimum_experience": 5,
        "location": "Remote",
        "skills": [
            {"skill": "Python", "importance": "MANDATORY"},
            {"skill": "Docker", "importance": "PREFERRED"}
        ]
    }

    create_res = await client.post("/api/requirements", json=req_payload)
    assert create_res.status_code == 201
    req_data = create_res.json()
    assert req_data["job_title"] == "Backend Architect"
    assert len(req_data["skills"]) == 2

    # Check dashboard stats after creating requirement
    dash_res2 = await client.get("/api/dashboard/stats")
    assert dash_res2.json()["active_requirements"] == 1

    # Cleanup
    del_res = await client.delete(f"/api/requirements/{req_data['id']}")
    assert del_res.status_code == 204
