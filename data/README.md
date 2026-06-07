# data — 학습용 데이터

> `.gitignore` 규칙: 압축 원본(`*.zip` 등)·`data/raw/`·`data/processed/`·`*.xlsx`/`*.parquet` 만 제외.
> **`data/aihub/`(AI Hub 데이터)는 git 추적한다** — Claude가 직접 읽고 변환 스크립트를 맞추기 위함.
> (AI Hub 공개 데이터 + private 레포 전제. 풀어둔 JSON은 추적, 압축 zip은 제외)

## 폴더 규약

```
data/
├── samples/                 ← git 추적 (더미·골든셋 등 작은 샘플)
│   └── complaints_dummy.csv
├── aihub/                   ← git 추적 (압축 푼 파일을 여기에 넣고 push → Claude가 읽음)
│   ├── 감성대화/              ← 1단계 KoBERT (감정→정상/주의/위험)
│   │   ├── Training/
│   │   │   └── 감성대화말뭉치(최종데이터)_Training.json
│   │   └── Validation/
│   │       └── 감성대화말뭉치(최종데이터)_Validation.json
│   └── 공적말하기/            ← 2단계 순화 LLM (공적/격식 문체)
│       ├── Training/
│       └── Validation/
└── processed/               ← git 제외 (prepare_*.py 변환 산출물, text,label CSV)
```

## 넣고 올리는 법
1. AI Hub → **라벨링데이터**만 다운로드(원천데이터 불필요) → 압축 해제.
2. 풀린 파일을 `data/aihub/감성대화/`, `data/aihub/공적말하기/` 아래에 넣기 (하위 구조 달라도 OK).
3. **GitHub Desktop에서 Commit → Push** → Claude가 직접 읽고 `prepare_*.py`를 실제 구조에 맞춰 작성.

## 변환
- `ml/classifier/prepare_aihub.py` → `감성대화` JSON → `data/processed/complaints_{train,val}.csv` (text,label)
- `ml/rewriter/prepare_speech.py` (작성 예정) → `공적말하기` → 순화 학습 포맷
