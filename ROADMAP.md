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
- **MetricalTree-proper phrasal stress** — ✅ gradient port shipped: Dozat's
  algorithm (lexical stress classes, 3-variant disambiguation ensemble, NSR
  with the noun-compound rule, cumulative total stress, per-sentence min-max
  norm) now runs over spaCy dep-projection trees and emits `pstress`/
  `tstress` ∈ [0,1] columns with `syntax=True`; the grid consumes `tstress`
  for phrase-level rows (nuclear stress = tallest column). Remaining
  refinements: constituency-backed trees (benepar/Stanza as an optional
  extra) if dep projections prove too coarse; dictionary-derived lexical
  stress classes (cadence's own refinement). **Caveat** stands: phrasal
  constraints added zero accuracy for fixed-template verse — this is for
  prose rhythm and naturalness ranking.
- **Phrasal variants of stress constraints** (`*_p`, `*_t`) — ✅ shipped:
  `w_stress_p`/`s_unstress_p` (pstress) and `w_stress_t`/`s_unstress_t`
  (tstress), cadence-threshold semantics, inert without `syntax=True`.
  Remaining: `w_peak_p`/`s_trough_p` need cadence's pstrength (local
  peak/valley) feature, not yet ported.
- **Multi-engine comparison** — never shipped in cadence (vestigial `ENGINE`
  constant); the idea survives in its `notebooks/engines.ipynb` scratch
  harness. Low priority unless a second engine (e.g. MetricalTree-proper)
  actually lands.
- **Reference notebooks** — before relying on memory of the algorithms, see
  cadence's `notebooks/test-bounding.ipynb` (cleanest statement of the
  harmonic-bounding algorithm) and `engines.ipynb` (cross-engine harness).

## Parser

- ✅ **Vectorize `unres_within`/`unres_across`** — already done (commit
  932d3df, audit sprint); the item here was stale.
- ✅ **Bounding elite pre-screen** — candidates dominated by one of the
  K=16 best-total candidates are eliminated in O(K·S) before the exact
  O(S²) kernel runs on the survivors (mean ~3 of ~180 on the sonnets);
  byte-identical by transitivity of dominance. CPU parse 9.5s → 1.9s,
  now ≈ GPU. This also moots the former **GPU/CPU dispatch** item: the
  exact kernel's workload is tiny either way, and the GPU is no longer
  needed for parsing at all.
- **Scansion prefiltering** — skip scansions where strong positions wildly
  mismatch stressed syllables before full constraint evaluation. (Less
  urgent post-screen: profile before bothering.)
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
