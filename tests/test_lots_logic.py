import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock swisseph and flatlib before importing LotsLogic
mock_swe = MagicMock()
mock_flatlib = MagicMock()
mock_const = MagicMock()

# Setup mock constants
mock_const.SUN = 'Sun'
mock_const.MOON = 'Moon'
mock_const.MERCURY = 'Mercury'
mock_const.VENUS = 'Venus'
mock_const.MARS = 'Mars'
mock_const.JUPITER = 'Jupiter'
mock_const.SATURN = 'Saturn'
mock_flatlib.const = mock_const

sys.modules['swisseph'] = mock_swe
sys.modules['flatlib'] = mock_flatlib
sys.modules['flatlib.const'] = mock_const

# Now import LotsLogic
from lots_logic import LotsLogic

class TestLotsLogic(unittest.TestCase):
    def setUp(self):
        self.logic = LotsLogic()
        self.mock_chart = MagicMock()
        self.mock_chart.date.jd = 2461041.5  # Some JD

        # Setup mock planets in chart
        self.sun = MagicMock()
        self.sun.lon = 150.5  # Near Regulus
        self.moon = MagicMock()
        self.moon.lon = 200.0 # Not near Spica

        self.mock_chart.get.side_effect = lambda p_id: {
            'Sun': self.sun,
            'Moon': self.moon,
            'Mercury': MagicMock(lon=0),
            'Venus': MagicMock(lon=0),
            'Mars': MagicMock(lon=0),
            'Jupiter': MagicMock(lon=0),
            'Saturn': MagicMock(lon=0)
        }.get(p_id, MagicMock(lon=0))

    @patch('lots_logic.swe')
    def test_get_fixed_stars_success(self, mock_swe_local):
        # Mock swisseph.fixstar2_ut return value
        # returns (data, name) where data is [lon, lat, ...]
        mock_swe_local.fixstar2_ut.side_effect = lambda name, jd: (
            ([150.1, 0, 0, 0, 0, 0], 'Regulus') if name == 'Regulus' else
            ([204.0, 0, 0, 0, 0, 0], 'Spica')
        )

        trans_planets = {'Sun': '太陽', 'Moon': '月亮'}
        findings = self.logic.get_fixed_stars(self.mock_chart, trans_planets)

        # Sun at 150.5 is within 1.5 degrees of Regulus (150.1)
        self.assertTrue(any(f['star'] == 'Regulus (軒轅十四)' and f['planet'] == '太陽' for f in findings))
        mock_swe_local.fixstar2_ut.assert_any_call('Regulus', 2461041.5)

    @patch('lots_logic.swe')
    def test_get_fixed_stars_fallback(self, mock_swe_local):
        # Mock swisseph.fixstar2_ut to raise an exception
        mock_swe_local.fixstar2_ut.side_effect = Exception("File not found")

        trans_planets = {'Sun': '太陽', 'Moon': '月亮'}
        # Even with exception, it should use fallback values
        # Sun at 150.5 is within 1.5 degrees of fallback Regulus (150.1)
        findings = self.logic.get_fixed_stars(self.mock_chart, trans_planets)

        self.assertTrue(any(f['star'] == 'Regulus (軒轅十四)' and f['planet'] == '太陽' for f in findings))

if __name__ == '__main__':
    unittest.main()
