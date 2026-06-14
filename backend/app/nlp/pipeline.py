"""1단계 분류 파이프라인 (백엔드용).

흐름:
    1) 긴급 룰(detect_emergency) → 걸리면 '위험' 강제 + 우선순위 상단
    2) 학습된 KoBERT 모델이 있으면 그것으로 분류
    3) 없으면 휴리스틱 키워드 분류로 폴백 (모델 학습 전에도 데모 가능)

→ 메타데이터(원어조 추정·강도·긴급·카테고리)를 분리 보존(절대원칙 4).
ml/classifier 의 긴급룰·라벨 정의를 단일 출처로 재사용한다.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ml/ 패키지를 import 경로에 추가 (단일 출처 재사용)
_ML_DIR = Path(__file__).resolve().parents[3] / "ml"
if str(_ML_DIR) not in sys.path:
    sys.path.insert(0, str(_ML_DIR))

from classifier.emergency_rules import detect_emergency  # noqa: E402
from classifier.labels import DANGER, ID2LABEL, LABELS  # noqa: E402

# ── 휴리스틱 키워드 (모델 학습 전 폴백) ──────────────────────────────────────
_DANGER_KW = [
    "고소", "고발", "소송", "변호사", "법적", "책임지", "자격", "당장",
    "가만", "신고", "기자", "죽", "학대", "폭행", "안 넘어",
]
_CAUTION_KW = [
    "속상", "서운", "불만", "납득", "부실", "뒤처", "방치", "개선",
    "아쉽", "왜", "곤란", "걱정",
]
_CATEGORY_KW = {
    "안전·폭력": ["다쳤", "다치", "맞고", "안전", "학폭", "사고", "부상"],
    "환불·분쟁": ["환불", "비용", "돈", "결제", "정산", "수강료", "교재비"],
    "학습상담": ["학습", "진도", "성적", "수업", "공부", "수행평가", "받아쓰기"],
    "단순문의": ["일정", "준비물", "확인", "문의", "안내문", "식단"],
    "칭찬·감사": ["감사", "고맙", "덕분"],
}


def _heuristic_label(text: str) -> tuple[str, float]:
    d = sum(text.count(k) for k in _DANGER_KW)
    c = sum(text.count(k) for k in _CAUTION_KW)
    excl = text.count("!") + text.count("?")
    if d >= 1:
        return "위험", min(0.5 + 0.1 * d, 0.95)
    if c >= 1 or excl >= 2:
        return "주의", min(0.5 + 0.1 * (c + excl // 2), 0.9)
    return "정상", 0.6


def _guess_category(text: str) -> str:
    best, best_hits = "감정성불만", 0
    for cat, kws in _CATEGORY_KW.items():
        hits = sum(1 for k in kws if k in text)
        if hits > best_hits:
            best, best_hits = cat, hits
    return best


def _intensity(text: str) -> int:
    score = text.count("!") + sum(text.count(k) for k in _DANGER_KW)
    return 3 if score >= 3 else 2 if score >= 1 else 1


class Pipeline:
    """1단계 분류 파이프라인. 모델 경로가 있으면 KoBERT, 없으면 휴리스틱."""

    def __init__(self, model_dir: str | None = None):
        self.model_dir = model_dir
        self._clf = None
        self._mode = "heuristic"
        if model_dir and Path(model_dir).exists():
            self._mode = "kobert"  # 실제 로드는 최초 호출 시 지연

    def _ensure_model(self):
        if self._clf is None and self._mode == "kobert":
            from classifier.predict import Classifier

            self._clf = Classifier(self.model_dir)

    def classify(self, text: str) -> dict:
        emg = detect_emergency(text)

        if self._mode == "kobert":
            self._ensure_model()
            pred = self._clf.predict(text)
            label, score = pred.label, pred.score
            model_label = pred.model_label
            overridden = pred.overridden
        else:
            model_label, score = _heuristic_label(text)
            label = model_label
            overridden = False
            # 휴리스틱에도 긴급 오버라이드 적용
            if emg.is_emergency and label != ID2LABEL[DANGER]:
                label, score, overridden = ID2LABEL[DANGER], 1.0, True

        return {
            "label": label,
            "score": round(float(score), 4),
            "model_label": model_label,      # 룰 적용 전 (메타데이터)
            "overridden": overridden,
            "emergency": emg.as_dict(),
            "category": _guess_category(text),
            "intensity": _intensity(text),   # 원어조 강도 추정 (메타데이터)
            "engine": self._mode,
        }


if __name__ == "__main__":
    pipe = Pipeline()  # 휴리스틱 모드
    tests = [
        "애가 체험학습 중 다쳤는데 당장 고소하겠습니다.",
        "우리 아이 수학 진도가 뒤처져 걱정입니다. 상담 가능할까요?",
        "급식 식단표 한 번 더 확인 부탁드립니다.",
        "이건 명백한 아동학대입니다. 변호사 통해 대응하겠습니다.",
    ]
    print(f"엔진: {pipe._mode}  (라벨: {LABELS})\n")
    for t in tests:
        r = pipe.classify(t)
        tag = "🚨" if r["emergency"]["is_emergency"] else "  "
        print(f"{tag} [{r['label']}/{r['category']}/강도{r['intensity']}] {t}")
        if r["overridden"]:
            print(f"      ↳ 긴급 오버라이드(모델:{r['model_label']}) 사유:{r['emergency']['categories']}")
