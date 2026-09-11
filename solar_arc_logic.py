"""
solar_arc_logic.py
西洋古典與現代事件占星：太陽弧推運模組 (Solar Arc Directions, SAD Engine)
依據理論：Noel Tyl《Solar Arcs: Transformation & Practical Guide》、Ebertin 宇宙生物學
核心功能：
1. 依據目標日期計算精確次限推進太陽弧度 (Solar Arc = Progressed Sun - Natal Sun)。
2. 將本命全盤星體 (七曜 + ASC/MC) 向前等弧推移。
3. 嚴格比對推運星與本命星形成的重大硬相位 (0°, 90°, 180°)，容許度限制在 <= 1.0° (對應前後一年內重大現實事件)。
4. 提供權威事件徵象解讀標籤。
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
import pandas as pd
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

class SolarArcLogic:
    MAJOR_HARD_ASPECTS = {
        0: '合相 (0°)',
        90: '四分相 (90°)',
        180: '對分相 (180°)'
    }

    # Noel Tyl 經典事件核心象徵關鍵詞
    EVENT_KEYWORDS = {
        ('Sun', 'MC'): "🌟 事業重大突破、名望與社會地位確立",
        ('Sun', const.ASC): "🚀 個人新起點、重大人生轉型與自主意志提升",
        ('Moon', 'MC'): "🏡 居所搬遷、公眾形象轉變、生活核心焦點轉移",
        ('Moon', const.ASC): "❤️ 情感關係重大承諾、個人生活環境重大變遷",
        ('Venus', 'Sun'): "💍 婚戀喜事、人際魅力高光、財富收益與尊榮",
        ('Venus', 'MC'): "💼 職場人際貴人相助、公眾聲望提升、美學/公關成就",
        ('Venus', const.ASC): "🌸 情感桃花、婚姻承諾、個人吸引力顛峰",
        ('Mars', 'Sun'): "🔥 雄心壯志爆發、新事業開創、注意競爭衝突與血光",
        ('Mars', 'MC'): "⚔️ 事業重大開創或競爭、獨立自主創業、職場硬仗",
        ('Mars', const.ASC): "⚡ 體能與精力高漲、主動出擊、注意意外或手術",
        ('Jupiter', 'Sun'): "💰 人生重大機遇、財富擴張、名利雙收、自信爆發",
        ('Jupiter', 'MC'): "🏆 職業晉升、得貴人強力提攜、版圖跨界拓展",
        ('Jupiter', 'Venus'): "🎉 大吉之兆、婚戀圓滿、大筆資金入帳",
        ('Jupiter', const.ASC): "✨ 人生視野大開、出國深造、順風順水",
        ('Saturn', 'Sun'): "🧱 承擔沉重社會責任、考驗耐力、結構性重組",
        ('Saturn', 'MC'): "🏛️ 事業權力頂峰與重大責任扛肩、嚴格考驗",
        ('Saturn', const.ASC): "⏳ 人生重大沉澱、現實壓力轉化為堅固基石",
        ('Saturn', 'Moon'): "🌧️ 心境沉重、家庭負擔、健康或體力考驗",
    }

    def __init__(self, trans_signs=None, trans_planets=None):
        self.trans_signs = trans_signs or {
            const.ARIES: '牡羊座', const.TAURUS: '金牛座', const.GEMINI: '雙子座',
            const.CANCER: '巨蟹座', const.LEO: '獅子座', const.VIRGO: '處女座',
            const.LIBRA: '天秤座', const.SCORPIO: '天蠍座', const.SAGITTARIUS: '射手座',
            const.CAPRICORN: '摩羯座', const.AQUARIUS: '水瓶座', const.PISCES: '雙魚座'
        }
        self.trans_planets = trans_planets or {
            const.SUN: '太陽', const.MOON: '月亮', const.MERCURY: '水星',
            const.VENUS: '金星', const.MARS: '火星', const.JUPITER: '木星',
            const.SATURN: '土星', const.ASC: '上升點', const.MC: '天頂',
            'Sun': '太陽', 'Moon': '月亮', 'Mercury': '水星',
            'Venus': '金星', 'Mars': '火星', 'Jupiter': '木星',
            'Saturn': '土星', 'Asc': '上升點', 'MC': '天頂'
        }

    def calculate_solar_arc_degrees(self, birth_dt_str: str, birth_time_str: str, utc_offset_str: str, lat: float, lon: float, target_date: Optional[Any] = None) -> float:
        """
        計算次限推進太陽弧度 (Solar Arc in degrees)
        一日一年法則：年齡 N 歲 = 出生後第 N 天的太陽黃經 - 本命太陽黃經
        """
        if target_date is None:
            target_date = date.today()
        if isinstance(target_date, datetime):
            target_date = target_date.date()

        clean_birth_str = birth_dt_str.replace('-', '/')
        birth_d = datetime.strptime(clean_birth_str, '%Y/%m/%d').date()
        age_days = (target_date - birth_d).days
        age_years = age_days / 365.2422
        if age_years < 0:
            age_years = 0.0

        # 本命盤
        dt_natal = Datetime(clean_birth_str, birth_time_str, utc_offset_str)
        pos = GeoPos(lat, lon)
        chart_natal = Chart(dt_natal, pos)
        natal_sun_lon = chart_natal.get(const.SUN).lon

        # 次限盤：出生時間 + age_years 天 (天數 = 實歲年齡)
        birth_datetime = datetime.strptime(f"{clean_birth_str} {birth_time_str}", "%Y/%m/%d %H:%M")
        prog_datetime = birth_datetime + pd.Timedelta(days=age_years)
        prog_date_str = prog_datetime.strftime("%Y/%m/%d")
        prog_time_str = prog_datetime.strftime("%H:%M")

        dt_prog = Datetime(prog_date_str, prog_time_str, utc_offset_str)
        chart_prog = Chart(dt_prog, pos)
        prog_sun_lon = chart_prog.get(const.SUN).lon

        solar_arc = (prog_sun_lon - natal_sun_lon) % 360
        return solar_arc, age_years

    def calculate_active_solar_arcs(
        self,
        chart: Chart,
        birth_dt_str: str,
        birth_time_str: str,
        utc_offset_str: str,
        lat: float,
        lon: float,
        target_date: Optional[Any] = None,
        max_orb: float = 1.0
    ) -> Dict[str, Any]:
        """
        計算當前目標日期下，所有活躍的太陽弧硬相位 (SA Hard Aspects with Orb <= 1.0°)
        """
        solar_arc, age_years = self.calculate_solar_arc_degrees(
            birth_dt_str, birth_time_str, utc_offset_str, lat, lon, target_date
        )

        targets = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN, const.ASC, const.MC]
        natal_points = {}
        for p_id in targets:
            try:
                obj = chart.get(p_id)
                if obj:
                    natal_points[p_id] = obj.lon
            except Exception:
                pass

        active_aspects = []

        # 檢驗 Directed Point vs Natal Point
        for sa_id, sa_natal_lon in natal_points.items():
            sa_directed_lon = (sa_natal_lon + solar_arc) % 360
            sa_sign_idx = int(sa_directed_lon // 30)
            sa_sign = const.LIST_SIGNS[sa_sign_idx]
            sa_deg = sa_directed_lon % 30

            for nat_id, nat_lon in natal_points.items():
                diff = abs(sa_directed_lon - nat_lon)
                if diff > 180:
                    diff = 360 - diff

                for angle, asp_name in self.MAJOR_HARD_ASPECTS.items():
                    orb = abs(diff - angle)
                    if orb <= max_orb:
                        # 取得事件關鍵字
                        kw = self.EVENT_KEYWORDS.get((sa_id, nat_id)) or self.EVENT_KEYWORDS.get((nat_id, sa_id)) or ""
                        
                        sa_name = self.trans_planets.get(sa_id, sa_id)
                        nat_name = self.trans_planets.get(nat_id, nat_id)

                        # 計算精確成相位月份預估 (差 orb 度，太陽弧每年約 1 度，即約 orb * 12 個月)
                        months_to_exact = round(orb * 12.0, 1)

                        active_aspects.append({
                            'sa_planet': sa_id,
                            'sa_planet_name': sa_name,
                            'sa_pos_str': f"{self.trans_signs.get(sa_sign, sa_sign)} {int(sa_deg)}°{int((sa_deg%1)*60):02d}'",
                            'aspect': asp_name,
                            'natal_planet': nat_id,
                            'natal_planet_name': nat_name,
                            'orb': round(orb, 2),
                            'orb_str': f"{round(orb, 2)}°",
                            'is_exact': orb <= 0.25,
                            'significance': kw
                        })

        # 依容許度由緊到鬆排序
        active_aspects.sort(key=lambda x: x['orb'])

        return {
            'target_date': str(target_date or date.today()),
            'age_years': round(age_years, 2),
            'solar_arc_degrees': round(solar_arc, 2),
            'solar_arc_str': f"{int(solar_arc)}°{int((solar_arc % 1) * 60):02d}'",
            'active_aspects': active_aspects,
            'summary': f"當前年齡 {round(age_years, 1)} 歲，太陽弧前推進 {int(solar_arc)}°{int((solar_arc % 1) * 60):02d}'，共偵測到 {len(active_aspects)} 組重大事件硬相位 (容許度 <= {max_orb}°)。"
        }
