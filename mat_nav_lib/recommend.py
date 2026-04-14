"""Composition recommendation via GlassPy GlassNet + Bayesian Optimization."""

from __future__ import annotations

from typing import Any

from .oxides import OXIDE_LIST


# ── Lookup table: formula → molar_mass ──────────────────────────────
_MOLAR_MASS: dict[str, float] = {o["formula"]: o["molar_mass"] for o in OXIDE_LIST}


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
        mm = _MOLAR_MASS.get(formula)
        if mm is None:
            raise KeyError(f"Unknown oxide formula: {formula!r}")
        moles[formula] = wt / mm if mm > 0 else 0.0

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
        mm = _MOLAR_MASS.get(formula)
        if mm is None:
            raise KeyError(f"Unknown oxide formula: {formula!r}")
        weights[formula] = mol * mm

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

# Typical scale for normalizing deviations (order-of-magnitude)
_PROPERTY_SCALE: dict[str, float] = {
    "Tg": 100.0,
    "Ts": 100.0,
    "CTE": 20.0,
    "Tc": 100.0,
    "Density": 0.5,
    "Young's modulus": 20.0,
    "Poisson ratio": 0.05,
    "Hardness": 2.0,
    "Nd": 0.05,
    "Vd": 10.0,
    "Viscosity": 2.0,
    "ε": 2.0,
    "tanδ": 0.01,
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
            result[prop] = float(df[col].iloc[0])
    return result


# ── Bayesian Optimization ──────────────────────────────────────────

def _build_search_space(
    oxides_wt: dict[str, float],
) -> tuple[list[str], list[tuple[float, float]]]:
    """Build (oxide_names, bounds) from current wt% composition."""
    names: list[str] = []
    bounds: list[tuple[float, float]] = []
    for formula, wt in oxides_wt.items():
        names.append(formula)
        if wt <= 0:
            bounds.append((0.0, 15.0))
        else:
            delta = max(wt * 0.3, 5.0)
            lo = max(0.0, wt - delta)
            hi = min(100.0, wt + delta)
            bounds.append((lo, hi))
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


def recommend_composition(
    oxides_wt: dict[str, float],
    property_targets: list[dict[str, Any]],
    max_oxides: int | None = None,
    n_candidates: int = 5,
    n_calls: int = 80,
) -> list[dict[str, Any]]:
    """Recommend optimised glass compositions via Bayesian optimisation.

    Args:
        oxides_wt: Current composition in wt%.
        property_targets: List of ``{property, mode, target, min, max}``.
        max_oxides: Max number of oxides with wt > 0.5%. ``None`` = no limit.
        n_candidates: Number of candidates to return.
        n_calls: Total evaluations for the optimiser.

    Returns:
        List of candidates sorted by score (ascending):
        ``[{oxides_wt: {…}, predicted: {…}, score: float}]``
    """
    from skopt import gp_minimize
    from skopt.space import Real

    oxide_names, bounds = _build_search_space(oxides_wt)

    # Priority weights: rank 0 → 1.0, rank 1 → 0.5, rank 2 → 0.25, …
    weights = [0.5 ** i for i in range(len(property_targets))]

    dimensions = [Real(lo, hi, name=name) for name, (lo, hi) in zip(oxide_names, bounds)]

    result = gp_minimize(
        func=lambda x: _objective(x, oxide_names, property_targets, weights),
        dimensions=dimensions,
        n_calls=n_calls,
        n_random_starts=min(20, n_calls // 3),
        random_state=42,
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

        # max_oxides filter
        if max_oxides is not None:
            n_active = sum(1 for v in wt_norm.values() if v > 0.5)
            if n_active > max_oxides:
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
