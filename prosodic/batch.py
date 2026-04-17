"""Batch parsing: parse many texts to disk via ``text.save()``.

Typical use:

    import prosodic
    items = [(tid, open(path).read()) for tid, path in corpus]
    prosodic.parse_corpus(items, "out/", n_workers=4, device='cpu')

Each text is saved to ``{out_dir}/{id}/`` as ``syll.parquet`` + ``parsed.parquet``
+ ``meta.json``. Reload via ``prosodic.TextModel.load({out_dir}/{id})``.
"""

import os
import sys
import traceback
from tqdm import tqdm


_SENTINEL = "meta.json"  # last file written by TextModel.save()


def _resolve_device(device):
    if device not in ('auto', 'cpu', 'gpu'):
        raise ValueError(f"device must be 'auto', 'cpu', or 'gpu'; got {device!r}")
    if device == 'auto':
        import prosodic.parsing.vectorized as vp
        return 'gpu' if vp.get_device() is not None else 'cpu'
    return device


def _set_device(device):
    """Pin the torch device for this process."""
    import prosodic.parsing.vectorized as vp
    if device == 'cpu':
        vp._torch_device = None
        vp._torch_checked = True
    elif device == 'gpu':
        dev = vp._get_torch_device()
        if dev is None:
            raise RuntimeError("No GPU available (neither CUDA nor MPS)")
        vp._torch_device = dev
        vp._torch_checked = True


def _normalize_item(item):
    if isinstance(item, dict):
        return str(item['id']), item.get('txt') or item.get('text') or ''
    tid, txt = item
    return str(tid), txt


def _parse_one(args):
    tid, txt, out_dir, resume, text_kwargs, meter_kwargs = args
    text_dir = os.path.join(out_dir, tid)
    if resume and os.path.exists(os.path.join(text_dir, _SENTINEL)):
        return (tid, 'skipped', None)
    try:
        import prosodic
        t = prosodic.TextModel(txt, **(text_kwargs or {}))
        t.parse(**(meter_kwargs or {}))
        t.save(text_dir)
        t.cleanup()
        return (tid, 'done', None)
    except Exception as e:
        return (tid, 'failed', f"{type(e).__name__}: {e}\n{traceback.format_exc()}")


def _init_worker(device):
    _set_device(device)


def parse_corpus(
    items,
    out_dir,
    *,
    n_workers=1,
    device='auto',
    resume=True,
    progress=True,
    text_kwargs=None,
    meter_kwargs=None,
    on_error='log',
    total=None,
):
    """Parse many texts and save each to ``{out_dir}/{id}/``.

    Returns a dict with ``n_done``, ``n_skipped``, ``n_failed``, ``errors``
    (list of ``(id, traceback)``).

    GPU is single-process — ``device='gpu'`` forces ``n_workers=1``.
    On CPU with many cores, ``n_workers=N`` parallelizes across texts.
    """
    if on_error not in ('log', 'raise'):
        raise ValueError(f"on_error must be 'log' or 'raise'; got {on_error!r}")

    resolved = _resolve_device(device)
    if resolved == 'gpu' and n_workers > 1:
        print(
            "[parse_corpus] GPU mode is single-process; forcing n_workers=1.",
            file=sys.stderr,
        )
        n_workers = 1

    os.makedirs(out_dir, exist_ok=True)
    _set_device(resolved)  # also applies to main process for serial mode

    def _iter_args():
        for item in items:
            tid, txt = _normalize_item(item)
            yield (tid, txt, out_dir, resume, text_kwargs, meter_kwargs)

    stats = {'n_done': 0, 'n_skipped': 0, 'n_failed': 0, 'errors': []}

    def _handle(res):
        tid, status, err = res
        if status == 'done':
            stats['n_done'] += 1
        elif status == 'skipped':
            stats['n_skipped'] += 1
        else:
            stats['n_failed'] += 1
            stats['errors'].append((tid, err))
            if on_error == 'raise':
                raise RuntimeError(f"parse_corpus failed on {tid}:\n{err}")
            print(
                f"[parse_corpus] FAILED {tid}: {err.splitlines()[0]}",
                file=sys.stderr,
            )

    if n_workers <= 1:
        it = _iter_args()
        if progress:
            it = tqdm(it, total=total, desc='parse_corpus')
        for args in it:
            _handle(_parse_one(args))
    else:
        import multiprocessing as mp
        ctx = mp.get_context('spawn')  # safer on macOS than fork
        with ctx.Pool(
            n_workers,
            initializer=_init_worker,
            initargs=(resolved,),
        ) as pool:
            it = pool.imap_unordered(_parse_one, _iter_args(), chunksize=1)
            if progress:
                it = tqdm(it, total=total, desc='parse_corpus')
            for res in it:
                _handle(res)

    return stats
