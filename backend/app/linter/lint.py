"""린트 실행 — 텍스트에서 위험 표현 구간을 찾아 코칭 피드백을 반환.

각 finding 은 (start, end) 문자 오프셋을 포함해 프론트 LintEditor 가 정확히
그 구간에 빨간줄을 긋게 한다.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .rules import all_rules


@dataclass
class LintFinding:
    rule_id: str
    category: str
    severity: str
    start: int
    end: int
    matched_text: str
    message: str
    suggestion: str

    def as_dict(self) -> dict:
        return asdict(self)


def lint_text(text: str) -> list[LintFinding]:
    """텍스트 전체에서 모든 룰의 매칭 구간을 수집(겹침 허용)."""
    findings: list[LintFinding] = []
    if not text:
        return findings
    for rule in all_rules():
        for m in re.finditer(rule.pattern, text):
            findings.append(
                LintFinding(
                    rule_id=rule.id,
                    category=rule.category,
                    severity=rule.severity,
                    start=m.start(),
                    end=m.end(),
                    matched_text=m.group(0),
                    message=rule.message,
                    suggestion=rule.suggestion,
                )
            )
    findings.sort(key=lambda f: (f.start, f.end))
    return findings


def lint_summary(text: str) -> dict:
    """엔드포인트 응답용 요약 + findings."""
    findings = lint_text(text)
    danger = sum(1 for f in findings if f.severity == "danger")
    return {
        "ok": len(findings) == 0,
        "total": len(findings),
        "danger": danger,
        "findings": [f.as_dict() for f in findings],
    }


if __name__ == "__main__":
    samples = [
        "세심히 살피지 못해 죄송합니다. 다시는 이런 일 없도록 하겠습니다.",
        "그건 오해이십니다. 저희도 최선을 다했습니다.",
        "다른 학부모님들은 다 만족하세요. 확인해 보겠습니다.",
        "속상하셨을 텐데 죄송합니다. 내일 오후까지 사실관계를 확인해 연락드리겠습니다.",
    ]
    for s in samples:
        res = lint_summary(s)
        flag = "✅" if res["ok"] else f"⚠️ {res['total']}건(위험 {res['danger']})"
        print(f"\n{flag} | {s}")
        for f in res["findings"]:
            print(f"   [{f['category']}] '{f['matched_text']}' → {f['suggestion']}")
