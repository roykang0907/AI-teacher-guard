import { useEffect, useState } from "react";
import { api } from "../api";
import type { Complaint, GuidelineRef, LintResult } from "../types";
import { labelColor, intensityBars } from "../ui";

interface Props {
  complaintId: number;
}

export function ComplaintDetail({ complaintId }: Props) {
  const [c, setC] = useState<Complaint | null>(null);
  const [showOriginal, setShowOriginal] = useState(false);
  const [draft, setDraft] = useState("");
  const [refs, setRefs] = useState<GuidelineRef[]>([]);
  const [lint, setLint] = useState<LintResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setC(null);
    setDraft("");
    setRefs([]);
    setLint(null);
    setShowOriginal(false);
    api.getComplaint(complaintId).then(setC);
  }, [complaintId]);

  if (!c) return <div className="p-6 text-slate-400">불러오는 중…</div>;

  async function getSuggestion() {
    setLoading(true);
    try {
      const s = await api.suggestDraft(complaintId);
      setDraft(s.suggestion);
      setRefs(s.references);
      setLint(null);
    } finally {
      setLoading(false);
    }
  }

  async function checkDraft() {
    if (!draft.trim()) return;
    setLint(await api.validateDraft(draft));
  }

  return (
    <div className="flex h-full flex-col gap-4 p-6">
      {/* 분류 헤더 */}
      <div className="flex items-center gap-2">
        <span
          className={`rounded border px-2 py-0.5 text-sm font-semibold ${labelColor[c.label]}`}
        >
          {c.label}
        </span>
        <span className="text-sm text-slate-500">{c.category}</span>
        <span className="text-sm text-slate-400">
          강도 {intensityBars(c.intensity)}
        </span>
        {c.emergency.is_emergency && (
          <span className="rounded bg-red-600 px-2 py-0.5 text-sm font-bold text-white">
            🚨 {c.emergency.categories.join(", ")}
          </span>
        )}
        {c.overridden && (
          <span className="text-xs text-slate-400">
            (모델 {c.model_label} → 룰 위험 승격)
          </span>
        )}
      </div>

      {/* 순화 카드 (기본) + 원본 토글 */}
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <div className="mb-1 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500">
            {showOriginal ? "원본 민원" : "순화 요약"}
          </span>
          <button
            onClick={() => setShowOriginal((v) => !v)}
            className="text-xs text-blue-600 hover:underline"
          >
            {showOriginal ? "순화본 보기" : "원본 보기"}
          </button>
        </div>
        <p className="whitespace-pre-wrap text-sm text-slate-800">
          {showOriginal ? c.original_text : c.rewritten_text || "(순화 미적용)"}
        </p>
      </div>

      {/* 답변 초안 */}
      <div className="flex flex-1 flex-col rounded-lg border border-slate-200 bg-white p-4">
        <div className="mb-2 flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-500">
            답변 초안
          </span>
          <button
            onClick={getSuggestion}
            disabled={loading}
            className="rounded bg-blue-600 px-2 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "생성 중…" : "AI 제안 받기"}
          </button>
          <button
            onClick={checkDraft}
            className="rounded border border-slate-300 px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50"
          >
            표현 점검
          </button>
        </div>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="‘AI 제안 받기’로 초안을 받아 직접 수정하세요."
          className="flex-1 resize-none rounded border border-slate-200 p-3 text-sm focus:border-blue-400 focus:outline-none"
        />

        {/* RAG 매칭 지침 */}
        {refs.length > 0 && (
          <div className="mt-2 rounded border border-blue-100 bg-blue-50 p-2 text-xs">
            <div className="mb-1 font-semibold text-blue-700">
              📎 관련 지침 (RAG)
            </div>
            <ul className="space-y-1">
              {refs.map((r, i) => (
                <li key={i} className="text-blue-900">
                  <span className="font-medium">[{r.source}]</span> {r.title}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* 표현 점검 결과 (인라인 밑줄 대신 목록) */}
        {lint && (
          <div className="mt-2 text-xs">
            {lint.ok ? (
              <span className="text-green-600">✅ 주의할 표현이 없습니다.</span>
            ) : (
              <ul className="space-y-1">
                {lint.findings.map((f, i) => (
                  <li
                    key={i}
                    className={
                      f.severity === "danger"
                        ? "text-red-600"
                        : "text-amber-700"
                    }
                  >
                    [{f.category}] “{f.matched_text}” — {f.suggestion}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
