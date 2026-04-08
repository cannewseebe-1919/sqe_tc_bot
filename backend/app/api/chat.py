import json
import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, UploadFile, File

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.schemas.schemas import ChatRequest, ChatResponse, FileUploadResponse
from app.services.llm_service import generate_tc_code
from app.services.file_parser import parse_file

settings = get_settings()
router = APIRouter(prefix="/api", tags=["chat"])

_redis: aioredis.Redis | None = None
_CONV_TTL = 3600 * 24  # 24 hours


async def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


def _conv_key(conv_id: str) -> str:
    return f"conversation:{conv_id}"


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    conv_id = req.conversation_id or str(uuid.uuid4())

    r = await _get_redis()
    raw = await r.get(_conv_key(conv_id))
    history: list[dict] = json.loads(raw) if raw else []

    reply, code = await generate_tc_code(
        user_message=req.message,
        file_content=req.file_content,
        conversation_history=history,
    )

    # Update history in Redis
    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": reply})
    await r.set(_conv_key(conv_id), json.dumps(history), ex=_CONV_TTL)

    return ChatResponse(
        reply=reply,
        code=code,
        test_case_id=None,
        conversation_id=conv_id,
    )


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    content = await file.read()
    extracted = parse_file(file.filename or "unknown", content)
    return FileUploadResponse(
        filename=file.filename or "unknown",
        extracted_text=extracted,
        char_count=len(extracted),
    )
