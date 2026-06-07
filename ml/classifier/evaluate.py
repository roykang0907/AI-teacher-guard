"""평가 지표 — Macro-F1 + 혼동행렬 + 위험 클래스 recall 집중 점검.

★ 위험을 정상으로 놓치는 false negative 가 이 시스템의 최악 사고다.
   따라서 Macro-F1 외에 '위험 recall'과 '위험→정상 오분류 수'를 별도 출력한다.
"""

from __future__ import annotations

from .labels import DANGER, LABELS, NORMAL


def build_compute_metrics():
    """transformers Trainer 의 compute_metrics 콜백을 생성."""
    import numpy as np
    from sklearn.metrics import f1_score, precision_score, recall_score

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        return {
            "macro_f1": f1_score(labels, preds, average="macro"),
            "macro_precision": precision_score(
                labels, preds, average="macro", zero_division=0
            ),
            "macro_recall": recall_score(
                labels, preds, average="macro", zero_division=0
            ),
            # 위험 클래스 recall 단독 추적 (낮으면 위험 누락이 많다는 뜻)
            "danger_recall": recall_score(
                labels, preds, labels=[DANGER], average="macro", zero_division=0
            ),
        }

    return compute_metrics


def report_danger_recall(y_true, y_pred, labels=LABELS) -> dict:
    """혼동행렬과 위험 클래스 누락을 사람이 읽기 좋게 출력."""
    from sklearn.metrics import classification_report, confusion_matrix

    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(labels))))
    print("혼동행렬 (행=실제, 열=예측):")
    header = "        " + " ".join(f"{l:>5}" for l in labels)
    print(header)
    for i, row in enumerate(cm):
        print(f"  {labels[i]:>4} " + " ".join(f"{v:>5}" for v in row))

    # 위험(실제) → 정상(예측) 으로 놓친 최악 케이스 수
    danger_to_normal = int(cm[DANGER][NORMAL])
    print(f"\n🚨 위험→정상 오분류(최악 FN): {danger_to_normal} 건")

    print("\n분류 리포트:")
    print(
        classification_report(
            y_true, y_pred, target_names=labels, zero_division=0, digits=3
        )
    )
    return {"danger_to_normal": danger_to_normal, "confusion_matrix": cm.tolist()}
