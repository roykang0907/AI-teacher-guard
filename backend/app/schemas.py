"""Pydantic 요청/응답 스키마."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# ── 요청 ──
class ComplaintIngest(BaseModel):
    text: str = Field(..., min_length=1, description="학부모 민원 원문")


class DraftSuggestRequest(BaseModel):
    complaint_id: int


class DraftValidateRequest(BaseModel):
    text: str = Field(..., description="교사 답변 초안")


# ── 응답 ──
class ComplaintOut(BaseModel):
    id: int
    created_at: datetime
    original_text: str
    rewritten_text: str | None
    label: str
    score: float
    model_label: str | None
    overridden: bool
    category: str | None
    intensity: int
    emergency: dict
    priority: int
    status: str

    class Config:
        from_attributes = True


class ComplaintListItem(BaseModel):
    id: int
    created_at: datetime
    label: str
    category: str | None
    intensity: int
    priority: int
    status: str
    emergency: dict
    rewritten_text: str | None  # 목록은 순화 카드 미리보기

    class Config:
        from_attributes = True


class LintFindingOut(BaseModel):
    rule_id: str
    category: str
    severity: str
    start: int
    end: int
    matched_text: str
    message: str
    suggestion: str


class LintResult(BaseModel):
    ok: bool
    total: int
    danger: int
    findings: list[LintFindingOut]
    disclaimer: str


class GuidelineRef(BaseModel):
    source: str
    title: str
    text: str


class DraftSuggestion(BaseModel):
    complaint_id: int
    suggestion: str
    engine: str
    references: list[GuidelineRef]  # RAG 매칭 지침
    disclaimer: str
