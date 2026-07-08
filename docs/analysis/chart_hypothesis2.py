# -*- coding: utf-8 -*-
"""
가설2 — 교권침해 심각성 '계층별 인식차이' 막대그래프
Image #1(HTML 인포그래픽)을 Image #3·#4(matplotlib) 스타일로 재현.

스타일 포인트(=#3·#4 느낌):
  - 흰 배경, top/right 스파인 제거, 옅은 가로 그리드
  - 코랄(#E8583C)·블루(#5B8FF0)·그레이(#AEB4BC) 팔레트
  - 막대 위=평균(막대색 글씨), 막대 안=동의(4점↑) 비율(흰 글씨)
  - 점선 기준선 + 프레임 범례(좌상단), 라운드 주석 박스
  - Mac/Windows 어디서든 한글 폰트 자동 탐지

실행:  python docs/analysis/chart_hypothesis2.py
출력:  docs/analysis/04_가설2_계층별_인식차이.png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D


# ---------------------------------------------------------------- 한글 폰트
def set_korean_font():
    candidates = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",              # macOS
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",      # macOS
        "/Library/Fonts/NanumGothic.ttf",
        "C:/Windows/Fonts/malgun.ttf",                             # Windows
        "C:/Windows/Fonts/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",         # Linux
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                fm.fontManager.addfont(p)
                name = fm.FontProperties(fname=p).get_name()
                plt.rcParams["font.family"] = name
                return name
            except Exception:
                pass
    installed = {f.name for f in fm.fontManager.ttflist}
    for n in ["Apple SD Gothic Neo", "AppleGothic", "Malgun Gothic",
              "NanumGothic", "NanumSquare"]:
        if n in installed:
            plt.rcParams["font.family"] = n
            return n
    return None


set_korean_font()
plt.rcParams["axes.unicode_minus"] = False

# ---------------------------------------------------------------- 데이터
CORAL, BLUE, GRAY = "#E8583C", "#5B8FF0", "#AEB4BC"
COLORS = {"교사": CORAL, "학부모": BLUE, "학생": GRAY}
INK, MUTE, LINE = "#2E2E2E", "#6b6b6b", "#9aa0a6"

# (그룹, 평균, 동의비율%)
QUESTIONS = [
    {"label": 'Q12\n"소수의 과도한 민원이\n교사 전체에 부담"',
     "bars": [("교사", 4.66, 96.9), ("학부모", 4.15, 81.9)]},
    {"label": 'Q13\n"우리나라 교권침해\n문제가 심각한 수준"',
     "bars": [("교사", 4.66, 100.0), ("학부모", 3.97, 72.2)]},
    {"label": 'Q15\n"법적 환경이 교사의\n교육활동을 위축"',
     "bars": [("교사", 4.75, 96.9), ("학부모", 4.03, 73.6), ("학생", 3.93, 68.9)]},
]

# ---------------------------------------------------------------- 플롯
fig, ax = plt.subplots(figsize=(10, 6.4))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

W = 0.24
GX = [0.0, 1.15, 2.30]          # 그룹 중심 x

for gc, q in zip(GX, QUESTIONS):
    n = len(q["bars"])
    for i, (grp, mean, agree) in enumerate(q["bars"]):
        x = gc + (i - (n - 1) / 2) * W
        c = COLORS[grp]
        ax.bar(x, mean, width=W, color=c, zorder=3,
               edgecolor="white", linewidth=0.6)
        # 막대 위 = 평균
        ax.text(x, mean + 0.07, f"{mean:.2f}", ha="center", va="bottom",
                fontsize=12, fontweight="bold", color=c, zorder=4)
        # 막대 안 = 동의 비율
        ax.text(x, mean - 0.30, f"동의\n{agree:.1f}%", ha="center", va="top",
                fontsize=9, fontweight="bold", color="white", zorder=4,
                linespacing=1.05)

# 동의 기준선(4점)
ax.axhline(4, color=LINE, ls="--", lw=1.3, zorder=1)

# 계층 차이 최대 주석 (우상단 고정 — 막대와 겹치지 않게)
ax.text(0.985, 0.965, "Q15 계층 차이 최대\n교사 4.75  ›  학생 3.93",
        transform=ax.transAxes, ha="right", va="top",
        fontsize=9.5, color=CORAL, fontweight="bold", linespacing=1.25,
        bbox=dict(boxstyle="round,pad=0.45", fc="white", ec=CORAL, lw=1.3))

# ---- 축/그리드/스파인 (#3·#4 느낌) ----
ax.set_ylim(0, 5.8)
ax.set_yticks([0, 1, 2, 3, 4, 5])
ax.set_ylabel("5점 척도 평균 (동의도)", fontsize=12, color=INK)
ax.set_xticks(GX)
ax.set_xticklabels([q["label"] for q in QUESTIONS], fontsize=10.5, color=INK)
ax.tick_params(colors="#555555", length=0)
ax.grid(axis="y", color="#e8e8e8", lw=0.9)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color("#cccccc")

# ---- 범례 (프레임, 좌상단) ----
handles = [Patch(facecolor=COLORS[g], label=g) for g in ("교사", "학부모", "학생")]
handles.append(Line2D([0], [0], color=LINE, ls="--", lw=1.3, label="동의 기준 (4점)"))
leg = ax.legend(handles=handles, loc="upper left", fontsize=10,
                frameon=True, framealpha=1.0, edgecolor="#d9d9d9",
                borderpad=0.7, labelspacing=0.5)
leg.get_frame().set_linewidth(0.9)

# ---- 제목(2줄) ----
ax.set_title("교권침해 심각성 인식 — 교사·학부모·학생, 얼마나 다르게 느끼나?",
             fontsize=15, fontweight="bold", color=INK, pad=34)
ax.text(0.5, 1.055,
        "5점 척도 평균  ·  막대 위 = 평균, 막대 안 = 동의(4점↑) 비율  ·  3계층 n=149",
        transform=ax.transAxes, ha="center", va="bottom",
        fontsize=10.5, color=MUTE)

# ---- 하단 결론 캡션 ----
fig.text(0.5, 0.005,
         "가설 2 채택 — 교사(4.66~4.75) > 학부모(3.97~4.15) > 학생(3.93): "
         "계층별 인식 차이가 뚜렷",
         ha="center", fontsize=9, color="#888888")

plt.tight_layout(rect=[0, 0.03, 1, 1])

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPATH = os.path.join(HERE, "04_가설2_계층별_인식차이.png")
fig.savefig(OUTPATH, dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("saved", OUTPATH)
