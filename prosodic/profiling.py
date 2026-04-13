"""Benchmark prosodic on Shakespeare sonnets.

Usage:
    python -m prosodic.profiling          # run benchmarks, print markdown table
    python -m prosodic.profiling --json   # output JSON
"""

import time
import sys
import json
import numpy as np


SONNET_PATH = "corpora/corppoetry_en/en.shakespeare.txt"


def _time(fn, warmup=0, repeat=1):
    """Time a function, return min elapsed seconds."""
    for _ in range(warmup):
        fn()
    times = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        result = fn()
        times.append(time.perf_counter() - t0)
    return min(times), result


def _has_gpu():
    try:
        import torch
        return torch.backends.mps.is_available() or torch.cuda.is_available()
    except Exception:
        return False


def _gpu_name():
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.get_device_name(0)
        elif torch.backends.mps.is_available():
            return "Apple MPS"
    except Exception:
        pass
    return None


def _has_spacy():
    try:
        import spacy
        spacy.load("en_core_web_sm")
        return True
    except Exception:
        return False


def _clear_caches():
    """Clear in-memory caches so each benchmark starts fresh."""
    import prosodic
    from prosodic.langs.langs import Language
    lang = Language("en")
    if hasattr(lang, 'get_sylls_ipa_ll'):
        lang.get_sylls_ipa_ll.cache_clear()
    from prosodic.langs.langs import get_word
    get_word.cache_clear()
    # clear token2ipa cached_property so it reloads from disk
    lang.__dict__.pop('token2ipa', None)


def run_benchmarks(sonnet_path=SONNET_PATH, repeat=1):
    """Run benchmarks and return list of result dicts."""
    import prosodic
    from prosodic.parsing.meter import Meter
    from prosodic.parsing.vectorized import parse_batch_from_df

    results = []
    has_gpu = _has_gpu()
    has_syntax = _has_spacy()

    # Warm up espeak/caches with a throwaway call
    _ = prosodic.TextModel("hello world")

    # --- Init (TextModel construction) ---
    _clear_caches()
    elapsed, text = _time(
        lambda: prosodic.TextModel(fn=sonnet_path),
        repeat=repeat,
    )
    n_lines = len(text.lines)
    results.append({"step": "init", "time": elapsed, "lines": n_lines})

    # --- Parse (CPU) ---
    import prosodic.parsing.vectorized as vpmod
    orig_device = vpmod._torch_device
    vpmod._torch_device = None  # force CPU-only bounding
    meter = Meter()
    elapsed_parse_cpu, _ = _time(
        lambda: parse_batch_from_df(text._syll_df, meter),
        repeat=repeat,
    )
    results.append({"step": "parse_cpu", "time": elapsed_parse_cpu, "lines": n_lines})
    vpmod._torch_device = orig_device

    # --- Parse (GPU) ---
    if has_gpu:
        elapsed_parse_gpu, _ = _time(
            lambda: parse_batch_from_df(text._syll_df, meter),
            repeat=repeat,
        )
        results.append({"step": "parse_gpu", "time": elapsed_parse_gpu, "lines": n_lines})

    # --- Entity construction ---
    text._children_built = False
    text._children_data = []
    elapsed_ents, _ = _time(
        lambda: text._build_children(),
        repeat=1,  # can only build once
    )
    results.append({"step": "entities", "time": elapsed_ents, "lines": n_lines})

    # --- Syntax (if available) ---
    if has_syntax:
        _ = prosodic.TextModel("hello world", syntax=True)
        _clear_caches()
        elapsed_syn, text_syn = _time(
            lambda: prosodic.TextModel(fn=sonnet_path, syntax=True),
            repeat=repeat,
        )
        results.append({"step": "syntax_init", "time": elapsed_syn, "lines": n_lines})

    return results, {
        "n_lines": n_lines,
        "has_gpu": has_gpu,
        "gpu_name": _gpu_name(),
        "has_syntax": has_syntax,
    }


# v2 reference timings (master branch, Apple M1, measured 2026-04-13)
V2_INIT = 5.29
V2_PARSE = 72.97


def format_markdown(results, meta):
    """Format results as a comparison table."""
    r = {d["step"]: d["time"] for d in results}
    n = meta["n_lines"]

    init_v3 = r.get("init", 0) + r.get("entities", 0)
    parse_cpu_v3 = r.get("parse_cpu", 0)
    parse_gpu_v3 = r.get("parse_gpu")
    syntax_overhead = r.get("syntax_init", 0) - r.get("init", 0) if "syntax_init" in r else None

    rows = []

    def row(step, v2, v3):
        speedup = f"{v2/v3:.0f}x" if v2 and v3 and v3 > 0 else "—"
        v2s = f"{v2:.2f}s" if v2 else "—"
        v3s = f"{v3:.2f}s" if v3 else "—"
        return f"| {step} | {v2s} | {v3s} | {speedup} |"

    rows.append(row("Init (tokenize + pronunciations + entities)", V2_INIT, init_v3))
    rows.append(row("Parse (CPU)", V2_PARSE, parse_cpu_v3))
    if parse_gpu_v3:
        rows.append(row("Parse (GPU)", V2_PARSE, parse_gpu_v3))
    e2e_v2 = V2_INIT + V2_PARSE
    rows.append(row("**End-to-end (CPU)**", e2e_v2, init_v3 + parse_cpu_v3))
    if parse_gpu_v3:
        rows.append(row("**End-to-end (GPU)**", e2e_v2, init_v3 + parse_gpu_v3))
    if syntax_overhead is not None:
        rows.append(f"| + syntax (spaCy dep parse) | — | +{syntax_overhead:.2f}s | — |")

    lines = [
        f"Shakespeare sonnets ({n} lines). `python -m prosodic.profiling`\n",
        "| Step | v2 | v3 | Speedup |",
        "|---|---|---|---|",
        *rows,
    ]

    # batch-only note
    init_only = r.get("init", 0)
    if parse_gpu_v3:
        batch_total = init_only + parse_gpu_v3
        batch_speedup = e2e_v2 / batch_total
        lines.append(f"\nv3 without entity access (DF-only): **{batch_total:.1f}s** = **{batch_speedup:.0f}x faster**")

    return "\n".join(lines)


def format_json(results):
    """Format results as JSON."""
    return json.dumps(results, indent=2)


def main():
    import os
    os.environ["LOGURU_LEVEL"] = "ERROR"
    output_json = "--json" in sys.argv
    results, meta = run_benchmarks()
    if output_json:
        print(format_json(results))
    else:
        print(format_markdown(results, meta))


if __name__ == "__main__":
    main()
