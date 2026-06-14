// 백엔드 schemas.py 와 1:1 대응

export type Label = "정상" | "주의" | "위험";

export interface Emergency {
  is_emergency: boolean;
  categories: string[];
  keywords: string[];
}

export interface ComplaintListItem {
  id: number;
  created_at: string;
  label: Label;
  category: string | null;
  intensity: number;
  priority: number;
  status: string;
  emergency: Emergency;
  rewritten_text: string | null;
}

export interface Complaint extends ComplaintListItem {
  original_text: string;
  score: number;
  model_label: string | null;
  overridden: boolean;
}

export interface LintFinding {
  rule_id: string;
  category: string;
  severity: "warn" | "danger";
  start: number;
  end: number;
  matched_text: string;
  message: string;
  suggestion: string;
}

export interface LintResult {
  ok: boolean;
  total: number;
  danger: number;
  findings: LintFinding[];
  disclaimer: string;
}

export interface GuidelineRef {
  source: string;
  title: string;
  text: string;
}

export interface DraftSuggestion {
  complaint_id: number;
  suggestion: string;
  engine: string;
  references: GuidelineRef[];
  disclaimer: string;
}
