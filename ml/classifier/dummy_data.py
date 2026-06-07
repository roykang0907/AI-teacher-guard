"""더미 학습 데이터 생성기.

AI Hub 감성 대화 말뭉치 승인 대기 동안 **학습→예측 파이프라인 골격을
실제로 돌려보기 위한** 가상 민원 샘플을 생성한다.
실제 학부모 발화가 아닌 자체 작성 가상 시나리오다(절대원칙 7).

승인 후에는 이 생성기 대신 `classifier.prepare_aihub` (추후 작성)로
실데이터를 동일 스키마(text,label)로 변환해 train.py에 투입한다.
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

from .labels import LABELS

# 클래스별 문장 템플릿 (가상 시나리오). {…}는 슬롯.
_SUBJECTS = ["우리 아이", "저희 애", "제 아들", "제 딸", "아이"]
_TOPICS = ["급식", "수업", "체험학습", "생활기록부", "평가", "친구 관계", "안전"]

TEMPLATES: dict[str, list[str]] = {
    "정상": [
        "{topic} 관련해서 안내문을 다시 확인하고 싶어 문의드립니다.",
        "{subject} {topic} 일정이 어떻게 되는지 알려주실 수 있을까요?",
        "선생님 늘 신경 써 주셔서 감사합니다. {topic} 잘 부탁드립니다.",
        "{topic} 준비물 목록을 한 번 더 공유해 주시면 감사하겠습니다.",
        "안녕하세요, {subject} 담임 선생님께 {topic} 관련 간단히 여쭤봅니다.",
    ],
    "주의": [
        "{subject} {topic} 때문에 속상해하는데 어떻게 된 일인지 궁금합니다.",
        "{topic} 처리가 좀 아쉬웠습니다. 다시 살펴봐 주시면 좋겠습니다.",
        "{subject}가 {topic} 이후로 많이 불안해해서 걱정이 됩니다.",
        "이번 {topic} 안내가 늦어 혼란스러웠습니다. 개선 부탁드립니다.",
        "{topic}에 대해 설명이 부족했던 것 같아 불만이 남습니다.",
    ],
    "위험": [
        "{subject} {topic} 관리를 어떻게 하는 겁니까, 당장 책임지세요.",
        "이딴 식으로 {topic} 할 거면 학교를 왜 보냅니까? 가만 안 둡니다.",
        "{subject}가 {topic} 때문에 다쳤는데 당장 고소하겠습니다.",
        "선생이 자격이 있긴 합니까? {topic} 이거 명백한 아동학대 아닙니까.",
        "{topic} 똑바로 못 하면 교육청에 신고하고 변호사 부르겠습니다.",
    ],
}


def generate(n_per_class: int = 60, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    rows: list[dict] = []
    for label in LABELS:
        templates = TEMPLATES[label]
        for _ in range(n_per_class):
            tmpl = rng.choice(templates)
            text = tmpl.format(
                subject=rng.choice(_SUBJECTS),
                topic=rng.choice(_TOPICS),
            )
            rows.append({"text": text, "label": label})
    rng.shuffle(rows)
    return rows


def write_csv(rows: list[dict], out_path: str | Path) -> Path:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(rows)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="더미 민원 학습 데이터 생성")
    parser.add_argument(
        "--out",
        default="../data/samples/complaints_dummy.csv",
        help="출력 CSV 경로",
    )
    parser.add_argument("--n", type=int, default=60, help="클래스당 샘플 수")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rows = generate(n_per_class=args.n, seed=args.seed)
    out = write_csv(rows, args.out)

    # 분포 요약
    from collections import Counter

    dist = Counter(r["label"] for r in rows)
    print(f"✅ {len(rows)}건 생성 → {out}")
    for label in LABELS:
        print(f"  {label}: {dist[label]}")


if __name__ == "__main__":
    main()
