#!/usr/bin/env python3
"""
Unit tests for HoraryEngineLogic in my-astro-app.
"""

import unittest
from horary_engine_logic import HoraryEngineLogic
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const

class TestHoraryEngineLogic(unittest.TestCase):
    def setUp(self):
        self.engine = HoraryEngineLogic()

    def test_classify_quesited_house_career(self):
        res = self.engine.classify_quesited_house("請問我這次求職面試會錄取這家外商嗎？")
        self.assertEqual(res["quesited_house"], 10)
        self.assertIn("第 10 宮", res["house_name"])

        res2 = self.engine.classify_quesited_house("我想創業開公司未來的事業發展如何？")
        self.assertEqual(res2["quesited_house"], 10)

    def test_classify_quesited_house_romance_and_contract(self):
        res = self.engine.classify_quesited_house("我和前男友還有機會復合嗎？")
        self.assertEqual(res["quesited_house"], 7)
        self.assertIn("第 7 宮", res["house_name"])

        res2 = self.engine.classify_quesited_house("這份商業合夥簽約合作順利嗎？")
        self.assertEqual(res2["quesited_house"], 7)

        res3 = self.engine.classify_quesited_house("這場官司訴訟對手會退讓和解嗎？")
        self.assertEqual(res3["quesited_house"], 7)

    def test_classify_quesited_house_wealth_and_investment(self):
        res = self.engine.classify_quesited_house("請問投資這檔股票會賺錢嗎？")
        self.assertEqual(res["quesited_house"], 8)

        res2 = self.engine.classify_quesited_house("請問我下個月能順利加薪並提高待遇薪水嗎？")
        self.assertEqual(res2["quesited_house"], 2)

    def test_classify_quesited_house_home_lost_items(self):
        res = self.engine.classify_quesited_house("這間買房子的價格合適嗎？能順利成交嗎？")
        self.assertEqual(res["quesited_house"], 4)

        res2 = self.engine.classify_quesited_house("遺失的皮夾找得回來嗎？")
        self.assertEqual(res2["quesited_house"], 4)

    def test_classify_quesited_house_health_and_pets(self):
        res = self.engine.classify_quesited_house("生病看醫生進行這個手術能順利康復嗎？")
        self.assertEqual(res["quesited_house"], 6)

        res2 = self.engine.classify_quesited_house("走失的寵物貓能回家嗎？")
        self.assertEqual(res2["quesited_house"], 6)

    def test_perfection_and_timing_with_real_chart(self):
        # 建立一個測試盤 (台北，2026/08/13 12:00)
        dt = Datetime("2026/08/13", "12:00", "+08:00")
        pos = GeoPos(25.0330, 121.5654)
        chart = Chart(dt, pos, hsys=const.HOUSES_WHOLE_SIGN)

        # 宮位計算 (整宮制)
        asc_lon = chart.get(const.ASC).lon
        asc_sign_idx = int(asc_lon // 30)
        houses = []
        for i in range(12):
            s_idx = (asc_sign_idx + i) % 12
            s_const = const.LIST_SIGNS[s_idx]
            houses.append({
                "id": i + 1,
                "sign": s_const,
                "lon": float(s_idx * 30),
                "ruler": self.engine.dignities.RULERS.get(s_const, const.MARS)
            })

        planets_data = []
        for p_id in [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN]:
            p = chart.get(p_id)
            planets_data.append({
                "id": p_id,
                "sign": p.sign,
                "lon": p.lon,
                "house_num": self.engine.get_planet_house_num(p.lon, houses)
            })

        # 測試目標第 10 宮
        perf = self.engine.analyze_perfection(chart, houses, 10, planets_data)
        self.assertIn("overall_verdict", perf)
        self.assertIn("verdict_desc", perf)
        self.assertIn("lord_1_id", perf)
        self.assertIn("lord_q_id", perf)
        self.assertIn("is_perfected", perf)

        # 測試應期計算
        timing = self.engine.calculate_timing(chart, houses, perf)
        self.assertIn("delta_degrees", timing)
        self.assertIn("estimated_timeframe", timing)
        self.assertIn("time_unit", timing)
        self.assertIn("pacing_description", timing)

        # 測試月亮流動全景
        m_flow = self.engine.get_moon_flow(chart)
        self.assertIn("moon_sign", m_flow)
        self.assertIn("is_voc", m_flow)

    def test_classical_reception_and_aspect_details(self):
        # 測試互容：金星在牡羊座 (火星守護，金星落陷)，火星在金牛座 (金星守護，火星落陷) -> 雙向互容
        r_str = self.engine.check_classical_reception(const.VENUS, 15.0, const.MARS, 45.0)
        self.assertIn("互容", r_str)

        # 測試單向接納：太陽在白羊座 (火星守護)，火星在射手座
        r_str2 = self.engine.check_classical_reception(const.SUN, 10.0, const.MARS, 250.0)
        self.assertIn("火星 接納 太陽", r_str2)

if __name__ == "__main__":
    unittest.main()
