"""CSV(text,label) 로딩 · 8:1:1 분할 · 토큰화 Dataset."""

from __future__ import annotations

import csv
from pathlib import Path

from .config import TrainConfig
from .labels import LABEL2ID


def load_rows(csv_path: str | Path) -> list[dict]:
    """text,label CSV 를 읽어 dict 리스트로 반환."""
    rows: list[dict] = []
    with Path(csv_path).open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            text = (r.get("text") or "").strip()
            label = (r.get("label") or "").strip()
            if not text or label not in LABEL2ID:
                continue
            rows.append({"text": text, "label": label, "label_id": LABEL2ID[label]})
    return rows


def stratified_split(rows: list[dict], cfg: TrainConfig):
    """클래스 비율을 유지한 8:1:1 분할."""
    import random
    from collections import defaultdict

    by_label: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_label[r["label"]].append(r)

    rng = random.Random(cfg.seed)
    train, val, test = [], [], []
    for label, items in by_label.items():
        rng.shuffle(items)
        n = len(items)
        n_test = max(1, int(n * cfg.test_ratio))
        n_val = max(1, int(n * cfg.val_ratio))
        test += items[:n_test]
        val += items[n_test : n_test + n_val]
        train += items[n_test + n_val :]
    rng.shuffle(train)
    return train, val, test


class ComplaintDataset:
    """transformers Trainer 호환 torch Dataset.

    torch 미설치 환경에서 import 만으로 죽지 않도록 torch import 를 지연한다.
    """

    def __init__(self, rows: list[dict], tokenizer, max_length: int = 128):
        self.rows = rows
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int):
        import torch

        row = self.rows[idx]
        enc = self.tokenizer(
            row["text"],
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        item = {k: v.squeeze(0) for k, v in enc.items()}
        item["labels"] = torch.tensor(row["label_id"], dtype=torch.long)
        return item
