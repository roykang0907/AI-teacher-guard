"""민원 엔드포인트 — ingest / list / detail."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import Complaint
from ..nlp.pipeline import Pipeline
from ..nlp.rewrite import rewrite_complaint
from ..schemas import ComplaintIngest, ComplaintListItem, ComplaintOut

router = APIRouter(prefix="/api/complaints", tags=["complaints"])

_pipeline = Pipeline(model_dir=settings.classifier_model_dir)

_LABEL_WEIGHT = {"정상": 1, "주의": 2, "위험": 3}


def compute_priority(label: str, intensity: int, emergency: bool) -> int:
    """우선순위 점수 — 긴급 > 위험 > 강도순. 대시보드 큐 정렬용."""
    return _LABEL_WEIGHT.get(label, 1) * 10 + intensity * 2 + (50 if emergency else 0)


@router.post("/ingest", response_model=ComplaintOut)
def ingest(payload: ComplaintIngest, db: Session = Depends(get_db)):
    text = payload.text.strip()
    if not text:
        raise HTTPException(400, "빈 민원입니다.")

    # 1단계 분류 + 긴급 룰
    result = _pipeline.classify(text)
    is_emg = result["emergency"]["is_emergency"]

    # 2단계 순화 (옵션)
    rewritten = None
    if settings.auto_rewrite:
        rewritten, _ = rewrite_complaint(text)

    c = Complaint(
        original_text=text,
        rewritten_text=rewritten,
        label=result["label"],
        score=result["score"],
        model_label=result["model_label"],
        overridden=result["overridden"],
        category=result["category"],
        intensity=result["intensity"],
        emergency=result["emergency"],
        priority=compute_priority(result["label"], result["intensity"], is_emg),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("", response_model=list[ComplaintListItem])
def list_complaints(
    status: str | None = None,
    label: str | None = None,
    db: Session = Depends(get_db),
):
    """우선순위(긴급도) 내림차순 목록."""
    stmt = select(Complaint)
    if status:
        stmt = stmt.where(Complaint.status == status)
    if label:
        stmt = stmt.where(Complaint.label == label)
    stmt = stmt.order_by(Complaint.priority.desc(), Complaint.created_at.desc())
    return list(db.scalars(stmt))


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    c = db.get(Complaint, complaint_id)
    if not c:
        raise HTTPException(404, "민원을 찾을 수 없습니다.")
    return c
