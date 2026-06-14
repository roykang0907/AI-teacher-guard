# notebooks

## train_classifier_klue_roberta_colab.ipynb
1단계 분류기(klue/roberta-base, 정상/주의/위험) Colab 학습 노트북.
- 레포 없이 self-contained — 감성대화 JSON 2개만 업로드
- 라벨 순서 0정상/1주의/2위험 (백엔드 연동 규약 준수)
- 학습→평가(Macro-F1·혼동행렬·위험 recall)→모델 zip 다운로드
- 결과: `CLASSIFIER_MODEL_DIR=<푼 경로> uvicorn app.main:app --reload` 로 백엔드 연동

> Colab 런타임을 GPU(T4)로 설정 후 위에서부터 실행.
