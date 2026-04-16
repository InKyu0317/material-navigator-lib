"""Composition recommendation via GlassPy GlassNet + Bayesian Optimization."""

from __future__ import annotations

import math
from typing import Any, Callable

from .oxides import OXIDE_LIST


# ── Lookup table: formula → molar_mass ──────────────────────────────
_MOLAR_MASS: dict[str, float] = {o["formula"]: o["molar_mass"] for o in OXIDE_LIST}

# Unicode subscript digits → ASCII (e.g. SiO₂ → SiO2)
_SUB_TABLE = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def _normalise_formula(formula: str) -> str:
    """Convert unicode subscript notation to plain ASCII."""
    return formula.translate(_SUB_TABLE)


# ── wt% ↔ mol% conversion ──────────────────────────────────────────

def wt_to_mol(oxides_wt: dict[str, float]) -> dict[str, float]:
    """Convert weight-percent composition to mole-percent.

    Args:
        oxides_wt: ``{formula: wt%}`` — values need NOT sum to 100.

    Returns:
        ``{formula: mol%}`` summing to 100.

    Raises:
        KeyError: if a formula is not in OXIDE_LIST.
    """
    moles = {}
    for formula, wt in oxides_wt.items():
        key = _normalise_formula(formula)
        mm = _MOLAR_MASS.get(key)
        if mm is None:
            raise KeyError(f"Unknown oxide formula: {formula!r}")
        moles[key] = wt / mm if mm > 0 else 0.0

    total = sum(moles.values())
    if total == 0:
        return {f: 0.0 for f in oxides_wt}
    return {f: m / total * 100.0 for f, m in moles.items()}


def mol_to_wt(oxides_mol: dict[str, float]) -> dict[str, float]:
    """Convert mole-percent composition to weight-percent.

    Args:
        oxides_mol: ``{formula: mol%}`` — values need NOT sum to 100.

    Returns:
        ``{formula: wt%}`` summing to 100.

    Raises:
        KeyError: if a formula is not in OXIDE_LIST.
    """
    weights = {}
    for formula, mol in oxides_mol.items():
        key = _normalise_formula(formula)
        mm = _MOLAR_MASS.get(key)
        if mm is None:
            raise KeyError(f"Unknown oxide formula: {formula!r}")
        weights[key] = mol * mm

    total = sum(weights.values())
    if total == 0:
        return {f: 0.0 for f in oxides_mol}
    return {f: w / total * 100.0 for f, w in weights.items()}


# ── Property mapping (UI name → GlassNet target column) ────────────

PROPERTY_MAP: dict[str, str] = {
    "Tg": "Tg",
    "Ts": "Tstrain",
    "CTE": "CTEbelowTg",
    "Tc": "CrystallizationPeak",
    "Density": "Density293K",
    "Young's modulus": "YoungModulus",
    "Poisson ratio": "PoissonRatio",
    "Hardness": "Microhardness",
    "Nd": "RefractiveIndex",
    "Vd": "AbbeNum",
    "Viscosity": "Viscosity1273K",
    "ε": "Permittivity",
    "tanδ": "TangentOfLossAngle",
}

# GlassNet returns these columns in Kelvin; must subtract 273.15 for °C output.
_KELVIN_PROPERTIES: frozenset[str] = frozenset({"Tg", "Ts", "Tc"})

# GlassNet returns these columns as log₁₀ values; must apply 10^x (× multiplier) conversion.
# Format: {ui_prop: multiplier}  →  value = 10^raw * multiplier
_LOG10_PROPERTIES: dict[str, float] = {
    "CTE": 1e7,   # log10(K⁻¹) → ×10⁻⁷/°C
    "tanδ": 1.0,  # log10(tanδ) → tanδ (linear)
}

# Typical scale for normalizing deviations (order-of-magnitude, after unit conversion)
_PROPERTY_SCALE: dict[str, float] = {
    "Tg": 100.0,
    "Ts": 100.0,
    "CTE": 30.0,   # ×1e-7/°C units; soda-lime ~87, borosilicate ~32
    "Tc": 100.0,
    "Density": 0.5,
    "Young's modulus": 20.0,
    "Poisson ratio": 0.05,
    "Hardness": 2.0,
    "Nd": 0.05,
    "Vd": 10.0,
    "Viscosity": 2.0,
    "ε": 2.0,
    "tanδ": 0.005,  # linear tanδ units; typical 0.001–0.02
}


# ── GlassNet prediction wrapper ────────────────────────────────────

_glassnet_instance = None


def _get_glassnet():
    """Lazy-load singleton GlassNet model."""
    global _glassnet_instance
    if _glassnet_instance is None:
        from glasspy.predict import GlassNet
        _glassnet_instance = GlassNet()
    return _glassnet_instance


def predict_properties(
    composition_mol: dict[str, float],
    targets: list[str],
) -> dict[str, float]:
    """Predict glass properties for a mol%-composition using GlassNet.

    Args:
        composition_mol: ``{formula: mol%}``.
        targets: UI property names (keys of ``PROPERTY_MAP``).

    Returns:
        ``{ui_property: predicted_value}`` for each requested target.
    """
    gn = _get_glassnet()
    df = gn.predict(composition_mol)

    result: dict[str, float] = {}
    for prop in targets:
        col = PROPERTY_MAP.get(prop)
        if col and col in df.columns:
            value = float(df[col].iloc[0])
            # GlassNet returns temperature properties in Kelvin → convert to °C
            if prop in _KELVIN_PROPERTIES:
                value -= 273.15
            # GlassNet returns some properties as log₁₀ → convert to linear
            elif prop in _LOG10_PROPERTIES:
                value = (10.0 ** value) * _LOG10_PROPERTIES[prop]
            result[prop] = value
    return result


# ── Convenience wrappers ──────────────────────────────────────────

def predict_from_wt(
    oxides_wt: dict[str, float],
    targets: list[str],
) -> dict[str, float]:
    """Predict properties from a **wt%** composition (handles unicode).

    Normalises formula keys, converts wt→mol, then calls
    :func:`predict_properties`.
    """
    normed = {_normalise_formula(k): v for k, v in oxides_wt.items()}
    mol = wt_to_mol(normed)
    return predict_properties(mol, targets)


# ── Oxide scoring (GlassNet sensitivity) ──────────────────────────

_OXIDE_INFO: dict[str, dict[str, str]] = {
    o["formula"]: {"name_ko": o["name_ko"], "category": o["category"]}
    for o in OXIDE_LIST
}


def score_oxides(
    base_composition_wt: dict[str, float],
    target_properties: list[str],
    priority_weights: list[float] | None = None,
) -> list[dict[str, Any]]:
    """Score candidate oxides by their GlassNet sensitivity.

    For each oxide **not** already in *base_composition_wt*, adds 5 wt%
    (proportionally reducing the rest), predicts properties with GlassNet,
    and computes a weighted deviation score.

    Args:
        base_composition_wt: Current composition in wt%.
        target_properties: UI property names (keys of ``PROPERTY_MAP``).
        priority_weights: Per-property weights (same length as
            *target_properties*).  Defaults to ``[1, 0.5, 0.25, …]``.

    Returns:
        List of ``{formula, name_ko, category, score, stars}`` sorted
        descending by *score*.
    """
    # Normalise & build baseline
    base = {_normalise_formula(k): v for k, v in base_composition_wt.items()}
    total_wt = sum(base.values())
    if total_wt <= 0:
        return []
    base_norm = {k: v / total_wt * 100.0 for k, v in base.items()}

    if priority_weights is None:
        priority_weights = [0.5 ** i for i in range(len(target_properties))]

    # Baseline prediction
    base_mol = wt_to_mol(base_norm)
    baseline_pred = predict_properties(base_mol, target_properties)

    existing = set(base_norm.keys())
    raw_scores: list[tuple[str, float]] = []

    for formula in _MOLAR_MASS:
        if formula in existing:
            continue

        # Add 5 wt% of candidate, proportionally reduce base
        factor = 95.0 / 100.0
        trial = {k: v * factor for k, v in base_norm.items()}
        trial[formula] = 5.0

        trial_mol = wt_to_mol(trial)
        trial_pred = predict_properties(trial_mol, target_properties)

        # Weighted absolute change
        raw = 0.0
        for i, prop in enumerate(target_properties):
            bp = baseline_pred.get(prop)
            tp = trial_pred.get(prop)
            if bp is None or tp is None or math.isnan(bp) or math.isnan(tp):
                continue
            scale = _PROPERTY_SCALE.get(prop, 1.0)
            w = priority_weights[i] if i < len(priority_weights) else 0.1
            raw += w * abs(tp - bp) / scale

        raw_scores.append((formula, raw))

    if not raw_scores:
        return []

    # Normalise to 0–1
    max_raw = max(s for _, s in raw_scores)
    if max_raw <= 0:
        max_raw = 1.0

    results: list[dict[str, Any]] = []
    for formula, raw in raw_scores:
        norm_score = round(raw / max_raw, 4)
        stars = max(1, min(5, round(norm_score * 5)))
        info = _OXIDE_INFO.get(formula, {"name_ko": formula, "category": "other"})
        results.append({
            "formula": formula,
            "name_ko": info["name_ko"],
            "category": info["category"],
            "score": norm_score,
            "stars": stars,
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results


# ── Bayesian Optimization ──────────────────────────────────────────

# Common flux / modifier oxides to consider as extra dimensions
_COMMON_EXTRAS = [
    "Na2O", "K2O", "Li2O", "CaO", "MgO", "BaO", "ZnO",
    "B2O3", "PbO", "SrO", "TiO2", "ZrO2", "La2O3", "Fe2O3",
]


def _build_search_space(
    oxides_wt: dict[str, float],
    max_extras: int | None = None,
    search_bounds: dict[str, dict[str, float]] | None = None,
) -> tuple[list[str], list[tuple[float, float]]]:
    """Build (oxide_names, bounds) from current wt% composition.

    If *search_bounds* is provided, use those bounds for matching oxides.
    If *max_extras* is given, up to that many common oxides not already in
    the composition are appended with a 0–15 wt% range.
    """
    names: list[str] = []
    bounds: list[tuple[float, float]] = []
    for formula, wt in oxides_wt.items():
        names.append(formula)
        if search_bounds and formula in search_bounds:
            sb = search_bounds[formula]
            lo = max(0.01, float(sb.get("lo", 0.01)))
            hi = float(sb.get("hi", 100.0))
            # Ensure valid range for skopt: lo must be strictly < hi.
            # Swap inverted bounds; if equal, expand hi by 1 wt%.
            if lo > hi:
                lo, hi = hi, lo
            if lo >= hi:
                hi = lo + 1.0
            bounds.append((lo, hi))
        elif wt <= 0:
            bounds.append((0.01, 15.0))
        else:
            delta = max(wt * 0.3, 5.0)
            lo = max(0.0, wt - delta)
            hi = min(100.0, wt + delta)
            bounds.append((lo, hi))

    # Add extra common oxides not already present
    if max_extras and max_extras > 0:
        existing = set(names)
        added = 0
        for formula in _COMMON_EXTRAS:
            if formula not in existing and formula in _MOLAR_MASS:
                names.append(formula)
                bounds.append((0.0, 15.0))
                added += 1
                if added >= max_extras:
                    break

    return names, bounds


def _objective(
    x: list[float],
    oxide_names: list[str],
    property_targets: list[dict[str, Any]],
    weights: list[float],
) -> float:
    """Objective function for skopt: lower is better."""
    # Normalise to Σ=100 wt%
    total = sum(x)
    if total <= 0:
        return 1e6
    wt_norm = [v / total * 100.0 for v in x]
    oxides_wt = dict(zip(oxide_names, wt_norm))

    # Convert to mol% and predict
    oxides_mol = wt_to_mol(oxides_wt)
    target_names = [t["property"] for t in property_targets]
    predicted = predict_properties(oxides_mol, target_names)

    # Compute weighted penalty
    penalty = 0.0
    for i, t in enumerate(property_targets):
        prop = t["property"]
        pred_val = predicted.get(prop)
        if pred_val is None:
            continue

        scale = _PROPERTY_SCALE.get(prop, 1.0)
        mode = t.get("mode", "단일값")

        if mode == "단일값":
            target_val = t.get("target")
            if target_val is not None:
                penalty += weights[i] * abs(pred_val - target_val) / scale
        elif mode == "범위":
            lo = t.get("min")
            hi = t.get("max")
            if lo is not None:
                penalty += weights[i] * max(0.0, lo - pred_val) / scale
            if hi is not None:
                penalty += weights[i] * max(0.0, pred_val - hi) / scale
        elif mode == "최솟값":
            target_val = t.get("target")
            if target_val is not None:
                penalty += weights[i] * max(0.0, target_val - pred_val) / scale
        elif mode == "최댓값":
            target_val = t.get("target")
            if target_val is not None:
                penalty += weights[i] * max(0.0, pred_val - target_val) / scale

    return penalty


def recommend_composition_streaming(
    oxides_wt: dict[str, float],
    property_targets: list[dict[str, Any]],
    search_bounds: dict[str, dict[str, float]] | None = None,
    max_extras: int = 0,
    n_candidates: int = 5,
    n_calls: int = 40,
    callback: Callable[[dict[str, Any]], None] | None = None,
) -> list[dict[str, Any]]:
    """Recommend compositions with per-iteration callback for streaming.

    Args:
        oxides_wt: Current composition in wt%.
        property_targets: List of ``{property, mode, target, min, max}``.
        search_bounds: Optional per-oxide bounds ``{oxide: {lo, hi}}``.
        max_extras: Extra common oxides to add to search space.
        n_candidates: Number of candidates to return.
        n_calls: Total evaluations for the optimiser.
        callback: Called after each iteration with
            ``{iteration, n_calls, best_score, current_score, best_wt}``.

    Returns:
        List of candidates sorted by score (ascending).
    """
    from skopt import gp_minimize
    from skopt.space import Real

    # Normalise formula keys (unicode subscripts → ASCII)
    oxides_wt = {_normalise_formula(k): v for k, v in oxides_wt.items()}

    base_oxide_names = set(oxides_wt.keys())

    oxide_names, bounds = _build_search_space(
        oxides_wt, max_extras=max_extras, search_bounds=search_bounds,
    )

    # Priority weights: rank 0 → 1.0, rank 1 → 0.5, rank 2 → 0.25, …
    weights = [0.5 ** i for i in range(len(property_targets))]

    dimensions = [Real(lo, hi, name=name) for name, (lo, hi) in zip(oxide_names, bounds)]

    # Track iteration for callback
    _iter_state = {"i": 0, "best_score": float("inf")}

    def _skopt_callback(res):
        _iter_state["i"] += 1
        current = float(res.func_vals[-1])
        if current < _iter_state["best_score"]:
            _iter_state["best_score"] = current
        if callback is not None:
            # Best wt% so far
            total = sum(res.x)
            best_wt = {}
            if total and total > 0:
                best_wt = {n: round(v / total * 100.0, 2) for n, v in zip(oxide_names, res.x)}
            callback({
                "iteration": _iter_state["i"],
                "n_calls": n_calls,
                "best_score": round(_iter_state["best_score"], 4),
                "current_score": round(current, 4),
                "best_wt": best_wt,
            })

    result = gp_minimize(
        func=lambda x: _objective(x, oxide_names, property_targets, weights),
        dimensions=dimensions,
        n_calls=n_calls,
        n_random_starts=min(20, n_calls // 3),
        random_state=42,
        callback=[_skopt_callback],
    )

    # Collect all evaluated points, sort by objective value
    scored: list[tuple[float, list[float]]] = sorted(
        zip(result.func_vals, result.x_iters),
        key=lambda t: t[0],
    )

    # Build candidate list
    target_names = [t["property"] for t in property_targets]
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[float, ...]] = set()

    for score, x in scored:
        if len(candidates) >= n_candidates:
            break

        # Normalise
        total = sum(x)
        if total <= 0:
            continue
        wt_norm = {name: round(v / total * 100.0, 2) for name, v in zip(oxide_names, x)}

        # max_extras filter — count only *new* oxides
        if max_extras > 0:
            n_new = sum(1 for name, v in wt_norm.items() if v > 0.5 and name not in base_oxide_names)
            if n_new > max_extras:
                continue

        # Dedup (round to 1 decimal)
        key = tuple(round(v, 1) for v in wt_norm.values())
        if key in seen:
            continue
        seen.add(key)

        # Predict for the final candidate
        oxides_mol = wt_to_mol(wt_norm)
        predicted = predict_properties(oxides_mol, target_names)

        candidates.append({
            "oxides_wt": wt_norm,
            "predicted": predicted,
            "score": round(float(score), 4),
        })

    return candidates


def recommend_composition(
    oxides_wt: dict[str, float],
    property_targets: list[dict[str, Any]],
    max_oxides: int | None = None,
    n_candidates: int = 5,
    n_calls: int = 40,
) -> list[dict[str, Any]]:
    """Backward-compatible wrapper around :func:`recommend_composition_streaming`."""
    return recommend_composition_streaming(
        oxides_wt=oxides_wt,
        property_targets=property_targets,
        max_extras=max_oxides or 0,
        n_candidates=n_candidates,
        n_calls=n_calls,
    )
