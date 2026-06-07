# data — 학습용 데이터 (대용량 원본은 git 제외)

> `.gitignore` 규칙: `data/aihub/`, `data/raw/`, `*.xlsx`, `*.parquet`, `*.zip` 은 추적 제외.
> 작은 샘플(`data/samples/`)만 git 추적한다.

## 폴더 규약

```
data/
├── samples/                 ← git 추적 (더미·골든셋 등 작은 샘플)
│   └── complaints_dummy.csv
├── aihub/                   ← git 제외 (AI Hub 원본 보관)
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

## 받는 방법
- AI Hub → 해당 데이터셋 → **라벨링데이터**만 받으면 됨(원천데이터 불필요).
- INNORIX Agent로 다운로드 → 압축 해제 → 위 경로에 배치.

## 변환
- `ml/classifier/prepare_aihub.py` (작성 예정) → `감성대화` JSON → `data/processed/complaints.csv` (text,label)
- `ml/rewriter/prepare_speech.py` (작성 예정) → `공적말하기` → 순화 학습 포맷
