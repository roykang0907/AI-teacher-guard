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

## rewriter/ — 2단계 순화 LLM (Qwen2.5-14B QLoRA → GGUF → Ollama)

| 파일 | 역할 |
|---|---|
| `synth_data.py` | 합성 민원(원문↔공적표현) 1000건 생성 |
| `dataset.py` | 순화 쌍 → chat instruction 포맷 |
| `train_qlora.py` | Qwen2.5-14B QLoRA(r=16, α=32, 4-bit) 학습 |
| `merge_lora.py` | LoRA 어댑터 병합 |
| `export_ollama.sh` + `Modelfile` | 병합→GGUF(Q6_K)→`ollama create` |

```bash
pip install -r rewriter/requirements.txt
python -m rewriter.synth_data --n 1000                       # 데이터
python -m rewriter.train_qlora --data ../data/processed/synth.jsonl   # 학습(GPU)
BASE=Qwen/Qwen2.5-14B-Instruct ./rewriter/export_ollama.sh   # → Ollama 등록
# 백엔드: OLLAMA_MODEL=aitg-sunhwa uvicorn app.main:app --reload
```

> ⚠️ QLoRA 4-bit(bitsandbytes)는 CUDA 전용 → 학습은 Colab/A100 권장.
> Apple Silicon은 추론(Ollama)만 담당. (역할 분담: 학습 실행=사용자)
