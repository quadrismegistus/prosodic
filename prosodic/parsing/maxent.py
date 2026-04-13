"""Maximum Entropy constraint weight learner for metrical phonology.

Given hand-annotated poetry scansions, learns optimal constraint weights
so that the annotated parse has the highest probability under a log-linear
(MaxEnt / Harmonic Grammar) model.

Based on Goldwater & Johnson (2003) and Bruce Hayes' MaxEnt OT framework.

Usage:
    from prosodic.parsing.maxent import MaxEntTrainer

    # annotations: list of (line_text, scansion_str, frequency)
    # or a DataFrame with columns: text, scansion, frequency
    trainer = MaxEntTrainer(meter)
    trainer.load_annotations(annotations)
    trainer.train()
    trainer.report()

    # apply learned weights
    meter.constraints = trainer.learned_weights()
"""

import numpy as np
import pandas as pd
from ..imports import *
from .vectorized import parse_batch_from_df


class MaxEntTrainer:
    """Learns constraint weights from annotated scansion data.

    Uses L-BFGS-B optimization of log-likelihood with L2 regularization.
    All heavy computation is vectorized numpy.

    Args:
        meter: Meter object for parsing.
        regularization: L2 regularization strength (higher = more shrinkage).
        zones: positional zone splitting for constraints.
            - None: no splitting (default). One weight per constraint.
            - "initial": split into initial (first 2 syllables) vs rest.
              Doubles the constraint count. Lets the model learn that e.g.
              trochaic inversion in foot 1 costs less.
            - "foot": split per metrical foot (every 2 syllable positions).
              Creates C * max_feet constraints.
            - int N: split line into N equal zones by syllable index.
    """

    def __init__(self, meter, regularization=1.0, zones=None):
        self.meter = meter
        self.regularization = regularization
        self.zones = zones
        self._annotations = None  # DataFrame: text, scansion, frequency
        self._line_data = None    # list of dicts with viols + observed freq vectors
        self._constraint_names = None  # expanded names (with zone suffixes)
        self._base_constraint_names = None  # original constraint names
        self._weights = None

    def _parse_text(self, text_input, lang=DEFAULT_LANG):
        """Parse text and return (results_dict, original_line_strings).

        Args:
            text_input: a string, list of strings, or TextModel.
        Returns:
            (results, line_texts) where results is {line_num: LazyParseList}
            and line_texts is [str, ...] in line_num order.
        """
        from ..texts import TextModel
        if isinstance(text_input, TextModel):
            text = text_input
            # recover lines from the raw input
            raw = text._txt if hasattr(text, '_txt') else ""
            input_lines = [l.strip() for l in raw.split("\n") if l.strip()]
        elif isinstance(text_input, list):
            input_lines = [l.strip() for l in text_input if l.strip()]
            text = TextModel("\n".join(input_lines), lang=lang)
        else:
            input_lines = [l.strip() for l in text_input.split("\n") if l.strip()]
            text = TextModel(text_input, lang=lang)
        results = parse_batch_from_df(text._syll_df, self.meter)
        line_nums = sorted(results.keys())
        # map line_num -> original text by position
        line_texts = [input_lines[i] if i < len(input_lines) else ""
                      for i in range(len(line_nums))]
        return results, line_texts

    def _zone_split(self, viols_3d):
        """Split (S, N, C) violations into zone-aware (S, C*Z) features.

        Sums violations within each zone of the syllable axis, producing
        separate feature columns for each (constraint, zone) pair.

        Args:
            viols_3d: (S, N, C) int8 array of per-syllable violations.

        Returns:
            (S, C*Z) float64 array of zone-summed violations.
        """
        S, N, C = viols_3d.shape
        zones = self.zones

        if zones is None:
            return viols_3d.sum(axis=1).astype(np.float64)  # (S, C)

        # build zone boundaries: list of (start, end) slices
        if zones == "initial":
            boundaries = [(0, 2), (2, N)]
        elif zones == "foot":
            boundaries = [(i, min(i + 2, N)) for i in range(0, N, 2)]
        elif isinstance(zones, int):
            step = max(1, N // zones)
            boundaries = []
            for z in range(zones):
                start = z * step
                end = (z + 1) * step if z < zones - 1 else N
                boundaries.append((start, end))
        else:
            raise ValueError(f"Unknown zones: {zones!r}")

        Z = len(boundaries)
        result = np.zeros((S, C * Z), dtype=np.float64)
        for z, (start, end) in enumerate(boundaries):
            result[:, z * C:(z + 1) * C] = viols_3d[:, start:end, :].sum(axis=1)
        return result

    def _make_zone_names(self, base_names, nsylls):
        """Generate expanded constraint names with zone suffixes."""
        zones = self.zones
        if zones is None:
            return list(base_names)

        if zones == "initial":
            zone_labels = ["_init", "_rest"]
        elif zones == "foot":
            n_feet = (nsylls + 1) // 2
            zone_labels = [f"_f{i+1}" for i in range(n_feet)]
        elif isinstance(zones, int):
            zone_labels = [f"_z{i+1}" for i in range(zones)]
        else:
            raise ValueError(f"Unknown zones: {zones!r}")

        return [f"{name}{zlabel}" for zlabel in zone_labels for name in base_names]

    def _build_line_data(self, results, line_texts, scansion_map):
        """Build self._line_data from parse results and a scansion mapping.

        Args:
            results: {line_num: LazyParseList}
            line_texts: [str, ...] in line_num order
            scansion_map: dict {line_text: [(scansion_str, frequency), ...]}
                or None (no annotations, all lines get uniform observed).
        """
        self._line_data = []
        self._base_constraint_names = None
        n_unmatched = 0

        # first pass: collect raw data and find max syllable count for zone naming
        raw_entries = []
        max_nsylls = 0
        line_nums = sorted(results.keys())
        for i, ln in enumerate(line_nums):
            lpl = results[ln]
            line_text = line_texts[i]

            if self._base_constraint_names is None:
                self._base_constraint_names = list(lpl._constraint_names)

            nsylls = lpl._all_viols.shape[1]
            if nsylls > max_nsylls:
                max_nsylls = nsylls

            raw_entries.append((line_text, lpl))

        # set up zone-expanded constraint names using max syllable count
        self._constraint_names = self._make_zone_names(
            self._base_constraint_names, max_nsylls
        )
        n_features = len(self._constraint_names)

        # second pass: zone-split and pad to consistent feature dimension
        for line_text, lpl in raw_entries:
            viols_sum = self._zone_split(lpl._all_viols)  # (S, C*Z_local)
            n_scansions = viols_sum.shape[0]

            # pad if this line has fewer zones than the max
            if viols_sum.shape[1] < n_features:
                padded = np.zeros((n_scansions, n_features), dtype=np.float64)
                padded[:, :viols_sum.shape[1]] = viols_sum
                viols_sum = padded

            scansion_strs = ["".join(scan) for scan in lpl._all_scansions]
            scansion_set = set(scansion_strs)

            observed = np.zeros(n_scansions, dtype=np.float64)
            if scansion_map is not None:
                for annot_scan, freq in scansion_map.get(line_text, []):
                    if not isinstance(annot_scan, str) or annot_scan not in scansion_set:
                        n_unmatched += 1
                        continue
                    for j, s in enumerate(scansion_strs):
                        if s == annot_scan:
                            observed[j] = freq
                            break

            obs_sum = observed.sum()
            if obs_sum > 0:
                observed /= obs_sum

            self._line_data.append({
                "text": line_text,
                "viols": viols_sum,
                "observed": observed,
                "scansions": scansion_strs,
            })

        n_matched = sum(1 for ld in self._line_data if ld["observed"].sum() > 0)
        n_total = len(self._line_data)
        if n_unmatched or n_matched < n_total:
            log.warning(
                f"{n_total - n_matched}/{n_total} lines had no matching "
                f"scansion among parser candidates (syllable count mismatch?)"
            )

        self._weights = np.zeros(n_features, dtype=np.float64)

    def load_annotations(self, data, lang=DEFAULT_LANG):
        """Load annotated scansion data and parse all lines.

        Args:
            data: list of (line_text, scansion_str, frequency) tuples,
                  or a DataFrame with columns: text, scansion, frequency.
            lang: language code for parsing.
        """
        if isinstance(data, list):
            df = pd.DataFrame(data, columns=["text", "scansion", "frequency"])
        else:
            df = data.copy()
        self._annotations = df

        unique_texts = df["text"].unique().tolist()
        results, line_texts = self._parse_text(unique_texts, lang=lang)

        # build scansion_map: {text: [(scansion, frequency), ...]}
        scansion_map = {}
        for _, row in df.iterrows():
            scansion_map.setdefault(row["text"], []).append(
                (row["scansion"], row["frequency"])
            )

        self._build_line_data(results, line_texts, scansion_map)

    def load_text(self, text, target_scansion, lang=DEFAULT_LANG):
        """Load a text and assign a uniform target scansion to all lines.

        Lines whose syllable count doesn't match the target scansion length
        are skipped (with a warning).

        Args:
            text: a string, list of line strings, or TextModel.
            target_scansion: e.g. "wswswswsws" for iambic pentameter.
            lang: language code for parsing.
        """
        results, line_texts = self._parse_text(text, lang=lang)

        # every line gets the same target scansion
        scansion_map = {
            lt: [(target_scansion, 1.0)] for lt in line_texts
        }

        self._build_line_data(results, line_texts, scansion_map)

    def _precompute(self):
        """Group lines by scansion count and pre-stack for vectorized ops."""
        from collections import defaultdict
        groups = defaultdict(lambda: {"viols": [], "observed": [], "indices": []})
        for i, ld in enumerate(self._line_data):
            s = ld["viols"].shape[0]
            groups[s]["viols"].append(ld["viols"])
            groups[s]["observed"].append(ld["observed"])
            groups[s]["indices"].append(i)
        self._groups = {}
        for s, g in groups.items():
            self._groups[s] = {
                "viols": np.stack(g["viols"]),        # (L, S, C)
                "observed": np.stack(g["observed"]),   # (L, S)
            }

    @staticmethod
    def _softmax_probs(viols, weights):
        """Compute scansion probabilities via softmax over weighted violations.

        Weights are negative (more violations = lower probability), so we
        compute scores = viols @ weights where weights <= 0.
        """
        scores = viols @ weights  # (S,) or (L, S)
        # numerical stability: subtract max
        scores -= scores.max(axis=-1, keepdims=True)
        exp_scores = np.exp(scores)
        return exp_scores / exp_scores.sum(axis=-1, keepdims=True)

    def _neg_log_likelihood_and_grad(self, weights):
        """Compute negative log-likelihood and gradient (for minimization).

        Fully vectorized over lines within each scansion-count group.
        """
        neg_ll = 0.0
        n_c = len(self._constraint_names)
        neg_grad = np.zeros(n_c, dtype=np.float64)

        for g in self._groups.values():
            viols = g["viols"]        # (L, S, C)
            observed = g["observed"]  # (L, S)

            probs = self._softmax_probs(viols, weights)  # (L, S)

            # log-likelihood: sum of observed * log(prob)
            safe_probs = np.clip(probs, 1e-30, None)
            neg_ll -= (observed * np.log(safe_probs)).sum()

            # gradient: sum over lines of (observed - predicted) @ viols
            diff = observed - probs  # (L, S)
            # (L, S).T @ ... but we want sum over L of diff[l] @ viols[l]
            # = einsum('ls,lsc->c', diff, viols)
            neg_grad -= np.einsum('ls,lsc->c', diff, viols)

        # L2 regularization
        neg_ll += (weights ** 2).sum() / (2 * self.regularization)
        neg_grad += weights / self.regularization

        return neg_ll, neg_grad

    def train(self, only_negative_weights=True, verbose=False, **kwargs):
        """Train constraint weights via L-BFGS-B optimization.

        Args:
            only_negative_weights: if True, clamp weights <= 0 (more
                violations = worse, which is the standard OT/HG convention).
            verbose: print optimization progress.
            **kwargs: extra args passed to scipy.optimize.minimize (e.g.
                maxiter, ftol).
        """
        if self._line_data is None:
            raise ValueError("Call load_annotations() or load_text() first")

        from scipy.optimize import minimize

        self._precompute()

        n_c = len(self._constraint_names)
        x0 = np.zeros(n_c, dtype=np.float64)

        bounds = [(-np.inf, 0.0) if only_negative_weights else (None, None)
                  for _ in range(n_c)]

        options = {"maxiter": kwargs.pop("maxiter", 10000), "disp": verbose}
        options.update(kwargs.pop("options", {}))

        result = minimize(
            fun=lambda w: self._neg_log_likelihood_and_grad(w),
            x0=x0, method="L-BFGS-B", jac=True,
            bounds=bounds, options=options, **kwargs,
        )

        self._weights = result.x
        self._train_params = {
            "method": "L-BFGS-B",
            "only_negative_weights": only_negative_weights,
            "converged": result.success,
            "iterations": result.nit,
            "message": result.message.decode() if isinstance(result.message, bytes) else str(result.message),
        }

    def learned_weights(self):
        """Return learned weights as a dict {constraint_name: weight}.

        Weights are returned as positive values (negated from internal
        representation) for compatibility with Meter.constraints.
        """
        return {
            name: float(-self._weights[i]) if self._weights[i] != 0 else 0.0
            for i, name in enumerate(self._constraint_names)
        }

    def predict(self):
        """Return a DataFrame with observed vs predicted frequencies per line."""
        rows = []
        for ld in self._line_data:
            probs = self._softmax_probs(ld["viols"], self._weights)
            for i, scan in enumerate(ld["scansions"]):
                rows.append({
                    "text": ld["text"],
                    "scansion": scan,
                    "observed": ld["observed"][i],
                    "predicted": probs[i],
                })
        return pd.DataFrame(rows)

    def report(self):
        """Print a summary of learned weights and predictions."""
        weights = self.learned_weights()
        params = self._train_params

        print("=" * 60)
        print("MaxEnt Training Report")
        print("=" * 60)
        print()
        print(f"Method: {params.get('method', 'gradient ascent')}")
        print(f"Iterations: {params.get('iterations', params.get('actual_epochs', '?'))}")
        if 'converged' in params:
            print(f"Converged: {params['converged']} ({params.get('message', '')})")
        print(f"Regularization: {self.regularization}")
        neg_ll, _ = self._neg_log_likelihood_and_grad(self._weights)
        print(f"Log-likelihood: {-neg_ll:.4f}")
        print()

        print("Learned Constraint Weights")
        print("-" * 40)
        max_name_len = max(len(n) for n in weights) if weights else 20
        for name, w in weights.items():
            print(f"  {name:{max_name_len}s}  {w:.4f}")
        print()

        print("Predictions")
        print("-" * 60)
        pred_df = self.predict()
        for text, group in pred_df.groupby("text", sort=False):
            print(f'  "{text}"')
            interesting = group[(group["observed"] > 0) | (group["predicted"] > 0.01)]
            for _, row in interesting.iterrows():
                print(f"    {row['scansion']:20s}  "
                      f"obs={row['observed']:.1%}  pred={row['predicted']:.1%}")
            print()

    def apply_to_meter(self):
        """Set learned weights on the meter."""
        self.meter.constraints = self.learned_weights()
        # clear cached properties that depend on constraints
        for attr in ("constraint_funcs", "parse_constraint_funcs",
                     "position_constraint_funcs"):
            self.meter.__dict__.pop(attr, None)
        self.meter._key = None
