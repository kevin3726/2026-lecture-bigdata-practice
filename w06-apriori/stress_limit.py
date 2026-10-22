"""Bounded stress experiment: results marked incomplete on an early stop."""
from pathlib import Path
import sys, random, time, tracemalloc, json
from itertools import accumulate,combinations
from collections import Counter
root=Path(__file__).resolve().parent
items,basket_count,average,support=20000,50000,60,3
rng=random.Random(246)
population=list(range(items))
cdf=list(accumulate(1/(i+1)**.8 for i in population))
# Larger supplementary data, not a modification of the grading harness.
baskets=[set(rng.choices(population,cum_weights=cdf,
          k=max(2,int(rng.gauss(average,4))))) for _ in range(basket_count)]
counts=Counter(i for basket in baskets for i in basket)
frequent={i for i,c in counts.items() if c>=support}
tracemalloc.start()
start=time.perf_counter()
pairs=Counter()
reason=None
processed=0
for processed,basket in enumerate(baskets,start=1):
    for pair in combinations(sorted(basket&frequent),2):
        pairs[pair]+=1
    if processed%64==0:
        current,peak=tracemalloc.get_traced_memory()
        elapsed=time.perf_counter()-start
        if peak>=1024*1024*1024:
            reason="1 GiB traced-allocation safety limit"
            break
        if elapsed>=60:
            reason="60 second pass-two waiting limit"
            break
elapsed=time.perf_counter()-start
current,peak=tracemalloc.get_traced_memory()
tracemalloc.stop()
result={"support":support,"items":items,"baskets":basket_count,"average_draws":average,
        "seed":246,"frequent_items":len(frequent),"processed_baskets":processed,
        "total_baskets":len(baskets),"pass_two_seconds":elapsed,
        "peak_pair_counters_observed":len(pairs),"traced_peak_bytes":peak,
        "completed":reason is None,"stop_reason":reason,
        "input":"supplementary Zipf(0.8), cached CDF, without planted pairs",
        "timing_scope":"pass two only; generation and pass one excluded",
        "note":"An early-stop candidate count is a lower bound, not a complete frequent-pair answer."}
(root/"out"/"stress_limit.json").write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2),flush=True)
