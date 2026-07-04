import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
import numpy as np
from prosodic.parsing.vectorized import _unres_within_batch, _unres_across_batch
from prosodic.parsing.constraints import _word_boundary_vectorized

disable_caching()


def _rand_case(rng):
    S = int(rng.randint(1, 9)); N = int(rng.randint(1, 8)); L = int(rng.randint(1, 5))
    return dict(
        position_ids=np.sort(rng.randint(0, max(N, 1), (S, N)), axis=1).astype(np.int32),
        position_sizes=rng.randint(1, 3, (S, N)).astype(np.int32),
        word_ids=np.sort(rng.randint(0, max(N, 1), (L, N)), axis=1).astype(np.int32),
        heavy=rng.randint(0, 2, (L, N)).astype(bool),
        stressed=rng.randint(0, 2, (L, N)).astype(bool),
        func_word=rng.randint(0, 2, (L, N)).astype(bool),
        meter_vals=rng.randint(0, 2, (S, N)).astype(bool),
        S=S, N=N, L=L,
    )


def test_unres_within_matches_reference():
    rng = np.random.RandomState(0)
    for _ in range(40):
        c = _rand_case(rng); S, N, L = c["S"], c["N"], c["L"]
        got = _unres_within_batch(c["position_ids"], c["position_sizes"],
                                  c["word_ids"], c["heavy"], c["stressed"])
        exp = np.zeros((L, S, N), dtype=np.int8)
        for l in range(L):
            for j in range(1, N):
                for s in range(S):
                    in_pos = (c["position_ids"][s, j] == c["position_ids"][s, j - 1]
                              and c["position_sizes"][s, j] >= 2)
                    if in_pos and c["word_ids"][l, j] == c["word_ids"][l, j - 1] and \
                            (c["heavy"][l, j - 1] or not c["stressed"][l, j - 1]):
                        exp[l, s, j] = 1
        assert np.array_equal(got, exp)


def test_unres_across_matches_reference():
    rng = np.random.RandomState(1)
    for _ in range(40):
        c = _rand_case(rng); S, N, L = c["S"], c["N"], c["L"]
        got = _unres_across_batch(c["position_ids"], c["position_sizes"],
                                  c["word_ids"], c["func_word"], c["meter_vals"])
        exp = np.zeros((L, S, N), dtype=np.int8)
        for l in range(L):
            for j in range(1, N):
                for s in range(S):
                    in_pos = (c["position_ids"][s, j] == c["position_ids"][s, j - 1]
                              and c["position_sizes"][s, j] >= 2)
                    diff_word = c["word_ids"][l, j] != c["word_ids"][l, j - 1]
                    nbf = not (c["func_word"][l, j - 1] and c["func_word"][l, j])
                    if in_pos and diff_word and (c["meter_vals"][s, j] or nbf):
                        exp[l, s, j] = 1
        assert np.array_equal(got, exp)


def test_word_foot_matches_reference():
    rng = np.random.RandomState(2)
    for _ in range(40):
        c = _rand_case(rng); S, N, L = c["S"], c["N"], c["L"]
        f = {"L": L, "S": S, "N": N, "word_ids_raw": c["word_ids"],
             "position_ids": c["position_ids"]}
        got = _word_boundary_vectorized(f)
        exp = np.zeros((L, S, N), dtype=np.int8)
        for l in range(L):
            for j in range(1, N):
                for s in range(S):
                    wb = c["word_ids"][l, j] != c["word_ids"][l, j - 1]
                    fb = c["position_ids"][s, j] != c["position_ids"][s, j - 1]
                    if wb and not fb:
                        exp[l, s, j] = 1
        assert np.array_equal(got, exp)
