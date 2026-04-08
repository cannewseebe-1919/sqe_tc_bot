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

## 환경변수 전체 목록

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

## 주요 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/health` | 헬스체크 |
| GET | `/api/auth/saml/login` | SAML SSO 로그인 |
| POST | `/api/auth/saml/acs` | SAML ACS 콜백 |
| POST | `/api/chat` | AI 채팅 (TC 생성) |
| POST | `/api/chat/upload` | 파일 업로드 (Word/PDF) |
| GET | `/api/testcases` | TC 목록 조회 |
| POST | `/api/testcases` | TC 저장 |
| PUT | `/api/testcases/{id}` | TC 수정 |
| DELETE | `/api/testcases/{id}` | TC 삭제 |
| POST | `/api/execution/request` | TC 실행 요청 → Executor 전달 |
| GET | `/api/execution/{id}/status` | 실행 상태 조회 |
| POST | `/api/git/push` | TC 코드 GitHub push |

## 프로젝트 구조

```
sqe_tc_bot/
├── backend/
│   ├── app/
│   │   ├── api/           # API 라우터 (auth, chat, testcase, execution, git)
│   │   ├── core/          # 설정, 인증, SAML
│   │   │   └── saml/      # SAML IdP 설정 파일
│   │   ├── models/        # SQLAlchemy 모델 (User, TestCase, Execution)
│   │   ├── schemas/       # Pydantic 스키마
│   │   └── services/      # 비즈니스 로직 (LLM, 파일파싱, Executor 통신)
│   ├── alembic/           # DB 마이그레이션
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/         # LoginPage, MainPage
│   │   └── components/    # Chat, CodeEditor(Monaco), DeviceSelector, GitPush
│   └── package.json
└── docker-compose.yml
```

## 연동 서비스

이 프로젝트는 [Test Executor](https://github.com/cannewseebe-1919/sqe_tc_executor)와 함께 사용합니다.
TC Generator에서 생성한 테스트 코드를 Executor로 전달하여 실제 Android 단말에서 실행합니다.
