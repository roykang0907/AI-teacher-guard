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

SYSTEM_PROMPT = (  # 순화 작업
    "반드시 한국어로만 작성한다. 너는 학부모 민원을 공적인 표현으로 다듬는다. "
    "학부모가 제기한 문제와 요구를 감정·공격 표현을 빼고 중립적인 한두 문장으로 요약하라. "
    "교사의 답변·약속을 쓰지 말고 학부모가 무엇을 문제삼고 무엇을 원하는지만 적는다. 요약문만 출력하라."
)
DRAFT_SYSTEM = (  # 답변 작업
    "반드시 한국어로만 작성한다. 너는 교사가 학부모에게 보낼 답변 초안을 쓴다. "
    "학부모의 감정과 자녀에게 먼저 공감하고, 사실 확인 전이므로 잘못을 인정하지 말고 확인하겠다는 태도로, "
    "구체적 후속(면담·확인·연락)을 제안하라. 교권·법령 같은 학교 방어 논리를 언급하지 말고, "
    "4~5문장으로 따뜻하고 간결하게 본문만 출력하라."
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


# 작업을 확실히 구분하기 위한 user 메시지 지시문 (학습=추론 동일 유지 필수)
SUNHWA_INSTR = "다음 학부모 민원을 공적인 표현으로 요약해줘.\n민원: "
DAPBYEON_INSTR = "다음 학부모 민원에 대해 교사가 학부모에게 보낼 답변 초안을 작성해줘.\n민원: "


def to_messages(pair: dict) -> list[dict]:
    """원문 → 순화 메시지 리스트."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": SUNHWA_INSTR + pair["original"]},
        {"role": "assistant", "content": pair["rewritten"]},
    ]


def to_reply_messages(pair: dict) -> list[dict]:
    """원문 → 교사 답변 메시지 리스트."""
    return [
        {"role": "system", "content": DRAFT_SYSTEM},
        {"role": "user", "content": DAPBYEON_INSTR + pair["original"]},
        {"role": "assistant", "content": pair["reply"]},
    ]


def build_dataset(jsonl_path: str | Path):
    """HF datasets.Dataset 로 변환. 순화 + 답변 두 작업 모두 포함."""
    from datasets import Dataset

    pairs = load_pairs(jsonl_path)
    rows = []
    for p in pairs:
        rows.append({"messages": to_messages(p)})       # 순화
        if p.get("reply"):
            rows.append({"messages": to_reply_messages(p)})  # 답변
    return Dataset.from_list(rows)


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
