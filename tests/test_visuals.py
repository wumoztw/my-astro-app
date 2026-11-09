#!/usr/bin/env python3
"""Unit tests for the pure-Python SVG chart engine (visuals.py)"""
import unittest
import xml.etree.ElementTree as ET
from datetime import date

from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

from logic import AstrologyLogic
from backend.synastry_logic import SynastryLogic
from visuals import (render_lilly_square_chart_svg,
                     render_interactive_chart_viewer,
                     render_temperament_svg, render_dispositor_tree_svg,
                     render_timeline_gantt_svg, render_printable_astro_book_html)
from profiles_logic import ProfilesManager


def build_report(horary=False):
    logic = AstrologyLogic()
    d, t, off, lat, lon = "1990/01/01", "12:00", "+08:00", 25.033, 121.565
    chart = Chart(Datetime(d, t, off), GeoPos(lat, lon), hsys=const.HOUSES_WHOLE_SIGN)
    asc = chart.get(const.ASC)
    houses = logic.calculate_whole_sign_houses(asc.lon)
    planets = logic.get_planets_data(chart, houses)
    is_day = logic.is_day_birth(chart, houses)
    tgt = date(2026, 1, 1)
    rd = {
        'chart': chart, 'planets': planets, 'houses': houses, 'is_day': is_day,
        'lots': logic.calculate_lots(chart, houses, is_day),
        'prof_info': logic.calculate_profections(chart, houses, d, current_date=tgt),
        'f_data': logic.get_firdaria_data(d, is_day, current_date=tgt),
        'sa_data': logic.calculate_solar_arcs(chart, d, t, off, lat, lon, target_date=tgt),
        'sec_prog_data': logic.calculate_secondary_progressions(chart, houses, d, t, off, lat, lon, target_date=tgt),
        'tert_prog_data': logic.calculate_tertiary_progressions(chart, houses, d, t, off, lat, lon, target_date=tgt),
        'asc_lon': asc.lon, 'mc_lon': chart.get(const.MC).lon, 'horary_analysis': None,
        'meta': {'birth_date_str': d, 'birth_time_str': t, 'location_city': '台北市', 'lat': lat, 'lon': lon,
                 'utc_offset_str': off, 'chart_type': 'horary' if horary else 'natal'},
    }
    rd['zr_data'] = logic.calculate_zodiacal_releasing(chart, is_day, d, current_date=tgt)
    rd['sr_data'] = logic.calculate_solar_return(chart, houses, d, 8.0, lat, lon, target_year=2026, sr_city='台北市')
    if not horary:
        dt_b = Datetime("1992/06/15", "12:00", "+08:00")
        rd['synastry_data'] = SynastryLogic().generate_synastry_report(
            "甲", Datetime(d, t, off), GeoPos(lat, lon), "乙", dt_b, GeoPos(lat, lon))
    if horary:
        rd['horary_analysis'] = logic.analyze_horary_chart(chart, houses, "我會順利錄取這份工作嗎？", planets)
    return rd


class TestVisuals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.natal = build_report()
        cls.horary = build_report(horary=True)

    def assertValidSvg(self, svg):
        self.assertTrue(svg.lstrip().startswith("<svg"))
        ET.fromstring(svg)  # well-formed XML
        self.assertNotIn("nan", svg.lower().replace("nanosecond", ""))

    def test_square_natal(self):
        svg = render_lilly_square_chart_svg(self.natal)
        self.assertValidSvg(svg)
        self.assertIn('viewBox="0 0 820 820"', svg)
        for i in range(1, 13):
            self.assertIn(f'id="house-{i}"', svg)
        for g in ("☉", "☽", "♄", "⊗"):
            self.assertIn(g, svg)
        self.assertIn("古典占星本命星盤", svg)
        self.assertIn("ASC 上升", svg)
        self.assertLess(render_lilly_square_chart_svg(self.natal, show_lots=False).count("⊗"), svg.count("⊗"))

    def test_square_horary_highlights(self):
        svg = render_lilly_square_chart_svg(self.horary)
        self.assertValidSvg(svg)
        self.assertIn("古典卜卦占星盤", svg)
        self.assertIn("sig-badge", svg)
        self.assertIn("裁決", svg)

    def test_viewer(self):
        svg = render_lilly_square_chart_svg(self.natal)
        page = render_interactive_chart_viewer(svg, "my_chart")
        self.assertIn("<svg", page)
        self.assertIn("navigator.clipboard.write", page)
        self.assertIn("ClipboardItem", page)
        self.assertIn("image/png", page)
        self.assertIn("toDataURL", page)
        self.assertIn("copy-status", page)
        self.assertIn("my_chart", page)

    def test_themes(self):
        for theme in ("parchment", "starry_night"):
            svg = render_lilly_square_chart_svg(self.natal, theme=theme)
            self.assertValidSvg(svg)
            self.assertEqual('class="star"' in svg, theme == "starry_night")
        self.assertIn('fill="#0B1120"', render_lilly_square_chart_svg(self.natal, theme="starry_night"))
        self.assertIn('fill="#FAF6EE"', render_lilly_square_chart_svg(self.natal))
        self.assertIn('fill="#0B1120"', render_interactive_chart_viewer(
            render_lilly_square_chart_svg(self.natal, theme="starry_night")))
        self.assertIn('BG = "#FAF6EE"', render_interactive_chart_viewer(render_lilly_square_chart_svg(self.natal)))

    def test_synastry_report(self):
        syn = self.natal["synastry_data"]
        for k in ("person_a", "person_b", "planets", "asc_b_str", "sun_b_str", "moon_b_str", "b_in_a_overlays",
                  "a_in_b_overlays", "cross_aspects", "receptions", "resonance_scores"):
            self.assertIn(k, syn)
        self.assertEqual(len(syn["planets"]), 7)
        self.assertTrue(all(1 <= p["overlay_house"] <= 12 for p in syn["planets"]))
        for a in syn["cross_aspects"]:
            self.assertEqual(a["aspect"], a["aspect_name"])
            self.assertIn(a["angle"], (0, 60, 90, 120, 180))
        for r in syn["receptions"]:
            self.assertIn(r["type"], ("互容 (Mutual Reception)", "單向接納 (Reception)"))
        sc = syn["resonance_scores"]
        for k in ("business_harmony_score", "romantic_harmony_score", "tension_index"):
            self.assertTrue(10 <= sc[k] <= 98)

    def test_synastry_prompt(self):
        from thematic_reports_logic import ThematicReportsLogic
        syn = self.natal["synastry_data"]
        ctx = ThematicReportsLogic.extract_thematic_context(self.natal, "synastry")
        for k in ("person_a", "person_b", "resonance_scores", "receptions", "cross_aspects"):
            self.assertEqual(ctx[k], syn[k])
        prompt = ThematicReportsLogic.generate_thematic_prompt(self.natal, "synastry")
        self.assertIn("【甲】與【乙】", prompt)
        for h in ("## 1.", "## 2.", "## 3.", "## 4.", "## 5.", "💡 延伸性問題建議"):
            self.assertIn(h, prompt)
        self.assertNotIn("<Chart", prompt)

    def _enriched(self):
        rd = dict(self.natal)
        rd['fixed_stars'] = [{'planet': '太陽', 'star': 'Regulus (軒轅十四)', 'orb': '0.5°'}]
        rd['almuten'] = {'almuten_id': 'Sun', 'almuten_name': '太陽', 'almuten_score': 20}
        rd['lots'] = list(rd['lots']) + [dict(rd['lots'][0], lon=(40.0 + 30 * i)) for i in range(4)]
        return rd

    def test_fixed_star_markers(self):
        rd = self._enriched()
        self.assertValidSvg(render_lilly_square_chart_svg(rd))
        self.assertIn("★ 恆星合相", render_lilly_square_chart_svg(rd))
        self.assertNotIn("★ 恆星合相", render_lilly_square_chart_svg(rd, show_stars=False))

    def test_almuten_crown(self):
        rd = self._enriched()
        for svg in (render_lilly_square_chart_svg(rd),):
            self.assertIn("👑", svg)
            self.assertIn("全盤總御星：太陽 (20分)", svg)
        self.assertNotIn("👑", render_lilly_square_chart_svg(self.natal))

    def test_all_six_lots(self):
        rd = self._enriched()
        for fn in (render_lilly_square_chart_svg,):
            svg = fn(rd, show_all_lots=True)
            self.assertValidSvg(svg)
            for g in ("⚷", "♡", "⚔", "✵"):
                self.assertIn(g, svg)
            self.assertNotIn("⚷", fn(rd))

    def test_antiscia_square(self):
        import copy
        rd = copy.copy(self.natal)
        planets = [dict(p) for p in rd["planets"]]
        for p in planets:
            if p["id"] == "Sun":
                p["lon"] = p["longitude"] = 60.0
            elif p["id"] == "Moon":
                p["lon"] = p["longitude"] = 120.0
        rd["planets"] = planets
        sq = render_lilly_square_chart_svg(rd, show_antiscia=True)
        self.assertValidSvg(sq)
        self.assertIn("🪞 映點接觸", sq)
        self.assertNotIn("🪞", render_lilly_square_chart_svg(rd))
        logic = AstrologyLogic()
        findings = logic.get_antiscia(rd["chart"])
        self.assertIsInstance(findings, list)
        for f in findings:
            for k in ("p1", "p2", "type", "orb", "p1_id", "p2_id", "p1_lon", "p2_lon", "antiscion_lon"):
                self.assertIn(k, f)
        rows = logic.get_antiscia_positions(rd["chart"])
        self.assertEqual(len(rows), 7)
        for r in rows:
            self.assertAlmostEqual(r["antiscion"], (180 - r["lon"]) % 360)
            self.assertAlmostEqual(r["contra_antiscion"], (360 - r["lon"]) % 360)

    def test_solar_return_logic(self):
        sr = self.natal['sr_data']
        natal_sun = self.natal['chart'].get(const.SUN).lon
        diff = abs((sr['sr_sun_lon'] - natal_sun + 180) % 360 - 180)
        self.assertLess(diff, 0.01)
        self.assertEqual(len(sr['planets']), 7)
        self.assertIn(sr['sr_asc_in_natal_house'], range(1, 13))
        self.assertTrue(sr['sr_datetime_local'].startswith("2026/"))
        self.assertTrue(sr['sr_asc_natal_house_theme'])
        for p in sr['active_aspects']:
            self.assertLessEqual(p['orb'], 2.0)

    def test_solar_return_leap_birthday(self):
        from solar_return_logic import SolarReturnLogic
        jd = SolarReturnLogic().find_solar_return_jd(340.0, 2027, 2, 29)
        self.assertLess(abs(((340.0 - __import__('swisseph').calc_ut(jd, 0)[0][0] + 180) % 360) - 180), 1e-5)

    def test_timeline_gantt_svg(self):
        from visuals import render_timeline_gantt_svg
        for theme in ("parchment", "starry_night"):
            svg = render_timeline_gantt_svg(self.natal, theme=theme)
            self.assertValidSvg(svg)
            self.assertIn('viewBox="0 0 920 440"', svg)
            self.assertIn('class="timeline-now-line"', svg)
            self.assertEqual(svg.count('class="firdaria-major"'), 9)
            self.assertIn('class="zr-l1"', svg)
            self.assertIn('class="zr-l2"', svg)
        self.assertValidSvg(render_timeline_gantt_svg({}))

    def test_solar_return_prompt(self):
        from thematic_reports_logic import ThematicReportsLogic
        p = ThematicReportsLogic.generate_thematic_prompt(self.natal, "solar_return")
        self.assertIn("太陽返照盤", p)
        self.assertIn(self.natal['sr_data']['sr_asc_str'], p)
        self.assertIn("法達", p)

    def test_natal_core(self):
        logic = AstrologyLogic()
        n = self.natal
        al = logic.calculate_almuten(n['chart'], n['houses'], n['is_day'])
        nc = logic.calculate_natal_core(n['chart'], n['houses'], n['planets'], n['is_day'], al)
        tp = nc['temperament']
        self.assertAlmostEqual(sum(tp['humors'].values()), 100.0, delta=0.5)
        self.assertEqual(set(tp['qualities']), {'hot', 'cold', 'dry', 'moist'})
        self.assertEqual(len(tp['factors']), 7)
        hd = nc['hyleg_data']
        for k in ('syzygy', 'hyleg', 'alcocoden', 'candidates', 'summary'):
            self.assertIn(k, hd)
        self.assertIn(hd['syzygy']['syzygy_house'], range(1, 13))
        self.assertIn(hd['hyleg']['house'], range(1, 13))
        dp = nc['dispositors']
        self.assertEqual(len(dp['house_fly_chains']), 12)
        self.assertEqual(len(dp['planet_dispositor_edges']), 7)
        self.assertEqual(len(nc['dignities_matrix']), 11)
        for svg in (render_temperament_svg(tp, "parchment"), render_temperament_svg(tp, "starry_night")):
            self.assertValidSvg(svg)
            self.assertIn('viewBox="0 0 760 220"', svg)
        for th in ("parchment", "starry_night"):
            svg = render_dispositor_tree_svg(dp, th)
            self.assertValidSvg(svg)
            self.assertIn('viewBox="0 0 760 280"', svg)
            if len(dp['self_dispositors']) < 7:
                self.assertIn('marker-end="url(#arrow', svg)

    def test_predictive_extensions(self):
        logic = AstrologyLogic()
        n = self.natal
        tgt = date(2026, 1, 1)
        lat, lon = 25.033, 121.565
        lr = logic.calculate_lunar_return(n['chart'], n['houses'], 8.0, lat, lon, target_date=tgt, lr_city='台北市')
        diff = abs(((lr['lr_moon_lon'] - lr['natal_moon_lon'] + 180) % 360) - 180)
        self.assertLess(diff, 0.01)
        self.assertEqual(len(lr['planets']), 7)
        self.assertIn(lr['lr_asc_in_natal_house'], range(1, 13))
        tr = logic.calculate_transits(n['chart'], n['houses'], 8.0, lat, lon, target_date=tgt)
        self.assertEqual(len(tr['planets']), 7)
        ph = logic.calculate_planetary_hours(date(2026, 1, 1), "12:00", 8.0, lat, lon, asc_sign_const=const.LEO)
        self.assertEqual(len(ph['hours_table']), 24)
        self.assertEqual(ph['day_ruler_id'], 'Jupiter')
        self.assertEqual(ph['hours_table'][0]['ruler_id'], 'Jupiter')
        self.assertIn(ph['active_hour']['ruler_id'], ('Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon'))
        self.assertTrue(ph['horary_radicality'][:1] in ("✅", "⚠"))
        ph_polar = logic.calculate_planetary_hours(date(2026, 6, 21), "02:00", 0.0, 80.0, 0.0, asc_sign_const=const.ARIES)
        self.assertEqual(len(ph_polar['hours_table']), 24)
        mp = logic.calculate_monthly_profections_calendar(n['chart'], n['houses'], "1990/01/01", 2026)
        self.assertEqual(len(mp), 12)
        self.assertEqual(sorted(r['house_num'] for r in mp), list(range(1, 13)))
        self.assertEqual(mp[0]['start_date'], "2026/01/01")

    def test_profiles_manager(self):
        pm = ProfilesManager
        base = pm.default_profiles()
        lst = pm.save_profile(base, "小明", "1985/05/05", "08:30", "高雄市", 22.62, 120.31, 8.0)
        self.assertEqual(len(lst), len(base) + 1)
        lst = pm.save_profile(lst, "小明", "1985/05/06", "08:30", "高雄市", 22.62, 120.31, 8.0)
        self.assertEqual(len(lst), len(base) + 1)
        self.assertEqual([p for p in lst if p["name"] == "小明"][0]["date"], "1985/05/06")
        again = pm.import_profiles_json(pm.default_profiles(), pm.export_profiles_json(lst))
        self.assertEqual(again, lst)
        self.assertEqual(len(pm.delete_profile(lst, "小明")), len(base))
        with self.assertRaises(ValueError):
            pm.import_profiles_json([], "not json")

    def test_printable_book(self):
        logic = AstrologyLogic()
        n = self.natal
        nc = logic.calculate_natal_core(n['chart'], n['houses'], n['planets'], n['is_day'])
        rd = dict(n, natal_core=nc, person_name="測試<者>")
        html_ = render_printable_astro_book_html(rd, ai_messages=[{"role": "user", "content": "q"},
                                                                  {"role": "assistant", "content": "AI 解析內容"}])
        self.assertTrue(html_.startswith("<!DOCTYPE html>"))
        self.assertIn("window.print()", html_)
        self.assertIn("@page {", html_)
        self.assertIn("size: A4;", html_)
        self.assertIn("古典占星專業命書", html_)
        self.assertIn("測試&lt;者&gt;", html_)
        self.assertIn("AI 解析內容", html_)
        for needle in (render_lilly_square_chart_svg(rd, True, "parchment", True, True, True)[:60],
                       render_temperament_svg(nc['temperament'])[:60],
                       render_dispositor_tree_svg(nc['dispositors'])[:60],
                       render_timeline_gantt_svg(rd)[:60]):
            self.assertIn(needle, html_)
        self.assertGreaterEqual(html_.count("<svg"), 4)
        self.assertIn("<table>", html_)

    def test_primary_directions_and_aspect_hints(self):
        from primary_directions_logic import calculate_primary_directions
        from rectification_logic import rectify_birth_time, EVENT_TYPES
        rd = self.natal
        # 1. Primary directions calculation
        dirs = calculate_primary_directions(rd, "1990/01/01", max_age=80)
        self.assertGreater(len(dirs), 10)
        first_d = dirs[0]
        self.assertIn("age", first_d)
        self.assertIn("event_date_str", first_d)
        self.assertIn("significator", first_d)
        self.assertIn("promissor", first_d)
        self.assertIn("aspect_name", first_d)

        # 2. Rectification calculation
        def dummy_calc(d, t, off, lat, lon):
            return rd['chart']

        events = [{"date": "2015-06-15", "type": "career_promotion"}]
        cands = rectify_birth_time(dummy_calc, "1990/01/01", "12:00", search_window_mins=4, step_minutes=2, events_list=events)
        self.assertGreater(len(cands), 0)
        self.assertIn("confidence_score", cands[0])

        # 3. Clean square chart rendering and integrated aspect panel
        svg_chart = render_lilly_square_chart_svg(rd, show_aspect_bar=True)
        self.assertIn("William Lilly", svg_chart)
        self.assertIn("✦ 托勒密行星主要交角與相位提示", svg_chart)
        self.assertIn("viewBox=\"0 0 820 920\"", svg_chart)
        svg_no_aspect = render_lilly_square_chart_svg(rd, show_aspect_bar=False)
        self.assertNotIn("✦ 托勒密行星主要交角與相位提示", svg_no_aspect)
        self.assertIn("viewBox=\"0 0 820 820\"", svg_no_aspect)


if __name__ == "__main__":
    unittest.main()
