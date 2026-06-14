"""답변 초안 엔드포인트 — suggest(RAG+LLM) / validate(린터)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..linter.lint import lint_summary
from ..models import Complaint
from ..nlp.rewrite import draft_reply
from ..schemas import (
    DraftSuggestion,
    DraftSuggestRequest,
    DraftValidateRequest,
    LintResult,
)

router = APIRouter(prefix="/api/draft", tags=["draft"])


@router.post("/suggest", response_model=DraftSuggestion)
def suggest(payload: DraftSuggestRequest, db: Session = Depends(get_db)):
    """민원에 대한 답변 초안 제안. (RAG 매칭은 STEP 3 pgvector 연동 시 추가)"""
    c = db.get(Complaint, payload.complaint_id)
    if not c:
        raise HTTPException(404, "민원을 찾을 수 없습니다.")
    suggestion, engine = draft_reply(
        c.original_text,
        c.rewritten_text,
        category=c.category,
        emergency=bool(c.emergency and c.emergency.get("is_emergency")),
    )
    return DraftSuggestion(
        complaint_id=c.id,
        suggestion=suggestion,
        engine=engine,
        disclaimer=settings.disclaimer,
    )


@router.post("/validate", response_model=LintResult)
def validate(payload: DraftValidateRequest):
    """교사 답변 초안의 위험 표현 검출 (실시간 빨간줄 근거)."""
    summary = lint_summary(payload.text)
    return LintResult(**summary, disclaimer=settings.disclaimer)
