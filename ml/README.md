# ml — 모델 학습 / 변환

## classifier/ — 1단계 공격성 분류 (KoBERT) ⭐ 첫 코드

민원 텍스트를 `정상 / 주의 / 위험` 3클래스로 분류한다.

| 파일 | 역할 |
|---|---|
| `labels.py` | 3클래스 정의 + 감성 대화 말뭉치 감정→3클래스 매핑 |
| `emergency_rules.py` | 긴급 키워드 룰 사전(학폭·아동학대·자해·고소) — 위험 강제 승격 |
| `dummy_data.py` | 더미 학습 데이터(가상 시나리오) 생성 |
| `dataset.py` | CSV 로딩 · 8:1:1 층화분할 · 토큰화 Dataset |
| `model.py` | KoBERT 토크나이저/모델 로더 |
| `config.py` | 하이퍼파라미터 · 클래스 가중치(위험 강조) |
| `train.py` | 학습→평가(Macro-F1/혼동행렬)→저장 골격 |
| `evaluate.py` | 지표 + **위험→정상 false negative** 집중 점검 |
| `predict.py` | 추론 + 긴급 룰 오버라이드 + 메타데이터 분리 |

### 토크나이저 없이도 검증 가능 (torch 불필요)

```bash
python -m classifier.labels            # 감정→3클래스 매핑 확인
python -m classifier.emergency_rules   # 긴급 룰 탐지 확인
python -m classifier.dummy_data --out ../data/samples/complaints_dummy.csv
```

### 전체 파이프라인 (torch/transformers 설치 후, 학습 머신)

```bash
pip install -r requirements.txt
# KoBERT 토크나이저:
pip install 'git+https://github.com/SKTBrain/KoBERT.git#egg=kobert_tokenizer&subdirectory=kobert_hf'

python -m classifier.train --data ../data/samples/complaints_dummy.csv --dummy
python -m classifier.predict --model outputs/kobert-classifier \
    --text "애 관리를 어떻게 하길래 다쳐서 오냐, 당장 고소하겠다"
```

승인 후 AI Hub 감성 대화 말뭉치를 `text,label` 스키마로 변환해 `--data` 에 투입하면
같은 코드로 실데이터 파인튜닝이 된다.

## (예정)
- `rewriter/` — 2단계 순화 LLM (Qwen2.5-14B QLoRA → GGUF → Ollama)
- `prepare_aihub.py` — AI Hub 원본 → text,label 변환
