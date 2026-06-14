import { useEffect, useState } from "react";
import { api } from "./api";
import type { ComplaintListItem } from "./types";
import { ComplaintList } from "./components/ComplaintList";
import { ComplaintDetail } from "./components/ComplaintDetail";

const DISCLAIMER =
  "본 제안은 AI가 생성한 참고용이며, 최종 판단과 책임은 교사에게 있습니다.";

export default function App() {
  const [items, setItems] = useState<ComplaintListItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      const list = await api.listComplaints();
      setItems(list);
      setError(null);
      if (selectedId === null && list.length) setSelectedId(list[0].id);
    } catch (e) {
      setError("백엔드(localhost:8000)에 연결할 수 없습니다. uvicorn 실행을 확인하세요.");
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function addComplaint() {
    if (!text.trim()) return;
    setBusy(true);
    try {
      const c = await api.ingest(text.trim());
      setText("");
      await refresh();
      setSelectedId(c.id);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* 헤더 */}
      <header className="flex items-center gap-3 border-b border-slate-200 bg-white px-5 py-3">
        <h1 className="text-lg font-bold">aiteacherguard</h1>
        <span className="text-xs text-slate-400">교사 민원 대시보드</span>
        <div className="ml-auto flex gap-2">
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addComplaint()}
            placeholder="민원 원문을 붙여넣고 Enter…"
            className="w-96 rounded border border-slate-300 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none"
          />
          <button
            onClick={addComplaint}
            disabled={busy}
            className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {busy ? "분석 중…" : "민원 추가"}
          </button>
        </div>
      </header>

      {error && (
        <div className="bg-red-50 px-5 py-2 text-sm text-red-700">{error}</div>
      )}

      {/* 본문: 좌(우선순위 큐) / 우(상세) */}
      <main className="flex flex-1 overflow-hidden">
        <aside className="w-80 shrink-0 overflow-y-auto border-r border-slate-200 bg-white">
          <div className="border-b border-slate-100 px-4 py-2 text-xs font-semibold text-slate-500">
            우선순위 큐 ({items.length})
          </div>
          <ComplaintList
            items={items}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </aside>
        <section className="flex-1 overflow-y-auto">
          {selectedId !== null ? (
            <ComplaintDetail complaintId={selectedId} />
          ) : (
            <div className="p-8 text-slate-400">민원을 선택하세요.</div>
          )}
        </section>
      </main>

      {/* disclaimer 고정 */}
      <footer className="border-t border-slate-200 bg-slate-50 px-5 py-2 text-center text-xs text-slate-500">
        {DISCLAIMER}
      </footer>
    </div>
  );
}
