"""백엔드 설정 (환경변수 기반)."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings:
    # DB: 기본 SQLite(설치 없이 바로 실행). 풀 RAG는 docker-compose의 Postgres+pgvector.
    #   Postgres 예: postgresql+psycopg://aitg:aitg@localhost:5432/aitg
    database_url: str = os.environ.get(
        "DATABASE_URL", f"sqlite:///{REPO_ROOT / 'backend' / 'aitg.db'}"
    )

    # 2단계 순화 LLM (로컬 Ollama). 외부 API 금지(절대원칙 3).
    ollama_url: str = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    ollama_model: str = os.environ.get("OLLAMA_MODEL", "qwen2.5:14b")

    # 1단계 KoBERT 모델 경로(없으면 휴리스틱 폴백)
    classifier_model_dir: str | None = os.environ.get("CLASSIFIER_MODEL_DIR") or None

    # 순화 자동 수행 여부(ingest 시). Ollama 미가동 시 graceful stub.
    auto_rewrite: bool = os.environ.get("AUTO_REWRITE", "1") == "1"

    disclaimer: str = "본 제안은 AI가 생성한 참고용이며, 최종 판단과 책임은 교사에게 있습니다."


settings = Settings()
