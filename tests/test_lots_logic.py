import unittest
from unittest.mock import MagicMock
import sys

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
            'Sun': self.sun,
            'Moon': self.moon,
            'Mercury': MagicMock(lon=0),
            'Venus': MagicMock(lon=0),
            'Mars': MagicMock(lon=0),
            'Jupiter': MagicMock(lon=0),
            'Saturn': MagicMock(lon=0)
        }.get(p_id, MagicMock(lon=0))

    def test_get_fixed_stars_success(self):
        # Sun at 150.5 is within 1.5 degrees of Regulus (150.32)
        trans_planets = {'Sun': '太陽', 'Moon': '月亮'}
        findings = self.logic.get_fixed_stars(self.mock_chart, trans_planets)

        self.assertTrue(any(f['star'] == 'Regulus (軒轅十四)' and f['planet'] == '太陽' for f in findings))

    def test_get_fixed_stars_no_match(self):
        # Set all planets to 15° Aries (15.0°) - no fixed star exists near 15° Aries
        self.sun.lon = 15.0
        self.moon.lon = 15.0
        self.mock_chart.get.side_effect = lambda p_id: MagicMock(lon=15.0)

        trans_planets = {'Sun': '太陽', 'Moon': '月亮', 'Mercury': '水星', 'Venus': '金星', 'Mars': '火星', 'Jupiter': '木星', 'Saturn': '土星'}
        findings = self.logic.get_fixed_stars(self.mock_chart, trans_planets)

        self.assertEqual(len(findings), 0)

if __name__ == '__main__':
    unittest.main()
