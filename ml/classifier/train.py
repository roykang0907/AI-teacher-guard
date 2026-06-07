"""KoBERT 1단계 분류기 학습 골격.

더미 데이터로 학습→평가→저장까지 도는 파이프라인을 먼저 검증하고,
AI Hub 승인 후 동일 스키마(text,label) 실데이터로 그대로 재실행한다.

사용:
    python -m classifier.train --data ../data/samples/complaints_dummy.csv --dummy
    python -m classifier.train --data ../data/aihub/train.csv --epochs 4

평가 원칙: Macro-F1 + 혼동행렬, ★ 위험→정상 false negative 최소화 최우선.
"""

from __future__ import annotations

import argparse

from .config import TrainConfig
from .dataset import ComplaintDataset, load_rows, stratified_split
from .evaluate import build_compute_metrics, report_danger_recall
from .labels import LABELS
from .model import load_model, load_tokenizer


def pick_device() -> str:
    """CUDA(Colab) > MPS(맥북) > CPU 순으로 선택."""
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class WeightedTrainer:
    """위험 클래스 가중 손실을 위한 Trainer 래퍼 팩토리.

    transformers.Trainer 를 상속하되, import 지연을 위해 함수 내부에서 정의한다.
    """

    @staticmethod
    def build(cfg: TrainConfig):
        import torch
        from transformers import Trainer

        weights = torch.tensor(cfg.class_weights, dtype=torch.float)

        class _Trainer(Trainer):
            def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
                labels = inputs.pop("labels")
                outputs = model(**inputs)
                logits = outputs.logits
                loss_fct = torch.nn.CrossEntropyLoss(
                    weight=weights.to(logits.device)
                )
                loss = loss_fct(logits.view(-1, cfg.num_labels), labels.view(-1))
                return (loss, outputs) if return_outputs else loss

        return _Trainer


def main() -> None:
    parser = argparse.ArgumentParser(description="KoBERT 1단계 분류기 학습")
    parser.add_argument("--data", required=True, help="text,label CSV 경로")
    parser.add_argument("--output", default=None, help="모델 저장 경로")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument(
        "--dummy",
        action="store_true",
        help="더미 데이터 골격 검증 모드(에폭 축소 등 빠른 실행)",
    )
    args = parser.parse_args()

    cfg = TrainConfig()
    if args.output:
        cfg.output_dir = args.output
    if args.epochs:
        cfg.epochs = args.epochs
    if args.batch_size:
        cfg.batch_size = args.batch_size
    if args.lr:
        cfg.lr = args.lr
    if args.dummy:
        cfg.epochs = min(cfg.epochs, 2)  # 골격 검증은 빠르게

    import numpy as np  # noqa: F401  (compute_metrics 의존)
    import torch
    from transformers import TrainingArguments, set_seed

    set_seed(cfg.seed)
    device = pick_device()
    print(f"▶ device={device} | backbone={cfg.backbone} | epochs={cfg.epochs}")

    # 1) 데이터
    rows = load_rows(args.data)
    if not rows:
        raise SystemExit(f"데이터가 비었습니다: {args.data}")
    train_rows, val_rows, test_rows = stratified_split(rows, cfg)
    print(f"  data: train={len(train_rows)} val={len(val_rows)} test={len(test_rows)}")

    # 2) 토크나이저 / 모델
    tokenizer = load_tokenizer(cfg)
    model = load_model(cfg)

    train_ds = ComplaintDataset(train_rows, tokenizer, cfg.max_length)
    val_ds = ComplaintDataset(val_rows, tokenizer, cfg.max_length)
    test_ds = ComplaintDataset(test_rows, tokenizer, cfg.max_length)

    # 3) 학습 설정
    targs = TrainingArguments(
        output_dir=cfg.output_dir,
        num_train_epochs=cfg.epochs,
        per_device_train_batch_size=cfg.batch_size,
        per_device_eval_batch_size=cfg.batch_size,
        learning_rate=cfg.lr,
        weight_decay=cfg.weight_decay,
        warmup_ratio=cfg.warmup_ratio,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        logging_steps=10,
        fp16=cfg.fp16 and device == "cuda",
        report_to=[],
        seed=cfg.seed,
    )

    trainer_cls = (
        WeightedTrainer.build(cfg)
        if cfg.use_class_weights
        else __import__("transformers").Trainer
    )
    trainer = trainer_cls(
        model=model,
        args=targs,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        compute_metrics=build_compute_metrics(),
    )

    # 4) 학습
    trainer.train()

    # 5) 테스트 평가 (혼동행렬 + 위험 recall)
    print("\n=== TEST 평가 ===")
    preds = trainer.predict(test_ds)
    logits = preds.predictions
    y_pred = logits.argmax(axis=-1)
    y_true = [r["label_id"] for r in test_rows]
    report_danger_recall(y_true, y_pred, labels=LABELS)

    # 6) 저장
    trainer.save_model(cfg.output_dir)
    tokenizer.save_pretrained(cfg.output_dir)
    print(f"\n✅ 모델 저장 → {cfg.output_dir}")


if __name__ == "__main__":
    main()
