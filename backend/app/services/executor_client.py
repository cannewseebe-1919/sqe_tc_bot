"""Test Executor API client — singleton httpx client for connection pooling."""

import httpx

from app.core.config import get_settings

settings = get_settings()

_client: httpx.AsyncClient | None = None


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.EXECUTOR_BASE_URL,
            timeout=30.0,
        )
    return _client


async def close_client():
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None


async def get_devices() -> dict:
    client = await _get_client()
    resp = await client.get("/api/devices")
    resp.raise_for_status()
    return resp.json()


async def request_execution(test_code: str, device_id: str, requested_by: str) -> dict:
    client = await _get_client()
    resp = await client.post(
        "/api/execute",
        json={
            "test_code": test_code,
            "device_id": device_id,
            "requested_by": requested_by,
            "callback_url": settings.EXECUTOR_CALLBACK_URL,
        },
    )
    resp.raise_for_status()
    return resp.json()


async def get_execution_status(execution_id: str) -> dict:
    client = await _get_client()
    resp = await client.get(f"/api/execute/{execution_id}/status")
    resp.raise_for_status()
    return resp.json()
