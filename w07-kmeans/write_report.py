"""Regenerate Korean reports and charts from saved measurements."""
from pathlib import Path
import json, math, os, sys
root=Path(__file__).resolve().parent
out=root/"out"
data=json.loads((out/"curse.json").read_text())
rows=data["runs"]
dims=[r for r in rows if r["points"]==1000]
vary=sorted([r for r in rows if r["dim"]==50],key=lambda r:r["points"])
full=json.loads((out/"full_pair_extrema.json").read_text())["runs"]
init=json.loads((out/"initialization.json").read_text())
perf=json.loads((out/"benchmark_details.json").read_text())
if (root.parents[2]/"Week 06"/"작업용"/".plot-libs").exists():
    sys.path.insert(0,str(root.parents[2]/"Week 06"/"작업용"/".plot-libs"))
os.environ.setdefault("MPLCONFIGDIR",str(root.parent/".matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,3,figsize=(13,4))
ds=[r["dim"] for r in dims]
axes[0].loglog(ds,[r["contrast"] for r in dims],"o-",label="Sample contrast")
axes[0].axhline(1,color="gray",linestyle="--",label="1.0")
axes[0].axhline(.5,color="gray",linestyle=":",label="0.5")
axes[0].set_ylabel("(max - min) / min")
axes[0].legend()
axes[1].loglog(ds,[r["mean"] for r in dims],"o-",label="Measured mean")
axes[1].loglog(ds,[math.sqrt(d/6) for d in ds],"--",label="sqrt(d/6)")
axes[1].set_ylabel("Mean Euclidean distance")
axes[1].legend()
axes[2].loglog(ds,[r["relative_stdev"] for r in dims],"o-")
axes[2].set_ylabel("Standard deviation / mean")
for ax in axes:
    ax.set_xlabel("Dimension")
    ax.grid(True,which="both",alpha=.25)
fig.suptitle("Uniform unit-cube points: sampled distance concentration (n=1,000)")
fig.tight_layout()
fig.savefig(out/"curse_curve.png",dpi=160)
fig.savefig(out/"curse_curve.svg")
plt.close(fig)
a3=next(r for r in dims if r["contrast"]<1)
a05=next(r for r in dims if r["contrast"]<.5)
largest=max(dims,key=lambda r:r["dim"])
lines=[
"# Task 2: 차원에 따른 거리 집중 실험","",
"측정일: 2026-10-31 (한국 시간). CPU: AMD Ryzen 7 260 w/ Radeon 780M Graphics. RAM: 33,591,296,000 bytes (31.28 GiB). Windows 11, Python 3.12.14. Codex/ChatGPT, Chrome, Defender, Explorer가 실행 중이었고 백그라운드 부하는 통제하지 않았다. 시간은 단일 실행값이다.",
"","## A1·A2·A3·A5: 차원별 측정","",
"각 차원에서 단위 초입방체 [0,1]^d의 균등 점 1,000개를 생성했다. 최대 20,000번 점 쌍을 무작위로 뽑고 자기 자신인 쌍은 제외한다. 같은 쌍의 중복 추출은 허용하므로 아래 pairs는 서로 다른 쌍의 수가 아니다. min/max는 표본 극값이며 전체 점 쌍의 최근접·최원거리와 다르다.",
"","| 차원 d | 유효 pairs | min | max | mean | 표준편차 | contrast | 상대 표준편차 | 시간(초) |",
"|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
for r in dims:
    lines.append(f"| {r['dim']} | {r['pairs']:,} | {r['min']:.5f} | {r['max']:.5f} | {r['mean']:.5f} | {r['stdev']:.5f} | {r['contrast']:.5f} | {r['relative_stdev']:.5f} | {r['seconds']:.4f} |")
lines += [
"","![Distance contrast, mean, and relative spread](curse_curve.png)","",
f"측정한 차원 중 contrast<1이 처음 관측된 것은 d={a3['dim']} ({a3['contrast']:.5f}), <0.5는 d={a05['dim']} ({a05['contrast']:.5f})다. 따라서 시험한 점 사이의 첫 통과 구간은 각각 20–50차원, 100–200차원이다. 정확한 전환 차원이나 전체 점 쌍의 전환점을 측정한 것은 아니며, 특히 50차원 값은 1에 가깝다.",
"상대 표준편차도 약 0.476→0.019로 감소했다. 보통 거리들의 전반적 집중을 보려면 표본 극값과 표본 수에 민감한 contrast보다 상대 표준편차가 더 안정적이라고 판단했다. 다만 실제 최근접·최원거리의 격차가 목적이면 contrast도 유용하다. 어느 하나만으로 '모든 거리 기반 알고리즘이 무의미하다'고 결론 낼 수는 없다.",
"","## A4: 평균 거리는 d가 아니라 sqrt(d)에 가깝게 증가","",
"| d | 실측 mean | sqrt(d/6) | mean/sqrt(d) |","|---:|---:|---:|---:|"]
for r in dims:
    d=r["dim"]
    lines.append(f"| {d} | {r['mean']:.5f} | {math.sqrt(d/6):.5f} | {r['mean']/math.sqrt(d):.5f} |")
lines += [
"","독립 균등 좌표 X,Y에서 E[(X−Y)^2]=1/6이므로 E[D²]=d/6이다. 이것은 E[D]=sqrt(d/6)와 정확히 같다는 뜻은 아니지만, 큰 d에서 D가 집중하므로 평균도 그 값에 가까워진다. mean/sqrt(d)는 고차원에서 약 0.408로 안정되어 1/sqrt(6)≈0.40825와 맞는다. 예를 들어 d=200→1000은 5배인데 평균은 약 2.23배로 sqrt(5)≈2.236에 가깝고 선형 5배가 아니다.",
"","## A6: 같은 차원에서 점 개수 바꾸기","",
"50차원, 최대 20,000번 추출이라는 표본 예산을 고정한 기본 코드의 결과다. 점 생성 뒤 같은 RNG로 쌍을 뽑으므로 n이 바뀌면 쌍 표본도 바뀐다.",
"","| n | 표본 pairs | contrast | 상대 표준편차 |","|---:|---:|---:|---:|"]
for r in vary:
    lines.append(f"| {r['points']:,} | {r['pairs']:,} | {r['contrast']:.5f} | {r['relative_stdev']:.5f} |")
lines += [
"","표본 contrast는 약 0.811, 0.928, 0.982, 1.022, 0.877로 변해 n에 대해 단조 증가하지 않았다. 이를 'n의 영향이 없다'고 결론 내릴 수는 없다. 고정 개수의 무작위 쌍은 전체 극값을 보장하지 않기 때문이다.",
"추가로 동일한 1,000개 점에서 앞의 100·300·1,000개를 중첩 부분집합으로 사용해 모든 서로 다른 점 쌍을 계산했다.",
"","| n | 전체 pairs | 전체 contrast | 상대 표준편차 | 시간(초) |","|---:|---:|---:|---:|---:|"]
for r in full:
    lines.append(f"| {r['points']:,} | {r['pairs']:,} | {r['contrast']:.5f} | {r['relative_stdev']:.5f} | {r['seconds']:.4f} |")
lines += [
"","중첩 입력의 전체 쌍에서는 점을 추가해도 최소 거리가 커지거나 최대 거리가 작아질 수 없으므로 contrast가 감소하지 않는다. 실측도 0.811→1.021→1.306으로 증가했다. 특히 같은 d=50,n=1,000에서도 전체 contrast=1.306은 표본값 0.982와 다르므로 A3의 50차원 통과를 전체 극값의 보편 경계로 해석하면 안 된다.",
"","## A7: 가장 큰 차원의 실행 시간","",
f"기본 차원 실험의 최대 d=1,000,n=1,000은 {largest['seconds']:.4f}초 걸렸다. 이 시간에는 점 생성과 표본 거리 계산이 포함되고 그 뒤의 요약 통계 계산은 제외된다. 보충 전체 쌍 실험의 최대 n=1,000,d=50,499,500쌍은 {full[-1]['seconds']:.4f}초였다. 두 실험의 작업량은 서로 다르다.",
"","## A8: 3주차 Jaccard LSH에도 그대로 적용되는가?","",
"이번 결과는 균등한 독립 유클리드 좌표의 실험이다. 문서 shingle 집합의 Jaccard 유사도나 실제 문서 분포가 같다는 근거는 아니므로 이 수치만으로 3주차 LSH가 실패한다고 할 수 없다. MinHash의 일치 확률과 Jaccard 사이의 관계, 밴딩 후보 확률도 이 유클리드 차원 증가만으로 깨지지 않는다.",
"다만 실제 문서에서도 의미 있는 쌍과 무관한 쌍의 유사도가 비슷하게 몰리면 LSH의 후보 분리가 어려워질 수 있다. 중요한 것은 해당 데이터에서 Jaccard 분포와 유사/비유사 쌍의 격차다. 3주차에서는 심은 근접 중복과 다른 문서의 격차가 있었으므로 별도의 관측으로 평가해야 한다.",
"","## 재현","",chr(96)*3+"text",
"python task2_curse.py --dims 2,5,10,20,50,100,200,500,1000",
"python task2_curse.py --dims 50 --points 100",
"python task2_curse.py --dims 50 --points 500",
"python task2_curse.py --dims 50 --points 2000",
"python task2_curse.py --dims 50 --points 5000",
"python extra_experiments.py",
"python write_report.py",chr(96)*3,"",
"curse.json은 실행 결과를 추가한다. 보고서 재생성 전 기존 실행과 재측정을 구분해야 한다. 핵심 구현과 검사는 표준 라이브러리만 사용하며 write_report.py의 그래프 생성만 matplotlib이 필요하다."]
(out/"curse.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
b=perf["bounds"]
obs=f"""# Week 7 관찰 기록

## Task 1
빈 군집은 비어 있지 않은 군집의 평균들에서 가장 멀리 떨어진 입력 점으로 결정적으로 재배치했다. 기존 중심을 유지하는 방법과 달리 다음 배정에서 빈 군집이 점을 얻을 기회를 주지만 다른 군집 결과를 만들 수 있다.
40개 seed에서 세 덩어리 복원(SSE<1)은 random {init['random']['success_sse_below_1']}/40, k-means++ {init['++']['success_sse_below_1']}/40이며 평균 SSE는 각각 {init['random']['mean_sse']:.5f}, {init['++']['mean_sse']:.5f}였다. ++의 D² 가중 초기 선택은 잘 분리된 시작점을 얻는 대신 사전 거리 계산을 쓰므로 이미 좋은 중심이 있거나 초기화 비용이 지배적인 경우에는 그 비용을 피할 수 있다.
최적으로 달성 가능한 SSE는 k가 커져도 증가하지 않고 k=n에서는 0이 가능하므로 SSE만 최소화하면 과도하게 잘게 나누게 된다. 복잡도·해석 가능성·elbow 또는 별도 품질 지표를 함께 봐야 하며 개별 무작위 실행의 지역 최솟값까지 k에 대해 단조라는 보장은 없다.

## Task 2
n=1,000·최대 20,000회 무작위 쌍 추출에서 contrast<1은 시험한 차원 중 50(0.982), <0.5는 200(0.372)에서 처음 관측됐다. 평균 거리는 sqrt(d)에 가깝게 증가하고 상대 표준편차는 0.476→0.019로 감소했으며 최대 d=1,000 실행은 {largest['seconds']:.4f}초였다.
50차원에서 고정 쌍 예산의 n 증가 실험은 contrast가 단조롭지 않았다. 같은 점들의 중첩 부분집합 전체 쌍을 계산하면 n=100→300→1,000에서 0.811→1.021→1.306으로 증가했으므로 n과 표본 예산을 구분해야 하며 50차원의 표본 경계를 전체 데이터 경계로 볼 수 없다.
Jaccard의 집합 유사도와 문서 분포는 이번 균등 유클리드 좌표와 다르므로 3주차 LSH가 이 실험 때문에 바로 실패하지는 않는다. 실제 Jaccard 값이 서로 비슷하게 집중하면 후보 분리가 어려울 수 있으므로 해당 유사도 분포와 근접 중복의 격차를 확인해야 한다.

## Task 3
Elkan 방식으로 점마다 현재 중심까지의 상한 1개와 각 k개 중심까지의 하한 k개를 저장했다. n=20,000,k=12에서 260,000개의 경계 값에 중심 간 거리·이동량 O(k²)와 배정 번호를 더하며, 이는 Python 객체를 포함한 실제 바이트 측정값은 아니다.
가장 많은 개별 후보 검사를 줄인 것은 중심별 거리 하한({b['lower_bound_skips']:,}회)이었고 중심 분리 경계와 전체 점 건너뛰기도 사용했다. 중심 이동 k회·중심 간 거리 k(k−1)/2회도 제공된 distance로 세며 경계 갱신·검사는 O(nk) 수치 연산이지만 매번 d차원 거리를 계산하는 것보다 저렴했다.
기준과 43회 매 반복의 배정·최종 중심이 동일하여 SSE={perf['baseline']['sse']:.8f}의 차이는 정확히 0이었다. 거리 계산은 {perf['baseline']['calls']:,}→{perf['yours']['calls']:,}회({perf['distance_cut']:.4%} 감소)이고 첫 배정은 240,000회, 이동 12회까지 포함한 첫 반복은 240,012회로 전체의 {perf['first_iteration_fraction']:.4%}였다; 이는 근사가 아니라 검증된 경계로 생략한 결과다.
"""
(out/"observation.md").write_text(obs,encoding="utf-8")
print("Korean report, observations, PNG and SVG saved",flush=True)
