"""AI Hub 감성 대화 말뭉치(018) → 1단계 학습용 text,label CSV 변환.

데이터는 사용자 머신에만 있고 git 으로 동기화되지 않으므로(개인정보·대용량 제외),
이 스크립트는 **사용자 머신에서 실행**해 `data/aihub/감성대화/` 하위를
재귀 탐색하여 변환한다.

감성 대화 말뭉치 라벨링데이터 구조(공식):
    [
      {
        "profile": {"emotion": {"type": "E18", "situation": [...]}, ...},
        "talk":    {"content": {"HS01": "사람 발화1", "SS01": "...",
                                 "HS02": "사람 발화2", ...}}
      }, ...
    ]
- text  : 사람(화자) 발화 HS01·HS02·HS03 을 합친 것
- label : profile.emotion.type 코드(E10~E69) → 6대분류 → 3클래스

감정 코드 6대분류(십의 자리)→3클래스:
    E1x 분노 → 위험
    E2x 슬픔 / E3x 불안 / E4x 상처 / E5x 당황 → 주의
    E6x 기쁨 → 정상

사용:
    # 1) 구조·라벨 분포 먼저 점검 (한 줄 결과를 Claude에게 공유)
    python -m classifier.prepare_aihub --inspect
    # 2) 변환 → data/processed/complaints_{train,val}.csv
    python -m classifier.prepare_aihub
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from .labels import LABELS

# 6대분류(십의 자리 코드) → 3클래스
CATEGORY_BY_DECADE: dict[int, str] = {
    1: "분노",
    2: "슬픔",
    3: "불안",
    4: "상처",
    5: "당황",
    6: "기쁨",
}
CATEGORY_TO_CLASS: dict[str, str] = {
    "분노": "위험",
    "슬픔": "주의",
    "불안": "주의",
    "상처": "주의",
    "당황": "주의",
    "기쁨": "정상",
}

DEFAULT_BASE = Path(__file__).resolve().parents[2] / "data" / "aihub" / "감성대화"
DEFAULT_OUT = Path(__file__).resolve().parents[2] / "data" / "processed"


# ----------------------------------------------------------------------------
# 탐색 / 파싱 (구조 변형에 방어적)
# ----------------------------------------------------------------------------
def discover_json_files(base: Path) -> list[Path]:
    return sorted(p for p in base.rglob("*.json") if p.is_file())


def is_validation_path(path: Path) -> bool:
    s = str(path).lower()
    return "valid" in s or "val_" in s or "/val/" in s


def load_items(json_path: Path) -> list[dict]:
    """JSON 을 읽어 대화 item 리스트를 반환. 최상위가 list/dict 모두 처리."""
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "dataset", "documents", "annotations"):
            if isinstance(data.get(key), list):
                return data[key]
        # dict 한 건짜리
        return [data]
    return []


def extract_text(item: dict) -> str:
    """사람(화자) 발화를 합쳐 텍스트로. 키 변형(HS/Human 등)에 방어적."""
    talk = item.get("talk") or item.get("conversation") or {}
    content = talk.get("content") if isinstance(talk, dict) else None
    if not isinstance(content, dict):
        return ""
    human = [
        v
        for k, v in content.items()
        if isinstance(v, str) and v.strip() and k.upper().startswith(("HS", "H", "Q"))
    ]
    return " ".join(s.strip() for s in human)


def extract_emotion_code(item: dict) -> str:
    profile = item.get("profile") or {}
    emotion = profile.get("emotion") if isinstance(profile, dict) else None
    if isinstance(emotion, dict):
        return str(emotion.get("type") or emotion.get("emotion-id") or "").strip()
    # 폴백: 다른 위치
    return str(item.get("emotion") or "").strip()


def emotion_code_to_label(code: str) -> str | None:
    """E18 → 분노 → 위험. 매핑 불가 시 None."""
    digits = "".join(ch for ch in code if ch.isdigit())
    if not digits:
        return None
    decade = int(digits) // 10
    category = CATEGORY_BY_DECADE.get(decade)
    if category is None:
        return None
    return CATEGORY_TO_CLASS.get(category)


# ----------------------------------------------------------------------------
# 변환 / 점검
# ----------------------------------------------------------------------------
def convert(base: Path, out_dir: Path) -> dict:
    files = discover_json_files(base)
    if not files:
        raise SystemExit(f"JSON 을 찾지 못함: {base}  (압축 해제 후 넣었는지 확인)")

    train_rows: list[dict] = []
    val_rows: list[dict] = []
    skipped = 0
    for jp in files:
        bucket = val_rows if is_validation_path(jp) else train_rows
        for item in load_items(jp):
            text = extract_text(item)
            label = emotion_code_to_label(extract_emotion_code(item))
            if not text or label not in LABELS:
                skipped += 1
                continue
            bucket.append({"text": text, "label": label})

    out_dir.mkdir(parents=True, exist_ok=True)
    _write(out_dir / "complaints_train.csv", train_rows)
    _write(out_dir / "complaints_val.csv", val_rows)

    print(f"✅ 변환 완료 (skip={skipped})")
    for name, rows in (("train", train_rows), ("val", val_rows)):
        dist = Counter(r["label"] for r in rows)
        print(f"  {name}: {len(rows)}건  " + " ".join(f"{l}={dist[l]}" for l in LABELS))
    print(f"→ {out_dir/'complaints_train.csv'}")
    return {"train": len(train_rows), "val": len(val_rows), "skipped": skipped}


def _write(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["text", "label"])
        w.writeheader()
        w.writerows(rows)


def inspect(base: Path) -> None:
    """구조·감정코드 분포를 출력해 매핑을 검증한다(데이터 공유용)."""
    files = discover_json_files(base)
    print(f"# 탐색 경로: {base}")
    print(f"# 발견한 JSON: {len(files)}개")
    for f in files[:10]:
        print(f"  - {f.relative_to(base)}")
    if not files:
        return

    sample_items = load_items(files[0])
    print(f"\n# 첫 파일 item 수: {len(sample_items)}")
    if sample_items:
        first = sample_items[0]
        print(f"# 첫 item 최상위 키: {list(first.keys())}")
        print(f"# 추출 text 예시: {extract_text(first)[:80]!r}")
        print(f"# emotion code 예시: {extract_emotion_code(first)!r}")

    code_counter: Counter = Counter()
    label_counter: Counter = Counter()
    for f in files:
        for item in load_items(f):
            code = extract_emotion_code(item)
            code_counter[code[:1] + (code[1:2] if len(code) > 1 else "")] += 1
            lbl = emotion_code_to_label(code)
            label_counter[lbl or "(미매핑)"] += 1
    print("\n# 감정코드 십의자리 분포(상위):", dict(code_counter.most_common(12)))
    print("# 3클래스 매핑 결과:", dict(label_counter))


def main() -> None:
    ap = argparse.ArgumentParser(description="감성대화 말뭉치 → text,label 변환")
    ap.add_argument("--base", default=str(DEFAULT_BASE), help="감성대화 폴더")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="출력 폴더")
    ap.add_argument("--inspect", action="store_true", help="구조/분포만 점검")
    args = ap.parse_args()

    base = Path(args.base)
    if args.inspect:
        inspect(base)
    else:
        convert(base, Path(args.out))


if __name__ == "__main__":
    main()
