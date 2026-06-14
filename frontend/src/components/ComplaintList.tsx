import type { ComplaintListItem } from "../types";
import { labelColor, labelDot } from "../ui";

interface Props {
  items: ComplaintListItem[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  onDelete: (id: number) => void;
}

export function ComplaintList({ items, selectedId, onSelect, onDelete }: Props) {
  if (items.length === 0) {
    return (
      <div className="p-6 text-sm text-slate-400">
        민원이 없습니다. 위에서 민원을 추가해 보세요.
      </div>
    );
  }
  return (
    <ul className="divide-y divide-slate-100">
      {items.map((c) => (
        <li
          key={c.id}
          onClick={() => onSelect(c.id)}
          className={`cursor-pointer px-4 py-3 hover:bg-slate-50 ${
            selectedId === c.id ? "bg-slate-100" : ""
          }`}
        >
          <div className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${labelDot[c.label]}`} />
            <span
              className={`rounded border px-1.5 py-0.5 text-xs font-medium ${labelColor[c.label]}`}
            >
              {c.label}
            </span>
            {c.emergency.is_emergency && (
              <span className="rounded bg-red-600 px-1.5 py-0.5 text-xs font-bold text-white">
                🚨 긴급
              </span>
            )}
            <span className="ml-auto text-xs text-slate-400">
              우선 {c.priority}
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(c.id);
              }}
              title="삭제"
              className="text-slate-300 hover:text-red-600"
            >
              ✕
            </button>
          </div>
          <p className="mt-1 line-clamp-2 text-sm text-slate-600">
            {c.rewritten_text || "(순화 미적용)"}
          </p>
          <div className="mt-1 text-xs text-slate-400">
            {c.category} · 강도 {c.intensity}
          </div>
        </li>
      ))}
    </ul>
  );
}
