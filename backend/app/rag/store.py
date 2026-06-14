"""pgvector 벡터 저장/검색 (풀 구성 — DATABASE_URL=postgres + Ollama 임베딩).

ingest_seed() 로 시드 코퍼스를 임베딩해 적재하고, vector_search() 로 코사인
유사도 top-k 를 조회한다. SQLite 기본 구성에서는 사용하지 않는다(service 가 lexical 폴백).

적재:
    python -m app.rag.store --ingest      # DATABASE_URL=postgres... 필요
"""

from __future__ import annotations

from sqlalchemy import Integer, String, Text, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from ..config import settings
from .embed import EMBED_DIM, embed
from .seed import SEED_DOCS


class RagBase(DeclarativeBase):
    pass


def _vector_type():
    from pgvector.sqlalchemy import Vector

    return Vector(EMBED_DIM)


class RagDocument(RagBase):
    __tablename__ = "rag_documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(32), default="")
    chunk: Mapped[str] = mapped_column(Text)
    # 임베딩 컬럼은 pgvector 환경에서만 유효
    try:
        from pgvector.sqlalchemy import Vector

        embedding: Mapped[list[float]] = mapped_column(Vector(EMBED_DIM))
    except Exception:  # pragma: no cover
        pass


def _engine():
    return create_engine(settings.database_url, future=True)


def ensure_schema() -> None:
    eng = _engine()
    with eng.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    RagBase.metadata.create_all(eng)


def ingest_seed() -> int:
    """시드 코퍼스를 임베딩해 적재. 반환 적재 건수."""
    ensure_schema()
    eng = _engine()
    Session = sessionmaker(bind=eng)
    n = 0
    with Session() as s:
        for d in SEED_DOCS:
            vec = embed(f"{d['title']} {d['text']}")
            if vec is None:
                raise RuntimeError("Ollama 임베딩 실패 — nomic-embed-text 확인")
            s.add(
                RagDocument(
                    source=d["source"],
                    title=d["title"],
                    category=d.get("category", ""),
                    chunk=d["text"],
                    embedding=vec,
                )
            )
            n += 1
        s.commit()
    return n


def vector_search(query: str, k: int = 2) -> list[dict]:
    """코사인 유사도 top-k. 임베딩 불가 시 빈 리스트."""
    qv = embed(query)
    if qv is None:
        return []
    eng = _engine()
    Session = sessionmaker(bind=eng)
    with Session() as s:
        stmt = (
            select(RagDocument)
            .order_by(RagDocument.embedding.cosine_distance(qv))
            .limit(k)
        )
        return [
            {"source": d.source, "title": d.title, "text": d.chunk, "score": 1.0}
            for d in s.scalars(stmt)
        ]


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--ingest", action="store_true")
    args = ap.parse_args()
    if args.ingest:
        print(f"✅ 적재 {ingest_seed()}건")
