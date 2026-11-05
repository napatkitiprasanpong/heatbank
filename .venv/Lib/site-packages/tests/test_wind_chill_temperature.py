import numpy as np
import pytest

from pythermalcomfort.models.wind_chill_temperature import wind_chill_temperature
from tests.conftest import Urls, retrieve_reference_table, validate_result


def test_wind_chill_temperature(get_test_url, retrieve_data) -> None:
    """Test the wind_chill_temperature model against the shared validation table."""
    reference_table = retrieve_reference_table(
        get_test_url,
        retrieve_data,
        Urls.WIND_CHILL_TEMPERATURE.name,
    )
    tolerance = reference_table["tolerance"]

    for entry in reference_table["data"]:
        inputs = entry["inputs"]
        outputs = entry["outputs"]
        result = wind_chill_temperature(**inputs)

        validate_result(result, outputs, tolerance)


class TestWct:
    """Test cases for the wind chill temperature (WCT) model not covered by the validation table."""

    def test_wct_single_float_inputs(self) -> None:
        """Test that scalar inputs produce a scalar float result."""
        result = wind_chill_temperature(tdb=-5.0, v=5.5)

        assert isinstance(result.wct, float)
        assert round(result.wct, 1) == -7.5

    def test_wct_empty_lists(self) -> None:
        """Test that empty list inputs return an empty array."""
        assert np.allclose(
            wind_chill_temperature(tdb=[], v=[]).wct, np.asarray([]), equal_nan=True
        )

    def test_wct_list_inputs(self) -> None:
        """Test that list inputs are broadcast and return an ndarray."""
        result = wind_chill_temperature(
            tdb=[-5.0, -10.0], v=[5.5, 10.0], round_output=True
        )

        assert isinstance(result.wct, np.ndarray)
        assert np.allclose(result.wct, [-7.5, -15.3], atol=0.1)

    def test_wct_round_output_false_returns_unrounded(self) -> None:
        """Test that round_output=False bypasses rounding and returns the formula output.

        The shared validation table tolerates 0.1 K on wct, which is wider than the
        rounding step itself, so a regression that ignored round_output=False and
        returned -7.5 would still pass the fixture row. This local assertion pins
        the unrounded value tightly.
        """
        result = wind_chill_temperature(tdb=-5.0, v=5.5, round_output=False)

        expected = 13.12 + 0.6215 * -5.0 - 11.37 * 5.5**0.16 + 0.3965 * -5.0 * 5.5**0.16
        assert result.wct == pytest.approx(expected, abs=1e-9)
        assert result.wct != -7.5

    def test_wct_non_numeric_inputs(self) -> None:
        """Test that non-numeric inputs raise a TypeError."""
        with pytest.raises(TypeError):
            wind_chill_temperature(tdb="invalid", v=5.5)

        with pytest.raises(TypeError):
            wind_chill_temperature(tdb=-5.0, v="invalid")

        with pytest.raises(TypeError):
            wind_chill_temperature(tdb="invalid", v="invalid")
