# SQE TC Bot (TC Generator)

AI 기반 테스트 케이스 자동 생성 챗봇 서비스입니다.
자연어 또는 문서(Word/PDF)를 입력하면 dtgpt LLM을 통해 `test_executor_sdk` 기반의 Python 테스트 코드를 생성하고, Test Executor 서버로 실행을 요청합니다.

## 아키텍처

```
[Browser] ←→ [React Frontend :3000] ←→ [FastAPI Backend :8000] ←→ [dtgpt LLM API]
                                              ↕                         
                                     [PostgreSQL] [Redis]
                                              ↕
                                     [Test Executor :8001]
```

## 사전 요구사항

- **Docker** & **Docker Compose** (권장)
- 또는 로컬 실행 시:
  - Python 3.12+
  - Node.js 18+ & npm
  - PostgreSQL 16
  - Redis 7

---

## 빠른 시작 (Docker)

### 1. 저장소 클론

```bash
git clone https://github.com/cannewseebe-1919/sqe_tc_bot.git
cd sqe_tc_bot
```

### 2. 환경변수 설정

`backend/.env` 파일을 생성합니다:

```env
# dtgpt LLM API (필수)
DTGPT_BASE_URL=https://your-dtgpt-server.com/v1
DTGPT_API_KEY=your-api-key
DTGPT_MODEL=dtgpt

# Test Executor 서버 주소
EXECUTOR_BASE_URL=http://host.docker.internal:8001

# JWT 시크릿 (반드시 변경)
JWT_SECRET=your-strong-random-secret

# SAML SSO (운영 환경)
SAML_SP_ENTITY_ID=tc-generator
SAML_ACS_URL=https://your-domain.com/api/auth/saml/acs
SAML_SLO_URL=https://your-domain.com/api/auth/saml/slo
```

### 3. SAML IdP 설정

`backend/app/core/saml/settings.json`에서 IdP 정보를 수정합니다:

```json
{
  "idp": {
    "entityId": "https://your-idp.com/metadata",
    "singleSignOnService": {
      "url": "https://your-idp.com/sso"
    },
    "singleLogoutService": {
      "url": "https://your-idp.com/slo"
    },
    "x509cert": "YOUR_IDP_X509_CERTIFICATE"
  }
}
```

### 4. 실행

```bash
docker compose up -d
```

서비스가 시작됩니다:
- **Backend API**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 5. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

프론트엔드: http://localhost:3000

---

## 개발 환경 설정 (SSO 없이 개발하기)

사내 SSO(SAML) 환경이 구성되지 않은 로컬 개발 시, `DEV_MODE`를 활성화하면 인증을 우회하고 바로 메인 화면에 접근할 수 있습니다.

### 설정 방법

`frontend/.env.development` 파일에 다음 항목이 이미 포함되어 있습니다:

```env
VITE_DEV_MODE=true
```

`npm run dev` 실행 시 Vite가 `.env.development`를 자동으로 로드하므로 **별도 조작 없이** DEV_MODE가 활성화됩니다.

### 동작 방식

| 항목 | DEV_MODE=false (운영) | DEV_MODE=true (개발) |
|------|----------------------|----------------------|
| 인증 방식 | SAML SSO 리다이렉트 | 우회 (토큰 불필요) |
| 로그인 유저 | SSO에서 발급된 실제 유저 | `개발자 / dev@localhost` (목업) |
| `/auth/me` 호출 | 백엔드 실제 호출 | 목업 응답 반환 |

- `frontend/src/App.tsx`: `DEV_MODE=true`이면 `localStorage` 토큰 유무와 관계없이 `MainPage`로 바로 이동합니다.
- `frontend/src/services/api.ts`: `authApi.getCurrentUser()`가 `/auth/me` 대신 목업 유저 객체를 즉시 반환합니다.

> **주의**: `VITE_DEV_MODE=true`는 절대 운영(production) 빌드에 포함되지 않도록 `.env.production`에서는 `false`로 유지하거나 해당 변수를 삭제하세요.

---

## 대화 기억 기능 (Conversation History)

동일 세션 내에서 이전 대화 맥락을 유지하며 테스트 케이스를 수정·보완할 수 있습니다.

### 동작 방식

1. 첫 메시지 전송 시 백엔드가 새로운 `conversation_id`를 발급하여 응답에 포함합니다.
2. 프론트엔드(`ChatPanel`)는 이를 `state`에 저장하고, 이후 모든 요청에 `conversation_id`를 함께 전송합니다.
3. 백엔드는 Redis에 대화 이력을 저장하며, **24시간** 동안 유지됩니다.

```
[사용자 첫 메시지] → POST /api/chat { message, conversation_id: null }
                  ← { reply, code, conversation_id: "abc-123" }

[사용자 후속 메시지] → POST /api/chat { message, conversation_id: "abc-123" }
                    ← { reply, code, conversation_id: "abc-123" }  # 문맥 유지
```

### 파일 첨부 흐름

파일(Word/PDF)을 첨부하면 2단계로 처리됩니다:

```
1. POST /api/upload   (multipart/form-data) → { extracted_text }
2. POST /api/chat     (JSON) { message, conversation_id, file_content: extracted_text }
```

- `frontend/src/services/api.ts`의 `chatApi.uploadFile(file)`이 파일 업로드 후 텍스트 추출을 담당합니다.
- 이후 `chatApi.sendMessage(message, conversationId, fileContent)`로 JSON 형태로 `/chat`에 전달합니다.

---

## 프론트엔드 프록시 설정

`frontend/vite.config.ts`에 두 개의 프록시가 설정되어 있습니다:

| 프록시 경로 | 대상 서버 | 설명 |
|------------|----------|------|
| `/api/*` | `http://localhost:8000` | tc_bot 백엔드 (인증, 채팅, TC 관리 등) |
| `/executor-api/*` | `http://localhost:8001` | sqe_tc_executor (단말 조회, 테스트 실행) |

`/executor-api` 경로는 프록시 시 prefix가 제거되어 executor 서버의 실제 경로로 전달됩니다.

예시: 브라우저가 `/executor-api/api/devices`를 요청하면 → executor의 `http://localhost:8001/api/devices`로 포워딩됩니다.

---

## MCP 서버 설정 (Claude Code에서 테스트 실행)

`backend/mcp_server.py`는 Claude Code CLI에서 테스트를 직접 실행할 수 있는 [MCP(Model Context Protocol)](https://modelcontextprotocol.io) 서버입니다.

### 사전 조건

1. **sqe_tc_executor가 먼저 실행**되어 있어야 합니다 (`:8001` 포트).
2. Python 패키지 설치:

```bash
pip install mcp[cli] httpx
# 또는 requirements.txt로 한번에 설치
pip install -r backend/requirements.txt
```

### 자동 등록 방법

프로젝트 루트의 `.mcp.json`이 이미 설정되어 있어, `sqe_tc_bot` 폴더에서 Claude Code를 실행하면 MCP 서버가 **자동으로 등록**됩니다.

```json
// .mcp.json
{
  "mcpServers": {
    "sqe-executor": {
      "command": "python",
      "args": ["backend/mcp_server.py"],
      "env": {
        "EXECUTOR_BASE_URL": "http://localhost:8001",
        "BACKEND_URL": "http://localhost:8000",
        "EXECUTOR_JWT_TOKEN": ""
      }
    }
  }
}
```

`.claude/settings.json`에 `"enableAllProjectMcpServers": true`가 설정되어 있어 별도 승인 없이 활성화됩니다.

### 제공하는 툴 (5개)

| 툴 이름 | 설명 |
|---------|------|
| `list_devices` | 연결된 Android 단말 목록 조회 (ID, 상태, 모델, Android 버전) |
| `execute_test(test_code, device_id)` | 테스트 코드를 지정 단말에서 실행, `execution_id` 반환 |
| `get_execution_status(execution_id)` | 실행 상태 조회 (QUEUED / RUNNING / COMPLETED / FAILED / ABORTED) |
| `get_execution_result(execution_id)` | 완료된 테스트의 steps별 결과, crash_logs 등 상세 조회 |
| `wait_for_completion(execution_id)` | 완료까지 폴링 대기 후 상세 결과 반환 (기본 타임아웃 300초) |

### Claude Code에서 사용 예시

Claude Code 채팅창에 자연어로 요청하면 됩니다:

```
# 단말 목록 확인
"연결된 단말 목록 보여줘"

# 테스트 실행
"device-001에서 아래 테스트 코드 실행해줘:
from test_executor_sdk import TestCase
..."

# 실행 결과 확인
"방금 실행한 테스트 결과 알려줘"

# 실행부터 결과까지 한번에
"단말 목록 확인 후 첫 번째 단말에서 테스트 실행하고 결과 알려줘"
```

### 환경변수 (MCP 서버용)

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `EXECUTOR_BASE_URL` | sqe_tc_executor 서버 주소 | `http://localhost:8001` |
| `BACKEND_URL` | tc_bot 백엔드 주소 (콜백 URL용) | `http://localhost:8000` |
| `EXECUTOR_JWT_TOKEN` | JWT 토큰 (executor DEV_MODE=true이면 비워도 됨) | (빈 값) |

---

## 로컬 실행 (Docker 없이)

### Backend

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# .env 파일 생성 (위 환경변수 설정 참고)

# DB 마이그레이션
alembic upgrade head

# 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 환경변수 전체 목록

### Backend (`backend/.env`)

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `DATABASE_URL` | PostgreSQL 접속 URL | `postgresql+asyncpg://postgres:postgres@localhost:5432/tc_generator` |
| `REDIS_URL` | Redis 접속 URL | `redis://localhost:6379/0` |
| `DTGPT_BASE_URL` | dtgpt API 엔드포인트 | `https://dtgpt.example.com/v1` |
| `DTGPT_API_KEY` | dtgpt API 키 | (빈 값) |
| `DTGPT_MODEL` | 사용할 LLM 모델명 | `dtgpt` |
| `EXECUTOR_BASE_URL` | Test Executor 서버 URL | `http://localhost:8001` |
| `EXECUTOR_CALLBACK_URL` | 실행 결과 콜백 URL | `http://localhost:8000/api/execution-result` |
| `JWT_SECRET` | JWT 서명 시크릿 | `change-me-in-production` |
| `JWT_ALGORITHM` | JWT 알고리즘 | `HS256` |
| `JWT_EXPIRE_MINUTES` | JWT 만료 시간(분) | `60` |
| `SAML_SETTINGS_PATH` | SAML 설정 디렉토리 | `app/core/saml` |
| `CORS_ORIGINS` | 허용 CORS 도메인 | `["http://localhost:3000"]` |
| `DEBUG` | 디버그 모드 | `false` |

### Frontend (`frontend/.env.development` / `frontend/.env`)

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `VITE_DEV_MODE` | SSO 우회 개발 모드 활성화 | `false` |
| `VITE_API_BASE_URL` | 백엔드 API Base URL | `/api` (프록시 경유) |
| `VITE_EXECUTOR_API_URL` | Executor API Base URL | `/executor-api` (프록시 경유) |
| `VITE_EXECUTOR_WS_URL` | Executor WebSocket URL | `ws://localhost:8001` |

---

## 주요 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/health` | 헬스체크 |
| GET | `/api/auth/saml/login` | SAML SSO 로그인 |
| POST | `/api/auth/saml/acs` | SAML ACS 콜백 |
| GET | `/api/auth/me` | 현재 로그인 유저 정보 조회 |
| POST | `/api/chat` | AI 채팅 (TC 생성, `conversation_id` 지원) |
| POST | `/api/upload` | 파일 업로드 및 텍스트 추출 (Word/PDF) |
| GET | `/api/testcases` | TC 목록 조회 |
| POST | `/api/testcases` | TC 저장 |
| PUT | `/api/testcases/{id}` | TC 수정 |
| DELETE | `/api/testcases/{id}` | TC 삭제 |
| POST | `/api/execution/request` | TC 실행 요청 → Executor 전달 |
| GET | `/api/execution/{id}/status` | 실행 상태 조회 |
| POST | `/api/execution-result` | Executor 콜백 수신 |
| POST | `/api/git/push` | TC 코드 GitHub push |

---

## 프로젝트 구조

```
sqe_tc_bot/
├── .mcp.json                  # Claude Code MCP 서버 등록 설정
├── .claude/
│   └── settings.json          # Claude Code 프로젝트 설정 (enableAllProjectMcpServers)
├── backend/
│   ├── app/
│   │   ├── api/               # API 라우터 (auth, chat, testcase, execution, git)
│   │   ├── core/              # 설정, 인증, SAML
│   │   │   └── saml/          # SAML IdP 설정 파일
│   │   ├── models/            # SQLAlchemy 모델 (User, TestCase, Execution)
│   │   ├── schemas/           # Pydantic 스키마
│   │   └── services/          # 비즈니스 로직 (LLM, 파일파싱, Executor 통신)
│   ├── alembic/               # DB 마이그레이션
│   ├── mcp_server.py          # MCP 서버 (Claude Code 연동)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/             # LoginPage, MainPage
│   │   ├── components/        # Chat, CodeEditor(Monaco), DeviceSelector, GitPush
│   │   └── services/
│   │       ├── api.ts         # API 클라이언트 (DEV_MODE, conversation_id 지원)
│   │       └── types.ts       # TypeScript 타입 정의
│   ├── .env.development       # 개발 환경변수 (VITE_DEV_MODE=true)
│   ├── vite.config.ts         # Vite 설정 (프록시: /api, /executor-api)
│   └── package.json
└── docker-compose.yml
```

---

## 연동 서비스

이 프로젝트는 [sqe_tc_executor](https://github.com/cannewseebe-1919/sqe_tc_executor)와 함께 사용합니다.
TC Generator에서 생성한 테스트 코드를 Executor로 전달하여 실제 Android 단말에서 실행합니다.

전체 실행 순서:

```
1. sqe_tc_executor 실행 (포트 8001)
2. sqe_tc_bot 백엔드 실행 (포트 8000)
3. sqe_tc_bot 프론트엔드 실행 (포트 3000)
4. (선택) Claude Code에서 MCP 서버를 통해 직접 테스트 실행
```
