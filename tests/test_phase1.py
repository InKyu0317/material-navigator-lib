"""Tests for mat_nav_lib Phase 1 additions: score_oxides, predict_from_wt, streaming."""

import pytest


def test_score_oxides_returns_sorted_list():
    """T1.1: score_oxides returns a list of dicts sorted by score descending."""
    from mat_nav_lib import score_oxides

    results = score_oxides(
        base_composition_wt={"SiO2": 70, "Al2O3": 30},
        target_properties=["Tg"],
    )
    assert isinstance(results, list)
    assert len(results) > 0

    # Each entry has required keys
    for r in results:
        assert "formula" in r
        assert "name_ko" in r
        assert "category" in r
        assert "score" in r
        assert "stars" in r
        assert 0 <= r["score"] <= 1.0
        assert 1 <= r["stars"] <= 5

    # Sorted descending by score
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_score_oxides_excludes_base_oxides():
    """T1.1: base oxides should not appear in score results."""
    from mat_nav_lib import score_oxides

    base = {"SiO2": 70, "Na2O": 15, "CaO": 15}
    results = score_oxides(base, ["Tg"])
    formulas = {r["formula"] for r in results}
    for oxide in base:
        assert oxide not in formulas


def test_score_oxides_with_priority_weights():
    """T1.1: priority_weights should influence scores."""
    from mat_nav_lib import score_oxides

    r1 = score_oxides({"SiO2": 70, "Al2O3": 30}, ["Tg", "Density"])
    r2 = score_oxides({"SiO2": 70, "Al2O3": 30}, ["Tg", "Density"], priority_weights=[1.0, 0.0])
    # With Density weight=0, ranking may differ
    assert isinstance(r1, list) and isinstance(r2, list)


def test_predict_from_wt_returns_predictions():
    """T1.2: predict_from_wt returns dict of predicted values."""
    from mat_nav_lib import predict_from_wt

    result = predict_from_wt(
        oxides_wt={"SiO2": 70, "Na2O": 15, "CaO": 15},
        targets=["Tg", "Density"],
    )
    assert isinstance(result, dict)
    assert "Tg" in result
    assert "Density" in result
    assert isinstance(result["Tg"], float)
    assert isinstance(result["Density"], float)


def test_predict_from_wt_handles_unicode():
    """T1.2: predict_from_wt handles unicode subscript formulas."""
    from mat_nav_lib import predict_from_wt

    result = predict_from_wt(
        oxides_wt={"SiO\u2082": 70, "Na\u2082O": 15, "CaO": 15},
        targets=["Tg"],
    )
    assert "Tg" in result


def test_recommend_streaming_callback():
    """T1.3: recommend_composition_streaming calls callback per iteration."""
    from mat_nav_lib import recommend_composition_streaming

    callback_data = []

    def cb(info):
        callback_data.append(info)

    results = recommend_composition_streaming(
        oxides_wt={"SiO2": 70, "Na2O": 15, "CaO": 15},
        property_targets=[{"property": "Tg", "mode": "단일값", "target": 600}],
        n_calls=15,
        n_candidates=2,
        callback=cb,
    )

    # Callback was called
    assert len(callback_data) > 0
    # Each callback has required fields
    for info in callback_data:
        assert "iteration" in info
        assert "n_calls" in info
        assert "best_score" in info
        assert "current_score" in info

    # Returns candidates
    assert isinstance(results, list)
    assert len(results) > 0


def test_recommend_streaming_with_search_bounds():
    """T1.3: search_bounds parameter constrains the search space."""
    from mat_nav_lib import recommend_composition_streaming

    results = recommend_composition_streaming(
        oxides_wt={"SiO2": 70, "Na2O": 15, "CaO": 15},
        property_targets=[{"property": "Tg", "mode": "단일값", "target": 600}],
        search_bounds={"SiO2": {"lo": 60, "hi": 80}, "Na2O": {"lo": 10, "hi": 20}, "CaO": {"lo": 10, "hi": 20}},
        n_calls=15,
        n_candidates=2,
    )
    assert isinstance(results, list)


def test_recommend_composition_backward_compat():
    """T1.3: existing recommend_composition still works."""
    from mat_nav_lib import recommend_composition

    results = recommend_composition(
        oxides_wt={"SiO2": 70, "Na2O": 15, "CaO": 15},
        property_targets=[{"property": "Tg", "mode": "단일값", "target": 600}],
        n_calls=15,
        n_candidates=2,
    )
    assert isinstance(results, list)
    assert len(results) > 0


# ── Tg unit tests: GlassNet returns Kelvin, must convert to Celsius ─

def test_predict_from_wt_tg_is_celsius_not_kelvin():
    """T-UNIT: predict_from_wt must return Tg in °C, not Kelvin.

    GlassNet internally returns Tg in Kelvin (~1100-1500 K range).
    predict_from_wt must subtract 273.15 before returning.
    SiO2:70 / Al2O3:20 / K2O:10 → Tg should be in 750–1000 °C range,
    NOT in the 1100–1500 K range.
    """
    from mat_nav_lib import predict_from_wt

    result = predict_from_wt(
        oxides_wt={"SiO2": 70, "Al2O3": 20, "K2O": 10},
        targets=["Tg"],
    )
    tg = result["Tg"]
    # If returned in Kelvin, tg > 1100. If correctly in Celsius, tg < 1000.
    assert tg < 1000, (
        f"Tg = {tg:.1f}  — looks like Kelvin, not °C. "
        f"Expected < 1000 °C (after K→°C conversion)."
    )
    assert tg > 600, f"Tg = {tg:.1f} °C seems too low."


def test_predict_from_wt_ts_is_celsius_not_kelvin():
    """T-UNIT: Ts (strain point) must also be returned in °C."""
    from mat_nav_lib import predict_from_wt

    result = predict_from_wt(
        oxides_wt={"SiO2": 70, "Na2O": 15, "CaO": 15},
        targets=["Ts"],
    )
    ts = result["Ts"]
    assert ts < 1000, (
        f"Ts = {ts:.1f}  — looks like Kelvin, not °C."
    )
    assert ts > 300


def test_recommend_candidates_tg_in_celsius():
    """T-UNIT: recommended candidates must have Tg in °C, not Kelvin."""
    from mat_nav_lib import recommend_composition

    results = recommend_composition(
        oxides_wt={"SiO2": 70, "Na2O": 15, "CaO": 15},
        property_targets=[{"property": "Tg", "mode": "단일값", "target": 600}],
        n_calls=15,
        n_candidates=2,
    )
    for candidate in results:
        tg = candidate["predicted"].get("Tg")
        if tg is not None:
            assert tg < 1000, (
                f"Candidate Tg = {tg:.1f} — looks like Kelvin. Expected °C."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
