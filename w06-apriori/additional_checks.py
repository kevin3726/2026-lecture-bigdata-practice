"""Independent correctness checks on counts, pruning, and bucket collisions."""
from pathlib import Path
import random, json
from collections import Counter
from itertools import combinations
import task1_apriori as t
from task3_pcy import YourAlgorithm
root=Path(__file__).resolve().parent
rng=random.Random(3726)
cases=0
for _ in range(40):
    baskets=[set(rng.sample(range(10),rng.randrange(7))) for _ in range(15)]
    support=rng.randrange(1,9)
    truth=Counter(frozenset(p) for b in baskets for p in combinations(sorted(b),2))
    truth={p:c for p,c in truth.items() if c>=support}
    assert t.frequent_pairs(baskets,support)==truth
    for buckets in (1,16,64):
        assert YourAlgorithm(support,buckets).run(baskets)==truth
        cases+=1
small=[{"a","b"},{"a"},{"a"}]
rules={(a,b):(confidence,lift) for a,b,confidence,lift in t.association_rules(small,1,0)}
assert abs(rules["a","b"][0]-1/3)<1e-12
assert rules["b","a"]==(1.0,1.0)
assert abs(rules["a","b"][1]-1)<1e-12
assert t.frequent_singletons([["a","a"],["b"]],2)=={}
allowed=set(t.frequent_singletons(t.BASKETS,3))
original=t.combinations
def checked_combinations(items,k):
    assert set(items)<=allowed
    return original(items,k)
t.combinations=checked_combinations
t.frequent_pairs(t.BASKETS,3)
t.combinations=original
assert t.frequent_pairs([],1)=={}
assert YourAlgorithm(1,16).run([])=={}
result={"random_pcy_checks_including_full_collision":cases,
        "apriori_random_datasets":40,"counts_match_not_just_keys":True,
        "asymmetric_confidence_and_lift":"passed",
        "pruning_before_pair_enumeration":"passed",
        "duplicate_item_and_empty_input":"passed"}
(root/"out"/"additional_checks.json").write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
