# frontend — Expo(React Native) 비동기 대시보드 (예정)

`npm run web`(브라우저) + `npm run ios`(네이티브 앱) 동시 지원.

## 스택 (2026-06-07 확정 — Vite 웹에서 Expo로 변경)
- Expo (React Native) + TypeScript + Expo Router
- NativeWind (Tailwind 문법) + gluestack-ui (shadcn/ui 대체)
- Zustand (상태) · React Query (서버 상태)
- 커스텀 `LintEditor` — 답변 실시간 빨간줄 (TextInput + 하이라이트 오버레이, Tiptap 대체)

## 화면 (예정)
- 우선순위 큐 + 카테고리 필터 목록
- 순화 카드 + 원본 토글 + 메타데이터
- LintEditor 답변 코칭 + "AI 제안, 최종 책임은 교사" disclaimer 고정
