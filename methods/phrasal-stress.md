# Phrasal stress in prosodic

How prosodic computes phrasal (sentence-level) prominence, where the
algorithm comes from, and how our implementation differs from its ancestors.
Code: `prosodic/texts/phrasal_stress.py`. Enabled with
`TextModel(txt, syntax=True)`.

## Linguistic background

Lexical stress tells you which syllable of *within* is strong; it says
nothing about whether *within* is prominent **in its sentence**. That
second, relational kind of prominence is the subject of metrical phonology's
founding work:

- **Chomsky & Halle (1968, SPE)** formulated the **Nuclear Stress Rule
  (NSR)**: in a phrase, primary stress falls on the rightmost stressable
  constituent — recursively, so sentence prominence cascades down through
  phrases. The **Compound Stress Rule (CSR)** is its mirror inside compound
  nouns: stress the *left* member (*TIME machine*, not *time MACHINE*).
- **Liberman & Prince (1977)** recast these rules relationally: constituents
  are strong or weak only *relative to their sisters*, represented in binary
  metrical trees, with the metrical **grid** as the derived rhythmic
  representation. A word's prominence is a function of how many weak nodes
  dominate it.
- **Hayes (1983, 1995)** developed the grid-based side of the theory —
  prosodic's `grid_str()` display (marks stacked over syllables by
  prominence level) is a Hayes-style grid.
- **Anttila and colleagues** (e.g. Anttila, Dozat, Galbraith & Shapiro
  2020) operationalized these theories at corpus scale to study English
  phrasal stress, rhythm in prose, and its interaction with meter — using
  Dozat's MetricalTree tool, the direct ancestor of this module.

## What Dozat's MetricalTree did

[MetricalTree](https://github.com/tdozat/Metrics) (Timothy Dozat, 2015)
computes Liberman–Prince prominence over Stanford CoreNLP parses:

1. **Tree**: a constituency parse, with dependency labels decorating
   preterminals.
2. **Lexical stress classes**: each word is scored 0 (stressed content
   word), −1 (unstressed function word), or −0.5 (**ambiguous**) using
   word lists (*it*; *this/that/these/those*), PTB tag lists (CC, PRP$, TO,
   UH, DT unstressed; MD, IN, PRP, WP$, PDT, WDT, WP, WRB ambiguous), and
   dependency-label lists (det, expl, cc, mark unstressed; cop, neg, aux,
   auxpass ambiguous). Punctuation and contracted clitics are NaN.
3. **Disambiguation ensemble**: ambiguous words are resolved three
   deterministic ways — all stressed; unstressed only if monosyllabic;
   all unstressed — and results are averaged. This is what makes the
   output *gradient* rather than categorical: an ambiguous monosyllable
   ends up with fractional prominence.
4. **NSR pass** (`set_pstress`): bottom-up through the tree; in each
   phrase, the rightmost child with pstress 0 stays strong and every other
   child is demoted to −1. Inside NN-sequences (compounds) the scan is
   inverted per the CSR: the rightmost noun is provisionally weak and the
   noun to its left is strong.
5. **Total stress** (`set_stress`): each word's cumulative prominence =
   its lexical stress + its preterminal pstress + the sum of pstress
   values of every phrase dominating it — a direct arithmetization of
   Liberman & Prince's "count the weak nodes above you."
6. **Normalization**: per sentence, min–max normalize to [0, 1], where
   1.0 is the sentence's nuclear stress. Two outputs per word:
   **pstress** (preterminal phrasal stress: strong/weak within the local
   phrase) and **tstress** (total cumulative stress: global sentence
   prominence).

[cadence](https://github.com/quadrismegistus/cadence) (archived 2026-07)
carried this implementation forward over Stanza constituency parses, with
one simplification: by default it substituted binary dictionary lexical
stress for the ambiguity ensemble.

## What prosodic does differently

Prosodic v3 deliberately has **no constituency parser** (no Stanza, no
torch model downloads); its `syntax=True` pipeline is spaCy
dependency-only. The port therefore runs Dozat's algorithm over
**head-projection trees derived from the dependency parse**: every word
projects a phrase whose ordered children are the projections of its
dependents plus its own preterminal.

Naive projection is *not* equivalent to constituency, and the differences
matter exactly where the NSR looks. Three topology rules (found by
differential testing, below) restore congruence:

1. **NP-internal prenominal modifiers join bare.** A dependent with no
   dependents of its own whose relation is in {det, amod, compound,
   nummod, predet, neg, aux, auxpass} sits in its head's phrase as a bare
   preterminal — matching the flat Penn NP `(NP (DT the) (JJ quick)
   (NN fox))`, so NSR demotion reaches the adjective directly.
2. **Arguments always project**, even as single words — constituency wraps
   them (`NP(Jack)`, `WHADVP(When)`), and that wrapper *shields* the
   preterminal: when a subject phrase is demoted, the demotion lands on
   the phrase node, and the word's own pstress (where the ambiguity
   ensemble lives) survives. Notably `poss` is **not** in the bare set: a
   possessor is an inner NP (`NP(NP(Beauty 's) rose)`), and bare-joining
   it would wrongly trigger the compound rule (*BEAUTY'S rose*).
3. **Noun heads with right-side complements get an inner core.** For
   `the house that Jack built`, constituency gives
   `NP(NP(the house) SBAR)`: the relative clause wins the NSR, but the
   demotion hits the inner NP node and *house* keeps its preterminal
   strength. The projection replicates this by wrapping left material +
   head in an inner node whenever an NN-headed phrase has right
   dependents.

The compound rule needs no special handling beyond rule 1: `compound`
dependents are typically leaves, so they sit as bare NN preterminals
adjacent to the head noun — exactly the NN-sequence Dozat's scan expects.

Everything above the tree skeleton is ported faithfully: the lexical
stress classes, the 3-variant ensemble, the NSR/CSR scan (including its
break/skip idiosyncrasies), cumulative total stress, and per-sentence
min–max normalization. Output columns in `_syll_df`: `pstress`, `tstress`
(Float64, ∈ [0,1], NaN for punctuation and for sentences with no
variation), broadcast from words to their syllables.

### Validation

The port was cross-validated against cadence (Dozat's algorithm over
Stanza constituency, ambiguity ensemble replicated) on a 9-sentence
differential covering NSR baselines, compounds, ambiguous function words,
relative clauses, coordination, possessives, ditransitives, and PP
attachment (2026-07-05). Result: identical nuclear-stress placement on
9/9; identical orderings throughout; several sentences identical to two
decimals on every word. The differential caught two real bugs (the
shielding asymmetry behind topology rules 1–3, and `poss` in the bare
set) — the corrected, cross-validated values are pinned as unit tests in
`tests/test_phrasal_gradient.py`.

**One deliberate divergence**: in coordination (*dogs and cats*), Dozat's
flat-NP scan demotes non-final conjuncts to pstress −1; prosodic keeps
each conjunct's strength (both conjuncts carry accent in natural speech),
while tstress still ranks the final conjunct higher, matching the
reference ordering.

**Known limitations**: (a) attachment-height differences between spaCy
dependencies and constituency (e.g. fronted *When* sits higher as a
WHADVP than as an `advmod` edge) shift tstress magnitudes on a few words;
(b) whole-word possessive tokens (*Beauty's*) misparse in both spaCy and
Stanza when pre-tokenized — an input-level limitation; (c) the lexical
class lists are English-only.

## The two value systems, and what uses them

| | discrete `phrasal_stress` | gradient `pstress` / `tstress` |
|---|---|---|
| lineage | v3-native depth heuristic | Dozat MetricalTree port |
| values | 0 (root) … −6, Int | [0, 1] normalized, Float |
| computation | vectorized dep-tree depth + NSR/CSR sibling promotion | ensemble of NSR passes over projection trees |
| constraints | `w_prom`, `s_demoted` | `w_stress_p`, `s_unstress_p`, `w_stress_t`, `s_unstress_t` (cadence thresholds: prominent > 0, weak == 0) |
| grid | — | phrasal rows: word's primary syllable +1 level at tstress ≥ 0.5, +1 at nuclear |

All phrasal constraints are inert without `syntax=True`.

**Empirical caveat** (from the v3 MaxEnt experiments): on Shakespeare's
sonnets with a fixed `wswswswsws` target, phrasal constraints added no
accuracy over lexical stress. Phrasal prominence matters for **prose
rhythm** and **naturalness ranking** — cadence's research agenda — not
for fixed-template scansion.

## References

- Chomsky, N. & M. Halle (1968). *The Sound Pattern of English*.
- Liberman, M. & A. Prince (1977). On stress and linguistic rhythm. *LI* 8.
- Hayes, B. (1983). A grid-based theory of English meter. *LI* 14.
- Hayes, B. (1995). *Metrical Stress Theory*.
- Dozat, T. (2015). MetricalTree. github.com/tdozat/Metrics
- Anttila, A., T. Dozat, D. Galbraith & N. Shapiro (2020). Sentence stress
  in presidential speeches. In *Prosody in Syntactic Encoding*.
- Heuser, R. (2021–23). cadence. github.com/quadrismegistus/cadence
