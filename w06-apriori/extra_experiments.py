"""Extra experiments; keep outside upload folder."""
from pathlib import Path
import sys, json, time, tracemalloc, random, itertools
from collections import Counter
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root))
import bench
from task3_pcy import PlainApriori, YourAlgorithm

def measure(algo,baskets):
    tracemalloc.start()
    start=time.perf_counter()
    pairs=algo.run(baskets)
    seconds=time.perf_counter()-start
    current,peak=tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return pairs, {"seconds":seconds,"peak_bytes":peak,"peak_counters":algo.peak_counters,
                   "frequent_pairs":len(pairs)}

out=root/"out"
data=bench.build()
base=PlainApriori(50)
pairs=base.run(data)
singles=Counter(i for basket in data for i in basket)
rules=[]
for pair,count in pairs.items():
    a,b=sorted(pair)
    for source,target in ((a,b),(b,a)):
        confidence=count/singles[source]
        rules.append({"from":source,"to":target,"support_pair":count,
                      "support_from":singles[source],"support_to":singles[target],
                      "confidence":confidence,"reverse_confidence":count/singles[target],
                      "lift":confidence/(singles[target]/len(data))})
best=sorted(rules,key=lambda r:(-r["confidence"],r["from"],r["to"]))[0]
f=sum(c>=50 for c in singles.values())
stats={"highest_confidence_rule":best,"frequent_items_at_50":f,
       "all_possible_pairs":2000*1999//2,"survivor_possible_pairs":f*(f-1)//2,
       "observed_pair_counters":base.peak_counters}
(out/"rule_analysis.json").write_text(json.dumps(stats,indent=2))
print("Rule analysis:",json.dumps(stats),flush=True)
rows=[]
for size in (500,2000,5000,20000):
    subset=data[:size]
    answer,a=measure(PlainApriori(50),subset)
    algorithm=YourAlgorithm(50)
    mine,b=measure(algorithm,subset)
    assert mine==answer
    row={"baskets":size,"support":50,"plain":a,"pcy":b,
         "bucket_array_bytes":algorithm.bucket_array_bytes,
         "bitmap_bytes":algorithm.bitmap_bytes,
         "frequent_buckets":algorithm.frequent_buckets}
    rows.append(row)
    print("Memory",json.dumps(row),flush=True)
(out/"memory_crossover.json").write_text(json.dumps({"runs":rows},indent=2))
small=YourAlgorithm(50,buckets=1<<14)
start=time.perf_counter()
found=small.run(data)
assert found==pairs
result={"buckets":small.buckets,"peak_counters":small.peak_counters,
        "seconds":time.perf_counter()-start,"frequent_buckets":small.frequent_buckets,
        "bucket_array_bytes":small.bucket_array_bytes,"bitmap_bytes":small.bitmap_bytes,
        "same_counts_and_pairs":True}
(out/"small_buckets.json").write_text(json.dumps(result,indent=2))
print("Small bucket test",json.dumps(result),flush=True)
