import unittest
from datetime import date
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from solar_arc_logic import SolarArcLogic

class TestSolarArcLogic(unittest.TestCase):
    def setUp(self):
        self.sa_engine = SolarArcLogic()
        # 1990/01/01 12:00, Taipei (+08:00), 25.03, 121.56
        self.dt_natal = Datetime('1990/01/01', '12:00', '+08:00')
        self.pos = GeoPos(25.03, 121.56)
        self.chart = Chart(self.dt_natal, self.pos)

    def test_solar_arc_calculation(self):
        # 30 年後 (2020/01/01)
        target = date(2020, 1, 1)
        arc, age = self.sa_engine.calculate_solar_arc_degrees(
            '1990/01/01', '12:00', '+08:00', 25.03, 121.56, target
        )
        self.assertAlmostEqual(age, 30.0, delta=0.2)
        # 太陽每天大約行進 1 度，30 年約推進 29~31 度
        self.assertGreater(arc, 25.0)
        self.assertLess(arc, 35.0)

    def test_active_solar_arcs_structure(self):
        target = date(2024, 6, 1)
        res = self.sa_engine.calculate_active_solar_arcs(
            self.chart,
            '1990/01/01', '12:00', '+08:00', 25.03, 121.56, target_date=target, max_orb=1.0
        )
        self.assertIn('solar_arc_degrees', res)
        self.assertIn('age_years', res)
        self.assertIn('active_aspects', res)
        self.assertIn('summary', res)

        for asp in res['active_aspects']:
            self.assertLessEqual(asp['orb'], 1.0)
            self.assertIn(asp['aspect'], ['合相 (0°)', '四分相 (90°)', '對分相 (180°)'])

if __name__ == '__main__':
    unittest.main()
