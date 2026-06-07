"""긴급 키워드 룰 사전 — 분류 결과와 무관하게 우선순위 상단 노출.

핸드오프 문서 §2-3 / §3 절대원칙 2:
    안전·법적 사안(학폭·아동학대·자해·고소)은 룰로 즉시 '위험' 상단.
    진짜 긴급 민원을 모델이 놓치는 사고를 방지하는 안전망.

모델 분류 점수가 낮아도 여기서 걸리면 위험(DANGER)으로 강제 승격한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# 카테고리별 긴급 키워드. 표현 변형을 흡수하기 위해 정규식 조각으로 둔다.
EMERGENCY_KEYWORDS: dict[str, list[str]] = {
    "학교폭력": [
        "학폭", "학교폭력", "집단따돌림", "왕따", "괴롭힘", "폭행", "폭력",
        "때렸", "맞았", "빵셔틀", "학교폭력대책",
    ],
    "아동학대": [
        "아동학대", "정서학대", "신체학대", "방임", "학대", "체벌",
        "아이를 때", "신고하겠", "아동보호",
    ],
    "자해_자살": [
        "자해", "자살", "극단적 선택", "죽고 싶", "죽어버리", "죽겠다",
        "목숨", "유서", "위협",
    ],
    "법적조치": [
        "고소", "고발", "소송", "변호사", "법적 대응", "법적대응", "민사",
        "형사", "손해배상", "경찰", "112", "언론", "기자", "국민신문고",
        "교육청에 신고", "감사 요청",
    ],
}

# 정규식 사전 컴파일 (대소문자/공백 변형 흡수)
_COMPILED: dict[str, list[re.Pattern]] = {
    category: [re.compile(re.escape(kw)) for kw in kws]
    for category, kws in EMERGENCY_KEYWORDS.items()
}


@dataclass
class EmergencyMatch:
    """긴급 룰 매칭 결과."""

    is_emergency: bool = False
    categories: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "is_emergency": self.is_emergency,
            "categories": self.categories,
            "keywords": self.keywords,
        }


def detect_emergency(text: str) -> EmergencyMatch:
    """텍스트에서 긴급 키워드를 탐지한다.

    하나라도 걸리면 is_emergency=True. 매칭된 카테고리/키워드를 함께 반환해
    대시보드 우선순위 큐와 사유 표시에 활용한다.
    """
    if not text:
        return EmergencyMatch()

    matched_categories: list[str] = []
    matched_keywords: list[str] = []
    for category, patterns in _COMPILED.items():
        hit = False
        for pat in patterns:
            if pat.search(text):
                matched_keywords.append(pat.pattern)
                hit = True
        if hit:
            matched_categories.append(category)

    return EmergencyMatch(
        is_emergency=bool(matched_categories),
        categories=matched_categories,
        keywords=matched_keywords,
    )


if __name__ == "__main__":
    tests = [
        "애 관리를 어떻게 하길래 다쳐서 오냐, 당장 고소하겠다",
        "우리 아이가 학폭을 당한 것 같아요. 정확히 확인 부탁드립니다.",
        "체험학습 일정이 궁금해서 문의드립니다.",
        "선생님 항상 감사합니다.",
        "이건 명백한 아동학대입니다. 변호사 통해 소송하겠습니다.",
    ]
    for t in tests:
        m = detect_emergency(t)
        flag = "🚨 긴급" if m.is_emergency else "—"
        print(f"{flag:>6} | {m.categories} | {t}")
