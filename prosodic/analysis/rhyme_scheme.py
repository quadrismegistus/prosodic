"""Named rhyme scheme detection.

Given a sequence of integer rhyme IDs (one per line, 0 = no rhyme), match
against a catalog of named schemes (Sonnet, Petrarchan, Couplet, etc.) and
return the best fit by Jaccard similarity over rhyme-edge sets.

Ported from poesy (Heuser et al., Stanford Literary Lab).
"""
from __future__ import annotations

import csv
from functools import lru_cache
from importlib.resources import files
from itertools import product
from typing import List, Optional, Tuple

ALPHABET = "abcdefghijklmnopqrstuvwxyz"


@lru_cache(maxsize=1)
def load_named_schemes() -> List[Tuple[str, str]]:
    path = files("prosodic.analysis.data").joinpath("rhyme_schemes.txt")
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return [(row["Form"], row["Scheme"]) for row in reader]


def scheme_to_nums(scheme: str) -> List[int]:
    """Convert letter scheme like 'abab' to [1,2,1,2]. Singletons → 0."""
    s = scheme.replace(" ", "")
    return [ALPHABET.index(c) + 1 if s.count(c) > 1 else 0 for c in s]


def nums_to_scheme(nums: List[int]) -> List[str]:
    """Convert int IDs back to letter scheme (0 → '-')."""
    alphabet = "-" + ALPHABET
    return [alphabet[n] if n < len(alphabet) else str(n) for n in nums]


def _scheme_to_edges(scheme: List[int]) -> List[Tuple[int, int]]:
    """Pairs (i,j) with i<j sharing the same nonzero rhyme id."""
    pos: dict[int, list[int]] = {}
    for i, x in enumerate(scheme):
        if x == 0:
            continue
        pos.setdefault(x, []).append(i)
    edges = []
    for ids in pos.values():
        if len(ids) > 1:
            for a, b in product(ids, ids):
                if a < b:
                    edges.append((a, b))
    return edges


def _normalize_slice(slice_: List[int]) -> List[int]:
    """Renumber a slice so its rhyme ids are 1,2,3,... in order of appearance."""
    out = list(slice_)
    seen: dict[int, int] = {}
    next_id = 1
    for i, x in enumerate(out):
        if x == 0:
            continue
        if x not in seen:
            seen[x] = next_id
            next_id += 1
        out[i] = seen[x]
    return out


def _slice(seq: List[int], length: int) -> List[List[int]]:
    return [list(seq[i:i + length]) for i in range(0, len(seq), length)]


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / float(len(a | b))


def _score_scheme(rhyme_ids: List[int], scheme_letters: str) -> float:
    """Score a candidate scheme against observed rhyme ids.

    The rhyme ids are sliced into windows the size of the scheme; each window
    is renumbered so 'a' = first new rhyme, 'b' = second, etc., and compared
    by Jaccard similarity over rhyme-pair edges. Windows that don't divide
    evenly are penalized.
    """
    target = scheme_to_nums(scheme_letters)
    target_edges = set(_scheme_to_edges(target))
    n = len(target)
    matches: list[float] = []
    leftover = 0
    for window in _slice(rhyme_ids, n):
        normed = _normalize_slice(window)
        if len(normed) != n:
            leftover += 1
        obs_edges = set(_scheme_to_edges(target[:len(normed)]))
        win_edges = set(_scheme_to_edges(normed))
        matches.append(_jaccard(obs_edges, win_edges))
    return (sum(matches) / len(matches) if matches else 0.0) - leftover


def match_rhyme_scheme(rhyme_ids: List[int]) -> Optional[dict]:
    """Find the named rhyme scheme that best fits a sequence of rhyme IDs.

    Args:
        rhyme_ids: list of integer rhyme group IDs, one per line. 0 = no rhyme.

    Returns:
        dict with keys ``name``, ``form`` (letter scheme), ``accuracy`` (Jaccard
        score), and ``candidates`` (top 5 alternatives). Returns ``None`` if
        ``rhyme_ids`` is empty.
    """
    if not rhyme_ids:
        return None
    scored = []
    for name, scheme in load_named_schemes():
        scored.append((name, scheme, _score_scheme(rhyme_ids, scheme)))
    scored.sort(key=lambda x: (-x[2], -len(x[0])))
    best_name, best_form, best_acc = scored[0]
    return {
        "name": best_name,
        "form": best_form,
        "accuracy": best_acc,
        "candidates": [(n, f, s) for n, f, s in scored[:5]],
    }


def compute_rhyme_ids(text, max_dist: float = 0.4, window: int = 4) -> List[int]:
    """Compute per-line integer rhyme IDs from a TextModel.

    For each line, find the closest other line within ±``window`` (default 4)
    by feature-edit rime distance. If that closest neighbor is within
    ``max_dist``, union the two lines into the same rhyme group. Lines whose
    closest neighbor is too far get ID 0 (no rhyme).

    Default ``max_dist=0.4`` catches Shakespeare's near-rhymes (knights/wights,
    eyes/days) without merging unrelated finals; tighten for stricter, loosen
    for slant rhyme.
    """
    lines = list(text.lines)
    n = len(lines)
    if n == 0:
        return []

    # Pairwise distances within window (symmetric)
    dist = [[None] * n for _ in range(n)]
    for i in range(n):
        for j in range(max(0, i - window), min(n, i + window + 1)):
            if i == j:
                continue
            if dist[i][j] is None:
                d = lines[i].rime_distance(lines[j], max_dist=None)
                dist[i][j] = dist[j][i] = d

    # Union-find: each line joins its closest neighbor if within threshold
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            # keep the smaller index as root for stable IDs
            if ra < rb:
                parent[rb] = ra
            else:
                parent[ra] = rb

    # For each line, identify its closest neighbor within window
    closest = [None] * n
    for i in range(n):
        candidates = [(dist[i][j], j) for j in range(n)
                      if i != j and dist[i][j] is not None]
        if candidates:
            candidates.sort()
            closest[i] = candidates[0]  # (dist, j)

    # Union mutual nearest neighbors below threshold; this avoids cascading
    # merges where A's closest is B, but B's closest is C
    rhymes = [False] * n
    for i in range(n):
        if closest[i] is None:
            continue
        d, j = closest[i]
        if d > max_dist:
            continue
        if closest[j] is not None and closest[j][1] == i:
            union(i, j)
            rhymes[i] = True
            rhymes[j] = True
        elif d <= max_dist / 2:  # very close: union even if not mutual
            union(i, j)
            rhymes[i] = True
            rhymes[j] = True

    # Assign group IDs in order of first appearance, skipping un-rhymed lines
    ids: List[int] = []
    root_to_id: dict[int, int] = {}
    next_id = 1
    for i in range(n):
        if not rhymes[i]:
            ids.append(0)
            continue
        root = find(i)
        if root not in root_to_id:
            root_to_id[root] = next_id
            next_id += 1
        ids.append(root_to_id[root])
    return ids
