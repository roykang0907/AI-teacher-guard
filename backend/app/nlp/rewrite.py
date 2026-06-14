"""2단계 순화 — 로컬 Ollama 호출 (외부 API 금지, 절대원칙 3).

Ollama 미가동/미설치 시 graceful stub 으로 폴백해 데모가 끊기지 않게 한다.
실제 순화 품질은 Qwen2.5-14B QLoRA 파인튜닝(STEP 3) 후 향상된다.
"""

from __future__ import annotations

from ..config import settings

_REWRITE_SYSTEM = (
    "너는 학부모 민원을 교사가 보기 쉽게 다듬는 도우미다. "
    "감정·공격·과장 표현을 제거하고 핵심 요구만 공적이고 정중한 한 문장으로 요약하라. "
    "사실을 지어내지 말고, 요약문만 출력하라."
)

_DRAFT_SYSTEM = (
    "너는 교사의 학부모 답변 초안을 돕는 도우미다. "
    "공감 → 사실관계 확인 절차 → 후속 조치 약속 순으로 정중하게 작성하라. "
    "과실을 단정하지 말고, 확인 중임을 밝혀라. 답변 본문만 출력하라."
)


def _ollama_generate(prompt: str, system: str) -> str | None:
    """Ollama /api/generate 호출. 실패 시 None."""
    try:
        import httpx

        resp = httpx.post(
            f"{settings.ollama_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "system": system,
                "prompt": prompt,
                "stream": False,
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        return (resp.json().get("response") or "").strip()
    except Exception:
        return None


def rewrite_complaint(text: str) -> tuple[str, str]:
    """민원 순화. 반환 (순화문, engine)."""
    out = _ollama_generate(text, _REWRITE_SYSTEM)
    if out:
        return out, "ollama"
    # 폴백: 원문 보존 + 안내 (은폐 아님 — 원본 항상 열람 가능)
    return ("[자동 순화 미적용 — Ollama 미가동] 원문을 확인하세요.", "stub")


def draft_reply(complaint_text: str, rewritten: str | None = None) -> tuple[str, str]:
    """답변 초안 생성. 반환 (초안, engine)."""
    base = rewritten or complaint_text
    out = _ollama_generate(f"민원 요지: {base}\n위 민원에 대한 교사 답변 초안을 작성하라.", _DRAFT_SYSTEM)
    if out:
        return out, "ollama"
    return (
        "안녕하세요, 학부모님. 말씀 주신 내용 잘 확인했습니다. "
        "먼저 걱정 끼쳐 드린 점 유감스럽게 생각합니다. "
        "현재 사실관계를 확인하고 있으며, 확인되는 대로 다시 연락드리겠습니다.",
        "stub",
    )
