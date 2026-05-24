import sys
from unittest.mock import MagicMock, patch
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

