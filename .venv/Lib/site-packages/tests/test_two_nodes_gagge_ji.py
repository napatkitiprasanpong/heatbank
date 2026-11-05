import numpy as np
import pytest

from pythermalcomfort.models import two_nodes_gagge_ji
from pythermalcomfort.psychrometrics import p_sat_torr
from pythermalcomfort.utilities import body_surface_area


def test_two_nodes_gagge_ji_complete_time_series_regression() -> None:
    """Pin scalar and array time-series outputs from the pre-Numba implementation."""
    weight = 80.1
    bsa = body_surface_area(weight=weight, height=1.8)
    common = {
        "wme": 0,
        "body_surface_area": bsa,
        "p_atm": 101325,
        "position": "sitting",
        "acclimatized": True,
        "body_weight": weight,
    }

    scalar_result = two_nodes_gagge_ji(
        tdb=36.5,
        tr=36.5,
        v=0.25,
        met=0.95,
        clo=0.1,
        vapor_pressure=20 * p_sat_torr(tdb=36.5) / 100,
        length_time_simulation=6,
        **common,
    )
    assert isinstance(scalar_result.t_core, np.ndarray)
    assert isinstance(scalar_result.t_skin, np.ndarray)
    assert scalar_result.t_core.shape == (6,)
    assert scalar_result.t_skin.shape == (6,)
    np.testing.assert_allclose(
        scalar_result.t_core,
        [
            36.516105213824275,
            36.547685700888465,
            36.576012449954796,
            36.60164288217578,
            36.62502377928286,
            36.64651422522319,
        ],
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        scalar_result.t_skin,
        [
            36.774035566875106,
            36.40807561844041,
            36.11486504764158,
            35.87955212231442,
            35.69038774391016,
            35.53809246343035,
        ],
        rtol=1e-12,
        atol=1e-12,
    )

    array_result = two_nodes_gagge_ji(
        tdb=[36.5, 31.0],
        tr=[36.5, 31.5],
        v=[0.25, 0.2],
        met=[0.95, 0.7],
        clo=[0.1, 0.67],
        vapor_pressure=[
            20 * p_sat_torr(tdb=36.5) / 100,
            60 * p_sat_torr(tdb=31.0) / 100,
        ],
        length_time_simulation=4,
        **common,
    )
    assert isinstance(array_result.t_core, list)
    assert isinstance(array_result.t_skin, list)
    assert [values.shape for values in array_result.t_core] == [(4,), (4,)]
    assert [values.shape for values in array_result.t_skin] == [(4,), (4,)]
    np.testing.assert_allclose(
        array_result.t_core,
        [
            [
                36.516105213824275,
                36.547685700888465,
                36.576012449954796,
                36.60164288217578,
            ],
            [
                36.51006711047728,
                36.534910362727736,
                36.5569230515869,
                36.57647015573995,
            ],
        ],
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        array_result.t_skin,
        [
            [
                36.774035566875106,
                36.40807561844041,
                36.11486504764158,
                35.87955212231442,
            ],
            [
                36.67827501809432,
                36.34939739292867,
                36.064690097764036,
                35.81939854020882,
            ],
        ],
        rtol=1e-12,
        atol=1e-12,
    )


def test_two_nodes_gagge_ji_multidimensional_broadcast_output() -> None:
    """Each broadcast input element produces one independent time series."""
    inputs = {
        "v": 0.25,
        "met": 0.95,
        "clo": 0.1,
        "vapor_pressure": 20 * p_sat_torr(tdb=36.5) / 100,
        "length_time_simulation": 4,
    }
    result = two_nodes_gagge_ji(
        tdb=np.array([[36.5], [31.0]]),
        tr=np.array([36.5, 31.5]),
        **inputs,
    )
    expected = [
        two_nodes_gagge_ji(tdb=tdb, tr=tr, **inputs)
        for tdb in (36.5, 31.0)
        for tr in (36.5, 31.5)
    ]

    assert isinstance(result.t_core, list)
    assert isinstance(result.t_skin, list)
    assert [values.shape for values in result.t_core] == [(4,)] * 4
    assert [values.shape for values in result.t_skin] == [(4,)] * 4
    np.testing.assert_allclose(
        result.t_core, [item.t_core for item in expected], rtol=1e-12, atol=1e-12
    )
    np.testing.assert_allclose(
        result.t_skin, [item.t_skin for item in expected], rtol=1e-12, atol=1e-12
    )


# Scenarios based on Table 4 from the paper by Ji et al. (2022)
@pytest.mark.parametrize(
    (
        "tdb",
        "tr",
        "v",
        "met",
        "clo",
        "rh",
        "weight",
        "height",
        "expected_t_core",
        "expected_t_skin",
        "duration",
    ),
    [
        # Scenario 1
        (
            36.5,  # tdb
            36.5,  # tr
            0.25,  # v
            0.95,  # met
            0.1,  # clo
            20,  # rh
            80.1,  # body_weight (kg)
            1.8,  # height (m)
            37.446339126254756,  # expected t_core[-1]
            34.596469729370725,  # expected t_skin[-1]
            120,  # length_time_simulation
        ),
        # Scenario 2
        (
            36.5,
            36.5,
            0.25,
            0.96,
            0.1,
            60,
            80.1,
            1.8,
            37.512644583008566,
            34.85861523864417,
            120,
        ),
        # Scenario 3
        (
            31,
            31,
            0.2,
            0.7,
            0.67,
            60,
            55.7,
            1.525,
            37.16672342773386,
            34.29506493710769,
            150,
        ),
        # Scenario 4
        (
            27,
            27,
            0.2,
            0.7,
            0.67,
            60,
            55.7,
            1.525,
            36.69341582589469,
            33.64236786746656,
            150,
        ),
    ],
)
def test_two_nodes_gagge_ji_examples(
    tdb: float,
    tr: float,
    v: float,
    met: float,
    clo: float,
    rh: float,
    weight: float,
    height: float,
    expected_t_core: float,
    expected_t_skin: float,
    duration: int,
) -> None:
    """Test the two_nodes_gagge_ji function with predefined scenarios."""
    # compute vapor pressure from relative humidity and saturation vapor pressure
    vapor_pressure = rh * p_sat_torr(tdb=tdb) / 100

    # compute body surface area
    bsa = body_surface_area(weight=weight, height=height)

    result = two_nodes_gagge_ji(
        tdb=tdb,
        tr=tr,
        v=v,
        met=met,
        clo=clo,
        vapor_pressure=vapor_pressure,
        wme=0,
        body_surface_area=bsa,
        p_atm=101325,
        position="sitting",
        acclimatized=True,
        body_weight=weight,
        length_time_simulation=duration,
    )

    t_core_last = result["t_core"][-1]
    t_skin_last = result["t_skin"][-1]

    assert t_core_last == pytest.approx(expected_t_core, rel=1e-3)
    assert t_skin_last == pytest.approx(expected_t_skin, rel=1e-3)


def test_two_nodes_gagge_ji_list_tdb() -> None:
    """Test that the function can handle a list of tdb values."""
    tdb_list = [36.5, 36.5]
    tr = 36.5
    v = 0.25
    met = 0.95
    clo = 0.1
    rh = 20
    weight = 80.1
    height = 1.8
    sim_time = 120

    vapor_pressure = rh * p_sat_torr(tdb=36.5) / 100
    bsa = body_surface_area(weight=weight, height=height)

    result = two_nodes_gagge_ji(
        tdb=tdb_list,
        tr=tr,
        v=v,
        met=met,
        clo=clo,
        vapor_pressure=vapor_pressure,
        wme=0,
        body_surface_area=bsa,
        p_atm=101325,
        position="sitting",
        acclimatized=True,
        body_weight=weight,
        length_time_simulation=sim_time,
    )

    # expect two simulation results (one per tdb entry)
    t_core_list = result.t_core
    t_skin_list = result.t_skin

    assert isinstance(t_core_list, list)
    assert len(t_core_list) == 2
    assert isinstance(t_skin_list, list)
    assert len(t_skin_list) == 2

    # both simulations should yield the same final values as scenario 1
    expected_t_core = 37.446
    expected_t_skin = 34.596

    for core_arr, skin_arr in zip(t_core_list, t_skin_list, strict=False):
        assert core_arr[-1] == pytest.approx(expected_t_core, rel=1e-3)
        assert skin_arr[-1] == pytest.approx(expected_t_skin, rel=1e-3)


def test_invalid_position_raises_value_error() -> None:
    """Test that an invalid position raises a ValueError."""
    with pytest.raises(ValueError):
        two_nodes_gagge_ji(
            tdb=36.5,
            tr=36.5,
            v=0.25,
            met=0.95,
            clo=0.1,
            vapor_pressure=20 * p_sat_torr(tdb=36.5) / 100,
            wme=0,
            body_surface_area=body_surface_area(weight=80.1, height=1.8),
            p_atm=101325,
            position="lying",  # invalid posture
            acclimatized=True,
            body_weight=80.1,
            length_time_simulation=120,
        )


def test_unexpected_kwarg_raises_type_error() -> None:
    """Test that an unexpected keyword argument raises a TypeError."""
    with pytest.raises(TypeError) as excinfo:
        two_nodes_gagge_ji(
            tdb=36.5,
            tr=36.5,
            v=0.25,
            met=0.95,
            clo=0.1,
            vapor_pressure=20 * p_sat_torr(tdb=36.5) / 100,
            wme=0,
            body_surface_area=body_surface_area(weight=80.1, height=1.8),
            p_atm=101325,
            position="sitting",
            acclimatized=True,
            body_weight=80.1,
            length_time_simulation=120,
            foo="bar",  # unexpected argument
        )
    assert "Unexpected keyword arguments: ['foo']" in str(excinfo.value)


def test_non_numeric_tdb_raises_type_error() -> None:
    """Test that a non-numeric tdb raises a TypeError."""
    with pytest.raises(TypeError):
        two_nodes_gagge_ji(
            tdb="hot",  # invalid type
            tr=36.5,
            v=0.25,
            met=0.95,
            clo=0.1,
            vapor_pressure=20 * p_sat_torr(tdb=36.5) / 100,
            wme=0,
            body_surface_area=body_surface_area(weight=80.1, height=1.8),
            p_atm=101325,
            position="sitting",
            acclimatized=True,
            body_weight=80.1,
            length_time_simulation=120,
        )
