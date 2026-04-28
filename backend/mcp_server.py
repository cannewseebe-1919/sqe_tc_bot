"""
SQE Test Executor MCP Server

Claude CLI에서 테스트 실행을 직접 트리거할 수 있는 MCP 서버입니다.

사용법:
  1. 패키지 설치: pip install mcp httpx
  2. sqe_tc_bot 폴더에서 Claude Code 실행 (자동으로 .mcp.json 로드)

환경변수:
  EXECUTOR_BASE_URL  - executor 서버 주소 (기본: http://localhost:8001)
  BACKEND_URL        - tc_bot 백엔드 주소 (기본: http://localhost:8000)
  EXECUTOR_JWT_TOKEN - JWT 토큰 (DEV_MODE=true면 비워도 됨)
"""

import asyncio
import os
import httpx
from mcp.server.fastmcp import FastMCP

EXECUTOR_BASE_URL = os.getenv("EXECUTOR_BASE_URL", "http://localhost:8001")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
EXECUTOR_JWT_TOKEN = os.getenv("EXECUTOR_JWT_TOKEN", "")

mcp = FastMCP("SQE Test Executor")


def _auth_headers() -> dict:
    """JWT 토큰이 설정된 경우 Authorization 헤더를 반환합니다.
    executor의 DEV_MODE=true이면 토큰 없이도 동작합니다."""
    if EXECUTOR_JWT_TOKEN:
        return {"Authorization": f"Bearer {EXECUTOR_JWT_TOKEN}"}
    return {}


@mcp.tool()
async def list_devices() -> dict:
    """
    테스트에 사용 가능한 단말 목록을 반환합니다.
    각 단말의 ID, 이름, 상태(CONNECTED/TESTING/OFFLINE 등), 모델명, Android 버전, 큐 길이를 포함합니다.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{EXECUTOR_BASE_URL}/api/devices",
            headers=_auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def execute_test(
    test_code: str,
    device_id: str,
    requested_by: str = "mcp-user",
) -> dict:
    """
    테스트 코드를 지정한 단말에서 실행합니다.
    tc_bot 백엔드를 경유하여 실행 기록이 DB에 저장되고 콜백이 정상 처리됩니다.

    Args:
        test_code: 실행할 Python 테스트 코드 (TestCase SDK 기반)
        device_id: list_devices()로 조회한 단말 ID
        requested_by: 요청자 식별자 (기본값: mcp-user)

    Returns:
        execution_id, status (QUEUED or RUNNING), queue_position 포함
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{BACKEND_URL}/api/execute-code",
            json={
                "test_code": test_code,
                "device_id": device_id,
                "requested_by": requested_by,
            },
        )
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_execution_status(execution_id: str) -> dict:
    """
    테스트 실행 상태를 조회합니다.

    Args:
        execution_id: execute_test()에서 반환된 execution_id

    Returns:
        status (QUEUED/RUNNING/COMPLETED/FAILED/ABORTED), current_step, progress 등
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{EXECUTOR_BASE_URL}/api/execute/{execution_id}/status",
            headers=_auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_execution_result(execution_id: str) -> dict:
    """
    완료된 테스트의 상세 결과를 조회합니다.

    Args:
        execution_id: execute_test()에서 반환된 execution_id

    Returns:
        status, steps별 결과(PASSED/FAILED), crash_logs, device_info, 총 소요 시간 등
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{EXECUTOR_BASE_URL}/api/execute/{execution_id}/result",
            headers=_auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def wait_for_completion(execution_id: str, timeout_seconds: int = 300) -> dict:
    """
    테스트가 완료될 때까지 폴링하며 기다린 후 상세 결과를 반환합니다.

    Args:
        execution_id: 모니터링할 execution_id
        timeout_seconds: 최대 대기 시간 (기본 300초)

    Returns:
        완료 시 상세 결과(steps, crash_logs, device_info 포함), 타임아웃 시 TIMEOUT 상태
    """
    terminal_statuses = {"COMPLETED", "FAILED", "ABORTED"}
    elapsed = 0
    poll_interval = 3

    async with httpx.AsyncClient(timeout=10.0) as client:
        while elapsed < timeout_seconds:
            resp = await client.get(
                f"{EXECUTOR_BASE_URL}/api/execute/{execution_id}/status",
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") in terminal_statuses:
                # 상세 결과 조회
                result_resp = await client.get(
                    f"{EXECUTOR_BASE_URL}/api/execute/{execution_id}/result",
                    headers=_auth_headers(),
                )
                if result_resp.status_code == 200:
                    return result_resp.json()
                return data

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

    return {"execution_id": execution_id, "status": "TIMEOUT", "elapsed_seconds": elapsed}


if __name__ == "__main__":
    mcp.run()
