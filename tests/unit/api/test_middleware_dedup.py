import asyncio
import time

import httpx
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.middleware.request_deduplication import RequestDeduplicationMiddleware

app = FastAPI()

app.add_middleware(
    RequestDeduplicationMiddleware,
    max_size=100,
    default_ttl_seconds=10,
)

request_counts = {}


@app.get("/slow-endpoint/{path:path}")
async def slow_endpoint(req: Request, sleep_time: float = 0.5):
    """An endpoint that is deliberately slow to test concurrent requests."""
    # Since we dedup on method, path, query
    path = req.url.path
    if path not in request_counts:
        request_counts[path] = 0
    request_counts[path] += 1

    await asyncio.sleep(sleep_time)

    return JSONResponse(content={"status": "success", "count": request_counts[path]})


@pytest.mark.asyncio
async def test_dedup_concurrency():
    """Test that concurrent duplicate requests are deduplicated and only executed once."""
    request_counts.clear()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Fire multiple concurrent requests to the same endpoint
        # Use a path that is unique for this test run
        path = f"/slow-endpoint/{time.time()}"
        tasks = []
        for _ in range(5):
            tasks.append(client.get(f"{path}?sleep_time=0.5"))

        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        duration = time.time() - start_time

        # All responses should be successful
        assert all(r.status_code == 200 for r in responses)

        # Verify that the handler was only called once (request collapsing)
        # The request_counts key should have value 1
        # Find the key that matches our path
        actual_path = None
        for k in request_counts.keys():
            if k.startswith(path):
                actual_path = k
                break

        assert actual_path is not None
        assert request_counts[actual_path] == 1

        # Verify that all responses have the same count in their body
        for r in responses:
            assert r.json()["count"] == 1

        # Verify timing: it should take roughly sleep_time, not sleep_time * 5
        assert duration < 1.0  # 0.5s sleep + overhead

    # Verify that a subsequent request is also cached
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        res = await client.get(f"{path}?sleep_time=0.5")
        assert res.status_code == 200
        assert res.json()["count"] == 1
        # Handler count should still be 1
        assert request_counts[actual_path] == 1
