# Prosodic Repository Audit

**Generated:** 2026-07-04
**Scope:** Full repo — parsing core, text/word/language layer, web app + deployment, packaging/CI/hygiene.
**Method:** Four parallel deep-read audits, each finding traced to source. Items marked **✓ verified** were reproduced by executing code in `.venv` (Python 3.10) or by direct static confirmation. Items marked *(traced)* are confirmed by reading the code path but not separately executed.

This is a working document for successive sessions. Each finding has: a checkbox, `file:line`, severity, verification status, a concrete failure scenario, and a suggested fix. Check items off as they land. Nothing here has been fixed yet.

---

## How to use this file

- **Start with the "Fix today" cluster** below — all small, all verified, several affect the live site.
- Each item is independently actionable; you don't need to re-run the audit to work one.
- After fixing, tick the box and add the commit/PR ref inline.
- Re-verify with the reproduction snippet given (most findings include one).
- The full findings are grouped by subsystem after the priority cluster.

---

## Progress log

**FINAL — wave 4 + wrap-up (2026-07-04):** vectorized the last per-line constraint loops C18/C19 (#110, byte-identical), parse-cache/force/meter.fit correctness T4/C10 (#111), cheap espeak discovery T15 (#109), CI release-tag + secrets + stop stale-docs R9/R10 (#101/#108), langdetect seeded (deterministic, fixes flaky CI). **Consciously deferred (documented, not force-fit):** C11/F9 zone-aware bounding (narrow: MaxEnt zone_weights only, 0/14 measured conflicts, behavior change across 5 bounding call sites); C16/C17 entity constraint reference impls (affect only manually-built Parse objects, not the vectorized parser). Every HIGH/MED finding and all verification-surfaced correctness bugs are done.


**Update — wave 2 landed (2026-07-04):** MaxEnt gradient/alignment/prose C2–C4 (#94), dead-code removal ~2208 lines D1/D2/T19 (#92), small robustness W9/W10/C7 (#93), spaCy phrasal-stress batching T18 (#95). Remaining items mostly touch files in open PRs (imports.py, texts.py, vectorized.py, api.py, .github, pyproject) and are queued behind those merges to avoid conflicts. Note: Agent flagged imports.py:72-73 `PATH_MTREE` still references the deleted metricaltree dir — clean when imports.py is next touched (D3).


**2026-07-04, session 2 — fix-today cluster landed (uncommitted, working tree).**
- ✅ **P1** path traversal — `web/api.py` `serve_frontend` now resolves `realpath` and rejects anything outside the static root (falls through to SPA index). Verified: `%2e%2e%2f` probes no longer leak; legit assets + SPA routes still serve; 11/11 fast web tests pass.
- ✅ **P2 (high-value subset)** — removed `@cache` from `TextModel.parse` (fixes `parse(constraints=[list])` `TypeError` + TextModel is now GC'd after parse, verified via weakref); made the four pronunciation/vocab caches unbounded via `@cache(maxsize=None)` (`get_word`, `get_sylls_ipa_ll`, `get_sylls_text_l`, `syllabify_ipa`) — fixes the >128-word espeak/syllabify thrash. **Deferred (see P2-remainder below).**
- ✅ **P4** `wheeel`→`wheel`, ✅ **R2** MANIFEST prune, ✅ **R3** codecov token removed (⚠️ user must rotate + add `CODECOV_TOKEN` secret), ✅ **R6** pyproject metadata, ✅ **R7/R8** requirements/dev-dep dedup + add `requests`/`tqdm`, ✅ **R12** deleted `deployment/` — all via a parallel Sonnet agent.
- ✅ **R4/T11** removed the two hardcoded `sys.path.insert('/Users/.../hashstash')` lines from `imports.py` (hashstash is pip-installed; the dev paths didn't exist). Verified `import prosodic` still works.
- ✅ **P5** all-punctuation crash — `vectorized.py` guards empty `f0_line_s`; `TextModel('...').parse()` now returns 0 lines cleanly.
- Regression check: `test_parsing.py` + `test_v3.py` = 72 passed; fast web tests = 11 passed.

**Update — P3/F1 landed in PR #90** (`fix-parse-path-unification`, off master): `parse_batch` now routes through `evaluate_constraints_batch`, so the entity/web path evaluates all constraints; `evaluate_constraints` deleted; `test_entity_path_evaluates_all_constraints` added. Verified byte-identical to the DF path on variant-stable lines.

**Deferred deliberately (own PRs):**
- ~~**P3 / F1** unify the two parse paths~~ — **DONE (PR #90).**
- **P2-remainder:** (a) the global `@cache = lru_cache(maxsize=128)` alias footgun in `imports.py:28` still stands — bare `@cache` on *entity* methods (`wordform.py:147`, `syllables.py:236`, `wordtokenlist.py:210`, `lines.py:138`) is left at 128 on purpose (bounded = safe; making them unbounded risks per-instance leaks — needs a real audit). (b) `force=True` is still a no-op on cache hit (`parse_iter` / meter-level, C10/T4) — separate fix.

---

## 🔴 Fix-today cluster (verified, high blast radius)

- [x] **P1. Path traversal on the live site.** `prosodic/web/api.py:1038` (`serve_frontend`). ✓ verified.
  The catch-all `os.path.join(STATIC_BUILD_DIR, path)` has no containment check. Starlette percent-decodes the URL, so `%2e%2e%2f` escapes the static dir.
  Repro: `TestClient(app).get('/%2e%2e%2fapi.py')` → 200 with source; enough `../` reaches `/etc/passwd`.
  **Fix:** replace the hand-rolled handler with `app.mount("/", StaticFiles(directory=STATIC_BUILD_DIR, html=True))` (enforces containment), or add the `os.path.realpath(fp).startswith(realpath(STATIC_BUILD_DIR)+os.sep)` guard used in `read_corpus`.

- [x] **P2. `@cache` is `lru_cache(maxsize=128)`, not `functools.cache`.** `prosodic/imports.py:28`. ✓ verified.
  `from functools import lru_cache as cache` + bare `@cache` = 128-entry LRU (not unbounded). Ripples everywhere:
  - `t.parse(constraints=['w_peak'])` → `TypeError: unhashable type: 'list'` (LRU can't hash kwargs).
  - `@cache` on `TextModel.parse` (`texts.py:234`) pins up to 128 fully-parsed TextModels (memory leak in `parse_corpus`); `force=True` becomes a no-op after first call.
  - Corpora with >128 distinct words thrash `get_word`, re-run espeak, and append dup rows to `~/prosodic_data/data/en_cache.tsv`.
  **Fix:** decide per-callsite. Use an unbounded plain dict cache for `get_word`/`get_sylls_ipa_ll` (entries are tiny). Remove `@cache` from `TextModel.parse` entirely (it already caches results in `_parse_results`); this also fixes the list-constraints crash and `force`.

- [x] **P3. Web parse path silently ignores 8 of 15 constraints.** (PR #90) `prosodic/web/api.py` (all endpoints) → `prosodic/parsing/vectorized.py:584` (`evaluate_constraints`). *(traced + subagent-reproduced)*
  `parse_batch` (entity path, used by every web endpoint) calls a 7-constraint if/elif evaluator with no dispatch to `cfunc.vectorized`. `clash`, `lapse`, `w_heavy`, `s_light`, `s_func`, `word_foot`, `w_prom`, `s_demoted` → all-zero columns. Meter tab exposes exactly these.
  Subagent repro: same line gives `lapse=464, s_func=356` via `parse_batch_from_df` but `0, 0` via `parse_batch`.
  **Fix:** route `parse_batch` through `evaluate_constraints_batch` (with L=1) and delete `evaluate_constraints`. (This is the "unify the two parse paths" improvement — see Features.)

- [x] **P4. CI installs typosquat package `wheeel`.** `.github/workflows/unit-tests.yml:40`, `latest-release.yml:51`. ✓ verified live on PyPI (HTTP 200).
  `pip install -U pip wheeel` (typo for `wheel`) runs on every CI run, in the pipeline holding `PYPI_API_TOKEN` + SSH deploy keys. Arbitrary-code supply-chain exposure.
  **Fix:** `wheeel` → `wheel` in both files.

- [x] **P5. All-punctuation input crashes `.parse()`.** `prosodic/parsing/vectorized.py:54`. ✓ verified.
  `np.diff(f0_line_s, prepend=f0_line_s[0]-1)` indexes an empty array when no non-punc form-0 rows exist.
  Repro: `TextModel('...').parse()`, `'!!!'`, `'. . .'` → `IndexError: index 0 is out of bounds for axis 0 with size 0`. On the deployed API this is a 500.
  **Fix:** early-return empty `results` when `len(f0_line)==0`.

---

**Update — W2–W8 landed in PR #91** (`harden-web-app`, off master): XSS escaping at all `{@html}` sinks, event-loop offload for `/api/parse/stream`, bounded LRU text cache + per-text parse lock (concurrency), 500K-char input cap, security-headers middleware (CSP/nosniff/frame), corpora separator fix, SSE error events. Remaining: W9 (client.py error detail), W10 (cli os.system).

## Web app & deployment (`prosodic/web/`, `client.py`, `cli.py`, `deploy/`)

Publicly deployed at https://prosodic.app — security-relevant. No auth (intentional, public tool); no CORS middleware (safe same-origin default — not a finding).

- [x] **W1. Path traversal** — see **P1**. `api.py:1038`. HIGH. ✓
- [x] **W2. `parse_stream` blocks the event loop.** `api.py:665`; `deploy/prosodic.service:16`. MED. *(traced)*
  `parse_stream` is `async def` but calls sync CPU-bound `get_text()` / `_parse_and_build_rows()` directly (no `run_in_threadpool`). systemd runs uvicorn with no `--workers` → single loop. One large parse freezes the whole site.
  **Fix:** `await anyio.to_thread.run_sync(...)` for the parse; add workers + a concurrency cap.
- [x] **W3. XSS: user text embedded unescaped, rendered via `{@html}`.** `api.py:37` (`_render_slot`), `195` (`_raw_linepart_html`), `235`; sinks `ParseResults.svelte:244`, `LineViewTab.svelte:146`. MED. ✓
  `unit.txt` interpolated into HTML with no escaping. Inline words are fragmented (defuses most tags), but the **prose fallback** emits a linepart's raw text contiguously. Repro: an oversized (>18-syll, no phrase punctuation) line with `<svg onload=alert\`1\`>` produces the executable tag intact in `parse_html`. Self-XSS today; stored/reflected the moment a share link exists.
  **Fix:** `html.escape()` every `unit.txt`/`wt.txt` before interpolation.
- [x] **W4. Unbounded `_text_cache` + shared-mutable TextModel.** `api.py:24,30,410,971`. MED. *(traced)*
  Cache keyed by `(text, kwargs)`, never evicted → memory DoS. Worse: `get_text()` returns a *shared* TextModel; parsing writes results onto its line entities. Two concurrent `/api/parse` on the same text (e.g. the default Sonnet 1) with different weights clobber each other → a user can receive another user's scansion.
  **Fix:** bound the cache (LRU/size cap); don't store per-request parse state on the shared object (parse into request-local structures, or key cache by meter).
- [x] **W5. No server-side parse timeout or input-size guard.** `api.py:23` (`linelim=15000`). MED. *(traced)*
  `linelim` caps line count only — no per-line/char cap, no timeout. The Settings `parse_timeout` is never sent to the backend or enforced. Combined with W2, a few max-size requests pin the CPU.
  **Fix:** `asyncio.wait_for` around a threadpool parse; cap total syllables/chars; plumb `parse_timeout` through.
- [x] **W6. Corpora path check lacks trailing separator.** `api.py:343`. LOW. *(traced)*
  `startswith(corpora_dir)` without `os.sep` — a sibling dir like `corpora-secret` passes. No such sibling today; guard is subtly wrong. **Fix:** compare against `corpora_dir + os.sep`, use `os.path.realpath`.
- [x] **W7. nginx/deploy hardening gaps.** `deploy/nginx-prosodic.conf`. LOW.
  No `limit_req`/`limit_conn`; no `client_max_body_size` (relies on nginx 1 MB default); no CSP / `X-Content-Type-Options`; `proxy_read_timeout 300s` lets one request hold a connection 5 min (amplifies W2/W5). `prosodic.service` is otherwise good (non-root, `NoNewPrivileges`, `ProtectSystem=strict`, `PrivateTmp`). **Fix:** add a rate-limit zone + CSP header.
- [x] **W8. SSE swallows mid-stream errors.** `api.py:686`; `api.js:35`. LOW.
  If the parse raises after headers are sent, the generator dies with no `{'phase':'error'}` event; client `meta` stays null, UI hangs. **Fix:** wrap generator body in try/except, `yield sse({'phase':'error',...})`.
- [x] **W9. (PR #93) client.py mismatches.** LOW.
  `client.py:66,75` `raise_for_status()` discards the FastAPI `{"detail":...}` message → opaque remote errors. `client.py:294` `RemoteText.parse()` hardcodes `is_bounded=False` for all `/api/parse` rows, so `line.parses.bounded` is always empty on that path (only `parse_lines()` populates bounded).
- [x] **W10. (PR #93) `cli.py:40` `os.system(f'ipython -i -c "{imps}"')`.** LOW (not exploitable — `imps` is constant). Prefer `subprocess.run([...])`.

---

## Parsing core (`prosodic/parsing/`)

- [ ] **C1. Missing 8 constraints in entity path** — see **P3**. `vectorized.py:584`. HIGH.
- [x] **C2. (PR #94) MaxEnt gradient wrong for unmatched lines.** `maxent.py:315`. HIGH. ✓ (subagent numeric repro)
  For lines with `observed.sum()==0` (annotation matched no candidate scansion), LL term is 0 but gradient computes `-(0 - probs)@viols ≠ 0`. Analytic `[-0.100,-0.205]` vs finite-diff `[-0.500,-0.300]`. Fitting `wswswswsws` on a sonnet leaves several lines unmatched, each pushing weights → −∞ (checked only by regularization/bounds).
  **Fix:** exclude `obs_sum==0` lines in `_precompute`, or use `diff = observed - obs_sum[:,None]*probs`.
- [x] **C3. (PR #94) MaxEnt line/text misalignment when a line is dropped.** `maxent.py:142`. HIGH. ✓
  Maps parsed lines to input strings by position over `sorted(results.keys())`, but `parse_batch_from_df` omits <2-syllable lines (`vectorized.py:65`). Repro: a short line shifts every subsequent label → annotations matched to wrong lines. **Fix:** carry `line_num` through; map via the text's own line index.
- [x] **C4. (PR #94) `meter.fit()` / MaxEntTrainer crashes on any oversized (prose) line.** `maxent.py:178`. HIGH. ✓
  Accesses `lpl._all_viols`, but oversized lines get a plain `ParseList([])` (`vectorized.py:122`). `trainer.load_text(text_with_19syll_line, ...)` → `AttributeError: _all_viols`. **Fix:** skip results without `_all_viols`.
- [ ] **C5. All-punctuation DF parse crash** — see **P5**. `vectorized.py:54`. HIGH. ✓
- [ ] **C6. Bounding memory blowup near the syllable cap.** `vectorized.py:872`. HIGH/MED. *(traced)*
  Pairwise bounding materializes `(L,S,S,C)`. At nsylls=18, S≈8362 → ~0.98 GB (GPU int16) / ~3.9 GB (numpy int64) *per non-perfect line*, one allocation × L. Perfect-parse shortcut masks this for verse; prose lineparts at 16–18 sylls rarely parse perfectly. Even 10-syll corpora: 10K non-perfect lines ≈ 4.4 GB in one tensor.
  **Fix:** chunk over L with a memory budget; tile S×S for n≥16. (Also unblocks raising `MAX_SYLL_IN_PARSE_UNIT` past 18 — S grows ~1.62×/syllable.)
- [x] **C7. (PR #93) `text.parse().best_parses` crashes on any unparseable line.** `parselists.py:674`. MED. ✓
  `best_parse=None` appended to `ParseList`, whose `append` raises `ValueError: parse must be a Parse object`. **Fix:** filter Nones.
- [ ] **C8. Single-syllable lines silently vanish from parse results.** `vectorized.py:65`. MED. *(traced)*
  Skipped with no placeholder; `text.parse()` yields fewer entries than lines. Root cause of C3.
- [ ] **C9. DF-path ambiguity explores only "diagonal" form combos.** `vectorized.py:90`. MED. *(traced, structural)*
  Builds `max_fi+1` variants (each word at form *fi* else form 0) vs the entity path's `itertools.product` (`wordtokenlist.py:84`). A line with two 1-or-2-syllable words never evaluates cross combos (e.g. fire=2syll + heaven=1syll = 10 syllables). Natural-line probes happened to agree, but divergence is structural.
- [x] **C10. (#111) `meter.fit()` doesn't change `meter.key` → stale cached parses.** `meter.py:122`. MED. ✓
  `zones`/`zone_weights` stored as instance attrs, not in `_attrs`, so the key hash is unchanged; `texts.py:276` caches by `(meter.key, combine_by)` and ignores `force` on hit → parse→fit→re-parse returns pre-fit results.
- [ ] **C11. Zone-weighted scoring inconsistent with unweighted bounding.** `vectorized.py:952`. MED (theoretical). *(traced)*
  `best_parse` picked among unbounded only, but bounding uses per-constraint totals; under zone weights a "bounded" scansion in a low-weight zone can be the true argmin. Trainer scores over ALL scansions (incl. bounded); parse-time excludes them. 0/14 conflicts observed on a fitted sonnet.
  **Fix (paired):** zone-aware bounding — compute dominance on zone-split sums `(S, C·Z)` when `zone_weights` active.
- [ ] **C12. Regularization docs backwards + inconsistent defaults.** `maxent.py:99` vs `:341`. MED.
  Implements `w²/(2·reg)` (reg = Gaussian variance: higher = *less* shrinkage); docstring says "higher = more shrinkage". `MaxEntTrainer` defaults 1.0 (strong), `Meter.fit` uses 100.0.
- [ ] **C13. Ambiguous-form selection ignores zone weights.** `vectorized.py:256`. MED. *(traced)*
  Ranks form variants with flat weights even when `zone_weights` active → chosen pronunciation can differ from what the fitted scorer prefers.
- [ ] **C14. Dead code.** LOW. `prefilter_scansions` (`vectorized.py:522`, never called), `build_parses` (`vectorized.py:1256`), `Meter.get_pos_types` (`meter.py:83`), `is_strong_pos.ndim>0` else-branch (`vectorized.py:760`, ndim always 2), `NUM_GOING` (`meter.py:9`), unused `force` param in `parse_text`.
- [ ] **C15. `ParseSlot.position` defined twice.** `slots.py:40` & `:103`. LOW. Survivor returns `parent.parent` = the ParsePosition*List*, not the position; sole caller (`lines.py:51`) assigns to an unused var.
- [ ] **C16. Entity reference impls of clash/lapse/word_foot are no-ops.** `constraints.py:161,182,246` return all-None. `ParsePosition.init` re-run condition (`positions.py:64`) is always true (viold stores only violations), so `Parse.concat`/manual `Parse()` re-runs them and overwrites vectorized clash/lapse with zeros.
- [ ] **C17. Entity `unres_within/across` use `wf1 is wf2`.** `constraints.py:98,122`. LOW. WordForms are shared across tokens of the same type (cached `get_word`), so adjacent repeated words are misclassified as word-internal. DF path uses `word_num` correctly.
- [x] **C18 (#110). O(L×T) per-line scans + word_foot loop.** `vectorized.py:86,95`; `constraints.py:231`. LOW. `np_line == ln` per line inside loops → use sorted-group boundaries; `word_foot`'s per-line loop is a broadcastable outer product.
- [x] **C19 (#110). `unres_within`/`unres_across` still Python loops** (known roadmap). `evaluate_constraints_batch`. Both reduce to a word-boundary mask `(L,N)` × same-position mask `(S,N)`.
- [ ] **C20. Misc.** `_get_parse` cache quirks (`vectorized.py:1082`: ignores `rank` on hit, one-way `is_bounded`, negative-index dup keys); DF-path `to_html` renders literal "None" (`vectorized.py:1122`); `LazyParseList.data` docstring wrong ("unbounded before bounded" — it's a score argsort, `:1022`); duplicate `(text,scansion)` annotations overwrite frequency instead of accumulating (`maxent.py:210`).

---

## Text / word / language layer (`prosodic/texts/`, `words/`, `langs/`, `ents.py`)

- [ ] **T1. `@cache` = `lru_cache(128)`** — see **P2**. `imports.py:28`. HIGH. ✓
  Also: `get_word` (`langs.py:547`) called per token occurrence in `build_syll_df` (`syll_df.py:91`) → thrash + espeak re-runs + dup disk-cache rows; evicted TTS words never update the in-memory `token2ipa` cached_property (`langs.py:92`).
- [ ] **T2. `@cache` on `TextModel.parse` leaks + breaks semantics** — see **P2**. `texts.py:234`. HIGH. ✓
  Holds up to 128 parsed TextModels (not GC'd); `parse(constraints=[...])` → `TypeError: unhashable`; `force=True` no-op after first parse (`parse_iter` returns cached without consulting `force`, `texts.py:277`; DF path in `meter.py:176` ignores `force`/`lim`).
- [ ] **T3. `get_parses_df()`/`save()` return the wrong meter's results.** `texts.py:379`. HIGH. ✓
  `latest_key = next(reversed(self._line_parse_results))` — always the most-recently-parsed meter, not the one implied by `**meter_kwargs`. Repro: default `get_parses_df()`, then `parse(max_s=1,max_w=1)`, then default `get_parses_df()` → returns the strict meter's parses.
- [x] **T4. (#111) Partially consuming `parse_iter()` permanently truncates results.** `texts.py:280`. HIGH. ✓
  Cache list created up-front, filled as consumed; early stop (SSE disconnect, `next()`) → every later `parse()` for that meter yields only the consumed prefix. Also `lim` not in `parse_key`, so `parse_iter(lim=10)` then `parse_iter()` returns the truncated set.
- [ ] **T5. `TextModel.load()` → RecursionError.** `texts.py:630`. HIGH. ✓
  Never sets `_linepart_parse_results`/`_syntax`/`_syntax_model`. `.lineparts` (`texts.py:181`) hits `AttributeError`, swallowed by `Entity.__getattr__`, re-routed `lineparts → get_list → get_text_list → getattr(text,'lineparts')` → infinite loop. (See T13 root cause.)
- [ ] **T6. `cleanup()` builds all the entities it's freeing.** `texts.py:222`. HIGH. ✓
  `iter_all()` accesses `children` → `_build_children()`. DF-only batch path (`parse_corpus` → `_parse_one` → `t.cleanup()`, `batch.py:62`) constructs the full entity tree per text just to clear caches. Also `cleanup()` clears `_parse_results` but not `_line_parse_results`/`_linepart_parse_results` (the large numpy arrays).
- [ ] **T7. Parse results attach to Lines only if `parse()` runs before `.lines`.** `texts.py:153`. MED. ✓
  Attachment happens once inside the `lines` cached_property. `t.lines; t.parse()` → `t.lines[0]._parses is None` → silent fallback to slow per-line entity re-parsing. Attach loop iterates all meter keys → last key wins arbitrarily with two meters.
- [ ] **T8. Digits silently treated as punctuation.** `tokenizers.py:138`, `wordtype.py:159`. MED. ✓
  `is_punc = not any(isalpha)`. "3" / "1867" get `is_punc=1`, 0 syllables, vanish from scansion. Any metrical line with a numeral parses with missing positions. **Fix idea:** route digits through `num2words` per lang before `get_word` (see Features).
- [ ] **T9. `line.to_html()` crashes after DF-path parse.** `lines.py:48`. MED. ✓
  `parse.wordtoken2slots[...]` on a parse whose `wordtokens` is None. `t.parse(); t.lines[0].to_html()` → `TypeError: NoneType not subscriptable`. Natural user flow; surfaces the two-path seam as an opaque crash.
- [ ] **T10. No validation for whitespace-only/empty text.** `texts.py:54`. MED. ✓
  `not txt` checked before `clean_text(...).strip()`, so `TextModel("   ")` builds a `(0,0)` frame; `.save()` then crashes (`texts.py:582`, `_syll_df['line_num'].max()` on empty). Non-string input fails deep in `WordTokenList` with a confusing message.
- [x] **T11. Hard-coded dev paths shipped in the package.** `imports.py:2-3`. MED. ✓
  `sys.path.insert(0,'/Users/ryan/github/hashstash')` / `'/Users/rj416/...'`. Shadows pip-installed hashstash on your machines; dead weight for users. `imports.py:72` appends nonexistent `PATH_MTREE`.
- [ ] **T12. `WordType.wtoken` corrupts its own WordFormList.** `wordtype.py:85`. MED. Buggy *and* dead (zero callers). Passes `children=self.children` into `WordToken`, whose init re-parents the list, stealing it from the WordType.
- [ ] **T13. `Entity.__getattr__` returns None for typos + swallows property AttributeErrors.** `ents.py:267`. MED.
  `line.best_prase` → falsy None, not an error; any AttributeError inside a property getter is masked (root cause of T5). Also caches plural lists in `self.__dict__` (`ents.py:268`) that go stale if children mutate (e.g. `force_unstress()`). **Fix:** only fall through for known plural/list patterns; re-raise otherwise.
- [ ] **T14. `Entity.key`/`__hash__` raise bare `Exception` for parentless entities.** `ents.py:656`. MED. A standalone `WordToken("word")` in a set/dict raises an anonymous Exception; `__hash__`'s except only catches `TypeError` (`ents.py:580`), so it propagates.
- [x] **T15. (#109) espeak discovery walks large trees at import + misses `libespeak-ng.so`.** `langs.py:494`. MED.
  `set_espeak_env()` runs at import; on Linux without `-dev` it `os.walk`s all of `/usr/lib/...` before warning — multi-second import penalty on the standard failure path.
- [ ] **T16. `TextModel.hash` re-serializes full text every call.** `texts.py:211`. MED. Plain property, not cached; O(text size) per `parse()` and per hashed use.
- [ ] **T17. `Text()` factory can't enable syntax.** `texts.py:689`. API bug. ✓ `prosodic.Text("...", syntax=True)` → `TypeError` — documented entry point can't reach documented feature. No `syntax`/`**kwargs` param.
- [x] **T18. (PR #95) `add_phrasal_stress` runs one spaCy call per sentence.** `phrasal_stress.py:122`. PERF. Use `nlp.pipe` over pre-built Docs to batch.
- [x] **T19. (PR #92) LOW cluster.**
  - `WordTokenList.__getstate__/__setstate__` have debug `print()`s (`wordtokenlist.py:47,52`) — pickling spams stdout.
  - `tokenize_agnostic` regex `[\w']+|[.,!?; -—–'\n]` (`utils.py:436`) has an accidental range ` -—` (U+0020–U+2014); chars above U+2014 that aren't `\w` (`…`, CJK punct) are silently dropped → `line.txt` loses characters. Curly-quote `SEPS_PHRASE` entries (`imports.py:78`) are dead for the same reason (ftfy uncurls first).
  - `clean_text` rewrites em-dash → `" -- "` (`utils.py:451`); `line.txt` ≠ user input (cosmetic).
  - `detect_lang` (langdetect) is unseeded/nondeterministic; raises on letter-free text (`texts.py:59`).
  - `fix_num_sylls` pops empty list → IndexError; pads with `"?"` junk (`langs.py:330`).
  - `syllables.py:49` uses `assert` for input validation (vanishes under `python -O`).
- [ ] **T20. Clean bill of health:** DF vs Entity feature parity — 0 mismatches across a full sonnet for `is_stressed`/`is_heavy`/`is_strong`/`is_weak` (Entity returns None where DF stores False; both falsy). *No action needed — recorded so nobody re-audits it.*

---

## Packaging / CI / release (`pyproject.toml`, `requirements.txt`, `MANIFEST.in`, `.github/`)

- [ ] **R1. `wheeel` typosquat in CI** — see **P4**. HIGH. ✓
- [ ] **R2. Local builds ship `node_modules` to PyPI.** `MANIFEST.in`. HIGH. ✓
  `graft prosodic` + `include-package-data`; `egg-info/SOURCES.txt` has 1,518 node_modules entries. A local `twine upload` publishes ~70 MB. CI builds from clean checkout are safe. **Fix:** `prune prosodic/web/frontend/node_modules` + `prune prosodic/web/frontend/.svelte-kit`. (Also delete 6 grafts of nonexistent dirs: metricaltree, syllabiphon, tagged_samples, meters, dicts, web.)
- [ ] **R3. Committed codecov token.** `codecov.yml`. HIGH. ✓ Live token `a6cb4510-...` in public repo. Rotate → `CODECOV_TOKEN` secret. (Low blast radius: coverage spoofing.)
- [ ] **R4. Hardcoded dev paths shipped** — same as **T11**. `imports.py:2-3`. HIGH. ✓
- [ ] **R5. Version incoherence.** `_version.py` = 3.2.1 on master; PyPI = 3.3.0 (from app3). With `twine --skip-existing`, every master push publishes nothing until you pass 3.3.0. Only git tags: `1.1`, moving `stable` — no 3.x tags. **Fix:** bump past 3.3.0 when merging app3→master; tag `v3.x.y`; gate the pypi job on tag push or fail loudly instead of silent `--skip-existing`. Consider `__version__ = importlib.metadata.version("prosodic")` for runtime introspection.
- [ ] **R6. Stale PyPI metadata.** `pyproject.toml`. MED. Description "Prosodic 2"; `Development Status :: 2 - Pre-Alpha`; `requires-python >=3.8` (README says 3.9, CI tests only 3.12.0, venv is 3.10 — no actual 3.9+ syntax found via AST, so floor is untested not broken). Homepage → `/tree/develop` + dead `prosodic.stanford.edu`. **Fix:** set floor to `>=3.10`, update description/classifier/URLs.
- [ ] **R7. requirements.txt hygiene.** MED. Zero pins; `orjson` + `editdistance` listed twice; `svgling` dead; `plotnine` only in dead `sents/grids.py`; `loguru` unused directly. **`requests` (`imports.py:24`) and `tqdm` (`imports.py:14`) imported unconditionally but undeclared** (survive via transitive chains). `torch` used (`vectorized.py`) with no `[gpu]` extra. `panphon` commented out, satisfied by vendored `prosodic/lib/panphon` via `sys.path.append` (appended → a user's real panphon shadows it: silent version drift).
- [ ] **R8. Three overlapping dev-dep lists.** MED. `pyproject [dev]` lists `pytest-cov` + `pytest>=7.2` twice each; `[all]` duplicates `[dev]` minus selenium; `dev-requirements.txt` is a third list (with `nbformat` twice + `quarto` — the pip package isn't the Quarto CLI). CI installs dev-requirements.txt; pyproject extras are decorative.
- [x] **R9. (#101) CI gaps.** MED. No lint (`.style.yapf` never enforced); single exact Python 3.12.0; **no `pull_request` trigger** (fork PRs never tested); actions on @v3; pip cache `restore-keys` duplicates primary key; espeak apt-installed uncached every run. `latest-release.yml` publishes `docs/` to gh-pages with `render: false` (republishes stale prebuilt HTML). **Fix:** add `pull_request` trigger, 3.10/3.12 matrix, `ruff`/yapf-diff step, bump actions @v4/@v5.
- [x] **R10. (#108) Stale docs.** MED. `docs/` last touched Sep 2024 (v2); `docs/reference/` = 67 tracked pdoc HTML files incl. pages for deleted modules (`lexconvert.html`, metricaltree — 2.5 MB+). `README.ipynb` (60 KB) Feb 2024 v2-era. `README.md` itself is current (v3, valid `prosodic.Text`) but says "Python>=3.9" (contradicts pyproject). **Fix:** regenerate or stop republishing.
- [x] **R11. (#101) Test coverage holes.** MED. 244 tests collected (CLAUDE.md says 219 — drift). Zero tests for: `cli.py`, **`texts/phrasal_stress.py`** (no `syntax=True` anywhere in tests/ — headline feature), `profiling.py`, desktop scripts. MaxEnt: one direct test + endpoint coverage. No `conftest.py` — every file repeats `sys.path.append` + star-import + `disable_caching()`. `test_web.py:152` spawns real uvicorn on random port 5111–5211 (collision-prone) + hard-sleeps `NAPTIME` (5s local, **30s CI**). **Fix:** add `conftest.py`; poll health endpoint instead of sleeping.
- [ ] **R12. `deployment/` is dead.** MED. Sep 2024 Flask/supervisor config (runs as root) superseded by `deploy/` (systemd/nginx/certbot). Both tracked — a trap. Delete `deployment/`.
- [ ] **R13. LOW.** `langs/finnish/finnish.py:76` points at nonexistent `data/dicts/en/english.tsv` (and it's the English dict in the Finnish class). `web/api.py:27` `CORPORA_DIR` resolves to `site-packages/../corpora` when pip-installed → empty corpus dropdown for pip users (deployed server works by accident via `pip install -e .`). Tracked-but-churny: `web/static_build/` (25 hashed bundles — semi-justified so pip users get the UI), `notebooks/.ipynb_checkpoints/`, `.claude/scheduled_tasks.lock`. `imports.py:58` does `os.makedirs(~/prosodic_data/...)` at import time (side effect on `import prosodic`).

---

## Dead code (grep-verified, ~1,900 lines)

- [x] **D1. (PR #92)** `prosodic/sents/{trees,grids,syntax}.py` + all of `prosodic/lib/metricaltree/` (~1,700 lines) — reachable only via `stanza` (commented out of requirements) → unrunnable in a normal install. Phrasal stress is now spaCy-only (`texts/phrasal_stress.py`). `sents/sents.py` (SentenceList/SentPart) is still live via `TextModel.sents/.sentparts`. `svgling`/`plotnine` in requirements solely for this path.
- [x] **D2. (PR #92)** `prosodic/prosodic.py` — one line, imported by nothing.
- [ ] **D3.** Dead constants in `imports.py`: `USE_CACHE` (:64), `PATH_MTREE`+append (:72), `DASHES`/`REPLACE_DASHES` (:74), `PSTRESS_THRESH_DEFAULT` (:76), `TOKENIZER` (:77), `DEFAULT_PARSE_MAXSEC`/`DEFAULT_LINE_LIM`/`DEFAULT_PROCESSORS` (:82), `MIN/MAX_WORDS_IN_PHRASE` (:87), `GROUPBY_*` (:263); `NUMBUILT` (`texts.py:6`).
- [ ] **D4.** `WordType.wtoken` (T12), `prefilter_scansions`/`build_parses`/`Meter.get_pos_types` (C14), large commented blocks in `langs.py:430`, `wordtokenlist.py:148,241`.

---

## Feature / improvement ideas (worth the effort)

- [ ] **F1. Unify the two parse paths.** Make `parse_batch` extract features then delegate to `evaluate_constraints_batch` + `compute_bounding_batch`. Fixes P3/C1 outright, halves the dispatch surface, gives the entity/web path batched bounding. *Highest-leverage structural fix.*
- [ ] **F2. Number normalization.** Route digit tokens through `num2words` (per `lang`) before `get_word` instead of dropping them (fixes T8) — makes verse/prose with numerals scannable.
- [ ] **F3. DF-native HTML rendering.** Render from `_syll_df` + scansion arrays (word_num boundaries already in the DF) so `t.parse(); to_html()` works without the entity chain (fixes T9, complements T7). Collapses the most user-visible seam.
- [ ] **F4. Memory-budgeted bounding.** Chunk L + tile S×S at n≥16 (fixes C6); lets `MAX_SYLL_IN_PARSE_UNIT` rise past 18 for better prose.
- [ ] **F5. Vectorize `unres_within`/`unres_across`** (C19) — last per-line Python loops in the hot path.
- [ ] **F6. Request-hardening middleware** (web): `Semaphore` cap on concurrent parses + body-size limit + wall-clock timeout. Closes W2/W4/W5 together; makes the Settings `parse_timeout` real.
- [ ] **F7. Session-consistent pronunciation cache.** After a TTS hit, insert into in-memory `token2ipa`; dedupe disk cache on load; replace the accidental 128-LRUs on `get_word`/`get_sylls_ipa_ll` with unbounded dict caches (fixes T1 warm-path overhead).
- [ ] **F8. Shareable parse permalinks** — high value, but land W3 (output escaping) + a CSP header *first*, or self-XSS becomes stored XSS.
- [ ] **F9. Zone-aware bounding** (pairs with C11) — dominance on zone-split sums when `zone_weights` active; restores `best_parse` = true argmin.

---

## Test suite status (2026-07-04)

Full `pytest` **did not finish after 26+ minutes** of wall time (process state `U`/uninterruptible, ~15% CPU — slowly grinding, not hard-hung). A suite this size should complete in a few minutes; this is itself a finding worth investigating — likely culprits: the real-uvicorn/Selenium web test (`test_web.py:152`, spawns a server + 30 s `NAPTIME` sleep), the multiprocessing `parse_corpus` test, or espeak phonemizing many words on a cold cache. **Every finding above was reproduced independently of the suite**, so its pass/fail doesn't change any conclusion.

- [ ] **Investigate the pathologically slow/hanging test run.** Bisect with `pytest --durations=20` (or `-x` + per-file runs) to find the offender; convert the sleep-based web test to health-endpoint polling (R11); consider marking the slowest integration tests with a `@pytest.mark.slow` opt-in.

---

## Suggested first PR

Batch the fix-today cluster:
1. **Web robustness:** P1 (StaticFiles mount) + P5 (empty-syllable guard). Both small, both hit the live site.
2. **The `cache` alias (P2):** one-line `imports.py` change *plus* a careful pass over every `@cache` callsite — it ripples widely (fixes the list-constraints crash and `force`), so verify each cache's intended bound.
3. **P4 (`wheeel` → `wheel`):** trivial, urgent.
4. **P3/F1 (unify parse paths):** larger; can be its own PR, but it's the single most impactful correctness fix for the web app.
