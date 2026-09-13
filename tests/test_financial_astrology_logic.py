#!/usr/bin/env python3
"""
Unit tests for FinancialAstrologyLogic in my-astro-app.
"""

import unittest
from datetime import datetime
from financial_astrology_logic import FinancialAstrologyLogic
from logic import AstrologyLogic
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const


class TestFinancialAstrologyLogic(unittest.TestCase):
    def setUp(self):
        self.astro = AstrologyLogic()
        self.fin_astro = FinancialAstrologyLogic()

        # 建立老吳命盤 (1976/02/06 19:30 台北)
        dt = Datetime("1976/02/06", "19:30", "+08:00")
        pos = GeoPos(25.0330, 121.5654)
        self.chart = Chart(dt, pos, hsys=const.HOUSES_WHOLE_SIGN)
        self.houses = self.astro.calculate_whole_sign_houses(self.chart.get(const.ASC).lon)
        self.is_day = self.astro.is_day_birth(self.chart, self.houses)

    def test_bitcoin_genesis_chart_properties(self):
        genesis = self.fin_astro.get_bitcoin_genesis_chart()
        self.assertIn("chart_obj", genesis)
        self.assertEqual(genesis["genesis_block"], 0)
        self.assertTrue(len(genesis["planets"]) >= 7)
        self.assertTrue(any("摩羯" in p["sign"] for p in genesis["planets"] if p["name"] == "太陽"))

    def test_native_wealth_profile(self):
        profile = self.fin_astro.extract_native_wealth_profile(self.chart, self.houses)
        self.assertEqual(profile["lord_1"]["house_num"], 1)
        self.assertEqual(profile["lord_2"]["house_num"], 2)
        self.assertEqual(profile["lord_8"]["house_num"], 8)
        self.assertIn("金星", profile["venus"]["name"])
        self.assertIn("木星", profile["jupiter"]["name"])

    def test_cycle_slice_calculation(self):
        # 2013-11-30 比特幣第一輪大頂
        c_slice = self.fin_astro.calculate_cycle_slice(
            self.chart, self.houses, "1976/02/06", self.is_day, "2013/11/30"
        )
        self.assertEqual(c_slice["age"], 37)
        self.assertEqual(c_slice["profection_house"], 2)  # 37歲應入第2宮
        self.assertIn("金星", c_slice["lord_of_year"])

    def test_analyze_bitcoin_resonance_full_run(self):
        res = self.fin_astro.analyze_bitcoin_resonance(
            self.chart, self.houses, "1976/02/06", self.is_day
        )
        self.assertIn("overall_correlation_index", res)
        self.assertIn("resonance_type", res)
        self.assertIn("genesis_affinity_score", res)
        self.assertTrue(len(res["cycle_comparisons"]) >= 4)
        self.assertTrue(len(res["future_slices"]) >= 5)
        # 驗證分數區間在 0 ~ 100
        self.assertTrue(0 <= res["overall_correlation_index"] <= 100)
        self.assertTrue(0 <= res["genesis_affinity_score"] <= 100)


if __name__ == "__main__":
    unittest.main()
