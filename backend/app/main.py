"""aiteacherguard 백엔드 — FastAPI 진입점."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db
from .routers import complaints, draft


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # 테이블 생성
    yield


app = FastAPI(
    title="aiteacherguard API",
    description="학부모 악성 민원 대응 보조 — 1단계 분류·2단계 순화·3단계 답변 코칭",
    version="0.1.0",
    lifespan=lifespan,
)

# 프론트(Expo web/ios) 개발 편의를 위한 CORS (운영 시 도메인 제한 권장)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(complaints.router)
app.include_router(draft.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "ollama_model": settings.ollama_model,
        "classifier": "kobert" if settings.classifier_model_dir else "heuristic",
        "disclaimer": settings.disclaimer,
    }
