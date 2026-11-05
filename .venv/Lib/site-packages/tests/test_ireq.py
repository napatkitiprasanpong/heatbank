import numpy as np
import pytest

from pythermalcomfort.classes_return import IREQ
from pythermalcomfort.models import ireq

MET_116_W_M2 = 116.0 / 58.15
MET_175_W_M2 = 175.0 / 58.15
MET_400_W_M2 = 400.0 / 58.15


def test_ireq_scalar_example():
    result = ireq(
        tdb=-15.0,
        tr=-15.0,
        vr=2.0,
        rh=55.0,
        met=MET_175_W_M2,
        clo=2.8,
        p=50.0,
        walk_sp=1.1,
    )

    assert isinstance(result, IREQ)
    assert result.ireq_min == 1.6
    assert result.ireq_neutral == 1.9
    assert result.icl_min == 2.2
    assert result.icl_neutral == 2.6
    assert result.dle_min == "more than 8"
    assert result.dle_neutral == "more than 8"


@pytest.mark.parametrize(
    (
        "tdb",
        "tr",
        "vr",
        "met_w_m2",
        "clo",
        "expected_ireq_neutral",
        "expected_icl_neutral",
        "expected_dle_neutral",
    ),
    [
        (0, 0, 2, 90, 2.5, 2.6, 3.1, 2.3),
        (0, 0, 2, 145, 2.5, 1.5, 1.8, "more than 8"),
        (-10, -10, 2, 90, 2.5, 3.5, 4.4, 0.7),
        (-10, 0, 2, 145, 2.4, 1.9, 2.4, "more than 8"),
        (-20, -20, 2, 115, 4.2, 3.4, 4.2, "more than 8"),
        (-20, -20, 7, 115, 4.2, 3.5, 5.9, 1.1),
        (-30, -30, 2, 115, 4.2, 4.0, 5.0, 2.2),
        (-30, -30, 5, 175, 4.2, 2.6, 4.0, "more than 8"),
    ],
)
def test_ireq_iso_11079_table_f1(
    tdb,
    tr,
    vr,
    met_w_m2,
    clo,
    expected_ireq_neutral,
    expected_icl_neutral,
    expected_dle_neutral,
):
    walk_sp = max(0.5, min(0.0052 * (met_w_m2 - 58.0), 1.2))

    result = ireq(
        tdb=tdb,
        tr=tr,
        vr=vr,
        rh=85,
        met=met_w_m2 / 58.15,
        clo=clo,
        p=8,
        walk_sp=walk_sp,
        wme=0,
    )

    assert result.ireq_neutral == pytest.approx(expected_ireq_neutral, abs=0.11)
    assert result.icl_neutral == pytest.approx(expected_icl_neutral, abs=0.11)

    if expected_dle_neutral == "more than 8":
        assert result.dle_neutral == expected_dle_neutral
    else:
        assert result.dle_neutral == pytest.approx(expected_dle_neutral, abs=0.21)


def test_ireq_vectorized_inputs():
    result = ireq(
        tdb=[-15.0, -10.0],
        tr=[-15.0, -10.0],
        vr=[2.0, 1.0],
        rh=[55.0, 50.0],
        met=[MET_175_W_M2, MET_116_W_M2],
        clo=[2.8, 1.5],
        p=[50.0, 8.0],
        walk_sp=[1.1, 0.31],
    )

    assert np.allclose(result.ireq_min[0], 1.6)
    assert np.allclose(result.ireq_neutral[0], 1.9)
    assert np.allclose(result.icl_min[0], 2.2)
    assert np.allclose(result.icl_neutral[0], 2.6)
    assert result.dle_min[0] == "more than 8"
    assert result.dle_neutral[0] == "more than 8"

    assert np.allclose(result.ireq_min[1], 2.2)
    assert np.allclose(result.ireq_neutral[1], 2.6)
    assert np.allclose(result.icl_min[1], 2.5)
    assert np.allclose(result.icl_neutral[1], 2.9)
    assert np.allclose(result.dle_min[1], 0.8)
    assert np.allclose(result.dle_neutral[1], 0.6)


def test_ireq_limit_inputs_returns_nan_outside_iso_range():
    params = {
        "tdb": -15.0,
        "tr": -15.0,
        "vr": 0.2,
        "rh": 55.0,
        "met": MET_175_W_M2,
        "clo": 2.8,
        "p": 50.0,
        "walk_sp": 1.1,
    }

    result_limited = ireq(**params)
    assert np.isnan(result_limited.ireq_min)
    assert np.isnan(result_limited.ireq_neutral)
    assert np.isnan(result_limited.icl_min)
    assert np.isnan(result_limited.icl_neutral)
    assert np.isnan(result_limited.dle_min)
    assert np.isnan(result_limited.dle_neutral)

    result_unlimited = ireq(**params, limit_inputs=False)
    assert np.isfinite(result_unlimited.ireq_min)
    assert np.isfinite(result_unlimited.ireq_neutral)
    assert np.isfinite(result_unlimited.icl_min)
    assert np.isfinite(result_unlimited.icl_neutral)


def test_ireq_accepts_upper_met_boundary_with_max_walk_speed():
    result = ireq(
        tdb=-15.0,
        tr=-15.0,
        vr=2.0,
        rh=55.0,
        met=MET_400_W_M2,
        clo=2.8,
        p=50.0,
        walk_sp=1.2,
    )

    assert result.ireq_min == 0.3
    assert result.ireq_neutral == 0.6
    assert result.icl_min == 0.4
    assert result.icl_neutral == 0.8


def test_ireq_uses_wme_met_units_and_numeric_dle():
    result = ireq(
        tdb=-15.0,
        tr=-15.0,
        vr=2.0,
        rh=55.0,
        met=MET_175_W_M2,
        clo=2.8,
        p=50.0,
        walk_sp=1.1,
        wme=1.0,
    )

    assert result.ireq_min == 2.7
    assert result.ireq_neutral == 3.2
    assert result.icl_min == 3.8
    assert result.icl_neutral == 4.5
    assert result.dle_min == 1.3
    assert result.dle_neutral == 0.8


def test_ireq_non_physical_outputs_masked_before_rounding():
    result = ireq(
        tdb=10.0,
        tr=10.0,
        vr=0.4,
        rh=0.0,
        met=250.0 / 58.15,
        clo=0.0,
        p=1.0,
        walk_sp=0.9984,
    )

    assert np.isnan(result.ireq_min)
    assert np.isnan(result.icl_min)
    assert np.isnan(result.dle_min)


def test_ireq_non_physical_outputs_not_masked_when_limit_inputs_false():
    params = {
        "tdb": 10.0,
        "tr": 10.0,
        "vr": 0.4,
        "rh": 0.0,
        "met": 350.0 / 58.15,
        "clo": 0.0,
        "p": 1.0,
        "walk_sp": 0.9984,
    }

    result_limited = ireq(**params)
    assert np.isnan(result_limited.ireq_min)
    assert np.isnan(result_limited.icl_min)

    result_unlimited = ireq(**params, limit_inputs=False)
    assert result_unlimited.ireq_min < 0
    assert result_unlimited.icl_min < 0


def test_ireq_invalid_physical_inputs_raise():
    params = {
        "tdb": -15.0,
        "tr": -15.0,
        "vr": 2.0,
        "rh": 55.0,
        "met": MET_175_W_M2,
        "clo": 2.8,
        "p": 50.0,
        "walk_sp": 1.1,
    }

    with pytest.raises(ValueError, match="Air permeability"):
        ireq(**{**params, "p": -10.0})

    with pytest.raises(ValueError, match="Relative humidity"):
        ireq(**{**params, "rh": 105.0})

    with pytest.raises(ValueError, match="Clothing insulation"):
        ireq(**{**params, "clo": -1.0})

    with pytest.raises(ValueError, match="Walking speed"):
        ireq(**{**params, "walk_sp": -0.1})


def test_ireq_broadcasts_mixed_scalar_and_array_inputs():
    result = ireq(
        tdb=[-15.0, -10.0],
        tr=-15.0,
        vr=2.0,
        rh=55.0,
        met=MET_175_W_M2,
        clo=2.8,
        p=50.0,
        walk_sp=1.1,
    )

    assert result.ireq_min.shape == (2,)
    assert result.ireq_neutral.shape == (2,)
    assert np.allclose(result.ireq_min, [1.6, 1.4])
    assert np.allclose(result.ireq_neutral, [1.9, 1.7])


def test_ireq_public_api_export():
    from pythermalcomfort.models.ireq import ireq as implementation_ireq

    assert ireq is implementation_ireq
