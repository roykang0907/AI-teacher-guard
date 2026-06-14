"""로컬 임베딩 (Ollama). 외부 API 금지(절대원칙 3).

`ollama pull nomic-embed-text` 후 사용. 미가동 시 None 반환 → 서비스가 lexical 폴백.
"""

from __future__ import annotations

from ..config import settings

EMBED_MODEL = "nomic-embed-text"
EMBED_DIM = 768


def embed(text: str) -> list[float] | None:
    """단일 텍스트 임베딩. 실패 시 None."""
    try:
        import httpx

        resp = httpx.post(
            f"{settings.ollama_url}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=30.0,
        )
        resp.raise_for_status()
        vec = resp.json().get("embedding")
        return vec if vec else None
    except Exception:
        return None


def embed_many(texts: list[str]) -> list[list[float]] | None:
    out: list[list[float]] = []
    for t in texts:
        v = embed(t)
        if v is None:
            return None
        out.append(v)
    return out
