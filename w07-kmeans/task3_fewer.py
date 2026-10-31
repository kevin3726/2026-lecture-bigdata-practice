#!/usr/bin/env python3
"""Week 7 · Task 3 — The same clustering, with far fewer distances.

Textbook §7.3, and §7.1.3 for why distance is the expensive part.

`NaiveKMeans` does what the definition says: every iteration, compare every
point with every centroid. That is n x k distance computations per pass, and on
a real dataset the distance computation is almost the entire cost.

Most of that work is wasted. After the first couple of iterations, most points
do not change cluster, and most centroids barely move. The triangle inequality
lets you prove a point cannot have changed cluster **without measuring it**.

    python3 bench.py
    python3 bench.py --yours

Correctness first: your final SSE must match the baseline's. Fewer distances
with a worse clustering is not an improvement, it is a different algorithm.
"""


class NaiveKMeans:
    """Every point against every centroid, every iteration."""

    def __init__(self, k, max_iter=50):
        self.k, self.max_iter = k, max_iter

    def run(self, points, initial_centroids, distance):
        centroids = list(initial_centroids)
        labels = [None] * len(points)
        for self.iterations in range(1, self.max_iter + 1):
            changed = False
            for i, p in enumerate(points):
                best, bi = None, 0
                for j, c in enumerate(centroids):
                    d = distance(p, c)
                    if best is None or d < best - 1e-12:
                        best, bi = d, j
                if labels[i] != bi:
                    labels[i] = bi
                    changed = True
            centroids = _means(points, labels, self.k, centroids)
            if not changed:
                break
        return labels, centroids


def _means(points, labels, k, previous):
    out = []
    for j in range(k):
        group = [p for p, l in zip(points, labels) if l == j]
        if group:
            out.append(tuple(sum(v) / len(group) for v in zip(*group)))
        else:
            out.append(previous[j])
    return out


class YourKMeans:
    """Your k-means.

        __init__(k, max_iter=50)
        run(points, initial_centroids, distance) -> (labels, centroids)

    Same starting centroids, same `distance` function - which is counted. That
    counter is your score.

    The idea, from §7.3 and the triangle inequality:

        if a point is much closer to its current centroid than that centroid
        moved, and than any other centroid could have come, then it cannot have
        changed cluster, and you do not have to measure anything

    Keeping enough bookkeeping to make that test cheap, without keeping so much
    that the bookkeeping costs more than the distances, is the task.

    You may call `distance` on two centroids, and those calls are counted too -
    which is the correct accounting, since that is real work. There are k of
    them and n points, and k is much smaller than n. That asymmetry is the
    whole opening.
    """

    def __init__(self, k, max_iter=50):
        if k < 1 or max_iter < 1:
            raise ValueError("k and max_iter must be positive")
        self.k, self.max_iter = k, max_iter

    def run(self, points, initial_centroids, distance):
        n,k = len(points),self.k
        if len(initial_centroids)!=k:
            raise ValueError("need k initial centroids")
        centroids=list(initial_centroids)
        labels=[None]*n
        upper=[float("inf")]*n
        lower=[[0.0]*k for _ in points]
        self.calls=0
        self.per_iteration_calls=[]
        self.skipped_points=0
        self.lower_bound_skips=0
        self.separation_skips=0
        self.tighten_calls=0
        self.tie_fallbacks=0
        self.first_assignment_calls=0
        def dist(a,b):
            self.calls+=1
            return distance(a,b)
        for self.iterations in range(1,self.max_iter+1):
            before=self.calls
            changed=False
            if self.iterations==1:
                for i,p in enumerate(points):
                    ds=[dist(p,c) for c in centroids]
                    best,bi=None,0
                    for j,d in enumerate(ds):
                        if best is None or d<best-1e-12:
                            best,bi=d,j
                    labels[i]=bi
                    upper[i]=ds[bi]
                    lower[i]=ds
                changed=bool(n)
                self.first_assignment_calls=self.calls
            else:
                separation=[[0.0]*k for _ in range(k)]
                half_nearest=[float("inf")]*k
                for a in range(k):
                    for b in range(a+1,k):
                        half=dist(centroids[a],centroids[b])/2
                        separation[a][b]=separation[b][a]=half
                        half_nearest[a]=min(half_nearest[a],half)
                        half_nearest[b]=min(half_nearest[b],half)
                for i,p in enumerate(points):
                    a=labels[i]
                    # Conservative strict comparisons protect ties/rounding.
                    margin=1e-10*(1+upper[i])
                    if upper[i]+margin<half_nearest[a]:
                        self.skipped_points+=1
                        continue
                    exact=False
                    measured={}
                    best=upper[i]
                    bi=a
                    ambiguous=False
                    for j in range(k):
                        if j==bi:
                            continue
                        if best+margin<lower[i][j]:
                            self.lower_bound_skips+=1
                            continue
                        if best+margin<separation[bi][j]:
                            self.separation_skips+=1
                            continue
                        if not exact:
                            best=dist(p,centroids[bi])
                            self.tighten_calls+=1
                            measured[bi]=best
                            lower[i][bi]=best
                            exact=True
                            if best+margin<lower[i][j]:
                                self.lower_bound_skips+=1
                                continue
                            if best+margin<separation[bi][j]:
                                self.separation_skips+=1
                                continue
                        d=dist(p,centroids[j])
                        measured[j]=d
                        lower[i][j]=d
                        if abs(d-best)<=margin:
                            ambiguous=True
                        if d<best-1e-12:
                            best,bi=d,j
                    if ambiguous:
                        # Match the baseline's ascending-index epsilon comparator,
                        # rather than imposing a different fuzzy tie convention.
                        self.tie_fallbacks+=1
                        ds=[measured[j] if j in measured else dist(p,centroids[j])
                            for j in range(k)]
                        best,bi=None,0
                        for j,d in enumerate(ds):
                            if best is None or d<best-1e-12:
                                best,bi=d,j
                        lower[i]=ds
                    if labels[i]!=bi:
                        changed=True
                    labels[i]=bi
                    upper[i]=best
            new_centroids=_means(points,labels,k,centroids)
            if changed and self.iterations<self.max_iter:
                movement=[dist(a,b) for a,b in zip(centroids,new_centroids)]
                for i in range(n):
                    upper[i]+=movement[labels[i]]
                    lower[i]=[max(0.0,bound-move) for bound,move in zip(lower[i],movement)]
            centroids=new_centroids
            self.per_iteration_calls.append(self.calls-before)
            if not changed:
                break
        return labels,centroids
