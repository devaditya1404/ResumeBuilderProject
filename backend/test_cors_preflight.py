import asyncio
import httpx
from app.main import app

async def test_preflights():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        endpoints = [
            "/api/dashboard/stats",
            "/api/resumes/upload",
            "/api/candidates",
            "/api/requirements"
        ]
        origins = [
            "https://talentvault-frontend.onrender.com",
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:5173"
        ]
        
        for origin in origins:
            for ep in endpoints:
                res = await client.options(
                    ep,
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "POST" if "upload" in ep else "GET",
                        "Access-Control-Request-Headers": "content-type"
                    }
                )
                assert res.status_code == 200, f"Failed preflight for {origin} {ep}"
                assert res.headers.get("access-control-allow-origin") == origin, f"Missing header for {origin}"
                assert res.headers.get("access-control-allow-credentials") == "true"
        print("ALL OPTIONS PREFLIGHT TESTS PASSED 100%!")

if __name__ == "__main__":
    asyncio.run(test_preflights())
