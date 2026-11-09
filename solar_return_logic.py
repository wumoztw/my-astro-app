"""
solar_return_logic.py
太陽返照盤 / 流年返照盤 (Solar Return Chart Engine)
依據 Abu Ma'shar / Bonatti / Lilly：太陽回到本命精確黃經的瞬間起盤，
返照上升點落入本命第幾宮，決定該年度的核心主題。
"""

from datetime import date
from typing import Dict, Any, List, Optional

import swisseph as swe
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

SUN_MEAN_SPEED = 0.98564736  # deg/day

HOUSE_YEAR_THEMES = {
    1: "自我更新、身體形象與人生新起點之年",
    2: "財務收入、資源與自我價值之年",
    3: "溝通學習、手足近鄰與短程移動之年",
    4: "家庭居所、不動產與根基整頓之年",
    5: "戀愛創造、子女與娛樂投機之年",
    6: "健康工作、日常責任與服務壓力之年",
    7: "婚姻伴侶、合夥與公開對手之年",
    8: "共有資產、轉化危機與重大割捨之年",
    9: "遠行深造、信念出版與異地機遇之年",
    10: "事業聲望、社會地位與公眾成就之年",
    11: "友誼人脈、願景與貴人助力之年",
    12: "隱退療癒、潛在阻礙與靈性內省之年",
}

SIGN_RULERS = {
    const.ARIES: const.MARS, const.TAURUS: const.VENUS, const.GEMINI: const.MERCURY,
    const.CANCER: const.MOON, const.LEO: const.SUN, const.VIRGO: const.MERCURY,
    const.LIBRA: const.VENUS, const.SCORPIO: const.MARS, const.SAGITTARIUS: const.JUPITER,
    const.CAPRICORN: const.SATURN, const.AQUARIUS: const.SATURN, const.PISCES: const.JUPITER,
}

CLASSICAL = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN]
MAJOR_ASPECTS = {0: '合相 (0°)', 60: '六分相 (60°)', 90: '四分相 (90°)', 120: '三分相 (120°)', 180: '對分相 (180°)'}


def _sun_lon(jd: float) -> float:
    res = swe.calc_ut(jd, swe.SUN)
    return res[0][0] if isinstance(res[0], (tuple, list)) else res[0]


def _dms(lon: float) -> str:
    d = lon % 30
    deg = int(d)
    return f"{deg}°{int((d - deg) * 60):02d}'"


def _offset_str(hours: float) -> str:
    sign = '+' if hours >= 0 else '-'
    total_min = int(round(abs(hours) * 60))
    return f"{sign}{total_min // 60:02d}:{total_min % 60:02d}"


class SolarReturnLogic:
    def __init__(self, trans_signs=None, trans_planets=None):
        self.trans_signs = trans_signs or {}
        self.trans_planets = trans_planets or {}

    def find_solar_return_jd(self, natal_sun_lon: float, target_year: int, birth_month: int, birth_day: int) -> float:
        """求太陽精確回到本命黃經的儒略日 (UT)，精度 < 1e-6°。"""
        if birth_month == 2 and birth_day == 29:
            leap = (target_year % 4 == 0 and target_year % 100 != 0) or target_year % 400 == 0
            birth_day = 29 if leap else 28
        jd = swe.julday(target_year, birth_month, birth_day, 12.0)
        for _ in range(12):
            diff = ((natal_sun_lon - _sun_lon(jd) + 180.0) % 360.0) - 180.0
            if abs(diff) < 1e-6:
                break
            jd += diff / SUN_MEAN_SPEED
        return jd

    def _sign_zh(self, sign_const: str) -> str:
        return self.trans_signs.get(sign_const, sign_const)

    def calculate_solar_return(self, chart_natal: Chart, houses_natal: List[Dict[str, Any]], birth_dt_str: str,
                               utc_offset_hours: float, sr_lat: float, sr_lon: float,
                               target_year: Optional[int] = None, sr_city: str = "") -> Dict[str, Any]:
        if target_year is None:
            target_year = date.today().year
        natal_sun_lon = chart_natal.get(const.SUN).lon
        parts = birth_dt_str.replace('-', '/').split('/')
        birth_month, birth_day = int(parts[1]), int(parts[2])

        sr_jd = self.find_solar_return_jd(natal_sun_lon, target_year, birth_month, birth_day)
        # round to whole seconds first so the displayed time and chart time agree
        local_jd = sr_jd + utc_offset_hours / 24.0
        y, m, d, hour_f = swe.revjul(local_jd + 0.5 / 86400.0)
        total_sec = min(int(hour_f * 3600), 86399)
        hh, mm, ss = total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60
        sr_date_str = f"{y:04d}/{m:02d}/{d:02d}"
        sr_time_str = f"{hh:02d}:{mm:02d}"
        sr_time_full = f"{hh:02d}:{mm:02d}:{ss:02d}"

        sr_chart = Chart(Datetime(sr_date_str, sr_time_full, _offset_str(utc_offset_hours)),
                         GeoPos(sr_lat, sr_lon), hsys=const.HOUSES_WHOLE_SIGN)
        sr_asc = sr_chart.get(const.ASC)
        sr_mc = sr_chart.get(const.MC)
        sr_asc_lon, sr_mc_lon = sr_asc.lon, sr_mc.lon
        sr_asc_sign_zh = self._sign_zh(sr_asc.sign)
        sr_mc_sign_zh = self._sign_zh(sr_mc.sign)

        h1 = houses_natal[0]['lon'] if houses_natal else 0.0
        sr_h1 = int(sr_asc_lon // 30) * 30.0

        def natal_house(lon):
            return int(((lon - h1) % 360) // 30) + 1

        def sr_house(lon):
            return int(((lon - sr_h1) % 360) // 30) + 1

        sr_asc_in_natal_h = natal_house(sr_asc_lon)

        sr_planets_list = []
        for pid in CLASSICAL:
            p = sr_chart.get(pid)
            sr_planets_list.append({
                'id': pid,
                'name': self.trans_planets.get(pid, pid),
                'sign': self._sign_zh(p.sign),
                'degree_str': _dms(p.lon),
                'longitude': round(p.lon, 2),
                'sr_house_num': sr_house(p.lon),
                'natal_house_num': natal_house(p.lon),
                'is_retrograde': p.lonspeed < 0,
            })

        sr_ruler_id = SIGN_RULERS.get(sr_asc.sign)
        sr_ruler_zh = self.trans_planets.get(sr_ruler_id, sr_ruler_id)
        ruler_info = next((p for p in sr_planets_list if p['id'] == sr_ruler_id), {})

        sr_points = {pid: sr_chart.get(pid).lon for pid in CLASSICAL}
        sr_points[const.ASC], sr_points[const.MC] = sr_asc_lon, sr_mc_lon
        natal_points = {}
        for pid in CLASSICAL + [const.ASC, const.MC]:
            try:
                natal_points[pid] = chart_natal.get(pid).lon
            except Exception:
                pass
        names = dict(self.trans_planets)
        names.setdefault(const.MC, '天頂')
        active_aspects = []
        for sid, slon in sr_points.items():
            for nid, nlon in natal_points.items():
                diff = abs(slon - nlon) % 360
                diff = 360 - diff if diff > 180 else diff
                for ang, nm in MAJOR_ASPECTS.items():
                    orb = abs(diff - ang)
                    if orb <= 2.0:
                        active_aspects.append({
                            'sr_planet': sid, 'sr_planet_name': names.get(sid, sid),
                            'aspect': nm,
                            'natal_planet': nid, 'natal_planet_name': names.get(nid, nid),
                            'orb': round(orb, 2), 'orb_str': f"{orb:.2f}°",
                        })
        active_aspects.sort(key=lambda x: x['orb'])

        return {
            "target_year": target_year,
            "sr_datetime_local": f"{sr_date_str} {sr_time_full}",
            "sr_date_str": sr_date_str,
            "sr_time_str": sr_time_str,
            "sr_city": sr_city,
            "sr_asc_lon": round(sr_asc_lon, 2),
            "sr_asc_sign": sr_asc_sign_zh,
            "sr_asc_str": f"{sr_asc_sign_zh} {_dms(sr_asc_lon)}",
            "sr_mc_lon": round(sr_mc_lon, 2),
            "sr_mc_sign": sr_mc_sign_zh,
            "sr_mc_str": f"{sr_mc_sign_zh} {_dms(sr_mc_lon)}",
            "sr_asc_in_natal_house": sr_asc_in_natal_h,
            "sr_asc_natal_house_theme": HOUSE_YEAR_THEMES.get(sr_asc_in_natal_h, ""),
            "sr_ruler_id": sr_ruler_id,
            "sr_ruler_name": sr_ruler_zh,
            "sr_ruler_info": ruler_info,
            "sr_sun_lon": sr_chart.get(const.SUN).lon,
            "natal_sun_lon": natal_sun_lon,
            "planets": sr_planets_list,
            "active_aspects": active_aspects,
            "summary": (f"{target_year} 年太陽返照於 {sr_date_str} {sr_time_full} (UTC{_offset_str(utc_offset_hours)})，"
                        f"返照上升 {sr_asc_sign_zh} {_dms(sr_asc_lon)} 落入本命第 {sr_asc_in_natal_h} 宮："
                        f"{HOUSE_YEAR_THEMES.get(sr_asc_in_natal_h, '')}；年度主星為{sr_ruler_zh}，"
                        f"偵測到 {len(active_aspects)} 組返照-本命緊密相位 (容許度 <= 2°)。"),
        }
