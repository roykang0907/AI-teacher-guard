"""합성 민원 시나리오 템플릿 (가상 — 실제 학부모 발화 아님).

각 템플릿: (카테고리, 라벨, 강도, 핵심 원문 orig_core, 순화문 rewr).
- orig_core : 학부모 민원의 '핵심 문장' (접두/접미 감정표현은 generator 가 붙임)
- rewr      : 감정·과장 제거 후 핵심 요구만 남긴 공적 표현 (2단계 학습 타깃)

조사 처리: 슬롯 뒤 `[이/가] [을/를] [은/는] [와/과] [으로/로]` 마커를 쓰면
generator 가 앞 글자 받침에 따라 자동으로 올바른 조사를 선택한다.

6개 카테고리(핸드오프 §2-3):
    안전·폭력 / 환불·분쟁 / 학습상담 / 단순문의 / 감정성불만 / 칭찬·감사
라벨: 정상 / 주의 / 위험   강도: 1(낮음)~3(높음)
"""

from __future__ import annotations

# 슬롯 값
CHILD = ["우리 아이", "저희 애", "제 아들", "제 딸", "우리 애", "애"]
TOPIC_SAFETY = ["체험학습", "현장체험", "체육 수업", "쉬는 시간", "급식 시간", "등하교"]
TOPIC_REFUND = ["방과후 수업", "현장학습비", "교재비", "급식비", "수련회비", "특강비"]
TOPIC_STUDY = ["수학 진도", "받아쓰기", "독서 활동", "수행평가", "발표 수업", "영어 수업"]
TOPIC_INFO = ["준비물", "현장학습 일정", "방학 과제", "상담 일정", "급식 식단", "알림장"]
TOPIC_EMO = ["자리 배치", "모둠 편성", "생활지도", "알림장 안내", "숙제 분량", "청소 당번"]

# 핵심 원문(orig_core) — 끝에 마침표 없이, 접미 표현은 generator가 붙임
TEMPLATES: list[dict] = [
    # ---------------- 안전·폭력 (위험) ----------------
    {"category": "안전·폭력", "label": "위험", "intensity": 3, "topics": TOPIC_SAFETY,
     "orig_core": "{child}[이/가] {topic} 중에 다쳤는데 관리[을/를] 대체 어떻게 하는 겁니까",
     "rewr": "{topic} 중 발생한 {child}의 부상 경위 확인과 안전 조치를 요청드립니다."},
    {"category": "안전·폭력", "label": "위험", "intensity": 3, "topics": TOPIC_SAFETY,
     "orig_core": "{child}[이/가] {topic} 때 친구한테 맞고 왔는데 선생님[은/는] 뭐 하셨습니까",
     "rewr": "{topic} 중 {child} 간 발생한 갈등의 사실관계 확인과 관련 절차 안내를 요청드립니다."},
    {"category": "안전·폭력", "label": "주의", "intensity": 2, "topics": TOPIC_SAFETY,
     "orig_core": "{topic} 때 안전 관리가 너무 부실한 거 아닙니까",
     "rewr": "{topic} 시 안전 관리 방안과 사고 예방 절차에 대한 안내를 요청드립니다."},

    # ---------------- 환불·분쟁 (위험/주의) ----------------
    {"category": "환불·분쟁", "label": "위험", "intensity": 3, "topics": TOPIC_REFUND,
     "orig_core": "{topic}[으로/로] 낸 돈이 얼만데 이런 식으로 운영합니까",
     "rewr": "{topic} 운영 내역 확인과 환불 가능 여부 및 절차에 대한 안내를 요청드립니다."},
    {"category": "환불·분쟁", "label": "주의", "intensity": 2, "topics": TOPIC_REFUND,
     "orig_core": "{child}[이/가] {topic}[을/를] 안 갔는데 왜 비용[을/를] 다 떼갑니까",
     "rewr": "{child}가 참여하지 않은 {topic}의 비용 정산 기준에 대한 설명을 요청드립니다."},

    # ---------------- 학습상담 (주의/정상) ----------------
    {"category": "학습상담", "label": "주의", "intensity": 2, "topics": TOPIC_STUDY,
     "orig_core": "{child} {topic}[이/가] 너무 뒤처지는데 학교에서 신경은 쓰는 겁니까",
     "rewr": "{child}의 {topic} 학습 상황과 가정에서 도울 수 있는 방법에 대한 상담을 요청드립니다."},
    {"category": "학습상담", "label": "정상", "intensity": 1, "topics": TOPIC_STUDY,
     "q": False,
     "orig_core": "{child} {topic}[이/가] 요즘 어떤지 궁금해서 여쭤봅니다",
     "rewr": "{child}의 {topic} 학습 상황과 가정 지도 방법에 대한 상담을 요청드립니다."},

    # ---------------- 단순문의 (정상) ----------------
    {"category": "단순문의", "label": "정상", "intensity": 1, "topics": TOPIC_INFO,
     "q": False,
     "orig_core": "{topic} 안내문[을/를] 못 봐서 다시 한 번 확인하고 싶습니다",
     "rewr": "{topic} 안내 사항의 재확인을 요청드립니다."},
    {"category": "단순문의", "label": "정상", "intensity": 1, "topics": TOPIC_INFO,
     "q": False,
     "orig_core": "{child} {topic}[이/가] 어떻게 되는지 확인 부탁드립니다",
     "rewr": "{child}의 {topic} 관련 사항 확인을 요청드립니다."},

    # ---------------- 감정성불만 (위험/주의) ----------------
    {"category": "감정성불만", "label": "위험", "intensity": 3, "topics": TOPIC_EMO,
     "orig_core": "{topic} 이게 말이 됩니까, 선생님[이/가] 자격이 있긴 한 거예요",
     "rewr": "{topic} 운영 방식에 대한 결정 기준과 배경 설명을 요청드립니다."},
    {"category": "감정성불만", "label": "주의", "intensity": 2, "topics": TOPIC_EMO,
     "orig_core": "{child}[이/가] {topic} 때문에 속상해하던데 좀 더 신경 써 주실 수 없나요",
     "rewr": "{child}의 {topic} 관련 어려움에 대한 확인과 지도 방안 상담을 요청드립니다."},

    # ---------------- 칭찬·감사 (정상) ----------------
    {"category": "칭찬·감사", "label": "정상", "intensity": 1, "topics": TOPIC_STUDY,
     "q": False,
     "orig_core": "선생님 덕분에 {child}[이/가] {topic}에 흥미[을/를] 붙였어요",
     "rewr": "{child}의 {topic} 지도에 대한 감사 인사를 전합니다."},
]

# 라벨별 접두(감정 도입)·접미(요구/위협) — 원문에만 붙고 순화문엔 반영 안 됨
PREFIX = {
    "위험": ["", "아니 ", "진짜 ", "도대체 ", "하… "],
    "주의": ["", "저기 ", "그… ", "솔직히 "],
    "정상": ["", "안녕하세요, "],
}
CLOSER = {
    "위험": [
        "당장 책임지세요.",
        "이거 그냥 안 넘어갑니다.",
        "고소하겠습니다.",
        "교육청에 신고하겠습니다.",
        "변호사 통해 법적으로 대응하겠습니다.",
        "기자한테 제보하겠습니다.",
    ],
    "주의": [
        "답변 부탁드립니다.",
        "확인 좀 부탁드려요.",
        "많이 서운합니다.",
        "개선 부탁드립니다.",
    ],
    "정상": [
        "부탁드립니다.",
        "감사합니다.",
        "확인 부탁드려요.",
    ],
}
