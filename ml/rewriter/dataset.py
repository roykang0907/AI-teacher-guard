"""2단계 순화 LLM 학습 데이터 포맷.

합성데이터(synth.jsonl)의 (original → rewritten) 쌍을 instruction tuning 형식으로
변환한다. Qwen2.5-Instruct chat 템플릿에 맞춰 system/user/assistant 메시지로 구성.

- system: 순화 지침 (감정 제거, 핵심 요구만 공적 표현)
- user:   학부모 원문 민원
- assistant: 순화된 공적 표현 (학습 타깃)
"""

from __future__ import annotations

import json
from pathlib import Path

SYSTEM_PROMPT = (
    "너는 학부모 민원을 교사가 보기 쉽게 다듬는 도우미다. "
    "감정·공격·과장 표현을 제거하고 핵심 요구만 공적이고 정중한 한 문장으로 요약하라. "
    "사실을 지어내지 말고, 요약문만 출력하라."
)


def load_pairs(jsonl_path: str | Path) -> list[dict]:
    """synth.jsonl → [{original, rewritten, category, label}, ...]"""
    rows: list[dict] = []
    with Path(jsonl_path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("original") and r.get("rewritten"):
                rows.append(r)
    return rows


def to_messages(pair: dict) -> list[dict]:
    """한 쌍 → chat 메시지 리스트."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": pair["original"]},
        {"role": "assistant", "content": pair["rewritten"]},
    ]


def build_dataset(jsonl_path: str | Path):
    """HF datasets.Dataset 로 변환 (messages 컬럼). torch/datasets 지연 import."""
    from datasets import Dataset

    pairs = load_pairs(jsonl_path)
    return Dataset.from_list([{"messages": to_messages(p)} for p in pairs])


if __name__ == "__main__":
    # 포맷 검증 (torch/datasets 없이)
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "../data/processed/synth.jsonl"
    pairs = load_pairs(path)
    print(f"쌍 {len(pairs)}건 로드")
    if pairs:
        msgs = to_messages(pairs[0])
        for m in msgs:
            print(f"  [{m['role']}] {m['content'][:70]}")
