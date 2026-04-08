from datetime import datetime
from pydantic import BaseModel


# --- Chat ---
class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    file_content: str | None = None


class ChatResponse(BaseModel):
    reply: str
    code: str | None = None
    test_case_id: str | None = None
    conversation_id: str


# --- File Upload ---
class FileUploadResponse(BaseModel):
    filename: str
    extracted_text: str
    char_count: int


# --- TestCase ---
class TestCaseCreate(BaseModel):
    title: str
    code: str
    source_type: str = "chat"


class TestCaseUpdate(BaseModel):
    title: str | None = None
    code: str | None = None
    status: str | None = None


class TestCaseResponse(BaseModel):
    id: str
    title: str
    code: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    source_type: str
    status: str

    model_config = {"from_attributes": True}


# --- Execution ---
class ExecutionRequest(BaseModel):
    test_case_id: str
    device_id: str


class ExecutionStatusResponse(BaseModel):
    execution_id: str
    status: str
    current_step: str | None = None
    progress: str | None = None
    started_at: datetime | None = None


class StepResult(BaseModel):
    name: str
    status: str
    duration_sec: float
    screenshot_url: str | None = None
    log: str | None = None
    error_type: str | None = None


class ExecutionSummary(BaseModel):
    total_steps: int
    passed: int
    failed: int
    aborted: bool
    abort_reason: str | None = None


class DeviceInfo(BaseModel):
    model: str
    android_version: str
    resolution: str


class ExecutionResultCallback(BaseModel):
    execution_id: str
    status: str
    device_id: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total_duration_sec: float | None = None
    summary: ExecutionSummary
    steps: list[StepResult]
    crash_logs: list[str] = []
    device_info: DeviceInfo | None = None


# --- Device (from executor) ---
class DeviceResponse(BaseModel):
    id: str
    name: str
    status: str
    model: str
    android_version: str
    queue_length: int


class DeviceListResponse(BaseModel):
    devices: list[DeviceResponse]


# --- Git ---
class GitPushRequest(BaseModel):
    test_case_id: str
    repo_url: str
    branch: str = "main"
    token: str
    commit_message: str | None = None


class GitPushResponse(BaseModel):
    success: bool
    commit_sha: str | None = None
    message: str
