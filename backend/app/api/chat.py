import uuid

from fastapi import APIRouter, Depends, UploadFile, File

from app.core.auth import get_current_user
from app.schemas.schemas import ChatRequest, ChatResponse, FileUploadResponse
from app.services.llm_service import generate_tc_code
from app.services.file_parser import parse_file

router = APIRouter(prefix="/api", tags=["chat"])

# In-memory conversation store (replace with Redis in production)
_conversations: dict[str, list[dict]] = {}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    conv_id = req.conversation_id or str(uuid.uuid4())
    history = _conversations.get(conv_id, [])

    reply, code = await generate_tc_code(
        user_message=req.message,
        file_content=req.file_content,
        conversation_history=history,
    )

    # Update history
    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": reply})
    _conversations[conv_id] = history

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
