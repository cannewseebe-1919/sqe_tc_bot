from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.models.database import get_db
from app.models.models import Execution, ExecutionStep, TestCase
from app.schemas.schemas import (
    ExecutionRequest,
    ExecutionResultCallback,
    ExecutionStatusResponse,
    DeviceListResponse,
)
from app.services.executor_client import get_devices, request_execution, get_execution_status

router = APIRouter(prefix="/api", tags=["execution"])


@router.get("/devices", response_model=DeviceListResponse)
async def list_devices(user: dict = Depends(get_current_user)):
    data = await get_devices()
    return DeviceListResponse(**data)


@router.post("/execute", response_model=ExecutionStatusResponse)
async def execute_test(
    req: ExecutionRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tc = await db.get(TestCase, req.test_case_id)
    if not tc:
        raise HTTPException(status_code=404, detail="TestCase not found")

    result = await request_execution(
        test_code=tc.code,
        device_id=req.device_id,
        requested_by=user["email"],
    )

    execution = Execution(
        id=result["execution_id"],
        test_case_id=req.test_case_id,
        device_id=req.device_id,
        requested_by=user["email"],
        status=result["status"],
        queue_position=result.get("queue_position", 0),
    )
    db.add(execution)
    await db.commit()

    return ExecutionStatusResponse(
        execution_id=result["execution_id"],
        status=result["status"],
    )


@router.get("/execute/{execution_id}/status", response_model=ExecutionStatusResponse)
async def execution_status(
    execution_id: str,
    user: dict = Depends(get_current_user),
):
    data = await get_execution_status(execution_id)
    return ExecutionStatusResponse(**data)


@router.post("/execution-result")
async def execution_result_callback(
    result: ExecutionResultCallback,
    db: AsyncSession = Depends(get_db),
):
    """Callback endpoint: Test Executor calls this with execution results."""
    execution = await db.get(Execution, result.execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution.status = result.status
    execution.started_at = result.started_at
    execution.finished_at = result.finished_at
    execution.total_duration_sec = result.total_duration_sec

    for i, step in enumerate(result.steps):
        db.add(ExecutionStep(
            execution_id=result.execution_id,
            step_name=step.step_name,
            step_order=step.step_order if step.step_order else i + 1,
            status=step.status,
            duration_sec=step.duration_sec,
            screenshot_path=step.screenshot_url,
            log=step.log,
            error_type=step.error_type,
        ))

    await db.commit()
    return {"status": "ok"}
