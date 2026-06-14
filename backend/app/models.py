"""DB 모델 — 민원/답변 초안.

메타데이터(원어조·강도·긴급)는 분리 보존(절대원칙 4). 원본은 항상 보관(절대원칙 1).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 원본 (항상 열람 가능)
    original_text: Mapped[str] = mapped_column(Text)
    # 2단계 순화 결과 (기본 뷰)
    rewritten_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 1단계 분류 결과
    label: Mapped[str] = mapped_column(String(8))          # 정상/주의/위험
    score: Mapped[float] = mapped_column(Float, default=0.0)
    model_label: Mapped[str | None] = mapped_column(String(8), nullable=True)
    overridden: Mapped[bool] = mapped_column(default=False)

    # 메타데이터 (분리 보존)
    category: Mapped[str | None] = mapped_column(String(16), nullable=True)
    intensity: Mapped[int] = mapped_column(Integer, default=1)
    emergency: Mapped[dict] = mapped_column(JSON, default=dict)
    priority: Mapped[int] = mapped_column(Integer, default=0, index=True)

    status: Mapped[str] = mapped_column(String(16), default="new")  # new/in_progress/done

    drafts: Mapped[list["Draft"]] = relationship(back_populates="complaint")


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"))
    text: Mapped[str] = mapped_column(Text)
    lint: Mapped[dict] = mapped_column(JSON, default=dict)

    complaint: Mapped["Complaint"] = relationship(back_populates="drafts")
