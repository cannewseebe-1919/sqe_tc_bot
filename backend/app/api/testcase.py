from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.models.database import get_db
from app.models.models import TestCase
from app.schemas.schemas import TestCaseCreate, TestCaseUpdate, TestCaseResponse

router = APIRouter(prefix="/api/testcases", tags=["testcase"])


@router.post("/", response_model=TestCaseResponse, status_code=201)
async def create_testcase(
    req: TestCaseCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tc = TestCase(
        title=req.title,
        code=req.code,
        created_by=user["sub"],
        source_type=req.source_type,
    )
    db.add(tc)
    await db.commit()
    await db.refresh(tc)
    return tc


@router.get("/", response_model=list[TestCaseResponse])
async def list_testcases(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TestCase).where(TestCase.created_by == user["sub"]).order_by(TestCase.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{tc_id}", response_model=TestCaseResponse)
async def get_testcase(
    tc_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tc = await db.get(TestCase, tc_id)
    if not tc:
        raise HTTPException(status_code=404, detail="TestCase not found")
    return tc


@router.patch("/{tc_id}", response_model=TestCaseResponse)
async def update_testcase(
    tc_id: str,
    req: TestCaseUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tc = await db.get(TestCase, tc_id)
    if not tc:
        raise HTTPException(status_code=404, detail="TestCase not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(tc, field, value)
    await db.commit()
    await db.refresh(tc)
    return tc
