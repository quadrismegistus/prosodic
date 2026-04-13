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
    results.append({
        "step": "Init (tokenize + get_word + syll_df)",
        "time": elapsed,
        "lines": n_lines,
    })

    # --- Parse (CPU) ---
    import prosodic.parsing.vectorized as vpmod
    orig_device = vpmod._torch_device
    vpmod._torch_device = None  # force CPU-only bounding
    meter = Meter()
    elapsed_parse_cpu, _ = _time(
        lambda: parse_batch_from_df(text._syll_df, meter),
        repeat=repeat,
    )
    results.append({
        "step": "Parse (CPU)",
        "time": elapsed_parse_cpu,
        "lines": n_lines,
    })
    vpmod._torch_device = orig_device

    # --- Parse (GPU) ---
    if has_gpu:
        elapsed_parse_gpu, _ = _time(
            lambda: parse_batch_from_df(text._syll_df, meter),
            repeat=repeat,
        )
        results.append({
            "step": f"Parse (GPU: {_gpu_name()})",
            "time": elapsed_parse_gpu,
            "lines": n_lines,
        })

    # --- Entity construction ---
    # Clear cached children so we measure construction
    text._children_built = False
    text._children_data = []
    elapsed_ents, _ = _time(
        lambda: text._build_children(),
        repeat=1,  # can only build once
    )
    results.append({
        "step": "Build entities (lazy, on first .lines access)",
        "time": elapsed_ents,
        "lines": n_lines,
    })

    # --- Syntax (if available) ---
    if has_syntax:
        # warm spacy model
        _ = prosodic.TextModel("hello world", syntax=True)
        _clear_caches()
        elapsed_syn, text_syn = _time(
            lambda: prosodic.TextModel(fn=sonnet_path, syntax=True),
            repeat=repeat,
        )
        results.append({
            "step": "Init + syntax (spaCy dep parse)",
            "time": elapsed_syn,
            "lines": n_lines,
        })

    # --- v2 reference (master branch, measured offline) ---
    results.append({
        "step": "v2 reference (init + parse, no GPU)",
        "time": 81.4,
        "lines": n_lines,
        "note": "pre-v3 branch, entity-based parser",
    })

    return results


def format_markdown(results):
    """Format results as a markdown table."""
    lines = []
    lines.append("| Step | Time | Lines/sec |")
    lines.append("|---|---|---|")
    for r in results:
        t = r["time"]
        n = r["lines"]
        lps = n / t if t > 0 else float('inf')
        lines.append(f"| {r['step']} | {t:.2f}s | {lps:,.0f} |")
    return "\n".join(lines)


def format_json(results):
    """Format results as JSON."""
    return json.dumps(results, indent=2)


def main():
    import os
    os.environ["LOGURU_LEVEL"] = "ERROR"
    output_json = "--json" in sys.argv
    results = run_benchmarks()
    if output_json:
        print(format_json(results))
    else:
        print(format_markdown(results))


if __name__ == "__main__":
    main()
