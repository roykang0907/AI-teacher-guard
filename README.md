# aiteacherguard

> 학부모 악성 민원으로부터 **교사를 보호**하고, 그 결과 **학생의 학습권을 회복**하는
> **로컬 추론 기반 3단계 AI 시스템** (공모전 출품작).
>
> 핵심 메시지: **"교사를 보호함으로써 학생의 학습권을 회복한다."**

상세 설계·연구 근거는 [`CLAUDE.md`](./CLAUDE.md) 와 [`개발레포_CLAUDE_핸드오프.md`](./개발레포_CLAUDE_핸드오프.md) 참조.

---

## 시스템 3단계

| 단계 | 구성 | 모델 / 기술 | 역할 |
|---|---|---|---|
| **1단계** 분류 | 공격성 판단 엔진 | **KoBERT** (인코더) | 민원을 `정상/주의/위험` 3클래스 분류 + 긴급 키워드 룰 |
| **2단계** 순화 | 감정 순화 필터 + RAG | **Qwen2.5-14B** (디코더, QLoRA) · Ollama | 감정 제거 → 공적 표현 변환 + 법률/지침 RAG |
| **3단계** 답변 | 비동기 대시보드 + 린터 | 2단계 모델 + RAG · Expo(web/ios) | 순화 카드(원본 토글) + 답변 실시간 빨간줄 |

- **모델은 2개.** KoBERT는 인코더라 분류만 가능, 순화는 별도 생성형 디코더 LLM이 담당.
- **로컬 추론만** (외부 API 금지 — 개인정보 보호).

## 모노레포 구조

```
.
├── ml/          # KoBERT 분류기 · 순화 LLM 파인튜닝 · 변환 스크립트
│   └── classifier/   # 1단계 공격성 분류 (KoBERT) ← 첫 코드
├── backend/     # FastAPI · 파이프라인 · pgvector RAG · 린터 룰
├── frontend/    # Expo(React Native) 대시보드 — npm run web / npm run ios
├── data/        # 학습용 CSV (대용량 원본 제외, 샘플/더미만)
│   └── samples/      # 더미·골든셋 등 작은 샘플 (git 추적)
└── docs/        # 설계 메모
```

## 빠른 시작 — 1단계 KoBERT (더미 데이터)

AI Hub 데이터 승인을 기다리는 동안 **더미 데이터로 도는 학습→예측 파이프라인 골격**을 먼저 검증한다.

```bash
cd ml
pip install -r requirements.txt          # 학습 머신(맥북/Colab)에서

# 1) 더미 데이터 생성
python -m classifier.dummy_data --out ../data/samples/complaints_dummy.csv

# 2) 학습 (KoBERT 파인튜닝 골격)
python -m classifier.train --data ../data/samples/complaints_dummy.csv --dummy

# 3) 예측 (분류 + 긴급 룰 오버라이드)
python -m classifier.predict --text "애 관리를 어떻게 하길래 다쳐서 오냐, 당장 고소하겠다"
```

> 룰/라벨/더미 데이터 모듈은 torch 없이도 단독 실행·검증 가능:
> `python -m classifier.emergency_rules` · `python -m classifier.labels`

## 절대 원칙 (발표 방어 논리 = 변경 금지)

1. 순화 뷰 기본 + **원본 항상 열람 가능** (은폐 아님)
2. 긴급 분기 — 안전·법적 사안(학폭·아동학대·자해·고소)은 룰로 즉시 위험 상단
3. **로컬 추론만** (외부 API 금지)
4. 메타데이터(반복성·강도·원어조) 분리 저장
5. "AI 제안, 최종 책임은 교사" disclaimer 고정
6. 학습 데이터에 실제 학부모 발화 없음 (가상 시나리오 자체 작성)
