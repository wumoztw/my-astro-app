import unittest
from unittest.mock import MagicMock, patch
from flatlib import const
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
            const.SUN: self.sun,
            const.MOON: self.moon,
            const.MERCURY: MagicMock(lon=0),
            const.VENUS: MagicMock(lon=0),
            const.MARS: MagicMock(lon=0),
            const.JUPITER: MagicMock(lon=0),
            const.SATURN: MagicMock(lon=0)
        }.get(p_id, MagicMock(lon=0))

    @patch('lots_logic.swe')
    def test_get_fixed_stars_success(self, mock_swe_local):
        # Mock swisseph.fixstar2_ut return value
        # returns (data, name) where data is [lon, lat, ...]
        mock_swe_local.fixstar2_ut.side_effect = lambda name, jd: (
            ([150.1, 0, 0, 0, 0, 0], 'Regulus') if name == 'Regulus' else
            ([204.0, 0, 0, 0, 0, 0], 'Spica')
        )

        trans_planets = {const.SUN: '太陽', const.MOON: '月亮'}
        findings = self.logic.get_fixed_stars(self.mock_chart, trans_planets)

        # Sun at 150.5 is within 1.5 degrees of Regulus (150.1)
        self.assertTrue(any(f['star'] == 'Regulus (軒轅十四)' and f['planet'] == '太陽' for f in findings))
        mock_swe_local.fixstar2_ut.assert_any_call('Regulus', 2461041.5)

    @patch('lots_logic.swe')
    def test_get_fixed_stars_fallback(self, mock_swe_local):
        # Mock swisseph.fixstar2_ut to raise an exception
        mock_swe_local.fixstar2_ut.side_effect = Exception("File not found")

        trans_planets = {const.SUN: '太陽', const.MOON: '月亮'}
        # Even with exception, it should use fallback values
        # Sun at 150.5 is within 1.5 degrees of fallback Regulus (150.1)
        findings = self.logic.get_fixed_stars(self.mock_chart, trans_planets)

        self.assertTrue(any(f['star'] == 'Regulus (軒轅十四)' and f['planet'] == '太陽' for f in findings))

if __name__ == '__main__':
    unittest.main()

