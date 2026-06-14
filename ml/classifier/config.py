"""1단계 분류기 설정.

확정된 기술 결정(CLAUDE.md): `klue/roberta-base` (표준 AutoTokenizer, 팀원 담당).
환경변수 CLF_MODEL 로 백본 교체 가능(예: skt/kobert-base-v1, KoELECTRA 비교 실험용).
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class TrainConfig:
    # --- 모델 ---
    # 1단계 분류 백본: klue/roberta-base (확정). klue 는 표준 AutoTokenizer 사용.
    backbone: str = os.environ.get("CLF_MODEL") or os.environ.get(
        "KOBERT_MODEL", "klue/roberta-base"
    )
    num_labels: int = 3
    max_length: int = 128

    # --- 학습 하이퍼파라미터 (기준선) ---
    epochs: int = 4
    batch_size: int = 16
    lr: float = 2e-5
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    seed: int = 42

    # --- 분할 (8:1:1) ---
    val_ratio: float = 0.1
    test_ratio: float = 0.1

    # --- 클래스 가중치 ---
    # ★ 위험→정상 false negative 최소화가 최우선.
    # 감성대화 말뭉치는 주의(70%)로 크게 쏠려 있어, 학습 데이터 분포에서
    # 역빈도 가중치를 자동 계산하고 위험 클래스에 추가 부스트를 준다.
    use_class_weights: bool = True
    auto_class_weights: bool = True  # 학습 데이터에서 역빈도 가중치 자동 계산
    danger_boost: float = 1.3        # 위험 클래스 추가 가중(FN 최소화)
    # auto_class_weights=False 일 때 사용할 수동값 (정상, 주의, 위험)
    class_weights: tuple[float, float, float] = (2.6, 0.5, 1.9)

    # --- 경로 ---
    output_dir: str = "outputs/kobert-classifier"

    # --- 디바이스 ---
    # 맥북(MPS)/Colab(CUDA)/CPU 자동 선택은 train.py에서 처리.
    fp16: bool = False  # CUDA에서만 의미. MPS/CPU는 False.
