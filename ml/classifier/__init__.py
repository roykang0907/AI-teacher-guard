"""aiteacherguard 1단계 — 공격성 판단 엔진 (KoBERT 분류기).

민원 텍스트를 `정상 / 주의 / 위험` 3클래스로 분류하고,
긴급 키워드 룰로 안전·법적 사안을 즉시 위험 상단으로 끌어올린다.

핵심 평가 원칙: **위험을 정상으로 놓치는 false negative 최소화가 최우선.**
"""

from .labels import LABELS, LABEL2ID, ID2LABEL, map_emotion_to_label

__all__ = ["LABELS", "LABEL2ID", "ID2LABEL", "map_emotion_to_label"]
