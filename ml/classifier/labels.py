"""3클래스 라벨 정의 + AI Hub 감성 대화 말뭉치 감정 → 3클래스 매핑.

핸드오프 문서 §5 데이터 전략 기준:
    분노/혐오/공격 → 위험
    불만/슬픔/불안 → 주의
    중립/기쁨      → 정상
"""

from __future__ import annotations

# --- 3클래스 (순서 = id) ---
LABELS: list[str] = ["정상", "주의", "위험"]
LABEL2ID: dict[str, int] = {label: i for i, label in enumerate(LABELS)}
ID2LABEL: dict[int, str] = {i: label for i, label in enumerate(LABELS)}

NORMAL, CAUTION, DANGER = 0, 1, 2

# --- AI Hub 감성 대화 말뭉치 감정(대분류/세부) → 3클래스 ---
# 실제 데이터의 감정 컬럼명/값은 승인 후 확인하여 보강한다.
# 매핑되지 않은 감정은 보수적으로 '주의'(CAUTION)로 폴백한다(위험 누락 방지 성향).
EMOTION_TO_LABEL: dict[str, str] = {
    # 위험: 분노/혐오/공격 계열
    "분노": "위험",
    "노여움": "위험",
    "혐오": "위험",
    "경멸": "위험",
    "공격": "위험",
    "적대": "위험",
    "분개": "위험",
    # 주의: 불만/슬픔/불안 계열
    "불만": "주의",
    "짜증": "주의",
    "슬픔": "주의",
    "우울": "주의",
    "불안": "주의",
    "당황": "주의",
    "두려움": "주의",
    "상처": "주의",
    "실망": "주의",
    # 정상: 중립/기쁨 계열
    "중립": "정상",
    "기쁨": "정상",
    "행복": "정상",
    "감사": "정상",
    "만족": "정상",
    "평온": "정상",
}

DEFAULT_LABEL = "주의"  # 미매핑 감정 폴백 (보수적)


def map_emotion_to_label(emotion: str) -> str:
    """감성 대화 말뭉치 감정 라벨을 3클래스로 매핑한다.

    공백/세부분류 접미사를 제거한 뒤 키워드 부분일치로 매핑한다.
    """
    if not emotion:
        return DEFAULT_LABEL
    key = emotion.strip()
    if key in EMOTION_TO_LABEL:
        return EMOTION_TO_LABEL[key]
    # 부분일치 (예: "분노/격노", "E10_분노")
    for emo, label in EMOTION_TO_LABEL.items():
        if emo in key:
            return label
    return DEFAULT_LABEL


def label_to_id(label: str) -> int:
    return LABEL2ID[label]


if __name__ == "__main__":
    print("LABELS:", LABELS)
    print("LABEL2ID:", LABEL2ID)
    samples = ["분노", "E10_혐오", "불안감", "기쁨", "알수없는감정", ""]
    print("\n감정 → 3클래스 매핑 예시:")
    for s in samples:
        print(f"  {s!r:>16}  ->  {map_emotion_to_label(s)}")
