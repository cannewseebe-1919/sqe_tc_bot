# -----------------------------------------------
# 사내망 환경 변수
# -----------------------------------------------
ARG INTERNAL_REGISTRY=docker-registry.internal
ARG NPM_REGISTRY=http://npm-registry.internal

# ── 1단계: 빌드 ────────────────────────────────
FROM ${INTERNAL_REGISTRY}/node:18-alpine AS builder

ARG NPM_REGISTRY
ARG VITE_EXECUTOR_WS_URL=ws://localhost:8001

WORKDIR /app

# npm 레지스트리를 사내 레지스트리로 교체
RUN npm config set registry ${NPM_REGISTRY}

COPY package.json package-lock.json ./
RUN npm ci --prefer-offline

COPY . .

# WebSocket URL은 빌드 시점에 결정됨 (executor 서버 주소)
ENV VITE_EXECUTOR_WS_URL=${VITE_EXECUTOR_WS_URL}

RUN npm run build

# ── 2단계: nginx 서빙 ──────────────────────────
FROM ${INTERNAL_REGISTRY}/nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# 환경변수 치환을 지원하는 nginx 템플릿 설정
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80

# nginx 공식 이미지가 /docker-entrypoint.d/ 스크립트로 envsubst 자동 실행
