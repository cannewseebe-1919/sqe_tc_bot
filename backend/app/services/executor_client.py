import httpx

from app.core.config import get_settings

settings = get_settings()


async def get_devices() -> dict:
    async with httpx.AsyncClient(base_url=settings.EXECUTOR_BASE_URL) as client:
        resp = await client.get("/api/devices")
        resp.raise_for_status()
        return resp.json()


async def request_execution(test_code: str, device_id: str, requested_by: str) -> dict:
    async with httpx.AsyncClient(base_url=settings.EXECUTOR_BASE_URL) as client:
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
    async with httpx.AsyncClient(base_url=settings.EXECUTOR_BASE_URL) as client:
        resp = await client.get(f"/api/execute/{execution_id}/status")
        resp.raise_for_status()
        return resp.json()
