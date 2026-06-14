# backend — FastAPI 파이프라인 · 린터 · RAG(예정)

학부모 민원을 받아 **1단계 분류 → 2단계 순화 → 3단계 답변 코칭**을 API로 묶는다.
모델 학습/Ollama 없이도 **SQLite + 휴리스틱 분류**로 바로 데모가 돈다.

## 빠른 실행

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# http://localhost:8000/docs (Swagger)
```

> 기본값: SQLite(`backend/aitg.db`) + 휴리스틱 분류 + Ollama 미가동 시 stub.
> 설정은 환경변수(`.env.example` 참고).

## 엔드포인트 (5)
| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/complaints/ingest` | 민원 수신 → 1·2단계 파이프라인 → 저장 |
| GET | `/api/complaints` | 대시보드 목록 (우선순위 정렬, `?status=&label=`) |
| GET | `/api/complaints/{id}` | 순화본 + **원본** + 메타데이터 |
| POST | `/api/draft/suggest` | 답변 초안 제안 (Ollama, RAG는 STEP 3) |
| POST | `/api/draft/validate` | 답변 위험 표현 린터 (빨간줄 근거) |

## 분류 엔진
- `CLASSIFIER_MODEL_DIR` 미설정 → **휴리스틱**(키워드) 폴백 — 모델 학습 전 데모용
- KoBERT 학습 후 그 경로 지정 → 자동으로 KoBERT 사용
- 어느 경우든 **긴급 룰**(학폭·아동학대·자해·고소)은 위험으로 강제 승격

## 풀 구성 (2단계 RAG)
```bash
docker compose up -d            # Postgres + pgvector
export DATABASE_URL=postgresql+psycopg://aitg:aitg@localhost:5432/aitg
export OLLAMA_URL=http://localhost:11434   # ollama pull qwen2.5:14b
uvicorn app.main:app --reload
```

## 구조
```
app/
├── main.py          # FastAPI 진입점 (lifespan→테이블 생성)
├── config.py        # 환경변수 설정
├── db.py            # SQLAlchemy 엔진/세션
├── models.py        # Complaint / Draft
├── schemas.py       # Pydantic
├── nlp/
│   ├── pipeline.py  # 1단계 분류 (긴급룰 + KoBERT/휴리스틱)
│   └── rewrite.py   # 2단계 순화 (Ollama + stub 폴백)
├── linter/          # 답변 코칭 룰 + 린트 실행
└── routers/         # complaints / draft
```
