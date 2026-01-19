import swisseph as swe
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from datetime import datetime, date
import pandas as pd
from geopy.geocoders import ArcGIS

# Modular Imports
from dignities_logic import DignitiesLogic
from aspects_logic import AspectsLogic
from lots_logic import LotsLogic
from time_lords_logic import TimeLordsLogic

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
        import os
        ephem_path = os.path.abspath('ephem')
        if os.path.exists(ephem_path):
            swe.set_ephe_path(ephem_path)
            
        # Initialize Logic Modules
        self.dignities = DignitiesLogic()
        self.aspects = AspectsLogic()
        self.lots = LotsLogic()
        self.time_lords = TimeLordsLogic()

    def get_location_coordinates(self, location_name):
        try:
            geolocator = ArcGIS()
            location = geolocator.geocode(location_name, timeout=10)
            return (location.latitude, location.longitude) if location else None
        except Exception:
            return None

    def degree_to_dms(self, degree):
        d = int(degree)
        m = int((degree - d) * 60)
        s = int((degree - d - m/60) * 3600)
        return d, m, s

    def calculate_equal_houses(self, asc_lon):
        houses = []
        for i in range(12):
            house_lon = (asc_lon + i * 30) % 360
            sign_idx = int(house_lon // 30)
            sign_const = const.LIST_SIGNS[sign_idx]
            house_id = i + 1
            ruler_const = self.dignities.RULERS.get(sign_const)
            houses.append({
                'id': house_id,
                'id_str': self.TRANS_HOUSES.get(house_id, f"第{house_id}宮"),
                'lon': house_lon,
                'sign': self.TRANS_SIGNS.get(sign_const, sign_const),
                'degree': house_lon % 30,
                'ruler': self.TRANS_PLANETS.get(ruler_const, ruler_const)
            })
        return houses

    def get_house_of_lon(self, lon, houses):
        h1_lon = houses[0]['lon']
        diff = (lon - h1_lon) % 360
        return int(diff // 30) + 1

    def is_day_birth(self, chart, houses):
        sun = chart.get(const.SUN)
        house_num = self.get_house_of_lon(sun.lon, houses)
        return 7 <= house_num <= 12

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
