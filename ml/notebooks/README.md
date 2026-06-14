# notebooks

## train_classifier_klue_roberta_colab.ipynb
1단계 분류기(klue/roberta-base, 정상/주의/위험) Colab 학습 노트북.
- 레포 없이 self-contained — 감성대화 JSON 2개만 업로드
- 라벨 순서 0정상/1주의/2위험 (백엔드 연동 규약 준수)
- 학습→평가(Macro-F1·혼동행렬·위험 recall)→모델 zip 다운로드
- 결과: `CLASSIFIER_MODEL_DIR=<푼 경로> uvicorn app.main:app --reload` 로 백엔드 연동

> Colab 런타임을 GPU(T4)로 설정 후 위에서부터 실행.

## train_rewriter_qlora_colab.ipynb
2단계 순화·답변 LLM(Qwen2.5-7B) QLoRA 파인튜닝 (Unsloth).
- 입력: `synth.jsonl` (원문→순화 + 원문→답변 쌍)
- 두 작업 동시 학습 → GGUF(q4_k_m) export → 맥에서 `ollama create aitg-sunhwa`
- 백엔드 연결: `OLLAMA_MODEL=aitg-sunhwa uvicorn app.main:app --reload`
- 런타임 GPU(T4) 필요. 14B는 A100(Colab Pro).
