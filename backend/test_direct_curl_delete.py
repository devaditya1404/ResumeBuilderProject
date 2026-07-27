#!/usr/bin/env python3
"""
test_direct_curl_delete.py — Test direct backend DELETE and OPTIONS preflight via curl.
"""
import asyncio
import json
import os
import subprocess
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal, init_db
from app.models import Candidate


async def main():
    print("=" * 75)
    print("1. CREATING TEMPORARY DELETE TEST CANDIDATE VIA DB")
    print("=" * 75)

    await init_db()
    temp_id = str(uuid.uuid4())

    async with AsyncSessionLocal() as session:
        cand = Candidate(
            id=temp_id,
            name="DELETE TEST CANDIDATE",
            email="delete.test@example.com",
            current_designation="Temporary Tester"
        )
        session.add(cand)
        await session.commit()

    print(f"Created Temp Candidate ID: {temp_id}")

    # 2. Test OPTIONS CORS Preflight
    print("\n" + "=" * 75)
    print("2. TESTING CORS OPTIONS PREFLIGHT")
    print("=" * 75)
    cmd_options = f'curl -i -X OPTIONS http://127.0.0.1:8000/api/candidates/{temp_id} -H "Origin: http://localhost:3001" -H "Access-Control-Request-Method: DELETE"'
    res_options = subprocess.run(cmd_options, shell=True, capture_output=True, text=True)
    print("OPTIONS PREFLIGHT RESPONSE:")
    print(res_options.stdout[:500])

    # 3. Test Direct curl DELETE
    print("\n" + "=" * 75)
    print("3. TESTING DIRECT BACKEND CURL DELETE")
    print("=" * 75)
    cmd_delete = f'curl -i -X DELETE http://127.0.0.1:8000/api/candidates/{temp_id}'
    res_delete = subprocess.run(cmd_delete, shell=True, capture_output=True, text=True)
    print("CURL DELETE RESPONSE:")
    print(res_delete.stdout[:500])

    # 4. Verify candidate is deleted
    async with AsyncSessionLocal() as session:
        stmt = session.query(Candidate).where(Candidate.id == temp_id) if hasattr(session, 'query') else None
        res_cand = await session.execute(Candidate.__table__.select().where(Candidate.id == temp_id))
        del_check = res_cand.scalar_one_or_none()
        if del_check is None:
            print("\nVERIFICATION: Candidate successfully deleted from DB!")
            print("BACKEND DELETE DIRECT TEST: PASS")
        else:
            print("\nVERIFICATION FAIL: Candidate still in DB!")
            print("BACKEND DELETE DIRECT TEST: FAIL")


if __name__ == "__main__":
    asyncio.run(main())
