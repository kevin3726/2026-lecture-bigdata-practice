"""Reproducible initialization, full-pair, and exact-pruning experiments."""
from pathlib import Path
import random, json, math, time, hashlib
from itertools import combinations
import bench, task3_fewer as m
from task1_kmeans import kmeans,BLOBS,assign,update,sse_of
from task2_curse import euclid
root=Path(__file__).resolve().parent
out=root/"out"
init={}
for method in ("random","++"):
    sses=[kmeans(BLOBS,3,init=method,seed=seed)[2] for seed in range(40)]
    init[method]={"success_sse_below_1":sum(s<1 for s in sses),
                  "trials":40,"min_sse":min(sses),"max_sse":max(sses),
                  "mean_sse":sum(sses)/40}
(out/"initialization.json").write_text(json.dumps(init,indent=2))
print("Initialization:",json.dumps(init),flush=True)
# Nested prefixes: all pairs of a larger prefix contain every smaller prefix pair.
rng=random.Random(246+50)
points=[tuple(rng.random() for _ in range(50)) for _ in range(1000)]
extrema=[]
for n in (100,300,1000):
    start=time.perf_counter()
    ds=[euclid(a,b) for a,b in combinations(points[:n],2)]
    mean=sum(ds)/len(ds)
    row={"points":n,"dim":50,"pairs":len(ds),"min":min(ds),"max":max(ds),
         "contrast":(max(ds)-min(ds))/min(ds),"mean":mean,
         "relative_stdev":math.sqrt(sum((x-mean)**2 for x in ds)/len(ds))/mean,
         "seconds":time.perf_counter()-start,"method":"all pairs of nested prefixes"}
    extrema.append(row)
    print("Full-pair extrema:",json.dumps(row),flush=True)
(out/"full_pair_extrema.json").write_text(json.dumps({"runs":extrema},indent=2))
points,initial=bench.build()
original_means=m._means
traces={"baseline":[],"yours":[]}
phase="baseline"
def capture_means(points,labels,k,previous):
    traces[phase].append(hashlib.sha256(bytes(labels)).hexdigest())
    return original_means(points,labels,k,previous)
m._means=capture_means
results={}
outputs={}
for name,cls in (("baseline",m.NaiveKMeans),("yours",m.YourKMeans)):
    phase=name
    distance=bench.Distance()
    algo=cls(bench.K)
    start=time.perf_counter()
    labels,centroids=algo.run(points,initial,distance)
    outputs[name]=(labels,centroids)
    results[name]={"calls":distance.calls,"seconds":time.perf_counter()-start,
                   "iterations":algo.iterations,"sse":bench.sse(points,labels,centroids)}
    if name=="yours":
        assert distance.calls==algo.calls
        results["bounds"]={key:getattr(algo,key) for key in (
            "per_iteration_calls","first_assignment_calls","skipped_points",
            "lower_bound_skips","separation_skips","tighten_calls","tie_fallbacks")}
m._means=original_means
results["same_labels"]=outputs["baseline"][0]==outputs["yours"][0]
results["same_centroids"]=outputs["baseline"][1]==outputs["yours"][1]
results["same_iteration_assignments"]=traces["baseline"]==traces["yours"]
results["relative_sse_difference"]=abs(results["yours"]["sse"]-results["baseline"]["sse"])/results["baseline"]["sse"]
results["distance_cut"]=1-results["yours"]["calls"]/results["baseline"]["calls"]
results["first_iteration_fraction"]=results["bounds"]["per_iteration_calls"][0]/results["yours"]["calls"]
assert results["same_labels"] and results["same_centroids"] and results["same_iteration_assignments"]
(out/"benchmark_details.json").write_text(json.dumps(results,indent=2))
print("Exact pruning:",json.dumps(results),flush=True)
# Adversarial small inputs check ties, coincident centres, and empty clusters.
rng=random.Random(7)
cases=[
 ([(0.,),(0.,),(1.,),(1.,)],[(0.,),(0.,),(1.,)]),
 ([(-1.,),(1.,)],[(0.,),(0.,)]),
 ([(0.,),(1.,),(2.,)],[(0.,),(1e-13,),(2.,)]),
 ([(0.,0.),(1.,0.),(9.,0.)],[(0.,0.),(5.,0.),(100.,0.)])]
for _ in range(12):
    pts=[tuple(rng.uniform(-5,5) for _ in range(3)) for _ in range(35)]
    cases.append((pts,rng.sample(pts,4)))
for pts,cents in cases:
    a=m.NaiveKMeans(len(cents),50).run(pts,cents,bench.Distance())
    b=m.YourKMeans(len(cents),50).run(pts,cents,bench.Distance())
    assert a==b,(pts,cents,a,b)
assert assign([(0.,)], [(-1.,),(1.,)])==[0]
assert kmeans([(0.,),(0.,),(0.,)],3,init="++")[2]==0
assert all(c is not None for c in update([(0.,),(1.,)], [0,0],2))
(out/"additional_checks.json").write_text(json.dumps({
 "exact_small_graphless_point_cases":len(cases),"random_cases":12,
 "ties_empty_clusters_coincident_centers":"passed",
 "task1_tie_and_identical_point_initialization":"passed",
 "benchmark_all_iteration_assignments_identical":True},indent=2))
print("Additional correctness checks passed",flush=True)
