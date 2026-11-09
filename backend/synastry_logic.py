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

TRANS_PLANETS = {
    'Sun': '太陽', 'Moon': '月亮', 'Mercury': '水星', 'Venus': '金星',
    'Mars': '火星', 'Jupiter': '木星', 'Saturn': '土星', 'Asc': '上升點'
}
TRANS_SIGNS = {
    'Aries': '牡羊座', 'Taurus': '金牛座', 'Gemini': '雙子座', 'Cancer': '巨蟹座',
    'Leo': '獅子座', 'Virgo': '處女座', 'Libra': '天秤座', 'Scorpio': '天蠍座',
    'Sagittarius': '射手座', 'Capricorn': '摩羯座', 'Aquarius': '水瓶座', 'Pisces': '雙魚座'
}
CLASSICAL_PLANETS = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']


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
        
        # 取得 A 的 12 宮宮頭 (整宮制：以上升星座 0° 起算)
        try:
            asc_a = chart_a.get(const.ASC).lon
            house_cusps_a = [((int(asc_a // 30) + i) % 12) * 30.0 for i in range(12)]
        except Exception:
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
                            'planet_a_zh': TRANS_PLANETS.get(p_a, p_a),
                            'planet_b': p_b,
                            'planet_b_zh': TRANS_PLANETS.get(p_b, p_b),
                            'angle': angle,
                            'aspect': zh_name,
                            'aspect_name': zh_name,
                            'angle_diff': round(diff, 2),
                            'orb': round(orb, 2)
                        })
        return cross_aspects

    def _dignified_planets(self, sign):
        """回傳某星座中擁有廟(Domicile)或旺(Exaltation)尊貴的行星 {planet: 尊貴類型}"""
        res = {}
        ruler = self.DOMICILE_RULERS.get(sign)
        if ruler:
            res[ruler] = '廟'
        for planet, ex_sign in self.EXALTATIONS.items():
            if ex_sign == sign:
                res.setdefault(planet, '旺')
        return res

    def check_classical_reception(self, chart_a: Chart, chart_b: Chart):
        """
        檢查古典接納與互容 (Reception & Mutual Reception)
        當 A 的行星落在 B 某行星的廟/旺星座，即被該行星接納；雙方互相接納則為互容。
        """
        receptions = []
        for p_a in CLASSICAL_PLANETS:
            try:
                sign_a, _ = self.get_planet_sign(chart_a.get(p_a).lon)
            except Exception:
                continue
            for p_b in CLASSICAL_PLANETS:
                if p_a == p_b:
                    continue
                try:
                    sign_b, _ = self.get_planet_sign(chart_b.get(p_b).lon)
                except Exception:
                    continue
                # B 的 p_b 是否在 A 的 p_a 所在星座擁有尊貴 (A 被 B 接納)
                a_by_b = self._dignified_planets(sign_a).get(p_b)
                # A 的 p_a 是否在 B 的 p_b 所在星座擁有尊貴 (B 被 A 接納)
                b_by_a = self._dignified_planets(sign_b).get(p_a)
                if not a_by_b and not b_by_a:
                    continue
                za, zb = TRANS_PLANETS[p_a], TRANS_PLANETS[p_b]
                sa, sb = TRANS_SIGNS[sign_a], TRANS_SIGNS[sign_b]
                if a_by_b and b_by_a:
                    rtype = '互容 (Mutual Reception)'
                    desc = (f'A 的{za}（在{sa}）與 B 的{zb}（在{sb}）形成互容：'
                            f'{zb}為{sa}之{a_by_b}星，{za}為{sb}之{b_by_a}星')
                elif a_by_b:
                    rtype = '單向接納 (Reception)'
                    desc = f'A 的{za}（在{sa}）受 B 的{zb}接納（{zb}為{sa}之{a_by_b}星）'
                else:
                    rtype = '單向接納 (Reception)'
                    desc = f'B 的{zb}（在{sb}）受 A 的{za}接納（{za}為{sb}之{b_by_a}星）'
                receptions.append({
                    'planet_a': p_a, 'planet_b': p_b, 'type': rtype, 'description': desc
                })
        return receptions

    def generate_synastry_report(self, name_a, dt_a, pos_a, name_b, dt_b, pos_b):
        """
        綜合生成雙人古典合盤報告數據
        """
        chart_a = Chart(dt_a, pos_a, hsys=const.HOUSES_WHOLE_SIGN)
        chart_b = Chart(dt_b, pos_b, hsys=const.HOUSES_WHOLE_SIGN)
        
        overlays_b_in_a = self.calculate_house_overlays(chart_a, chart_b)
        overlays_a_in_b = self.calculate_house_overlays(chart_b, chart_a)
        cross_asp = self.calculate_cross_aspects(chart_a, chart_b)
        receptions = self.check_classical_reception(chart_a, chart_b)
        
        house_of_b = {o['planet']: o['overlay_house'] for o in overlays_b_in_a}
        planets_b = []
        for p_id in CLASSICAL_PLANETS:
            p_obj = chart_b.get(p_id)
            lon = p_obj.lon
            sign, deg = self.get_planet_sign(lon)
            planets_b.append({
                'id': p_id,
                'name': TRANS_PLANETS[p_id],
                'sign': TRANS_SIGNS[sign],
                'degree_str': f"{int(deg)}°{int((deg % 1) * 60):02d}'",
                'longitude': round(lon, 2),
                'is_retrograde': bool(p_obj.lonspeed < 0),
                'overlay_house': house_of_b.get(p_id)
            })

        def _pos_str(obj_id):
            sign, deg = self.get_planet_sign(chart_b.get(obj_id).lon)
            return f"{TRANS_SIGNS[sign]} {int(deg)}°{int((deg % 1) * 60):02d}'"

        return {
            'person_a': name_a,
            'person_b': name_b,
            'planets': planets_b,
            'asc_b_str': _pos_str(const.ASC),
            'sun_b_str': _pos_str(const.SUN),
            'moon_b_str': _pos_str(const.MOON),
            'b_in_a_overlays': overlays_b_in_a,
            'a_in_b_overlays': overlays_a_in_b,
            'cross_aspects': cross_asp,
            'receptions': receptions,
            'resonance_scores': self.calculate_synastry_resonance_score(chart_a, chart_b, cross_asp, receptions)
        }

    def calculate_synastry_resonance_score(self, chart_a: Chart, chart_b: Chart, cross_aspects=None, receptions=None) -> dict:
        """
        計算古典合盤關係能量量化指數 (Synastry Quantitative Resonance Score)
        依據古典吉凶星、互容接納、日月調和與跨盤交角加權。
        """
        if cross_aspects is None:
            cross_aspects = self.calculate_cross_aspects(chart_a, chart_b)
        if receptions is None:
            receptions = self.check_classical_reception(chart_a, chart_b)

        # 基礎起始分 60 分
        biz_score = 60.0
        love_score = 60.0
        tension_score = 15.0
        highlights = []

        # 1. 互容接納加分
        num_receptions = len(receptions)
        if num_receptions > 0:
            rec_bonus = min(num_receptions * 8.0, 24.0)
            biz_score += rec_bonus
            love_score += rec_bonus
            highlights.append(f"✨ 具備 {num_receptions} 組古典接納互容，彼此願意包容並形成利益或情感綁定 (+{int(rec_bonus)}分)")

        # 2. 跨盤相位加權
        benefics = ['Venus', 'Jupiter', 'Sun']
        malefics = ['Mars', 'Saturn']

        for asp in cross_aspects:
            p_a = asp.get('planet_a')
            p_b = asp.get('planet_b')
            ang = asp.get('angle')
            orb = asp.get('orb', 5.0)
            orb_factor = max(0.2, (6.0 - orb) / 6.0)

            # 日月和諧 (高契合度)
            if (p_a in ['Sun', 'Moon']) and (p_b in ['Sun', 'Moon']):
                if ang in [0, 60, 120]:
                    love_score += 15.0 * orb_factor
                    biz_score += 10.0 * orb_factor
                    highlights.append(f"☀️🌙 日月形成 {asp.get('aspect_name')}，心理與精神共鳴深刻")
                elif ang in [90, 180]:
                    tension_score += 12.0 * orb_factor
                    highlights.append(f"⚡ 日月形成 {asp.get('aspect_name')}，生活習性或意志存在摩擦")

            # 吉星加持 (金星、木星)
            if p_a in benefics and p_b in benefics:
                if ang in [0, 60, 120]:
                    biz_score += 8.0 * orb_factor
                    love_score += 10.0 * orb_factor

            # 水星 (商務溝通契合)
            if (p_a == 'Mercury' or p_b == 'Mercury') and ang in [0, 60, 120]:
                biz_score += 8.0 * orb_factor

            # 凶星張力 (火星、土星刑沖)
            if (p_a in malefics or p_b in malefics) and ang in [90, 180]:
                tension_score += 10.0 * orb_factor
                biz_score -= 5.0 * orb_factor
                love_score -= 6.0 * orb_factor
                highlights.append(f"⚠️ {p_a} 與 {p_b} 形成 {asp.get('aspect_name')}，需預防權力衝突或冷戰")

        # 邊界保護 20 ~ 98 分
        biz_final = max(25, min(98, round(biz_score, 1)))
        love_final = max(25, min(98, round(love_score, 1)))
        tension_final = max(10, min(95, round(tension_score, 1)))

        return {
            'business_harmony_score': biz_final,
            'romantic_harmony_score': love_final,
            'tension_index': tension_final,
            'highlights': highlights[:5],
            'summary': f"事業協同指數：{biz_final} 分 | 情感黏著指數：{love_final} 分 | 關係張力指數：{tension_final} 分"
        }
