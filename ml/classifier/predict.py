"""1단계 추론 — 모델 분류 + 긴급 룰 오버라이드.

파이프라인:
    1) KoBERT 로 정상/주의/위험 확률 산출
    2) 긴급 키워드 룰(detect_emergency) 에 걸리면 '위험'으로 강제 승격
       (모델 점수가 낮아도 안전·법적 사안은 놓치지 않는다 — 절대원칙 2)
    3) 메타데이터(원 모델 라벨, 긴급 사유)를 분리 보존 — 절대원칙 4

백엔드 /api/complaints/ingest 가 이 Classifier 를 호출하는 형태를 가정한다.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field

from .config import TrainConfig
from .emergency_rules import detect_emergency
from .labels import DANGER, ID2LABEL


@dataclass
class Prediction:
    label: str  # 최종 라벨(룰 오버라이드 반영)
    label_id: int
    score: float  # 최종 라벨의 모델 확률(오버라이드 시 1.0)
    model_label: str  # 룰 적용 전 모델 원 라벨 (메타데이터)
    probabilities: dict = field(default_factory=dict)
    emergency: dict = field(default_factory=dict)
    overridden: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


class Classifier:
    """학습된 KoBERT 분류기 + 긴급 룰 래퍼."""

    def __init__(self, model_dir: str, cfg: TrainConfig | None = None):
        self.cfg = cfg or TrainConfig()
        self.cfg.backbone = model_dir  # 저장된 모델 디렉터리에서 로드
        self.model_dir = model_dir
        self._tokenizer = None
        self._model = None

    def _lazy_load(self):
        if self._model is not None:
            return
        import torch
        from transformers import AutoModelForSequenceClassification

        from .model import load_tokenizer

        self._tokenizer = load_tokenizer(self.cfg)
        self._model = AutoModelForSequenceClassification.from_pretrained(
            self.model_dir, trust_remote_code=True
        )
        self._model.eval()
        self._torch = torch

    def predict(self, text: str) -> Prediction:
        self._lazy_load()
        torch = self._torch

        enc = self._tokenizer(
            text,
            truncation=True,
            max_length=self.cfg.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        with torch.no_grad():
            logits = self._model(**enc).logits
        probs = torch.softmax(logits, dim=-1).squeeze(0).tolist()
        model_id = int(max(range(len(probs)), key=lambda i: probs[i]))
        model_label = ID2LABEL[model_id]

        # 긴급 룰 오버라이드
        emg = detect_emergency(text)
        if emg.is_emergency and model_id != DANGER:
            return Prediction(
                label=ID2LABEL[DANGER],
                label_id=DANGER,
                score=1.0,
                model_label=model_label,
                probabilities={ID2LABEL[i]: round(p, 4) for i, p in enumerate(probs)},
                emergency=emg.as_dict(),
                overridden=True,
            )

        return Prediction(
            label=model_label,
            label_id=model_id,
            score=round(probs[model_id], 4),
            model_label=model_label,
            probabilities={ID2LABEL[i]: round(p, 4) for i, p in enumerate(probs)},
            emergency=emg.as_dict(),
            overridden=False,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="1단계 분류 추론")
    parser.add_argument("--model", default="outputs/kobert-classifier")
    parser.add_argument("--text", required=True)
    args = parser.parse_args()

    clf = Classifier(args.model)
    pred = clf.predict(args.text)

    print(f"입력: {args.text}")
    print(f"→ 최종 라벨: {pred.label} (score={pred.score})")
    if pred.overridden:
        print(f"  ⚠️ 긴급 룰 오버라이드: 모델은 '{pred.model_label}' 였으나 위험으로 승격")
        print(f"  사유: {pred.emergency['categories']}")
    print(f"  확률분포: {pred.probabilities}")


if __name__ == "__main__":
    main()
