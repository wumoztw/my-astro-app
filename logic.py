import swisseph as swe
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from datetime import datetime, date
import pandas as pd
from geopy.geocoders import ArcGIS
from timezonefinder import TimezoneFinder
import pytz
import functools

@functools.lru_cache(maxsize=128)
def _cached_geocode(location_name: str):
    """Cached geocoding to avoid repeated API calls."""
    geolocator = ArcGIS()
    try:
        location = geolocator.geocode(location_name, timeout=10)
        return (location.latitude, location.longitude) if location else None
    except Exception:
        return None

# Modular Imports
from dignities_logic import DignitiesLogic
from aspects_logic import AspectsLogic
from lots_logic import LotsLogic
from time_lords_logic import TimeLordsLogic
import streamlit as st
import os

@st.cache_resource
def init_ephemeris():
    """Initializes the Swiss Ephemeris path once."""
    ephem_path = os.path.abspath('ephem')
    if os.path.exists(ephem_path):
        swe.set_ephe_path(ephem_path)
    return True

class AstrologyLogic:
    # Localization Dictionaries (Shared)
    TRANS_PLANETS = {
        const.SUN: '太陽', const.MOON: '月亮', const.MERCURY: '水星',
        const.VENUS: '金星', const.MARS: '火星', const.JUPITER: '木星',
        const.SATURN: '土星', const.ASC: '上升點', 'Sun': '太陽',
        'Moon': '月亮', 'Mercury': '水星', 'Venus': '金星', 'Mars': '火星',
        'Jupiter': '木星', 'Saturn': '土星', 'Asc': '上升點', 'Ascendant': '上升點'
    }

    PLANET_GLYPHS = {
        const.SUN: '☉', const.MOON: '☽', const.MERCURY: '☿',
        const.VENUS: '♀', const.MARS: '♂', const.JUPITER: '♃',
        const.SATURN: '♄', const.ASC: 'Ⓐ', 'Sun': '☉', 'Moon': '☽',
        'Mercury': '☿', 'Venus': '♀', 'Mars': '♂', 'Jupiter': '♃',
        'Saturn': '♄', 'Asc': 'Ⓐ', 'Ascendant': 'Ⓐ'
    }

    TRANS_SIGNS = {
        const.ARIES: '牡羊座', const.TAURUS: '金牛座', const.GEMINI: '雙子座',
        const.CANCER: '巨蟹座', const.LEO: '獅子座', const.VIRGO: '處女座',
        const.LIBRA: '天秤座', const.SCORPIO: '天蠍座', const.SAGITTARIUS: '射手座',
        const.CAPRICORN: '摩羯座', const.AQUARIUS: '水瓶座', const.PISCES: '雙魚座',
        'Aries': '牡羊座', 'Taurus': '金牛座', 'Gemini': '雙子座', 'Cancer': '巨蟹座',
        'Leo': '獅子座', 'Virgo': '處女座', 'Libra': '天秤座', 'Scorpio': '天蠍座',
        'Sagittarius': '射手座', 'Capricorn': '摩羯座', 'Aquarius': '水瓶座', 'Pisces': '雙魚座'
    }

    TRANS_ASPECTS = {
        'Conjunction': '合相 (0°)', 'Sextile': '六分相 (60°)',
        'Square': '四分相 (90°)', 'Trine': '三分相 (120°)',
        'Opposition': '對分相 (180°)'
    }

    TRANS_HOUSES = {
        1: '第一宮 (命宮)', 2: '第二宮', 3: '第三宮', 4: '第四宮',
        5: '第五宮', 6: '第六宮', 7: '第七宮', 8: '第八宮',
        9: '第九宮', 10: '第十宮', 11: '第十一宮', 12: '第十二宮'
    }

    def __init__(self):
        # Cache initialization
        init_ephemeris()
            
        # Initialize Logic Modules
        self.dignities = DignitiesLogic()
        self.aspects = AspectsLogic()
        self.lots = LotsLogic()
        self.time_lords = TimeLordsLogic()
        self.tf = TimezoneFinder()

    def get_timezone_info(self, lat, lon):
        """Returns (timezone_name, utc_offset_hours) for given coordinates."""
        try:
            tz_name = self.tf.timezone_at(lat=lat, lng=lon)
            if tz_name:
                tz = pytz.timezone(tz_name)
                # Get offset for NOW using a naive datetime
                now = datetime.now()
                offset_seconds = tz.utcoffset(now).total_seconds()
                return tz_name, offset_seconds / 3600.0
            return None, None
        except Exception as e:
            print(f"Error in get_timezone_info: {e}")
            return None, None

    def get_location_coordinates(self, location_name):
        return _cached_geocode(location_name)

    def degree_to_dms(self, degree):
        d = int(degree)
        m = int((degree - d) * 60)
        s = int((degree - d - m/60) * 3600)
        return d, m, s

    def calculate_whole_sign_houses(self, asc_lon):
        """
        古典占星整宮制 (Whole Sign House, WSH)
        上升點所在之星座，整座 (0°00' - 30°00') 即為第一宮 (命宮)。
        之後各星座依序為第 2 至第 12 宮。
        """
        asc_sign_idx = int(asc_lon // 30)
        houses = []
        for i in range(12):
            curr_sign_idx = (asc_sign_idx + i) % 12
            house_lon = curr_sign_idx * 30.0
            sign_const = const.LIST_SIGNS[curr_sign_idx]
            house_id = i + 1
            ruler_const = self.dignities.RULERS.get(sign_const)
            houses.append({
                'id': house_id,
                'id_str': self.TRANS_HOUSES.get(house_id, f"第{house_id}宮"),
                'lon': house_lon,
                'sign': self.TRANS_SIGNS.get(sign_const, sign_const),
                'degree': 0.0,
                'ruler': self.TRANS_PLANETS.get(ruler_const, ruler_const)
            })
        return houses

    def calculate_equal_houses(self, asc_lon):
        """向後相容包裝：預設採用古典整宮制 (Whole Sign)"""
        return self.calculate_whole_sign_houses(asc_lon)

    def get_house_of_lon(self, lon, houses):
        h1_lon = houses[0]['lon']
        diff = (lon - h1_lon) % 360
        return int(diff // 30) + 1

    def is_day_birth(self, chart, houses=None):
        """
        古典天體力學日夜盤判定 (Diurnal vs Nocturnal Sect)
        當太陽位於上升點至下降點之間的地平線上方時為日間盤 (Day Chart)。
        天體周日視運動中，已升起但尚未落下的黃經弧度滿足 0 <= (asc.lon - sun.lon) % 360 <= 180。
        """
        sun = chart.get(const.SUN)
        asc = chart.get(const.ASC)
        diff_above = (asc.lon - sun.lon) % 360
        return 0 <= diff_above <= 180

    def get_planets_data(self, chart, houses):
        planets = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN]
        res = []
        is_day = self.is_day_birth(chart, houses)
        sun_lon = chart.get(const.SUN).lon
        
        for p_id in planets:
            p = chart.get(p_id)
            d, m, s = self.degree_to_dms(p.lon % 30)
            house_num = self.get_house_of_lon(p.lon, houses)
            
            # Use Modular Logic
            dig = self.dignities.calculate_essential_dignities(p.id, p.lon, is_day)
            acc = self.dignities.get_accidental_dignities(p.id, p.lon, house_num, sun_lon, p.lonspeed < 0)
            
            res.append({
                'id': p.id,
                'symbol': self.PLANET_GLYPHS.get(p.id, ''),
                'name': self.TRANS_PLANETS.get(p.id, p.id),
                'sign': self.TRANS_SIGNS.get(p.sign, p.sign),
                'degree_str': f"{d}°{m}'{s}\"",
                'retro': "Ⓡ" if p.lonspeed < 0 else "",
                'lon': p.lon,
                'house': self.TRANS_HOUSES.get(house_num, f"第{house_num}宮"),
                'house_num': house_num,
                'dignity': dig,
                'accidental': acc
            })
        return res

    def get_aspects(self, chart):
        return self.aspects.get_aspects(chart, self.TRANS_PLANETS, self.PLANET_GLYPHS, self.TRANS_ASPECTS)

    def calculate_lots(self, chart, houses, is_day):
        return self.lots.calculate_lots(chart, houses, is_day, self.TRANS_SIGNS, self.TRANS_HOUSES)

    def get_fixed_stars(self, chart):
        return self.lots.get_fixed_stars(chart, self.TRANS_PLANETS)

    def calculate_profections(self, chart, houses, birth_dt_str, current_date=None):
        return self.time_lords.calculate_profections(chart, self.TRANS_SIGNS, self.PLANET_GLYPHS, self.TRANS_PLANETS, birth_dt_str, current_date)

    def get_firdaria_data(self, birth_dt_str, is_day, current_date=None):
        return self.time_lords.get_firdaria_data(birth_dt_str, is_day, current_date)

    def calculate_moon_voc(self, chart):
        moon = chart.get(const.MOON)
        t_leave = (30 - (moon.lon % 30)) / moon.lonspeed if moon.lonspeed != 0 else 0
        moon_sign_idx = int(moon.lon // 30)
        moon_sign = self.TRANS_SIGNS.get(const.LIST_SIGNS[moon_sign_idx], str(moon_sign_idx))
        moon_degree = moon.lon % 30
        
        next_aspect = None
        min_t = float('inf')
        
        major_angles = {0: 'Conjunction', 60: 'Sextile', 90: 'Square', 120: 'Trine', 180: 'Opposition'}
        planets_to_check = [const.SUN, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN]
        
        for p_id in planets_to_check:
            planet = chart.get(p_id)
            rel_speed = planet.lonspeed - moon.lonspeed
            if rel_speed >= 0: continue
            
            rel_lon = (planet.lon - moon.lon) % 360
            max_orb = (self.aspects.ORBS.get(const.MOON, 12.0) + self.aspects.ORBS.get(p_id, 0)) / 2.0
            
            for angle, name in major_angles.items():
                targets = [angle] if angle in [0, 180] else [angle, 360 - angle]
                for T in targets:
                    dist = (rel_lon - T) % 360
                    t_perfect = dist / abs(rel_speed)
                    
                    if 0 < t_perfect < t_leave:
                        if dist <= max_orb:
                            if t_perfect < min_t:
                                min_t = t_perfect
                                degree_to_exact = t_perfect * moon.lonspeed
                                next_aspect = {
                                    'planet': self.TRANS_PLANETS.get(p_id, p_id),
                                    'type': self.TRANS_ASPECTS.get(name, name),
                                    'degree_to_exact': round(degree_to_exact, 2)
                                }
                                
        return {
            'is_voc': next_aspect is None,
            'moon_sign': moon_sign,
            'moon_degree': round(moon_degree, 2),
            'next_aspect': next_aspect
        }

