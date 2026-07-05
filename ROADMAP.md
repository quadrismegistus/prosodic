# Prosodic Roadmap

Planned and potential work, roughly ordered by value within each section.
Items graduate to CLAUDE.md's Done list when they ship. History: `analysis/`
absorbed [poesy](https://github.com/quadrismegistus/poesy) (now a thin shim
over prosodic ≥3.5); [cadence](https://github.com/quadrismegistus/cadence)
(prose-rhythm fork, archived 2026-07) was superseded by v3's `syntax=True`
prose handling — everything it did that prosodic doesn't is preserved below.

## From cadence

Capabilities unique to cadence at archive time (verified by full-repo audit +
live smoke test, 2026-07-05). Portable, in rough order of value-per-effort:

- **Hayes-style metrical grid view** — cadence's `sent.grid()` renders a
  plotnine stress grid over syllables; small and pedagogically excellent.
  ✅ API shipped (`analysis/grid.py`: `line.grid_str()` / `grid_df()` /
  `grid_plot()`, works on both parse paths). Remaining: render the grid in
  the web app's Line View tab (see "Parse table design polish" below), and
  a phrasal-prominence row once continuous phrasal stress exists (see
  MetricalTree item — the grid API takes extra rows without change).
- **nltk.Tree / svgling export** — cadence's metrical tree is an `nltk.Tree`
  subclass, so svgling SVG rendering came free. If v3 exports its
  phrasal-stress structure as `nltk.Tree` (`to_nltk_tree()`), notebook SVG
  trees are ~free. Small.
- **MetricalTree-proper phrasal stress** — Dozat's constituency-based
  algorithm (over Stanza constituency parses) with continuous, min-max
  normalized `pstress`/`tstress` per word, Anttila-style. v3's spaCy dep-tree
  `phrasal_stress` is a different lineage: discrete depth values, no
  constituency. The `libermanprince`/`maxent2` branches in the cadence repo
  hold an NSR-over-constituency prototype (`parsers/rhythm.py`). Substantive
  effort. **Caveat**: on Shakespeare sonnets with a fixed `wswswswsws`
  target, phrasal constraints added zero accuracy over lexical stress — this
  matters for prose rhythm and naturalness ranking, not fixed-template verse.
- **Phrasal variants of stress constraints** (`*_p`, `*_t`) — cadence scored
  w/s violations against *phrasal* stress values as systematic counterparts
  to every lexical stress constraint. v3 has only two bespoke phrasal
  constraints (`w_prom`, `s_demoted`) thresholded on dep-tree depth.
  Depends on the item above for the continuous values to be meaningful.
- **Multi-engine comparison** — never shipped in cadence (vestigial `ENGINE`
  constant); the idea survives in its `notebooks/engines.ipynb` scratch
  harness. Low priority unless a second engine (e.g. MetricalTree-proper)
  actually lands.
- **Reference notebooks** — before relying on memory of the algorithms, see
  cadence's `notebooks/test-bounding.ipynb` (cleanest statement of the
  harmonic-bounding algorithm) and `engines.ipynb` (cross-engine harness).

## Parser

- **Scansion prefiltering** — skip scansions where strong positions wildly
  mismatch stressed syllables before full constraint evaluation.
- **Vectorize `unres_within`/`unres_across`** — the last two constraints
  still run per-line Python loops in `evaluate_constraints_batch`; liftable
  to numpy with word-boundary masking.
- **GPU/CPU dispatch optimization** — CPU wins for n<11 single-line, GPU for
  n≥11 or batched; auto-dispatch by total work per nsylls group.
- **Lazy phoneme construction** — Syllable creates Phoneme objects eagerly;
  could defer to IPA-on-demand.
- **Ternary meter identification** — `meter.fit()` works for binary
  iambic/trochaic but anapestic/dactylic needs ternary-aware constraints or
  dynamic template matching.

## Analysis & display

- **Parse table design polish** — grid stress view over syllables in the web
  app (see the cadence grid item above; these are the same project).
- **Rhyme detection threshold tuning** — `RHYME_MAX_DIST=0` default is
  binary; gradient `rime_distance` works and `analysis/` uses the calibrated
  0.35 (Walker 1775, F1-optimal), but there's no calibrated "slant rhyme"
  band for the user-facing default.

## Languages

- **German (Blankvers)** — planned validation of the "flexible languages"
  claim; rule-based path like Finnish.
- **Esperanto** — community-requested (issue #36); phonemic orthography +
  fixed paroxytonic stress make it an easy `get_sylls_ll_rule()` language.

## Infrastructure

- **PyPI Trusted Publishing** — migrate `release.yml` off the long-lived
  `PYPI_API_TOKEN` secret to OIDC (`pypa/gh-action-pypi-publish` +
  `id-token: write`), as poesy 0.4.0 already does. Needs a one-time trusted
  publisher added on PyPI for prosodic first.
