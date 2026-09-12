#!/usr/bin/env python3
"""
Unit tests for TertiaryProgressionsLogic & ThematicReportsLogic
"""

import unittest
from datetime import date, datetime
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from logic import AstrologyLogic
from tertiary_progressions_logic import TertiaryProgressionsLogic
from thematic_reports_logic import ThematicReportsLogic

class TestTertiaryAndThematicLogic(unittest.TestCase):

    def setUp(self):
        self.astro = AstrologyLogic()
        self.tp = TertiaryProgressionsLogic(self.astro.TRANS_SIGNS, self.astro.TRANS_PLANETS)
        self.birth_dt_str = "1990/01/01"
        self.birth_time_str = "12:00"
        self.utc_offset_str = "+08:00"
        self.lat = 25.0330
        self.lon = 121.5654

        dt_natal = Datetime(self.birth_dt_str, self.birth_time_str, self.utc_offset_str)
        pos = GeoPos(self.lat, self.lon)
        self.chart_natal = Chart(dt_natal, pos, hsys=const.HOUSES_WHOLE_SIGN)
        self.houses = self.astro.calculate_whole_sign_houses(self.chart_natal.get(const.ASC).lon)

    def test_calculate_progressed_time(self):
        # 1 year = 365.2422 days -> tertiary days = 365.2422 / 27.321582 = ~13.368 days
        target_date = "1991-01-01"
        age_years, tert_days, prog_dt, _ = self.tp.calculate_progressed_time(
            self.birth_dt_str, self.birth_time_str, target_date
        )
        self.assertAlmostEqual(age_years, 1.0, delta=0.05)
        self.assertAlmostEqual(tert_days, 13.368, delta=0.1)
        self.assertEqual(prog_dt.year, 1990)
        self.assertEqual(prog_dt.month, 1)
        self.assertTrue(13 <= prog_dt.day <= 15)

    def test_calculate_tertiary_moon_and_chart(self):
        target_date = "2026-09-12"
        chart_prog, age_years, tert_days, prog_dt, _ = self.tp.calculate_tertiary_chart(
            self.birth_dt_str, self.birth_time_str, self.utc_offset_str,
            self.lat, self.lon, target_date
        )
        self.assertIsNotNone(chart_prog)
        self.assertGreater(age_years, 36.0)

        moon_info = self.tp.calculate_tertiary_moon(chart_prog, self.houses)
        self.assertIn("sign", moon_info)
        self.assertIn("degree_str", moon_info)
        self.assertTrue(1 <= moon_info["house_num"] <= 12)
        self.assertGreater(moon_info["days_left_in_sign"], 0)
        self.assertIn("weeks_left_in_sign", moon_info)
        self.assertIn("theme", moon_info)

    def test_calculate_tertiary_lunar_phase(self):
        target_date = "2026-09-12"
        chart_prog, _, _, _, _ = self.tp.calculate_tertiary_chart(
            self.birth_dt_str, self.birth_time_str, self.utc_offset_str,
            self.lat, self.lon, target_date
        )
        phase_info = self.tp.calculate_tertiary_lunar_phase(chart_prog)
        self.assertIn("phase_name", phase_info)
        self.assertIn("stage", phase_info)
        self.assertIn("angle", phase_info)
        self.assertIn("cycle_month", phase_info)

    def test_calculate_tertiary_progressions_full(self):
        result = self.tp.calculate_tertiary_progressions(
            self.chart_natal, self.houses, self.birth_dt_str, self.birth_time_str,
            self.utc_offset_str, self.lat, self.lon, target_date="2026-09-12"
        )
        self.assertIn("age_years", result)
        self.assertIn("tertiary_moon", result)
        self.assertIn("lunar_phase", result)
        self.assertIn("active_aspects", result)
        self.assertIn("summary", result)

    def test_thematic_reports_logic(self):
        mock_chart = {
            "name": "測試者",
            "birth_date": "1990/01/01",
            "birth_time": "12:00",
            "location": "台北",
            "houses": self.houses,
            "planets": [{"id": "Sun", "name": "太陽", "sign": "摩羯座"}, {"id": "Venus", "name": "金星", "sign": "水瓶座"}],
            "lots": [{"name": "幸運點", "sign": "雙子座"}, {"name": "精神點", "sign": "射手座"}],
            "almuten": {"almuten_name": "土星", "almuten_score": 25}
        }

        for topic in ["career", "wealth", "romance"]:
            prompt = ThematicReportsLogic.generate_thematic_prompt(mock_chart, topic)
            self.assertIn("測試者", prompt)
            self.assertIn("延伸性問題建議", prompt)
            self.assertIn("自行輸入問題", prompt)

if __name__ == "__main__":
    unittest.main()
