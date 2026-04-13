# SQE TC Bot (TC Generator)

AI(dtgpt)를 통해 자연어 또는 문서(Word/PDF)를 Python 테스트 코드로 자동 변환하고, sqe_tc_executor 서버에서 실행하는 서비스입니다.

**실행 환경**: Ubuntu Server (Docker 권장)

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

## 0단계: 사내망 환경 사전 설정

> **인터넷 차단 환경**이므로 아래 값을 사내 담당자에게 확인 후 기입하세요.

```
INTERNAL_DOCKER_REGISTRY = ______________   # 예: harbor.internal.company
INTERNAL_APT_MIRROR      = ______________   # 예: http://mirror.internal.company/ubuntu
INTERNAL_PIP_MIRROR      = ______________   # 예: http://pypi.internal.company/simple
INTERNAL_PIP_HOST        = ______________   # 예: pypi.internal.company
INTERNAL_NPM_REGISTRY    = ______________   # 예: http://npm.internal.company
DTGPT_BASE_URL           = ______________   # 예: http://dtgpt.internal.company/v1
DTGPT_API_KEY            = ______________   # dtgpt API 키
```

### Docker 데몬에 사내 레지스트리 등록

```bash
sudo nano /etc/docker/daemon.json
```

```json
{
  "insecure-registries": ["INTERNAL_DOCKER_REGISTRY"],
  "registry-mirrors": ["http://INTERNAL_DOCKER_REGISTRY"]
}
```

```bash
sudo systemctl restart docker
```

### 사내 레지스트리에서 필요한 이미지 확인

아래 이미지들이 사내 레지스트리에 있어야 합니다. 없으면 담당자에게 요청하세요:

- `INTERNAL_DOCKER_REGISTRY/python:3.12-slim`
- `INTERNAL_DOCKER_REGISTRY/node:18-alpine`
- `INTERNAL_DOCKER_REGISTRY/nginx:1.27-alpine`
- `INTERNAL_DOCKER_REGISTRY/postgres:16-alpine`
- `INTERNAL_DOCKER_REGISTRY/redis:7-alpine`

---

## 1단계: 프로젝트 다운로드

인터넷이 차단된 환경이므로, USB 또는 사내 git 서버를 통해 프로젝트를 옮깁니다.

```bash
# 사내 git 서버에서 클론하는 경우
git clone http://git.internal.company/sqe/sqe_tc_bot.git
cd sqe_tc_bot
```

---

## 2단계: 환경변수 파일 작성

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

**반드시 수정해야 할 항목 (★):**

```env
# ★ 사내 dtgpt 주소와 키
DTGPT_BASE_URL=http://dtgpt.internal.company/v1
DTGPT_API_KEY=실제-API-키

# ★ sqe_tc_executor 서버 주소 (executor가 동작하는 서버 IP)
EXECUTOR_BASE_URL=http://192.168.x.x:8001
EXECUTOR_CALLBACK_URL=http://이-서버-IP:8000/api/execution-result

# ★ JWT 시크릿 (sqe_tc_executor의 JWT_SECRET과 동일한 값)
JWT_SECRET=랜덤하고-강력한-시크릿값

# ★ CORS (프론트엔드 주소)
CORS_ORIGINS=["http://이-서버-IP:3000"]

# ★ SAML SSO (사내 IdP 정보 / 개발·테스트 시 DEV_MODE=true 사용 가능)
DEV_MODE=false
SAML_ACS_URL=http://이-서버-IP:8000/api/auth/saml/acs
SAML_IDP_METADATA_URL=http://idp.internal.company/metadata
```

> **개발/테스트 환경**: `DEV_MODE=true` 로 설정하면 SAML 없이 바로 사용 가능합니다.

---

## 3단계: 사내 레지스트리 주소 설정

`docker-compose.yml` 에서 사내 레지스트리 주소를 `.env` 파일로 관리합니다.

프로젝트 루트에 `.env` 파일 생성:

```bash
cat > .env << 'EOF'
# ★ 사내 인프라 주소 (아래 값을 실제 주소로 변경하세요)
INTERNAL_REGISTRY=harbor.internal.company
APT_MIRROR=http://mirror.internal.company/ubuntu
PIP_INDEX_URL=http://pypi.internal.company/simple
PIP_TRUSTED_HOST=pypi.internal.company
NPM_REGISTRY=http://npm.internal.company

# ★ executor 서버 주소
EXECUTOR_HOST=192.168.x.x
EXECUTOR_PORT=8001

# executor WebSocket 주소 (프론트엔드 빌드 시 결정됨)
VITE_EXECUTOR_WS_URL=ws://192.168.x.x:8001

# DB 비밀번호
DB_PASSWORD=변경하세요
EOF
```

---

## 4단계: SAML 설정 (운영 환경)

> DEV_MODE=true 사용 시 이 단계 건너뜀

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
    "entityId": "http://idp.internal.company/saml/metadata",
    "singleSignOnService": {
      "url": "http://idp.internal.company/saml/sso",
      "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    },
    "singleLogoutService": {
      "url": "http://idp.internal.company/saml/slo",
      "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    },
    "x509cert": "사내 IdP의 X509 인증서를 여기에 붙여넣기"
  }
}
```

---

## 5단계: 빌드 및 실행

```bash
# 이미지 빌드 (처음 또는 코드 변경 시)
docker compose build

# 백그라운드 실행
docker compose up -d

# 로그 확인
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

# 프론트엔드
# 브라우저에서 http://이-서버-IP:3000 접속
```

---

## 서비스 포트

| 서비스 | 호스트 포트 | 설명 |
|--------|------------|------|
| 프론트엔드 | 3000 | 사용자 접속 URL |
| 백엔드 API | 8000 | REST API (내부용, 직접 접근 불필요) |
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

# DB 접속
docker compose exec db psql -U postgres -d tc_generator
```

---

## 환경변수 전체 목록

### backend/.env

| 변수명 | 설명 | 필수 |
|--------|------|------|
| `DTGPT_BASE_URL` | 사내 dtgpt API 주소 | ★ |
| `DTGPT_API_KEY` | dtgpt API 키 | ★ |
| `DTGPT_MODEL` | LLM 모델명 (기본: `dtgpt`) | |
| `EXECUTOR_BASE_URL` | sqe_tc_executor 서버 주소 | ★ |
| `EXECUTOR_CALLBACK_URL` | 실행 결과를 받을 이 서버의 주소 | ★ |
| `JWT_SECRET` | JWT 서명 키 (executor와 동일) | ★ |
| `DATABASE_URL` | PostgreSQL 접속 URL | ★ |
| `REDIS_URL` | Redis 접속 URL | ★ |
| `DEV_MODE` | `true`: SAML 우회 개발모드 | |
| `SAML_ACS_URL` | SAML ACS 콜백 URL | 운영 |
| `SAML_IDP_METADATA_URL` | 사내 IdP 메타데이터 URL | 운영 |
| `CORS_ORIGINS` | 허용 CORS 도메인 | ★ |
| `DEBUG` | 디버그 로그 (기본: `false`) | |

### 루트 .env (docker-compose용)

| 변수명 | 설명 |
|--------|------|
| `INTERNAL_REGISTRY` | 사내 Docker 레지스트리 주소 |
| `APT_MIRROR` | 사내 Ubuntu apt 미러 URL |
| `PIP_INDEX_URL` | 사내 PyPI 미러 URL |
| `PIP_TRUSTED_HOST` | 사내 PyPI 미러 호스트명 |
| `NPM_REGISTRY` | 사내 npm 레지스트리 URL |
| `EXECUTOR_HOST` | executor 서버 IP/호스트명 |
| `VITE_EXECUTOR_WS_URL` | executor WebSocket 주소 (빌드 시 결정) |
| `DB_PASSWORD` | PostgreSQL 비밀번호 |

---

## 트러블슈팅

### 이미지를 pull 할 수 없음
```
Error response from daemon: pull access denied
```
→ 사내 레지스트리에 이미지가 없는 경우. 담당자에게 이미지 등록을 요청하세요.
→ `/etc/docker/daemon.json`에 `insecure-registries` 등록 여부 확인

### pip 패키지 설치 실패
```
Could not find a version that satisfies the requirement
```
→ `PIP_INDEX_URL`이 올바른지 확인
→ `PIP_TRUSTED_HOST`가 설정되어 있는지 확인

### DB 마이그레이션 오류
```bash
# 마이그레이션 기록 초기화 후 재시도
docker compose exec backend alembic stamp head
docker compose exec backend alembic upgrade head
```

### executor 연결 오류
→ `EXECUTOR_BASE_URL`이 executor 서버의 실제 IP:포트인지 확인
→ 방화벽에서 8001 포트 허용 여부 확인

### SAML 인증 오류
→ `backend/app/core/saml/settings.json`의 IdP 정보 확인
→ 테스트 시 `DEV_MODE=true` 사용

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
