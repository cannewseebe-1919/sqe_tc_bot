# SQE TC Bot (TC Generator)

AI(dtgpt)를 통해 자연어 또는 문서(Word/PDF)를 Python 테스트 코드로 자동 변환하고, sqe_tc_executor 서버에서 실행하는 서비스입니다.

**실행 환경**: Ubuntu Server — 전체 Docker Compose로 실행

---

## 아키텍처

```
[Browser]
   ↕ :3000
[nginx (Frontend)]
   ↕ /api/*  /executor-api/*
[FastAPI Backend :8000] ←→ [dtgpt LLM API (사내)]
   ↕                ↕
[PostgreSQL]     [Redis]
                    ↕
         [sqe_tc_executor :8001]  ←→  [Android 단말]
```

---

## 설정 파일 전체 요약

> 시작 전에 아래 표를 보고 어느 파일을 어디서 수정해야 하는지 파악하세요.

| 설정 항목 | 수정할 파일 | 위치 | 언제 |
|-----------|------------|------|------|
| Docker 사내 레지스트리 | `/etc/docker/daemon.json` | **서버 호스트** | 최초 1회 |
| Docker 빌드용 미러 주소 | `프로젝트 루트/.env` | **서버 호스트** (프로젝트 폴더 내) | 최초 1회 |
| 앱 환경변수 (dtgpt, JWT 등) | `backend/.env` | **서버 호스트** (프로젝트 폴더 내) | 최초 1회 |
| SAML IdP 정보 | `backend/app/core/saml/settings.json` | **서버 호스트** (프로젝트 폴더 내) | 운영 환경만 |

> **apt, pip, npm 설정은 서버 호스트에 직접 할 필요 없습니다.**
> 이 프로젝트는 전체가 Docker 컨테이너로 실행되므로, 미러 주소는 `루트/.env`에 입력하면 빌드 시 Docker 내부에 자동 적용됩니다.

---

## 사전 준비: 사내 인프라 주소 확인

아래 값을 사내 담당자에게 확인하세요. 이후 단계에서 사용합니다.

```
Docker 레지스트리 주소 : ___________________________  (예: harbor.company.internal)
apt 미러 URL          : ___________________________  (예: http://apt-mirror.company.internal/ubuntu)
PyPI 미러 URL         : ___________________________  (예: http://pypi-mirror.company.internal/simple)
PyPI 미러 호스트명     : ___________________________  (예: pypi-mirror.company.internal)
npm 레지스트리 URL     : ___________________________  (예: http://npm-registry.company.internal)
dtgpt API URL         : ___________________________  (예: http://dtgpt.company.internal/v1)
dtgpt API 키          : ___________________________
executor 서버 IP      : ___________________________  (sqe_tc_executor가 동작하는 서버 IP)
이 서버 IP            : ___________________________  (이 sqe_tc_bot 서버의 IP)
```

---

## 0단계: Docker 사내 레지스트리 등록

**작업 위치**: 서버 호스트 터미널

Docker가 사내 레지스트리에서 이미지를 받을 수 있도록 설정합니다. **최초 1회**만 하면 됩니다.

```bash
sudo nano /etc/docker/daemon.json
```

아래 내용을 입력합니다 (실제 레지스트리 주소로 변경):

```json
{
  "insecure-registries": ["harbor.company.internal"],
  "registry-mirrors": ["http://harbor.company.internal"]
}
```

저장 후 Docker 재시작:

```bash
sudo systemctl restart docker
```

### 사내 레지스트리에 필요한 이미지 확인

담당자에게 아래 이미지가 레지스트리에 등록되어 있는지 확인하세요:

```
harbor.company.internal/python:3.12-slim
harbor.company.internal/node:18-alpine
harbor.company.internal/nginx:1.27-alpine
harbor.company.internal/postgres:16-alpine
harbor.company.internal/redis:7-alpine
```

---

## 1단계: 프로젝트 다운로드

**작업 위치**: 서버 호스트 터미널

```bash
git clone http://git.company.internal/sqe/sqe_tc_bot.git
cd sqe_tc_bot
```

인터넷이 완전히 차단된 경우, USB 등으로 파일을 옮긴 뒤 압축을 해제하여 사용합니다.

---

## 2단계: 루트 `.env` 작성 — Docker 빌드 설정

**작업 위치**: 서버 호스트 터미널  
**파일 위치**: `sqe_tc_bot/.env` (프로젝트 최상단)

이 파일은 `docker-compose.yml`이 읽어서 Docker 이미지 빌드 시 사내 미러 주소를 컨테이너 내부에 주입합니다. **호스트에 apt/pip/npm을 직접 설정할 필요가 없는 이유**가 바로 이 파일 때문입니다.

```bash
# sqe_tc_bot/ 디렉토리에서 실행
nano .env
```

아래 내용을 입력합니다 (실제 주소로 변경):

```env
# ─── Docker 이미지 및 빌드용 사내 미러 주소 ──────────────────────
# Docker 빌드 시 컨테이너 내부에서 사용할 미러 주소입니다.
# 호스트에 apt/pip/npm을 직접 설정하는 것이 아닙니다.

INTERNAL_REGISTRY=harbor.company.internal
APT_MIRROR=http://apt-mirror.company.internal/ubuntu
PIP_INDEX_URL=http://pypi-mirror.company.internal/simple
PIP_TRUSTED_HOST=pypi-mirror.company.internal
NPM_REGISTRY=http://npm-registry.company.internal

# ─── executor 서버 연결 정보 ──────────────────────────────────────
EXECUTOR_HOST=192.168.0.xx          # executor 서버 IP
EXECUTOR_PORT=8001

# executor WebSocket 주소 (프론트엔드 빌드 시 사용, 브라우저에서 직접 연결)
VITE_EXECUTOR_WS_URL=ws://192.168.0.xx:8001

# ─── DB 비밀번호 ──────────────────────────────────────────────────
DB_PASSWORD=강력한비밀번호로변경
```

---

## 3단계: `backend/.env` 작성 — 앱 설정

**작업 위치**: 서버 호스트 터미널  
**파일 위치**: `sqe_tc_bot/backend/.env`

```bash
# sqe_tc_bot/ 디렉토리에서 실행
cp backend/.env.example backend/.env
nano backend/.env
```

★ 표시된 항목을 반드시 실제 값으로 변경하세요:

```env
# ─── 앱 기본 설정 ────────────────────────────────────────────────
APP_NAME=TC Generator
DEBUG=false
# 개발/테스트 시 true로 설정하면 SAML 로그인 없이 바로 사용 가능
DEV_MODE=false

# ─── 데이터베이스 ────────────────────────────────────────────────
# Docker Compose로 실행하므로 호스트명은 'db' 그대로 사용
DATABASE_URL=postgresql+asyncpg://postgres:강력한비밀번호로변경@db:5432/tc_generator  # ★

# ─── Redis ───────────────────────────────────────────────────────
# Docker Compose로 실행하므로 호스트명은 'redis' 그대로 사용
REDIS_URL=redis://redis:6379/0

# ─── dtgpt (사내 LLM API) ────────────────────────────────────────
DTGPT_BASE_URL=http://dtgpt.company.internal/v1       # ★ 실제 주소로 변경
DTGPT_API_KEY=실제-dtgpt-API-키                        # ★
DTGPT_MODEL=dtgpt

# ─── sqe_tc_executor 연결 ────────────────────────────────────────
EXECUTOR_BASE_URL=http://192.168.0.xx:8001             # ★ executor 서버 IP
EXECUTOR_CALLBACK_URL=http://이-서버-IP:8000/api/execution-result  # ★ 이 서버 IP

# ─── JWT (sqe_tc_executor의 JWT_SECRET과 반드시 동일) ─────────────
JWT_SECRET=랜덤하고-강력한-시크릿값-여기-입력          # ★
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# ─── SAML SSO (DEV_MODE=false 운영 환경에서만 필요) ──────────────
SAML_SP_ENTITY_ID=tc-generator
SAML_ACS_URL=http://이-서버-IP:8000/api/auth/saml/acs  # ★
SAML_SLO_URL=http://이-서버-IP:8000/api/auth/saml/slo
SAML_IDP_METADATA_URL=http://idp.company.internal/metadata  # ★
SAML_SETTINGS_PATH=app/core/saml

# ─── CORS ────────────────────────────────────────────────────────
CORS_ORIGINS=["http://이-서버-IP:3000"]                # ★ 이 서버 IP
```

> **개발/테스트 환경**: `DEV_MODE=true` 로 설정하면 SAML 없이 바로 사용 가능합니다.
> `DATABASE_URL`의 비밀번호는 루트 `.env`의 `DB_PASSWORD`와 동일하게 맞추세요.

---

## 4단계: SAML 설정 (운영 환경만)

> `DEV_MODE=true` 사용 시 이 단계를 건너뜁니다.

**작업 위치**: 서버 호스트 터미널  
**파일 위치**: `sqe_tc_bot/backend/app/core/saml/settings.json`

```bash
nano backend/app/core/saml/settings.json
```

```json
{
  "sp": {
    "entityId": "http://이-서버-IP:8000/api/auth/saml/metadata",
    "assertionConsumerService": {
      "url": "http://이-서버-IP:8000/api/auth/saml/acs",
      "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
    },
    "singleLogoutService": {
      "url": "http://이-서버-IP:8000/api/auth/saml/slo",
      "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    }
  },
  "idp": {
    "entityId": "http://idp.company.internal/saml/metadata",
    "singleSignOnService": {
      "url": "http://idp.company.internal/saml/sso",
      "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    },
    "singleLogoutService": {
      "url": "http://idp.company.internal/saml/slo",
      "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    },
    "x509cert": "사내 IdP 담당자에게 X509 인증서 문자열을 받아 여기에 붙여넣기"
  }
}
```

---

## 5단계: 빌드 및 실행

**작업 위치**: 서버 호스트 터미널 (`sqe_tc_bot/` 디렉토리)

```bash
# 이미지 빌드 (처음 또는 코드 변경 시)
docker compose build

# 백그라운드 실행
docker compose up -d

# 실시간 로그 확인
docker compose logs -f
```

### 첫 실행 시 DB 마이그레이션

```bash
docker compose exec backend alembic upgrade head
```

### 서비스 접속 확인

```bash
# 백엔드 헬스체크
curl http://localhost:8000/health
# {"status":"ok"} 가 나오면 정상

# 브라우저에서 프론트엔드 접속
# http://이-서버-IP:3000
```

---

## 서비스 포트

| 서비스 | 호스트 포트 | 설명 |
|--------|------------|------|
| 프론트엔드 (nginx) | **3000** | 사용자 브라우저 접속 URL |
| 백엔드 API | 8000 | REST API (내부용) |
| PostgreSQL | 5432 | DB |
| Redis | 6379 | 캐시/큐 |

---

## 운영 명령어

```bash
# 서비스 재시작
docker compose restart

# 서비스 중지
docker compose down

# 데이터 포함 완전 삭제 (주의!)
docker compose down -v

# 특정 서비스만 재시작
docker compose restart backend

# 실시간 로그
docker compose logs -f backend

# DB 직접 접속
docker compose exec db psql -U postgres -d tc_generator
```

---

## 환경변수 전체 목록

### `backend/.env`

| 변수명 | 설명 | 필수 |
|--------|------|------|
| `DTGPT_BASE_URL` | 사내 dtgpt API 주소 | ★ |
| `DTGPT_API_KEY` | dtgpt API 키 | ★ |
| `DTGPT_MODEL` | LLM 모델명 | 기본값: `dtgpt` |
| `EXECUTOR_BASE_URL` | sqe_tc_executor 서버 주소 | ★ |
| `EXECUTOR_CALLBACK_URL` | 실행 결과 콜백 URL (이 서버 주소) | ★ |
| `JWT_SECRET` | JWT 서명 키 (executor와 동일) | ★ |
| `DATABASE_URL` | PostgreSQL 접속 URL | ★ |
| `REDIS_URL` | Redis 접속 URL | ★ |
| `DEV_MODE` | `true`: SAML 우회 개발모드 | 기본값: `false` |
| `SAML_ACS_URL` | SAML ACS 콜백 URL | 운영만 |
| `SAML_IDP_METADATA_URL` | 사내 IdP 메타데이터 URL | 운영만 |
| `CORS_ORIGINS` | 허용 CORS 도메인 | ★ |

### 루트 `.env` (docker-compose 빌드용)

| 변수명 | 설명 | 사용 위치 |
|--------|------|-----------|
| `INTERNAL_REGISTRY` | 사내 Docker 레지스트리 | Docker 이미지 pull |
| `APT_MIRROR` | 사내 Ubuntu apt 미러 URL | 컨테이너 내부 apt |
| `PIP_INDEX_URL` | 사내 PyPI 미러 URL | 컨테이너 내부 pip |
| `PIP_TRUSTED_HOST` | 사내 PyPI 미러 호스트명 | 컨테이너 내부 pip |
| `NPM_REGISTRY` | 사내 npm 레지스트리 URL | 컨테이너 내부 npm |
| `EXECUTOR_HOST` | executor 서버 IP/호스트명 | nginx 프록시 설정 |
| `VITE_EXECUTOR_WS_URL` | executor WebSocket 주소 | 프론트엔드 빌드 시 |
| `DB_PASSWORD` | PostgreSQL 비밀번호 | DB 컨테이너 |

---

## 트러블슈팅

### Docker 이미지를 pull 할 수 없음
```
Error response from daemon: pull access denied
```
→ `/etc/docker/daemon.json`에 `insecure-registries` 등록 후 `sudo systemctl restart docker`
→ 사내 레지스트리에 이미지가 없는 경우 담당자에게 요청

### pip 패키지 설치 실패 (빌드 중)
```
Could not find a version that satisfies the requirement
```
→ 루트 `.env`의 `PIP_INDEX_URL`, `PIP_TRUSTED_HOST` 값이 올바른지 확인

### DB 마이그레이션 오류
```bash
docker compose exec backend alembic stamp head
docker compose exec backend alembic upgrade head
```

### executor 연결 오류
→ 루트 `.env`의 `EXECUTOR_HOST`가 실제 executor 서버 IP인지 확인
→ executor 서버에서 8001 포트가 열려있는지 확인 (`telnet 192.168.0.xx 8001`)

### SAML 인증 오류
→ `backend/app/core/saml/settings.json` IdP 정보 확인
→ 개발/테스트 시 `backend/.env`에서 `DEV_MODE=true` 사용

---

## 연동 서비스

- **sqe_tc_executor** — Android 단말에서 TC 실행 (반드시 먼저 실행)
- **dtgpt** — 사내 LLM API (TC 코드 생성)
- **사내 IdP** — SAML SSO 인증 (운영 시)

실행 순서:
```
1. sqe_tc_executor 서버 실행 (:8001)
2. sqe_tc_bot 실행 (:8000, :3000)
```
