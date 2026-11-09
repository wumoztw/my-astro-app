#!/usr/bin/env python3
"""Unit tests for the pure-Python SVG chart engine (visuals.py)"""
import math
import unittest
import xml.etree.ElementTree as ET
from datetime import date

from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

from logic import AstrologyLogic
from backend.synastry_logic import SynastryLogic
from visuals import (render_lilly_square_chart_svg, render_circular_chart_svg,
                     render_interactive_chart_viewer, spread_longitudes, draw_circular_chart)


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

    def test_circular_modes(self):
        for mode in ("none", "solar_arc", "secondary", "tertiary"):
            svg = render_circular_chart_svg(self.natal, overlay_mode=mode)
            self.assertValidSvg(svg)
            self.assertIn('viewBox="0 0 860 860"', svg)
            self.assertEqual("ov-badge" in svg, mode != "none", mode)
        self.assertValidSvg(render_circular_chart_svg(self.natal, show_lots=False, show_aspects=False))
        hs = render_circular_chart_svg(self.horary)
        self.assertValidSvg(hs)
        self.assertIn("sig-badge", hs)

    def test_ascendant_at_nine_o_clock(self):
        # house 1 cusp -> left-middle: the 1st sector boundary line starts at x < center
        svg = render_circular_chart_svg(self.natal)
        self.assertIn("第一宮", svg)

    def test_spread_longitudes(self):
        cases = [[10.0, 10.5, 11.0, 12.0], [359.0, 0.5, 1.0], [5.0] * 5, [100.0, 250.0], [42.0]]
        for lons in cases:
            res = spread_longitudes(lons, 6.5)
            self.assertEqual(len(res), len(lons))
            self.assertTrue(all(math.isfinite(x) for x in res))
            s = sorted(res)
            for a, b in zip(s, s[1:] + [s[0] + 360]) if len(s) > 1 else []:
                self.assertGreaterEqual(b - a, 6.5 - 1e-6)

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
            for svg in (render_lilly_square_chart_svg(self.natal, theme=theme),
                        render_circular_chart_svg(self.natal, theme=theme),
                        render_circular_chart_svg(self.natal, overlay_mode="synastry", theme=theme)):
                self.assertValidSvg(svg)
                self.assertEqual('class="star"' in svg, theme == "starry_night")
        self.assertIn('fill="#0B1120"', render_lilly_square_chart_svg(self.natal, theme="starry_night"))
        self.assertIn('fill="#FAF6EE"', render_circular_chart_svg(self.natal))
        self.assertIn('fill="#0B1120"', render_interactive_chart_viewer(
            render_circular_chart_svg(self.natal, theme="starry_night")))
        self.assertIn('BG = "#FAF6EE"', render_interactive_chart_viewer(render_circular_chart_svg(self.natal)))

    def test_synastry_overlay(self):
        svg = render_circular_chart_svg(self.natal, overlay_mode="synastry")
        self.assertValidSvg(svg)
        self.assertIn("外環：合盤對象 (乙)", svg)
        self.assertIn("內環：本命 (甲)", svg)
        self.assertEqual(svg.count('class="ov-badge"'), 7)
        self.assertIn("#FB7185", render_circular_chart_svg(self.natal, overlay_mode="synastry", theme="starry_night"))
        # no synastry data -> no outer badges, still valid
        nodata = dict(self.natal); nodata.pop("synastry_data")
        self.assertValidSvg(render_circular_chart_svg(nodata, overlay_mode="synastry"))

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

    def test_dignity_badges_circular(self):
        svg = render_circular_chart_svg(self._enriched())
        self.assertValidSvg(svg)
        self.assertIn('class="dignity-badge"', svg)
        self.assertNotIn('class="dignity-badge"', render_circular_chart_svg(self._enriched(), show_stars=False))

    def test_fixed_star_markers(self):
        rd = self._enriched()
        svg = render_circular_chart_svg(rd)
        self.assertIn('class="fixed-star-marker"', svg)
        self.assertIn("★軒轅十四", svg)
        self.assertValidSvg(render_lilly_square_chart_svg(rd))
        self.assertIn("★ 恆星合相", render_lilly_square_chart_svg(rd))
        self.assertNotIn("★ 恆星合相", render_lilly_square_chart_svg(rd, show_stars=False))

    def test_almuten_crown(self):
        rd = self._enriched()
        for svg in (render_circular_chart_svg(rd), render_lilly_square_chart_svg(rd)):
            self.assertIn("👑", svg)
            self.assertIn("全盤總御星：太陽 (20分)", svg)
        self.assertNotIn("👑", render_lilly_square_chart_svg(self.natal))

    def test_all_six_lots(self):
        rd = self._enriched()
        for fn in (render_circular_chart_svg, render_lilly_square_chart_svg):
            svg = fn(rd, show_all_lots=True)
            self.assertValidSvg(svg)
            for g in ("⚷", "♡", "⚔", "✵"):
                self.assertIn(g, svg)
            self.assertNotIn("⚷", fn(rd))

    def test_antiscia_circular_and_square(self):
        import copy
        rd = copy.copy(self.natal)
        planets = [dict(p) for p in rd["planets"]]
        for p in planets:
            if p["id"] == "Sun":
                p["lon"] = p["longitude"] = 60.0
            elif p["id"] == "Moon":
                p["lon"] = p["longitude"] = 120.0
        rd["planets"] = planets
        svg = render_circular_chart_svg(rd, show_antiscia=True)
        self.assertValidSvg(svg)
        for cls in ("solstice-axis", "antiscia-point", "antiscia-line"):
            self.assertIn(f'class="{cls}"', svg)
        for theme, col in (("parchment", "#8B5CF6"), ("starry_night", "#C084FC")):
            s2 = render_circular_chart_svg(rd, show_antiscia=True, theme=theme)
            self.assertIn(f'stroke="{col}" stroke-width="1.6" stroke-dasharray="6 4"', s2)
        self.assertNotIn("solstice-axis", render_circular_chart_svg(rd))
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

    def test_wrapper(self):
        self.assertIn("<svg", draw_circular_chart(self.natal))
        self.assertIsNone(draw_circular_chart({"year": 1990}))


if __name__ == "__main__":
    unittest.main()
