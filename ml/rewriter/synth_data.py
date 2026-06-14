"""합성 민원 데이터 생성기 (가상 시나리오).

감성대화 말뭉치가 비워둔 '학부모 민원' 도메인을 메운다. 출력은 두 용도에 쓰인다.
- 1단계 분류 보강: (original, label) — 실제 민원체 정상/주의/위험
- 2단계 순화 학습:  (original → rewritten) — 공격/감정 표현 → 공적 표현 쌍

각 레코드 메타데이터(강도·긴급·카테고리)도 분리 보존(절대원칙 4).
긴급 플래그는 classifier.emergency_rules 로 자동 태깅해 모듈 일관성을 유지한다.

사용:
    python -m rewriter.synth_data --n 1000 --out ../data/processed/synth.jsonl
    python -m rewriter.synth_data --n 30 --sample   # 레포 커밋용 작은 샘플
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import Counter
from pathlib import Path

from classifier.emergency_rules import detect_emergency
from classifier.labels import LABELS

from .scenarios import CHILD, CLOSER, PREFIX, TEMPLATES

DEFAULT_OUT = Path(__file__).resolve().parents[2] / "data" / "processed" / "synth.jsonl"
SAMPLE_OUT = Path(__file__).resolve().parents[2] / "data" / "samples" / "synth_complaints_sample.csv"


# --- 한국어 조사 자동 처리 ----------------------------------------------------
def _has_batchim(ch: str) -> bool:
    """한글 음절의 받침 유무. 받침 'ㄹ'은 별도 처리 위해 종성 index 도 반환 가능."""
    code = ord(ch)
    if 0xAC00 <= code <= 0xD7A3:
        return (code - 0xAC00) % 28 != 0
    return False


def _is_rieul(ch: str) -> bool:
    code = ord(ch)
    if 0xAC00 <= code <= 0xD7A3:
        return (code - 0xAC00) % 28 == 8  # 종성 ㄹ
    return False


def apply_josa(text: str) -> str:
    """슬롯 뒤 조사 마커([이/가] 등)를 앞 글자 받침에 맞게 치환."""

    def repl_pair(a_batchim: str, b_none: str):
        def _f(m: re.Match) -> str:
            prev = m.group(1)
            return prev + (a_batchim if _has_batchim(prev) else b_none)

        return _f

    text = re.sub(r"(.)\[이/가\]", repl_pair("이", "가"), text)
    text = re.sub(r"(.)\[을/를\]", repl_pair("을", "를"), text)
    text = re.sub(r"(.)\[은/는\]", repl_pair("은", "는"), text)
    text = re.sub(r"(.)\[와/과\]", repl_pair("과", "와"), text)

    def _ro(m: re.Match) -> str:
        prev = m.group(1)
        # 받침 없거나 ㄹ → '로', 그 외 받침 → '으로'
        return prev + ("로" if (not _has_batchim(prev) or _is_rieul(prev)) else "으로")

    text = re.sub(r"(.)\[으로/로\]", _ro, text)
    return text


def _fill(text: str, child: str, topic: str) -> str:
    return apply_josa(text.format(child=child, topic=topic))


def _compose_original(core: str, label: str, is_question: bool, rng: random.Random) -> str:
    """핵심 원문에 라벨별 접두/접미 감정표현을 붙여 원문 다양성·감정강도를 만든다."""
    prefix = rng.choice(PREFIX[label])
    closer = rng.choice(CLOSER[label])
    end = "?" if is_question else "."
    return f"{prefix}{core}{end} {closer}".strip()



def generate(n: int, seed: int = 42) -> list[dict]:
    """원문/순화문 쌍 + 메타데이터 레코드를 n건 생성(원문 기준 중복 제거)."""
    rng = random.Random(seed)
    records: list[dict] = []
    seen: set[str] = set()

    # 균형 잡힌 추출을 위해 템플릿을 순환하며 슬롯 변형
    attempts = 0
    while len(records) < n and attempts < n * 50:
        attempts += 1
        tmpl = rng.choice(TEMPLATES)
        topic = rng.choice(tmpl["topics"])
        child = rng.choice(CHILD)  # 한 레코드 안에서 원문·순화문 동일 호칭 유지
        core = _fill(tmpl["orig_core"], child, topic)
        original = _compose_original(core, tmpl["label"], tmpl.get("q", True), rng)
        if original in seen:
            continue
        seen.add(original)
        rewritten = _fill(tmpl["rewr"], child, topic)
        # 답변은 교사 화자이므로 학생을 '자녀분'으로 칭한다(학부모 말투 '제 아들' 방지)
        reply = _fill(tmpl["reply"], "자녀분", topic)
        emg = detect_emergency(original)
        records.append(
            {
                "original": original,
                "rewritten": rewritten,
                "reply": reply,
                "label": tmpl["label"],
                "category": tmpl["category"],
                "intensity": tmpl["intensity"],
                "emergency": emg.is_emergency,
                "emergency_categories": emg.categories,
            }
        )
    rng.shuffle(records)
    return records


def write_jsonl(records: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_classification_csv(records: list[dict], out: Path) -> None:
    """1단계 학습용 (text=original, label) CSV."""
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["text", "label"])
        w.writeheader()
        for r in records:
            w.writerow({"text": r["original"], "label": r["label"]})


def write_sample_csv(records: list[dict], out: Path) -> None:
    """레포 커밋용 사람이 읽기 좋은 샘플 CSV(전체 필드)."""
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["category", "label", "intensity", "emergency", "original", "rewritten"]
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)


def summarize(records: list[dict]) -> None:
    by_label = Counter(r["label"] for r in records)
    by_cat = Counter(r["category"] for r in records)
    emg = sum(1 for r in records if r["emergency"])
    print(f"✅ {len(records)}건 생성")
    print("  라벨:  " + " ".join(f"{l}={by_label[l]}" for l in LABELS))
    print("  카테고리: " + ", ".join(f"{k}={v}" for k, v in by_cat.most_common()))
    print(f"  긴급 태깅: {emg}건")


def main() -> None:
    ap = argparse.ArgumentParser(description="합성 민원 데이터 생성")
    ap.add_argument("--n", type=int, default=1000, help="생성 건수 목표")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="JSONL 출력 경로")
    ap.add_argument(
        "--sample",
        action="store_true",
        help="레포 커밋용 작은 샘플 CSV(data/samples)만 생성",
    )
    args = ap.parse_args()

    records = generate(args.n, args.seed)
    summarize(records)

    if args.sample:
        write_sample_csv(records, SAMPLE_OUT)
        print(f"→ 샘플 CSV: {SAMPLE_OUT}")
        return

    out = Path(args.out)
    write_jsonl(records, out)
    csv_out = out.with_name("synth_classification.csv")
    write_classification_csv(records, csv_out)
    print(f"→ JSONL(순화쌍+메타): {out}")
    print(f"→ CSV(1단계 분류용): {csv_out}")


if __name__ == "__main__":
    main()
