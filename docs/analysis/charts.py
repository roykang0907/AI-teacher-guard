# -*- coding: utf-8 -*-
import csv, statistics as st, os
from collections import Counter, defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# --- Korean font ---
FP = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
fm.fontManager.addfont(FP)
plt.rcParams["font.family"] = fm.FontProperties(fname=FP).get_name()
plt.rcParams["axes.unicode_minus"] = False

PATH = "/Users/roy/Documents/GitHub/AI-teacher-guard/민원과 교육활동 위축에 관한 계층별 인식 조사.csv"
OUT = "/Users/roy/Documents/GitHub/AI-teacher-guard/docs/analysis"
os.makedirs(OUT, exist_ok=True)

CIRCLED = {'①':1,'②':2,'③':3,'④':4,'⑤':5,'⑥':6,'⑦':7}
def num(cell):
    if not cell: return None
    return CIRCLED.get(cell.strip()[:1])

rows=[]
with open(PATH, encoding="utf-8") as f:
    rd=csv.reader(f); next(rd)
    for row in rd:
        if len(row)>=31 and row[1].strip(): rows.append(row)

def grp(r):
    g=r[1]
    return '교사' if '교사' in g else '학부모' if '학부모' in g else '학생' if '학생' in g else '기타'
by=defaultdict(list)
for r in rows: by[grp(r)].append(r)

C=dict(t_q3=3,t_q4=4,p_q5=14,p_q7=16,s_q5=21,q11=23,q12=24,q13=25,q14=26,q15=27,q17=29)
def mean_of(rl,c):
    v=[num(r[c]) for r in rl]; v=[x for x in v if x is not None]
    return (st.mean(v),len(v),v) if v else (None,0,[])
def agree(vals): return 100*sum(1 for x in vals if x>=4)/len(vals) if vals else 0

TEAL="#2a9d8f"; ORANGE="#e76f51"; BLUE="#264653"; YEL="#e9c46a"; GRAY="#8d99ae"
GC={'교사':BLUE,'학부모':ORANGE,'학생':TEAL}

def barlabels(ax, bars, fmt="{:.2f}", off=0.03):
    for b in bars:
        h=b.get_height()
        ax.text(b.get_x()+b.get_width()/2, h+off, fmt.format(h),
                ha="center", va="bottom", fontsize=10, fontweight="bold")

# ===================================================================
# FIG 1 — 종합 대시보드 (2x3)
# ===================================================================
fig, ax = plt.subplots(2,3, figsize=(18,11))
fig.suptitle("민원과 교육활동 위축에 관한 계층별 인식 조사  (N=%d: 교사 %d·학부모 %d·학생 %d)"
             % (len(rows),len(by['교사']),len(by['학부모']),len(by['학생'])),
             fontsize=17, fontweight="bold", y=0.98)

# (1) 핵심: 과도민원=문제 계층별
a=ax[0,0]
groups=['교사','학부모','학생']; keys=['q12','p_q7','s_q5']
means=[]; agr=[]
for g,k in zip(groups,keys):
    m,n,v=mean_of(by[g],C[k]); means.append(m); agr.append(agree(v))
bars=a.bar(groups,means,color=[GC[g] for g in groups])
barlabels(a,bars)
for i,(g,p) in enumerate(zip(groups,agr)):
    a.text(i,0.25,f"동의 {p:.0f}%",ha="center",color="white",fontsize=11,fontweight="bold")
a.set_ylim(0,5.3); a.axhline(3,color="gray",ls="--",lw=.8)
a.set_ylabel("평균 (1~5점)"); a.set_title("① ★ '과도한 민원이 교사를 위축시킨다'\n계층 모두 동의 (교사 Q12·학부모 Q7·학생 Q5)",fontsize=12,fontweight="bold")

# (2) 학부모 두 얼굴
a=ax[0,1]
lab=["Q11\n대부분 민원은\n정당한 관심","Q12\n일부 과도민원이\n교사에 부담","Q7\n과도민원이\n교사 위축"]
mv=[mean_of(by['학부모'],C[k])[0] for k in ['q11','q12','p_q7']]
cols=[GRAY,ORANGE,ORANGE]
bars=a.bar(lab,mv,color=cols)
barlabels(a,bars)
a.set_ylim(0,5.3); a.axhline(3,color="gray",ls="--",lw=.8)
a.set_ylabel("학부모 평균 (1~5점)")
a.set_title("② 학부모의 '두 얼굴'\n민원 전체 옹호(약) vs 과도민원=문제(강)",fontsize=12,fontweight="bold")

# (3) 공통문항 교사 vs 학부모 grouped
a=ax[0,2]
items=[('q11','대부분\n민원 정당'),('q12','일부 과도\n민원 부담'),('q13','교권침해\n심각'),
       ('q14','정당지도도\n신고불안'),('q15','법적환경\n위축')]
import numpy as np
x=np.arange(len(items)); w=0.38
tm=[mean_of(by['교사'],C[k])[0] for k,_ in items]
pm=[mean_of(by['학부모'],C[k])[0] for k,_ in items]
b1=a.bar(x-w/2,tm,w,label="교사",color=BLUE)
b2=a.bar(x+w/2,pm,w,label="학부모",color=ORANGE)
a.set_xticks(x); a.set_xticklabels([l for _,l in items],fontsize=9)
a.set_ylim(0,5.5); a.legend(); a.axhline(3,color="gray",ls="--",lw=.8)
a.set_ylabel("평균 (1~5점)")
for bars in (b1,b2): barlabels(a,bars,off=0.05)
a.set_title("③ 공통문항: 교사 vs 학부모\n'과도민원 부담'에서 격차 최소",fontsize=12,fontweight="bold")

# (4) 교사 Q3 민원경험
a=ax[1,0]
cnt=Counter(r[3].strip() for r in by['교사'] if r[3].strip())
order=sorted(cnt,key=lambda x:num(x) or 9)
labs=[k.split(' ',1)[1] for k in order]; vals=[cnt[k] for k in order]
cols=[GRAY]+[ORANGE]*(len(order)-1)
bars=a.barh(labs,vals,color=cols); a.invert_yaxis()
for b,v in zip(bars,vals):
    a.text(v+0.1,b.get_y()+b.get_height()/2,f"{v}명",va="center",fontsize=10,fontweight="bold")
a.set_xlabel("교사 수 (n=%d)"%len(by['교사']))
a.set_title("④ 교사 Q3: 지난 1년 도 넘는 민원 경험\n→ 61%가 1회 이상 경험",fontsize=12,fontweight="bold")

# (5) 교사 Q4 유형
a=ax[1,1]
typ=Counter()
for r in by['교사']:
    for p in r[4].split(';'):
        p=p.strip()
        if p: typ[p.split(' ',1)[1] if ' ' in p else p]+=1
mc=typ.most_common()
labs=[k for k,_ in mc]; vals=[v for _,v in mc]
bars=a.barh(labs,vals,color=BLUE); a.invert_yaxis()
for b,v in zip(bars,vals):
    a.text(v+0.1,b.get_y()+b.get_height()/2,str(v),va="center",fontsize=10,fontweight="bold")
a.set_xlabel("응답 횟수 (복수응답)")
a.set_title("⑤ 교사 Q4: 민원 주된 유형",fontsize=12,fontweight="bold")

# (6) 학부모 Q5 주변 목격
a=ax[1,2]
cnt=Counter(r[14].strip() for r in by['학부모'] if r[14].strip())
mc=cnt.most_common()
labs=[k.split(' ',1)[1] for k,_ in mc]; vals=[v for _,v in mc]
cols=[ORANGE if ('목격' in l or '들은' in l) else GRAY for l in labs]
bars=a.bar(range(len(labs)),vals,color=cols)
a.set_xticks(range(len(labs))); a.set_xticklabels(labs,fontsize=8,rotation=12)
for b,v in zip(bars,vals):
    a.text(b.get_x()+b.get_width()/2,v+0.2,f"{v}",ha="center",fontsize=10,fontweight="bold")
a.set_ylabel("학부모 수 (n=%d)"%sum(vals))
a.set_title("⑥ 학부모 Q5: 주변 과도민원 목격·전언\n→ 58%가 실재 체감",fontsize=12,fontweight="bold")

plt.tight_layout(rect=[0,0,1,0.96])
p1=os.path.join(OUT,"01_종합_대시보드.png")
fig.savefig(p1,dpi=150,bbox_inches="tight"); plt.close(fig)
print("saved",p1)

# ===================================================================
# FIG 2 — 핵심 단일 그래프 (발표 슬라이드용)
# ===================================================================
fig,a=plt.subplots(figsize=(9,6))
groups=['교사','학부모','학생']; keys=['q12','p_q7','s_q5']
means=[]; agr=[]
for g,k in zip(groups,keys):
    m,n,v=mean_of(by[g],C[k]); means.append(m); agr.append(agree(v))
bars=a.bar(groups,means,color=[GC[g] for g in groups],width=0.6)
for b,m,p in zip(bars,means,agr):
    a.text(b.get_x()+b.get_width()/2,m+0.05,f"{m:.2f}",ha="center",va="bottom",fontsize=15,fontweight="bold")
    a.text(b.get_x()+b.get_width()/2,0.3,f"동의 {p:.0f}%",ha="center",color="white",fontsize=13,fontweight="bold")
a.set_ylim(0,5.4); a.axhline(3,color="gray",ls="--",lw=1,label="중립(3점)")
a.set_ylabel("평균 동의도 (1~5점)",fontsize=12)
a.set_title("'과도한 민원이 교사를 위축시킨다'\n— 교사·학부모·학생 세 계층 모두 동의",fontsize=15,fontweight="bold")
a.legend(loc="upper right")
plt.tight_layout()
p2=os.path.join(OUT,"02_핵심_과도민원_계층합의.png")
fig.savefig(p2,dpi=150,bbox_inches="tight"); plt.close(fig)
print("saved",p2)

# ===================================================================
# FIG 3 — 응답자 구성 파이
# ===================================================================
fig,a=plt.subplots(figsize=(7,6))
gs=['교사','학부모','학생']; sz=[len(by[g]) for g in gs]
a.pie(sz,labels=[f"{g}\n{n}명" for g,n in zip(gs,sz)],autopct="%1.0f%%",
      colors=[GC[g] for g in gs],startangle=90,textprops={"fontsize":12,"fontweight":"bold"},
      wedgeprops={"edgecolor":"white","linewidth":2})
a.set_title("응답자 계층 구성 (N=%d)"%len(rows),fontsize=14,fontweight="bold")
plt.tight_layout()
p3=os.path.join(OUT,"03_응답자_구성.png")
fig.savefig(p3,dpi=150,bbox_inches="tight"); plt.close(fig)
print("saved",p3)
print("DONE")
