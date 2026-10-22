"""Regenerate the report from completed and explicitly partial measurements."""
from pathlib import Path
import json, os, sys
root=Path(__file__).resolve().parent
out=root/"out"
rows=json.loads((out/"explosion.json").read_text())["runs"]
stats=json.loads((out/"rule_analysis.json").read_text())
mem=json.loads((out/"memory_crossover.json").read_text())["runs"]
small=json.loads((out/"small_buckets.json").read_text())
stress=json.loads((out/"stress_limit.json").read_text())
best=stats["highest_confidence_rule"]
normal=mem[-1]
os.environ.setdefault("MPLCONFIGDIR",str(root.parent/".matplotlib"))
sys.path.insert(0,str(root.parent/".plot-libs"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(9,4.8))
xs=[r["support"] for r in rows]
ax.plot(xs,[r["peak_counters"] for r in rows],"o-",label="Peak candidate counters")
ax.plot(xs,[r["frequent_pairs"] for r in rows],"s-",label="Frequent pairs (answers)")
ax.set_xscale("log",base=2)
ax.set_yscale("log")
ax.invert_xaxis()
ax.set_xticks(xs,labels=[str(x) for x in xs])
ax.set_xlabel("Absolute support threshold (decreasing to the right)")
ax.set_ylabel("Count (log scale)")
ax.set_title("Apriori: stored candidates versus answers")
ax.grid(True,which="both",alpha=.25)
ax.legend()
fig.tight_layout()
fig.savefig(out/"explosion_curve.png",dpi=160)
fig.savefig(out/"explosion_curve.svg")
plt.close(fig)
lines=[
"# Task 2: 지지도를 낮출 때 후보와 정답 수의 변화","",
"측정일: 2026-10-22, 한국 시간. CPU: AMD Ryzen 7 260 w/ Radeon 780M Graphics. RAM: 33,591,296,000 bytes (31.28 GiB). Windows 11, Python 3.12.14. Chrome, Codex/ChatGPT가 실행 중이었으며 백그라운드 부하는 통제하지 않았다. 시간은 단일 실행이므로 변동이 있다.",
"","## A1·A3·A5: 기본 데이터의 완료된 실측","",
"교수님 bench.build(seed=246)의 상품 2,000개, 장바구니 20,000개를 사용했다. 지지도는 비율이 아닌 최소 등장 장바구니 수다. 아래 결과는 모두 끝까지 계산한 값이며, 확장 중단 실험과 섞지 않았다.",
"","| 지지도 | 후보 카운터 peak | 빈발 쌍(정답) | 시간(초) | 추적 peak(MiB) |","|---:|---:|---:|---:|---:|"]
for r in rows:
    lines.append(f"| {r['support']} | {r['peak_counters']:,} | {r['frequent_pairs']:,} | {r['seconds']:.3f} | {r['peak_bytes']/1048576:.2f} |")
lines += [
"","![Candidate counters and answers](explosion_curve.png)","",
f"9개 지지도로 최대/최소 {max(xs)/min(xs):.0f}배 범위를 측정했다. 그래프는 가로·세로 로그 축이며 오른쪽으로 갈수록 지지도가 낮다.",
"","## A4: 실제 증가 배율","",
"| 지지도 변화 | 후보 카운터 배율 | 정답 쌍 배율 |","|---|---:|---:|"]
for a,b in zip(rows,rows[1:]):
    lines.append(f"| {a['support']} → {b['support']} | {b['peak_counters']/a['peak_counters']:.3f} | {b['frequent_pairs']/a['frequent_pairs']:.3f} |")
lines += [
"","400→200→100→50에서 후보 카운터는 약 5.54배, 4.67배, 3.00배로 늘어 단순한 두 배 증가보다 컸다. 400→50 전체로는 후보가 약 77.49배 증가했지만 정답은 약 25.69배 증가했다. 특히 support=50에서는 820,259개의 후보 카운터를 저장해 6,397개의 정답만 얻었다.",
"25 이하에서는 후보가 893,456개로 포화되었다. 관측 가능한 상품 쌍은 유한하며 임계값을 더 낮춰도 새로 세어야 할 관측 쌍이 늘지 않기 때문이다. 이 구간의 정답은 17,045→893,456개로 계속 증가하므로 과제 설명의 '카운터는 계속 폭증하고 정답은 천천히 증가한다'가 모든 구간에서 맞지는 않았다. 낮은 지지도에서는 결과 사전 자체도 커져, 후보 수가 같아도 peak bytes는 증가했다. 입력 크기와 분포를 고정한 실측의 한계를 숨기지 않았다.",
"","## A2: 실제 중단 지점과 확장 실험","",
"기본 데이터는 support=1에서도 완료됐다. 이 PC에서 기본 데이터의 메모리 고갈이나 실행 불능을 관측했다고 주장할 수 없다. 상품 2,000개면 가능한 쌍의 이론적 상한도 1,999,000개이므로 고정 데이터에서 임계값만 계속 낮춰 무한히 폭증시킬 수 없다.",
"별도로 상품 20,000개·장바구니 50,000개·평균 추출 수 60·Zipf 지수 0.8·seed 246의 확장 데이터를 만들었다. 생성 시 누적 가중치를 재사용하며 planted pair를 추가하지 않아 기본 데이터와 다른 보충 실험이다. Apriori의 빈발 상품 필터 후 두 번째 단계의 정확한 카운팅을 수행했다.",
f"support={stress['support']}에서 {stress['processed_baskets']:,}/{stress['total_baskets']:,}개 장바구니를 처리한 뒤 {stress['pass_two_seconds']:.2f}초, 후보 {stress['peak_pair_counters_observed']:,}개, 추적 peak {stress['traced_peak_bytes']/1048576:.2f} MiB에서 중단했다. 중단 사유는 {stress['stop_reason']}이다.",
"사전에 60초 대기 또는 추적 할당 1GiB를 중단 기준으로 정하고 64개 장바구니마다 확인했다. 사전의 크기 확장과 검사 간격 때문에 실제 peak는 1GiB를 초과했다. 이는 엄격한 메모리 상한이나 PC 전체 RAM 고갈이 아니라 실행을 계속하지 않기 위한 작업 예산이다. 확장 실험의 카운터 수는 처리한 부분까지의 관측값으로 최종 peak의 하한이며, 빈발 쌍 정답은 완성하지 않았다. stress_limit.json의 completed=false로 명시했다. 이 시간은 입력 생성과 1차 패스를 제외한 2차 패스만이다.",
"","## Task 3 R5: 버킷 비용까지 포함한 실제 메모리","",
"1,048,576개 버킷을 unsigned 32-bit array로 보관한다. 실제 array 크기는 4,194,384 bytes(헤더 포함), 변환 후 비트맵은 131,129 bytes(헤더 포함)다. 비트맵을 만드는 순간에는 배열과 비트맵이 함께 존재한다. 전체 버킷 배열과 단일 상품 카운터는 두 번째 패스 전에 del로 해제한다.",
"peak_counters는 후보 쌍별 카운터만을 센 점수 지표다. 1차 패스의 1,048,576개 버킷 카운터까지 포함한 전체 정수 개수가 기준보다 작다는 주장은 하지 않았다. 촘촘한 배열의 정수와 Python 사전의 쌍 카운터는 개당 비용이 다르므로 실제 추적 peak도 따로 비교했다.",
"","| 장바구니 수 | Apriori 후보 peak | PCY 후보 peak | Apriori peak(MiB) | PCY peak(MiB) |","|---:|---:|---:|---:|---:|"]
for r in mem:
    a,b=r["plain"],r["pcy"]
    lines.append(f"| {r['baskets']:,} | {a['peak_counters']:,} | {b['peak_counters']:,} | {a['peak_bytes']/1048576:.3f} | {b['peak_bytes']/1048576:.3f} |")
lines += [
"","모든 행은 support=50, 같은 20,000개 데이터의 앞부분을 사용했으며 정답뿐 아니라 각 쌍의 등장 횟수까지 일치했다. 2,000개에서는 고정 배열 비용 때문에 PCY가 더 컸고, 5,000개에서는 PCY가 더 작았다. 따라서 이 분포·버킷 수·support에서 관측한 교차 구간은 2,000–5,000개 장바구니 사이이며 정확한 교차점이나 다른 데이터에 대한 보편 임계값은 아니다.",
f"버킷을 16,384개로 줄이자 {small['frequent_buckets']:,}개 모두 frequent가 되었고 후보 카운터가 {small['peak_counters']:,}개로 기준과 같아졌다. 배열은 작아졌지만 충돌 때문에 필터가 아무 후보도 거르지 못했다. 반면 기본 버킷 수에서는 6,946개 버킷만 통과하고 후보는 12,881개였다.",
f"기본 데이터에서 추적 peak는 Apriori {normal['plain']['peak_bytes']/1048576:.3f} MiB, PCY {normal['pcy']['peak_bytes']/1048576:.3f} MiB로 실제로도 절약됐다. 하지만 bench.py의 비추적 시간은 1.58초 대 3.99초로 PCY가 느렸다. 이 과제는 시간보다 peak 카운터를 점수화하며, 해시 계산과 추가 필터링 비용이 생긴다.",
"","## 측정 범위와 재현","",
"기본 Task 2 시간은 PlainApriori.run 전체다. tracemalloc은 알고리즘 실행 중 추적한 할당의 peak로 입력 장바구니 생성, 전체 프로세스 메모리, 전체 PC RAM과 다르다. 반환 결과 사전의 생성은 포함된다. memory_crossover.json은 별도 추적 실행이고 bench.txt는 추적 없는 성능 평가이므로 두 실행의 시간을 혼동하지 않는다. bench.py·test_tasks.py·PlainApriori는 원본을 유지했다.",
"",chr(96)*3+"text",
"python task2_explosion.py --supports 400,200,100,50,25,12,6,3,1",
"python extra_experiments.py",
"python stress_limit.py",
"python write_report.py",chr(96)*3,"",
"write_report.py는 그림 생성에 matplotlib을 사용한다. 핵심 구현과 교수님 검사는 Python 기본 라이브러리만 사용한다. 재실행한 측정은 explosion.json에 추가되므로 보고서 작성에 쓰는 실행을 구분한다."]
(out/"explosion.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
obs=f"""# Week 6 관찰 기록

## Task 1
합성 데이터 support=50의 최고 confidence 규칙 1468→0은 52/62={best['confidence']:.4%}이지만 역방향 0→1468은 52/13,080={best['reverse_confidence']:.4%}다. 1468 구매자의 다음 선택을 예측하는 방향이 더 유용하며, 장난감 예제는 네 상품이 모두 5회 등장해 그 예제만으로 비대칭을 보일 수 없었다.
최고 규칙의 lift는 {best['lift']:.4f}로 상품 0의 기본 등장률 65.4%를 감안하면 confidence만큼 강한 관계는 아니다. 62건의 선행 상품 표본에 기반한 관측이며 인과관계나 미래 성능을 보장하지 않으므로 추가 검증 없이 강한 추천 근거로 믿지는 않는다.
상품 2,000개의 모든 쌍은 1,999,000개이고 pass one 생존 상품 1,849개로 가능한 쌍은 1,708,476개다. 실제 관측되어 Apriori가 보관한 후보는 820,259개였으므로 가능한 조합 수와 실제 카운터 수를 구분했다.

## Task 2
Ryzen 7 260·RAM 31.28 GiB·Windows 11에서 기본 데이터는 support=1까지 완료됐다. 별도 확장 데이터(상품 20,000·장바구니 50,000·평균 추출 60)의 support=3에서 작업 예산 1GiB를 넘어 {stress['processed_baskets']:,}개 처리·{stress['pass_two_seconds']:.2f}초·peak {stress['traced_peak_bytes']/1048576:.1f} MiB에서 중단했으며 PC RAM 고갈이 아닌 안전 중단이다.
기본 데이터의 support 400→200→100→50에서 후보는 5.54배·4.67배·3.00배로 늘었지만 25 이하에서는 893,456개로 포화됐다. 64개 장바구니 간격으로 검사하는 확장 실험은 사전 크기 확장으로 중단 기준을 초과했으며 후보 11,220,932개는 부분 처리까지의 하한이지 완성 결과가 아니다.
400→50에서 후보는 약 77.49배, 정답은 25.69배 증가해 후보 820,259개로 정답 6,397개를 찾았다. 반대로 25 이하에서는 후보가 같아도 정답은 계속 증가해 결과 사전 메모리가 늘었으며, 임계값을 조금 낮추는 비용이 모든 구간에서 동일하거나 무한히 커지지는 않았다.

## Task 3
버킷 1,048,576개를 선택해 Python 쌍 사전보다 촘촘한 32-bit array(헤더 포함 4,194,384 bytes)를 사용했고 131,129-byte 비트맵으로 바꾼 뒤 배열을 해제했다. 후보 카운터는 820,259→12,881개(98.4% 감소)이며 정답 6,397쌍과 각각의 횟수까지 일치했다.
버킷 정수까지 포함하면 1차 패스의 카운터 수가 더 클 수 있으므로 점수만으로 RAM 절약을 주장하지 않았다. 추적 peak는 {normal['plain']['peak_bytes']/1048576:.3f}→{normal['pcy']['peak_bytes']/1048576:.3f} MiB였고 고정 support=50의 2,000개에서는 PCY가 더 크고 5,000개에서는 더 작아 실제 교차 구간은 2,000–5,000개였다; 입력 생성과 전체 프로세스 RAM은 측정 범위 밖이다.
버킷을 16,384개로 줄이자 모든 버킷이 통과하고 후보가 820,259개로 돌아와 효과가 사라졌다. 작은 고정 비용과 충돌에 의한 가지치기 약화 사이의 균형이 필요하며 시간은 오히려 1.58→3.99초로 늘었다.
"""
(out/"observation.md").write_text(obs,encoding="utf-8")
print("Reports and PNG/SVG plots regenerated",flush=True)
