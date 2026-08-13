"""
synastry_logic.py
古典占星合盤與關係對比模組 (Traditional Synastry & Mutual Reception Engine)
包含：
1. 雙盤宮位疊合 (House Overlays): 計算 Person B 的行星落入 Person A 的何宮。
2. 跨盤相位 (Cross-Aspects): 計算 Person A 與 Person B 行星之間的傳統交角與古典容許度。
3. 古典接納與互容 (Classical Reception & Mutual Reception): 檢查廟旺與互溶關係。
"""

from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from aspects_logic import AspectsLogic
from dignities_logic import DignitiesLogic

class SynastryLogic:
    def __init__(self):
        self.aspects_engine = AspectsLogic()
        self.dignities_engine = DignitiesLogic()
        
        # 傳統守護星對照表 (Domicile Rulers)
        self.DOMICILE_RULERS = {
            'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury',
            'Cancer': 'Moon', 'Leo': 'Sun', 'Virgo': 'Mercury',
            'Libra': 'Venus', 'Scorpio': 'Mars', 'Sagittarius': 'Jupiter',
            'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
        }
        
        # 傳統昂貴/廟旺位置 (Exaltations)
        self.EXALTATIONS = {
            'Sun': 'Aries', 'Moon': 'Taurus', 'Mercury': 'Virgo',
            'Venus': 'Pisces', 'Mars': 'Capricorn', 'Jupiter': 'Cancer', 'Saturn': 'Libra'
        }

    def get_planet_sign(self, planet_lon):
        """根據黃經 (0-360) 取得星座名稱與度數"""
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        sign_idx = int(planet_lon // 30)
        degree = planet_lon % 30
        return signs[sign_idx], degree

    def get_house_overlay(self, planet_lon, house_cusps):
        """
        計算某行星黃經落在對方星盤的哪一個宮位 (1-12)
        house_cusps: list of 12 float longitudes representing house cusps (Placidus/Whole Sign etc.)
        """
        for i in range(12):
            start = house_cusps[i]
            end = house_cusps[(i + 1) % 12]
            
            if start < end:
                if start <= planet_lon < end:
                    return i + 1
            else: # 跨越 0 度 (Aries)
                if planet_lon >= start or planet_lon < end:
                    return i + 1
        return 1 # Fallback

    def calculate_house_overlays(self, chart_a: Chart, chart_b: Chart):
        """
        計算 B 的行星落入 A 的宮位疊合 (B planets in A houses)
        """
        planets_to_check = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN, const.ASC]
        
        # 取得 A 的 12 宮宮頭
        house_cusps_a = [chart_a.get(f'House{i}').lon for i in range(1, 13)]
        
        overlays = []
        for p_id in planets_to_check:
            try:
                p_obj = chart_b.get(p_id)
                lon = p_obj.lon
                house_num = self.get_house_overlay(lon, house_cusps_a)
                sign, deg = self.get_planet_sign(lon)
                overlays.append({
                    'planet': p_id,
                    'longitude': round(lon, 2),
                    'sign': sign,
                    'degree': round(deg, 2),
                    'overlay_house': house_num
                })
            except Exception:
                continue
        return overlays

    def calculate_cross_aspects(self, chart_a: Chart, chart_b: Chart):
        """
        計算 A 與 B 行星之間的跨盤交角 (Cross-Aspects)
        """
        planets_to_check = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN, const.ASC]
        major_angles = {
            0: ('Conjunction', '合相 (0°)'),
            60: ('Sextile', '六合 (60°)'),
            90: ('Square', '刑相 (90°)'),
            120: ('Trine', '三合 (120°)'),
            180: ('Opposition', '對衝 (180°)')
        }
        
        cross_aspects = []
        for p_a in planets_to_check:
            try:
                obj_a = chart_a.get(p_a)
                lon_a = obj_a.lon
            except:
                continue
                
            for p_b in planets_to_check:
                try:
                    obj_b = chart_b.get(p_b)
                    lon_b = obj_b.lon
                except:
                    continue
                
                diff = abs(lon_a - lon_b)
                if diff > 180:
                    diff = 360 - diff
                
                # 檢查古典相位與容許度 (Orb ~ 6-8度)
                for angle, (eng_name, zh_name) in major_angles.items():
                    orb = abs(diff - angle)
                    if orb <= 7.0: # 古典容許度
                        cross_aspects.append({
                            'planet_a': p_a,
                            'planet_b': p_b,
                            'aspect': zh_name,
                            'angle_diff': round(diff, 2),
                            'orb': round(orb, 2)
                        })
        return cross_aspects

    def check_classical_reception(self, chart_a: Chart, chart_b: Chart):
        """
        檢查古典接納與互容 (Reception & Mutual Reception)
        當 A 的行星落在 B 守護星的星座，或反之。
        """
        planets_to_check = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN]
        
        receptions = []
        # 簡化示範：分析 A 與 B 各自行星的互容關係
        # 實作：對每個行星檢查其落入星座的守護星
        for p_a in planets_to_check:
            try:
                obj_a = chart_a.get(p_a)
                sign_a, _ = self.get_planet_sign(obj_a.lon)
                ruler_a = self.DOMICILE_RULERS.get(sign_a)
                
                # 檢查 B 是否有行星為 ruler_a
                for p_b in planets_to_check:
                    obj_b = chart_b.get(p_b)
                    if p_b == ruler_a:
                        receptions.append({
                            'description': f'A 的 {p_a}（在 {sign_a}）受 B 的守護星 {p_b} 接納 (A 仰慕/接受 B)'
                        })
            except:
                continue
                
        return receptions

    def generate_synastry_report(self, name_a, dt_a, pos_a, name_b, dt_b, pos_b):
        """
        綜合生成雙人古典合盤報告數據
        """
        chart_a = Chart(dt_a, pos_a)
        chart_b = Chart(dt_b, pos_b)
        
        overlays_b_in_a = self.calculate_house_overlays(chart_a, chart_b)
        overlays_a_in_b = self.calculate_house_overlays(chart_b, chart_a)
        cross_asp = self.calculate_cross_aspects(chart_a, chart_b)
        receptions = self.check_classical_reception(chart_a, chart_b)
        
        return {
            'person_a': name_a,
            'person_b': name_b,
            'b_in_a_overlays': overlays_b_in_a,
            'a_in_b_overlays': overlays_a_in_b,
            'cross_aspects': cross_asp,
            'receptions': receptions
        }
