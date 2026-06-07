"""KoBERT 토크나이저/모델 로더.

KoBERT는 토크나이저 로딩이 표준 AutoTokenizer와 다르다.
- skt/kobert-base-v1  → `kobert_tokenizer.KoBERTTokenizer`
- monologg/kobert     → AutoTokenizer(trust_remote_code=True) 로도 가능

토크나이저 로딩을 한 곳에 캡슐화해 train/predict가 동일 경로를 쓰게 한다.
"""

from __future__ import annotations

from .config import TrainConfig
from .labels import ID2LABEL, LABEL2ID


def load_tokenizer(cfg: TrainConfig):
    """백본에 맞는 토크나이저를 로드한다."""
    backbone = cfg.backbone
    if backbone.startswith("skt/kobert"):
        # 공식 KoBERT 경로
        try:
            from kobert_tokenizer import KoBERTTokenizer
        except ImportError as e:  # pragma: no cover - 안내용
            raise ImportError(
                "skt/kobert-base-v1 사용에는 kobert_tokenizer 가 필요합니다.\n"
                "  pip install 'git+https://github.com/SKTBrain/KoBERT.git#egg=kobert_tokenizer&subdirectory=kobert_hf'\n"
                "또는 KOBERT_MODEL=monologg/kobert 로 대안 백본을 사용하세요."
            ) from e
        return KoBERTTokenizer.from_pretrained(backbone)

    # monologg/kobert, KoELECTRA 등 AutoTokenizer 호환 백본
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(backbone, trust_remote_code=True)


def load_model(cfg: TrainConfig):
    """3클래스 분류 헤드가 붙은 시퀀스 분류 모델을 로드한다."""
    from transformers import AutoModelForSequenceClassification

    return AutoModelForSequenceClassification.from_pretrained(
        cfg.backbone,
        num_labels=cfg.num_labels,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        trust_remote_code=True,
    )
