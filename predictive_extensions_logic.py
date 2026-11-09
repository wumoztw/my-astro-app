"""
predictive_extensions_logic.py
預測與卜卦擴充：月亮返照盤、即時流年行運、迦勒底行星時 (含卜卦真卦檢驗)、12 個月流月小限日曆。
"""

import math
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional

import swisseph as swe
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

from solar_return_logic import HOUSE_YEAR_THEMES, SIGN_RULERS, CLASSICAL, MAJOR_ASPECTS, _dms, _offset_str

MOON_MEAN_SPEED = 13.176358  # deg/day

CHALDEAN_ORDER = ['Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon']
DAY_RULERS = {0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter', 4: 'Venus', 5: 'Saturn', 6: 'Sun'}

HOUR_MEANINGS = {
    'Jupiter': "💰 大吉：求財、簽約、晉見貴人、祈福",
    'Venus': "🌸 吉：約會、社交、合作、藝文",
    'Mercury': "🧠 平吉：商務談判、學習、文書、交易",
    'Sun': "👑 吉：謀求權位、公開發表、見長官",
    'Moon': "🌙 平：差旅、公眾事務、日常溝通",
    'Mars': "⚔️ 凶/剛：運動競技、外科、破除障礙（忌爭訟婚嫁）",
    'Saturn': "⏳ 凶/守：整頓舊務、購買土地、沉潛修煉（忌匆忙開創）",
}

TRIPLICITY_LORDS = {
    'Fire': ['Sun', 'Jupiter', 'Saturn'], 'Earth': ['Venus', 'Moon', 'Mars'],
    'Air': ['Saturn', 'Mercury', 'Jupiter'], 'Water': ['Venus', 'Mars', 'Moon'],
}
SIGN_ELEMENT = {
    const.ARIES: 'Fire', const.LEO: 'Fire', const.SAGITTARIUS: 'Fire',
    const.TAURUS: 'Earth', const.VIRGO: 'Earth', const.CAPRICORN: 'Earth',
    const.GEMINI: 'Air', const.LIBRA: 'Air', const.AQUARIUS: 'Air',
    const.CANCER: 'Water', const.SCORPIO: 'Water', const.PISCES: 'Water',
}
ELEMENT_QUALITIES = {'Fire': {'hot', 'dry'}, 'Earth': {'cold', 'dry'}, 'Air': {'hot', 'moist'}, 'Water': {'cold', 'moist'}}
PLANET_QUALITIES = {
    'Sun': {'hot', 'dry'}, 'Moon': {'cold', 'moist'}, 'Mercury': {'cold', 'dry'}, 'Venus': {'cold', 'moist'},
    'Mars': {'hot', 'dry'}, 'Jupiter': {'hot', 'moist'}, 'Saturn': {'cold', 'dry'},
}

BENEFICS = {'Jupiter', 'Venus', 'Sun'}
MALEFICS = {'Mars', 'Saturn'}


def _calc_lon(jd: float, body: int) -> float:
    res = swe.calc_ut(jd, body)
    return res[0][0] if isinstance(res[0], (tuple, list)) else res[0]


def _angdiff(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return 360 - d if d > 180 else d


def _fmt_hm(hours: float) -> str:
    total = int(round((hours % 24) * 60)) % 1440
    return f"{total // 60:02d}:{total % 60:02d}"


def _to_date(v: Any) -> date:
    if v is None:
        return date.today()
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    parts = str(v).replace('-', '/').split('/')
    return date(int(parts[0]), int(parts[1]), int(parts[2]))


class PredictiveExtensionsLogic:
    def __init__(self, trans_signs=None, trans_planets=None, planet_glyphs=None, dignities=None):
        self.trans_signs = trans_signs or {}
        self.trans_planets = trans_planets or {}
        self.glyphs = planet_glyphs or {}
        self.dignities = dignities

    def _sign_zh(self, sign_const: str) -> str:
        return self.trans_signs.get(sign_const, sign_const)

    @staticmethod
    def _natal_points(chart_natal: Chart) -> Dict[str, float]:
        pts = {}
        for pid in CLASSICAL + [const.ASC, const.MC]:
            try:
                pts[pid] = chart_natal.get(pid).lon
            except Exception:
                pass
        return pts

    def _names(self) -> Dict[str, str]:
        names = dict(self.trans_planets)
        names.setdefault(const.MC, '天頂')
        return names

    # ------------------------------------------------------------------ #4
    def find_lunar_return_jd(self, natal_moon_lon: float, target_date: date) -> float:
        """求月亮精確回到本命黃經、最接近 target_date 的儒略日 (UT)。"""
        jd = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)
        diff = ((natal_moon_lon - _calc_lon(jd, swe.MOON) + 180.0) % 360.0) - 180.0
        jd += diff / MOON_MEAN_SPEED
        for _ in range(30):
            diff = ((natal_moon_lon - _calc_lon(jd, swe.MOON) + 180.0) % 360.0) - 180.0
            if abs(diff) < 1e-6:
                break
            jd += diff / MOON_MEAN_SPEED
        return jd

    def calculate_lunar_return(self, chart_natal: Chart, houses_natal: List[Dict[str, Any]], utc_offset_hours: float,
                               lr_lat: float, lr_lon: float, target_date: Optional[Any] = None,
                               lr_city: str = "") -> Dict[str, Any]:
        target = _to_date(target_date)
        natal_moon_lon = chart_natal.get(const.MOON).lon
        lr_jd = self.find_lunar_return_jd(natal_moon_lon, target)
        local_jd = lr_jd + utc_offset_hours / 24.0
        y, m, d, hour_f = swe.revjul(local_jd + 0.5 / 86400.0)
        total_sec = min(int(hour_f * 3600), 86399)
        hh, mm, ss = total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60
        date_str = f"{y:04d}/{m:02d}/{d:02d}"
        time_full = f"{hh:02d}:{mm:02d}:{ss:02d}"

        lr_chart = Chart(Datetime(date_str, time_full, _offset_str(utc_offset_hours)),
                         GeoPos(lr_lat, lr_lon), hsys=const.HOUSES_WHOLE_SIGN)
        asc, mc = lr_chart.get(const.ASC), lr_chart.get(const.MC)
        asc_sign_zh, mc_sign_zh = self._sign_zh(asc.sign), self._sign_zh(mc.sign)

        h1 = houses_natal[0]['lon'] if houses_natal else 0.0
        lr_h1 = int(asc.lon // 30) * 30.0

        def natal_house(lon):
            return int(((lon - h1) % 360) // 30) + 1

        def lr_house(lon):
            return int(((lon - lr_h1) % 360) // 30) + 1

        asc_in_natal = natal_house(asc.lon)
        planets = []
        for pid in CLASSICAL:
            p = lr_chart.get(pid)
            planets.append({
                'id': pid, 'name': self.trans_planets.get(pid, pid), 'sign': self._sign_zh(p.sign),
                'degree_str': _dms(p.lon), 'longitude': round(p.lon, 2),
                'lr_house_num': lr_house(p.lon), 'natal_house_num': natal_house(p.lon),
                'is_retrograde': p.lonspeed < 0,
            })
        ruler_id = SIGN_RULERS.get(asc.sign)
        ruler_zh = self.trans_planets.get(ruler_id, ruler_id)

        lr_points = {pid: lr_chart.get(pid).lon for pid in CLASSICAL}
        lr_points[const.ASC], lr_points[const.MC] = asc.lon, mc.lon
        names = self._names()
        aspects = []
        for sid, slon in lr_points.items():
            for nid, nlon in self._natal_points(chart_natal).items():
                diff = _angdiff(slon, nlon)
                for ang, nm in MAJOR_ASPECTS.items():
                    orb = abs(diff - ang)
                    if orb <= 2.0:
                        aspects.append({
                            'lr_planet': sid, 'lr_planet_name': names.get(sid, sid), 'aspect': nm,
                            'natal_planet': nid, 'natal_planet_name': names.get(nid, nid),
                            'orb': round(orb, 2), 'orb_str': f"{orb:.2f}°",
                        })
        aspects.sort(key=lambda x: x['orb'])
        theme = HOUSE_YEAR_THEMES.get(asc_in_natal, "").replace("之年", "之月")
        return {
            'lr_datetime_local': f"{date_str} {time_full}",
            'lr_date_str': date_str,
            'lr_time_str': f"{hh:02d}:{mm:02d}",
            'lr_city': lr_city,
            'lr_asc_lon': round(asc.lon, 2),
            'lr_asc_sign': asc_sign_zh,
            'lr_asc_str': f"{asc_sign_zh} {_dms(asc.lon)}",
            'lr_mc_lon': round(mc.lon, 2),
            'lr_mc_str': f"{mc_sign_zh} {_dms(mc.lon)}",
            'lr_asc_in_natal_house': asc_in_natal,
            'lr_asc_natal_house_theme': theme,
            'lr_ruler_id': ruler_id,
            'lr_ruler_name': ruler_zh,
            'lr_moon_lon': lr_chart.get(const.MOON).lon,
            'natal_moon_lon': natal_moon_lon,
            'planets': planets,
            'active_aspects': aspects,
            'summary': (f"月亮返照於 {date_str} {time_full} (UTC{_offset_str(utc_offset_hours)})，"
                        f"返照上升 {asc_sign_zh} {_dms(asc.lon)} 落入本命第 {asc_in_natal} 宮：{theme}；"
                        f"當月主星為{ruler_zh}，共 {len(aspects)} 組返照-本命緊密相位 (容許度 <= 2°)。"),
        }

    # ------------------------------------------------------------------ #5
    def _transit_meaning(self, tid: str, ang: int, nname: str) -> str:
        tname = self.trans_planets.get(tid, tid)
        soft = ang in (0, 60, 120)
        if tid == 'Jupiter':
            return (f"流年木星{'合' if ang == 0 else '拱'}本命{nname}：貴人提攜與順遂擴張" if soft
                    else f"流年木星刑沖本命{nname}：過度擴張、用力過猛，宜節制承諾")
        if tid in MALEFICS:
            return (f"流年{tname}{'合' if ang == 0 else '拱'}本命{nname}：沉穩推進、紀律與行動力可轉為助力"
                    if (soft and ang != 0) else
                    f"流年{tname}{'合' if ang == 0 else '刑沖'}本命{nname}：現實考驗、壓力磨礪或結構重整")
        if tid == 'Venus':
            return f"流年金星{'合' if ang == 0 else ('拱' if soft else '刑沖')}本命{nname}：人際、財務與感情的契機" if soft \
                else f"流年金星刑沖本命{nname}：關係與花費需留意取捨"
        if tid == 'Sun':
            return f"流年太陽觸動本命{nname}：短期焦點與曝光，事件浮上檯面"
        if tid == 'Moon':
            return f"流年月亮觸動本命{nname}：短暫情緒起伏與日常事件的觸發點"
        return f"流年水星觸動本命{nname}：訊息、文書與溝通事務活絡"

    def calculate_transits(self, chart_natal: Chart, houses_natal: List[Dict[str, Any]], utc_offset_hours: float,
                           lat: float, lon: float, target_date: Optional[Any] = None,
                           target_time_str: str = "12:00") -> Dict[str, Any]:
        target = _to_date(target_date)
        date_str = f"{target.year:04d}/{target.month:02d}/{target.day:02d}"
        tr_chart = Chart(Datetime(date_str, target_time_str, _offset_str(utc_offset_hours)),
                         GeoPos(lat, lon), hsys=const.HOUSES_WHOLE_SIGN)
        h1 = houses_natal[0]['lon'] if houses_natal else 0.0
        planets = []
        for pid in CLASSICAL:
            p = tr_chart.get(pid)
            hn = int(((p.lon - h1) % 360) // 30) + 1
            planets.append({
                'id': pid, 'name': self.trans_planets.get(pid, pid), 'sign': self._sign_zh(p.sign),
                'degree_str': _dms(p.lon), 'longitude': round(p.lon, 2),
                'natal_house_num': hn, 'natal_house_str': f"本命第 {hn} 宮",
                'is_retrograde': p.lonspeed < 0,
            })
        names = self._names()
        natal_pts = self._natal_points(chart_natal)
        aspects = []
        for p in planets:
            for nid, nlon in natal_pts.items():
                diff = _angdiff(p['longitude'], nlon)
                for ang, nm in MAJOR_ASPECTS.items():
                    orb = abs(diff - ang)
                    if orb <= 2.5 and not (ang == 0 and p['id'] == nid):
                        nname = names.get(nid, nid)
                        aspects.append({
                            'transit_planet': p['id'], 'transit_planet_name': p['name'], 'aspect': nm,
                            'natal_planet': nid, 'natal_planet_name': nname,
                            'orb': round(orb, 2), 'orb_str': f"{orb:.2f}°",
                            'meaning': self._transit_meaning(p['id'], ang, nname),
                        })
        aspects.sort(key=lambda x: x['orb'])
        return {
            'target_datetime': f"{date_str} {target_time_str}",
            'planets': planets,
            'active_aspects': aspects,
            'summary': (f"{date_str} {target_time_str} 流年行運：偵測到 {len(aspects)} 組行運-本命主要相位 "
                        f"(容許度 <= 2.5°)" + (f"，最緊密：{aspects[0]['meaning']}" if aspects else "。")),
        }

    # ------------------------------------------------------------------ #6
    @staticmethod
    def _sun_times(target: date, lat: float, lon: float, utc_offset_hours: float):
        """近似日出日落 (地方時, 小時)；極端緯度夾限在安全範圍。"""
        n = target.timetuple().tm_yday
        decl = math.radians(23.44) * math.sin(math.radians(360.0 / 365.0 * (n - 81)))
        cos_h = -math.tan(math.radians(max(-89.0, min(89.0, lat)))) * math.tan(decl)
        cos_h = max(-1.0, min(1.0, cos_h))
        half_day = math.degrees(math.acos(cos_h)) / 15.0  # hours
        ascdiff = (half_day - 6.0) * 15.0
        # shift from solar noon to local clock time (longitude vs. zone meridian)
        shift = (utc_offset_hours * 15.0 - lon) / 15.0
        sunrise = max(4.5, min(7.5, 6.0 - ascdiff / 15.0 + shift))
        sunset = max(16.5, min(19.5, 18.0 + ascdiff / 15.0 + shift))
        return sunrise, sunset

    def calculate_planetary_hours(self, target_date: Any, birth_time_str: str, utc_offset_hours: float,
                                  lat: float, lon: float, asc_sign_const: Optional[str] = None) -> Dict[str, Any]:
        target = _to_date(target_date)
        day_ruler = DAY_RULERS[target.weekday()]
        sunrise, sunset = self._sun_times(target, lat, lon, utc_offset_hours)
        day_len = (sunset - sunrise) / 12.0
        night_len = (24.0 - (sunset - sunrise)) / 12.0
        start_idx = CHALDEAN_ORDER.index(day_ruler)

        table = []
        for i in range(24):
            if i < 12:
                start = sunrise + i * day_len
                end = start + day_len
                period = '日間'
            else:
                start = sunset + (i - 12) * night_len
                end = start + night_len
                period = '夜間'
            rid = CHALDEAN_ORDER[(start_idx + i) % 7]
            table.append({
                'hour_index': i + 1, 'period': period,
                'start_time': _fmt_hm(start), 'end_time': _fmt_hm(end),
                'start_h': start, 'end_h': end,
                'ruler_id': rid, 'ruler_name': self.trans_planets.get(rid, rid),
                'ruler_glyph': self.glyphs.get(rid, ''),
                'electional_meaning': HOUR_MEANINGS[rid],
            })

        try:
            bh, bm = birth_time_str.strip().split(':')[:2]
            t_h = int(bh) + int(bm) / 60.0
        except Exception:
            t_h = 12.0
        # hours before sunrise belong to the previous night's last hours (index 24 wraps)
        probe = t_h if t_h >= sunrise else t_h + 24.0
        active = table[-1]
        for row in table:
            end = row['end_h'] if row['end_h'] > row['start_h'] else row['end_h'] + 24.0
            start = row['start_h']
            if start <= probe < end or start <= probe + 24.0 < end:
                active = row
                break
        active_hour = {k: v for k, v in active.items() if k not in ('start_h', 'end_h')}
        for row in table:
            row.pop('start_h'), row.pop('end_h')

        radicality = ""
        if asc_sign_const:
            hr = active_hour['ruler_id']
            asc_ruler = SIGN_RULERS.get(asc_sign_const)
            element = SIGN_ELEMENT.get(asc_sign_const)
            if hr == asc_ruler:
                radicality = "✅ 完全同主 (行星時主星即上升守護星 — 真卦強效成立)"
            elif element and hr in TRIPLICITY_LORDS[element]:
                radicality = "✅ 同三分性元素 (行星時主星與上升星座同屬三分主星 — 真卦成立)"
            elif element and PLANET_QUALITIES[hr] == ELEMENT_QUALITIES[element]:
                radicality = "✅ 性質相通 (行星時主星與上升星座冷熱乾濕同質 — 卦象相契)"
            else:
                radicality = "⚠️ 非同主/同三分性 (需留意問卜動機是否清晰)"

        return {
            'day_ruler_id': day_ruler, 'day_ruler_name': self.trans_planets.get(day_ruler, day_ruler),
            'sunrise_str': _fmt_hm(sunrise), 'sunset_str': _fmt_hm(sunset),
            'active_hour': active_hour, 'horary_radicality': radicality, 'hours_table': table,
        }

    # ------------------------------------------------------------------ #8
    def calculate_monthly_profections_calendar(self, chart_natal: Chart, houses_natal: List[Dict[str, Any]],
                                               birth_dt_str: str, target_year: int) -> List[Dict[str, Any]]:
        parts = birth_dt_str.replace('-', '/').split('/')
        b_year, b_month, b_day = int(parts[0]), int(parts[1]), int(parts[2])

        def birthday(year: int) -> date:
            try:
                return date(year, b_month, b_day)
            except ValueError:  # Feb 29 in a non-leap year
                return date(year, 2, 28)

        annual_house = (target_year - b_year) % 12 + 1
        start0 = birthday(target_year)
        span = (birthday(target_year + 1) - start0).days
        rows = []
        for i in range(12):
            s = start0 + timedelta(days=int(round(i * span / 12.0)))
            e = start0 + timedelta(days=int(round((i + 1) * span / 12.0))) - timedelta(days=1)
            hnum = (annual_house + i - 1) % 12 + 1
            h = houses_natal[hnum - 1]
            lord_id = h.get('ruler_id')
            if lord_id in BENEFICS:
                tag = "🌟 吉星主政 (木/金/日)"
            elif lord_id in MALEFICS:
                tag = "⚡ 考驗磨礪 (火/土)"
            else:
                tag = "⚖️ 中性靈動 (水/月)"
            rows.append({
                'month_index': i + 1,
                'start_date': s.strftime("%Y/%m/%d"), 'end_date': e.strftime("%Y/%m/%d"),
                'house_num': hnum, 'house_name': h.get('id_str', f"第{hnum}宮"),
                'sign': h.get('sign', ''), 'lord_id': lord_id,
                'lord_name': self.trans_planets.get(lord_id, lord_id),
                'vitality_tag': tag,
                'focus_theme': HOUSE_YEAR_THEMES.get(hnum, "").replace("之年", "之月"),
            })
        return rows
