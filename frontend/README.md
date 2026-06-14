# frontend — Vite + React + TS 비동기 대시보드

교사용 민원 대시보드. 백엔드(FastAPI, `localhost:8000`)의 5개 엔드포인트에 연결된다.

## 실행

```bash
# 1) 백엔드 먼저 (다른 터미널)
cd ../backend && uvicorn app.main:app --reload

# 2) 프론트
cd frontend
npm install
npm run dev          # http://localhost:5173
```

> `/api` 요청은 vite 프록시로 백엔드(8000)에 전달된다(`vite.config.ts`).

## 기능 (STEP 5)
- **우선순위 큐** — 긴급/위험/강도순 정렬 목록 (좌측)
- **순화 카드 + 원본 토글** — 기본은 순화 요약, 클릭 시 원본 열람(은폐 아님)
- **메타데이터** — 라벨·카테고리·강도·긴급 사유 표시
- **AI 제안 답변 + 편집** — ‘AI 제안 받기’ → textarea 에서 교사가 수정
- **표현 점검** — 답변의 위험 표현을 목록으로 안내(인라인 빨간줄 대신)
- **disclaimer 고정** — "AI 제안, 최종 책임은 교사"

## 스택 노트
- 상태는 현재 로컬 `useState`로 단순 구현. 규모가 커지면 React Query(서버 상태)·Zustand(클라 상태) 도입.
- 실시간 빨간줄 에디터(Tiptap)는 요구 변경으로 제외 — 제안 답변 편집 방식.
- 앱이 필요하면 이 웹 코드를 Capacitor로 래핑 가능.

## 구조
```
src/
├── main.tsx                  # 진입점
├── App.tsx                   # 레이아웃 + 우선순위 큐 + 민원 추가
├── api.ts                    # 백엔드 호출
├── types.ts                  # 백엔드 schemas 대응 타입
├── ui.ts                     # 라벨 색상/강도 헬퍼
└── components/
    ├── ComplaintList.tsx     # 우선순위 큐 목록
    └── ComplaintDetail.tsx   # 순화/원본 + 답변 제안·편집·점검
```
