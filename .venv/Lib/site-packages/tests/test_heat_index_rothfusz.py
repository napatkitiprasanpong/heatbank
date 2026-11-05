import numpy as np
import pytest

from pythermalcomfort.models import heat_index_rothfusz
from tests.conftest import Urls, retrieve_reference_table, validate_result


def test_heat_index(get_test_url, retrieve_data) -> None:
    """Test the heat index function with various inputs."""
    reference_table = retrieve_reference_table(
        get_test_url,
        retrieve_data,
        Urls.HEAT_INDEX.name,
    )
    tolerance = reference_table["tolerance"]

    for entry in reference_table["data"]:
        inputs = entry["inputs"]
        outputs = entry["outputs"]
        result = heat_index_rothfusz(**inputs, limit_inputs=False)

        validate_result(result, outputs, tolerance)


def test_single_input_caution() -> None:
    """Test that the function returns a single value with caution category."""
    result = heat_index_rothfusz(tdb=29, rh=50, round_output=True)
    assert result.hi.shape == ()  # zero-dim ndarray
    assert result.hi.item() == pytest.approx(29.7, rel=1e-3)
    assert result.stress_category == "caution"


def test_below_threshold_produces_nan() -> None:
    """Test that the function returns NaN for heat index below threshold."""
    with pytest.warns(UserWarning):
        result = heat_index_rothfusz(tdb=25, rh=80)
    assert np.isnan(result.hi).item()
    assert np.isnan(result.stress_category)


def test_below_threshold_warns_scalar() -> None:
    """Scalar tdb below 27°C triggers a UserWarning with the specific value."""
    with pytest.warns(UserWarning, match=r"'tdb' has value 25\.0.*\[27\.0, inf\]"):
        heat_index_rothfusz(tdb=25, rh=80)


def test_below_threshold_warns_array() -> None:
    """Array with tdb below 27°C triggers a UserWarning with indices and values."""
    with pytest.warns(UserWarning, match=r"'tdb'.*\[20\.0\].*\[1\]"):
        result = heat_index_rothfusz(tdb=[30.0, 20.0, 28.5], rh=[70.0, 90.0, 50.0])
    assert np.isnan(result.hi[1])
    assert np.isfinite(result.hi[0]) and np.isfinite(result.hi[2])


def test_limit_inputs_false_no_warning(recwarn) -> None:
    """With limit_inputs=False, no UserWarning is raised for out-of-range tdb."""
    result = heat_index_rothfusz(tdb=25, rh=80, limit_inputs=False)
    assert len(recwarn) == 0
    assert np.isfinite(result.hi)


def test_vector_input_no_rounding() -> None:
    """Test that the function handles vector inputs correctly without rounding."""
    tdb = [30.0, 20.0, 28.5]
    rh = [70.0, 90.0, 50.0]
    with pytest.warns(UserWarning):
        result = heat_index_rothfusz(tdb=tdb, rh=rh, round_output=False)
    hi = result.hi
    # Shape matches inputs
    assert hi.shape == (3,)
    # First element has multiple decimals and matches expected formula
    assert hi[0] == pytest.approx(35.33, rel=1e-2)
    # Second element below threshold ⇒ NaN
    assert np.isnan(hi[1])
    # Third element above threshold ⇒ finite number
    assert np.isfinite(hi[2])
    # Stress categories array matches hi length
    assert isinstance(result.stress_category, np.ndarray)
    assert result.stress_category.shape == (3,)
    assert result.stress_category[0] == "extreme caution"


@pytest.mark.parametrize(
    ("tdb", "boundary", "category"),
    [
        (26.583615, 27.0, "caution"),
        (30.645013, 32.0, "extreme caution"),
        (35.152822, 41.0, "danger"),
        (39.775673, 54.0, "extreme danger"),
    ],
)
def test_category_uses_unrounded_heat_index(tdb, boundary, category) -> None:
    """Keep the higher category when display rounding reaches a bin edge."""
    rounded = heat_index_rothfusz(tdb, 50, limit_inputs=False)
    unrounded = heat_index_rothfusz(tdb, 50, round_output=False, limit_inputs=False)

    assert boundary < unrounded.hi < boundary + 0.05
    assert rounded.hi == boundary
    assert rounded.stress_category == unrounded.stress_category == category


@pytest.mark.parametrize("round_output", [True, False])
def test_category_rounding_with_broadcast_and_invalid_input(round_output) -> None:
    """Classify unrounded array values while preserving the applicability mask."""
    with pytest.warns(UserWarning):
        result = heat_index_rothfusz(
            [30.645013, 35.152822, 39.775673, 25],
            50,
            round_output=round_output,
        )

    np.testing.assert_array_equal(
        result.stress_category[:3], ["extreme caution", "danger", "extreme danger"]
    )
    assert np.isnan(result.hi[3])
    assert np.isnan(result.stress_category[3])
