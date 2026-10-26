import sys
from unittest.mock import MagicMock, patch
import pytest
import logic as logic_mod
from logic import AstrologyLogic


@pytest.fixture(autouse=True)
def _clear_geocode_cache():
    logic_mod._cached_geocode.cache_clear()
    yield
    logic_mod._cached_geocode.cache_clear()

def test_get_location_coordinates_success():
    """Test successful geocoding."""
    with patch('logic.ArcGIS') as mock_arcgis:
        mock_geolocator = MagicMock()
        mock_arcgis.return_value = mock_geolocator

        mock_location = MagicMock()
        mock_location.latitude = 25.0330
        mock_location.longitude = 121.5654
        mock_geolocator.geocode.return_value = mock_location

        logic = AstrologyLogic()
        coords = logic.get_location_coordinates("Taipei")

        assert coords == (25.0330, 121.5654)
        mock_geolocator.geocode.assert_called_once_with("Taipei", timeout=10)

def test_get_location_coordinates_none():
    """Test geocoding returning None."""
    with patch('logic.ArcGIS') as mock_arcgis:
        mock_geolocator = MagicMock()
        mock_arcgis.return_value = mock_geolocator

        mock_geolocator.geocode.return_value = None

        logic = AstrologyLogic()
        coords = logic.get_location_coordinates("Unknown Place")

        assert coords is None
        mock_geolocator.geocode.assert_called_once_with("Unknown Place", timeout=10)

def test_get_location_coordinates_exception():
    """Test geocoding raising an exception."""
    with patch('logic.ArcGIS') as mock_arcgis:
        mock_geolocator = MagicMock()
        mock_arcgis.return_value = mock_geolocator

        mock_geolocator.geocode.side_effect = Exception("Service unavailable")

        logic = AstrologyLogic()
        coords = logic.get_location_coordinates("Taipei")

        # Should return None when an exception occurs
        assert coords is None
        mock_geolocator.geocode.assert_called_once_with("Taipei", timeout=10)


def test_flatlib_compat_calc_ut_two_tuple():
    """Old flatlib + new pyswisseph: calc_ut returns (coords, flg), no IndexError."""
    from flatlib import const
    from flatlib.ephem import swe as fswe
    import swisseph
    logic_mod._apply_flatlib_compat()
    fake = ((100.0, 1.0, 1.0, 0.5, 0.1, 0.0), 258)
    with patch.object(swisseph, 'calc_ut', return_value=fake):
        obj = fswe.sweObject(const.SUN, 2451545.0)
        assert obj['lon'] == 100.0 and obj['lonspeed'] == 0.5 and obj['latspeed'] == 0.1
        assert fswe.sweObjectLon(const.SUN, 2451545.0) == 100.0
    flat = (7.0, 2.0, 1.0, 0.3, 0.2, 0.0)
    with patch.object(swisseph, 'calc_ut', return_value=flat):
        assert fswe.sweObject(const.MOON, 2451545.0)['lonspeed'] == 0.3


def test_flatlib_compat_chart_and_ascdiff():
    from flatlib import const, utils
    from flatlib.chart import Chart
    from flatlib.datetime import Datetime
    from flatlib.geopos import GeoPos
    logic_mod._apply_flatlib_compat()
    chart = Chart(Datetime('2000/01/01', '12:00', '+00:00'), GeoPos(25.03, 121.56))
    assert chart.get(const.SUN).lon is not None
    assert utils.ascdiff(23.5, 89.99) == pytest.approx(90.0)
