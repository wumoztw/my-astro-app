#!/usr/bin/env python3
"""
Unit tests for SecondaryProgressionsLogic (次限推運法 - 一日一年)
"""

import unittest
from datetime import date, datetime
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from logic import AstrologyLogic
from secondary_progressions_logic import SecondaryProgressionsLogic

class TestSecondaryProgressionsLogic(unittest.TestCase):

    def setUp(self):
        self.astro = AstrologyLogic()
        self.sp = SecondaryProgressionsLogic(self.astro.TRANS_SIGNS, self.astro.TRANS_PLANETS)
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
        # 30 years after 1990/01/01 -> target date 2020/01/01
        target_date = "2020-01-01"
        age_years, prog_dt, eval_td = self.sp.calculate_progressed_time(
            self.birth_dt_str, self.birth_time_str, target_date
        )
        self.assertAlmostEqual(age_years, 30.0, delta=0.1)
        # Progressed datetime should be birth_dt + ~30 days (1990/01/31)
        self.assertEqual(prog_dt.year, 1990)
        self.assertEqual(prog_dt.month, 1)
        self.assertTrue(30 <= prog_dt.day <= 31)

    def test_calculate_progressed_chart_and_moon(self):
        target_date = "2026-06-15"
        chart_prog, age_years, prog_dt, _ = self.sp.calculate_progressed_chart(
            self.birth_dt_str, self.birth_time_str, self.utc_offset_str,
            self.lat, self.lon, target_date
        )
        self.assertIsNotNone(chart_prog)
        self.assertGreater(age_years, 36.0)

        moon_info = self.sp.calculate_progressed_moon(chart_prog, self.houses)
        self.assertIn("sign", moon_info)
        self.assertIn("degree_str", moon_info)
        self.assertTrue(1 <= moon_info["house_num"] <= 12)
        self.assertGreater(moon_info["months_left_in_sign"], 0)
        self.assertIn("theme", moon_info)

    def test_lunar_phase_detection(self):
        # Check all 8 phases mapping
        for p in self.sp.LUNAR_PHASES:
            test_angle = (p["min_angle"] + p["max_angle"]) / 2.0
            matched = False
            for cand in self.sp.LUNAR_PHASES:
                if cand["min_angle"] <= test_angle < cand["max_angle"]:
                    self.assertEqual(cand["name"], p["name"])
                    matched = True
                    break
            self.assertTrue(matched)

    def test_calculate_secondary_progressions_full(self):
        result = self.sp.calculate_secondary_progressions(
            self.chart_natal, self.houses, self.birth_dt_str, self.birth_time_str,
            self.utc_offset_str, self.lat, self.lon, target_date="2026-09-12"
        )
        self.assertIn("age_years", result)
        self.assertIn("progressed_moon", result)
        self.assertIn("lunar_phase", result)
        self.assertIn("planets", result)
        self.assertIn("active_aspects", result)
        self.assertIn("summary", result)
        self.assertGreater(len(result["planets"]), 5)

if __name__ == "__main__":
    unittest.main()
