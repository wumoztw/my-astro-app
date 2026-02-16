import sys
from unittest.mock import MagicMock, patch

# Mock external dependencies before importing logic
mock_swisseph = MagicMock()
sys.modules['swisseph'] = mock_swisseph

mock_const = MagicMock()
mock_const.SUN = 'Sun'
mock_const.MOON = 'Moon'
mock_const.MERCURY = 'Mercury'
mock_const.VENUS = 'Venus'
mock_const.MARS = 'Mars'
mock_const.JUPITER = 'Jupiter'
mock_const.SATURN = 'Saturn'
mock_const.ASC = 'Asc'
mock_const.ARIES = 'Aries'
mock_const.TAURUS = 'Taurus'
mock_const.GEMINI = 'Gemini'
mock_const.CANCER = 'Cancer'
mock_const.LEO = 'Leo'
mock_const.VIRGO = 'Virgo'
mock_const.LIBRA = 'Libra'
mock_const.SCORPIO = 'Scorpio'
mock_const.SAGITTARIUS = 'Sagittarius'
mock_const.CAPRICORN = 'Capricorn'
mock_const.AQUARIUS = 'Aquarius'
mock_const.PISCES = 'Pisces'
mock_const.LIST_SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

sys.modules['flatlib'] = MagicMock()
sys.modules['flatlib.const'] = mock_const
sys.modules['flatlib.chart'] = MagicMock()
sys.modules['flatlib.datetime'] = MagicMock()
sys.modules['flatlib.geopos'] = MagicMock()

mock_streamlit = MagicMock()
mock_streamlit.cache_data = lambda x: x
mock_streamlit.cache_resource = lambda x: x
sys.modules['streamlit'] = mock_streamlit

sys.modules['pandas'] = MagicMock()
sys.modules['geopy'] = MagicMock()
sys.modules['geopy.geocoders'] = MagicMock()

# Now we can import AstrologyLogic
from logic import AstrologyLogic

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
