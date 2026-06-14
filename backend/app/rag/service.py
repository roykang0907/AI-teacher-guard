"""RAG 검색 서비스.

기본: 시드 코퍼스에 대한 lexical 검색(한국어 2-gram + 토큰 overlap) — 설치 없이 동작.
풀 구성: pgvector + Ollama 임베딩(store.py) — DATABASE_URL=postgres & 임베딩 가용 시.

draft/suggest 가 민원 텍스트로 관련 지침을 검색해 답변 근거로 제시한다.
"""

from __future__ import annotations

import re

from .seed import SEED_DOCS


def _shingles(text: str) -> set[str]:
    """한국어 친화 토큰: 공백 제거 2-gram + 단어 토큰."""
    compact = re.sub(r"\s+", "", text)
    grams = {compact[i : i + 2] for i in range(len(compact) - 1)}
    words = set(re.findall(r"[가-힣A-Za-z0-9]+", text))
    return grams | words


def lexical_search(query: str, category: str | None = None, k: int = 2) -> list[dict]:
    """시드 코퍼스 lexical 검색. 같은 카테고리 문서엔 가중치."""
    q = _shingles(query)
    if not q:
        return []
    scored: list[tuple[float, dict]] = []
    for d in SEED_DOCS:
        doc = _shingles(f"{d['title']} {d['text']} {d.get('category', '')}")
        overlap = len(q & doc)
        if overlap == 0 and d.get("category") != category:
            continue
        score = overlap + (3 if category and d.get("category") == category else 0)
        scored.append((score, d))
    scored.sort(key=lambda x: -x[0])
    return [
        {"source": d["source"], "title": d["title"], "text": d["text"], "score": s}
        for s, d in scored[:k]
        if s > 0
    ]


def retrieve(query: str, category: str | None = None, k: int = 2) -> list[dict]:
    """관련 지침 top-k. 가능하면 벡터 검색, 아니면 lexical."""
    try:
        from ..config import settings

        if settings.database_url.startswith("postgresql"):
            from .store import vector_search

            hits = vector_search(query, k=k)
            if hits:
                return hits
    except Exception:
        pass
    return lexical_search(query, category=category, k=k)


if __name__ == "__main__":
    tests = [
        ("애가 체험학습 중 다쳤는데 고소하겠습니다.", "안전·폭력"),
        ("방과후 수업비 환불해주세요.", "환불·분쟁"),
        ("아이 수학 진도 상담하고 싶어요.", "학습상담"),
    ]
    for q, cat in tests:
        print(f"\nQ: {q}  (cat={cat})")
        for h in retrieve(q, category=cat):
            print(f"  - [{h['source']}] {h['title']} (score={h['score']})")
