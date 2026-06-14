import type {
  Complaint,
  ComplaintListItem,
  DraftSuggestion,
  LintResult,
} from "./types";

const API = "/api"; // vite proxy → http://localhost:8000

async function j<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  listComplaints: (params?: { status?: string; label?: string }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return fetch(`${API}/complaints${q ? `?${q}` : ""}`).then(
      j<ComplaintListItem[]>
    );
  },

  getComplaint: (id: number) =>
    fetch(`${API}/complaints/${id}`).then(j<Complaint>),

  ingest: (text: string) =>
    fetch(`${API}/complaints/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    }).then(j<Complaint>),

  suggestDraft: (complaint_id: number) =>
    fetch(`${API}/draft/suggest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ complaint_id }),
    }).then(j<DraftSuggestion>),

  validateDraft: (text: string) =>
    fetch(`${API}/draft/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    }).then(j<LintResult>),
};
