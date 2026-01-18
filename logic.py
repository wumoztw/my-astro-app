import swisseph as swe
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.object import GenericObject
from datetime import datetime, date
import pandas as pd
from geopy.geocoders import ArcGIS

class AstrologyLogic:
    # Standard Classical Orbs (Moieties)
    ORBS = {
        const.SUN: 15.0,
        const.MOON: 12.0,
        const.MERCURY: 7.0,
        const.VENUS: 7.0,
        const.MARS: 8.0,
        const.JUPITER: 9.0,
        const.SATURN: 9.0
    }

    # Classical Sign Rulers (Traditional)
    RULERS = {
        const.ARIES: const.MARS,
        const.TAURUS: const.VENUS,
        const.GEMINI: const.MERCURY,
        const.CANCER: const.MOON,
        const.LEO: const.SUN,
        const.VIRGO: const.MERCURY,
        const.LIBRA: const.VENUS,
        const.SCORPIO: const.MARS,
        const.SAGITTARIUS: const.JUPITER,
        const.CAPRICORN: const.SATURN,
        const.AQUARIUS: const.SATURN,
        const.PISCES: const.JUPITER
    }

    # Localization Dictionaries (Traditional Chinese / Taiwan)
    # Mapping both flatlib constants and common strings for absolute robustness
    TRANS_PLANETS = {
        const.SUN: '太陽',
        const.MOON: '月亮',
        const.MERCURY: '水星',
        const.VENUS: '金星',
        const.MARS: '火星',
        const.JUPITER: '木星',
        const.SATURN: '土星',
        const.ASC: '上升點',
        'Sun': '太陽',
        'Moon': '月亮',
        'Mercury': '水星',
        'Venus': '金星',
        'Mars': '火星',
        'Jupiter': '木星',
        'Saturn': '土星',
        'Asc': '上升點',
        'Ascendant': '上升點'
    }

    PLANET_GLYPHS = {
        const.SUN: '☉',
        const.MOON: '☽',
        const.MERCURY: '☿',
        const.VENUS: '♀',
        const.MARS: '♂',
        const.JUPITER: '♃',
        const.SATURN: '♄',
        const.ASC: 'Ⓐ',
        'Sun': '☉',
        'Moon': '☽',
        'Mercury': '☿',
        'Venus': '♀',
        'Mars': '♂',
        'Jupiter': '♃',
        'Saturn': '♄',
        'Asc': 'Ⓐ',
        'Ascendant': 'Ⓐ'
    }

    TRANS_SIGNS = {
        const.ARIES: '牡羊座',
        const.TAURUS: '金牛座',
        const.GEMINI: '雙子座',
        const.CANCER: '巨蟹座',
        const.LEO: '獅子座',
        const.VIRGO: '處女座',
        const.LIBRA: '天秤座',
        const.SCORPIO: '天蠍座',
        const.SAGITTARIUS: '射手座',
        const.CAPRICORN: '摩羯座',
        const.AQUARIUS: '水瓶座',
        const.PISCES: '雙魚座',
        'Aries': '牡羊座', 'Taurus': '金牛座', 'Gemini': '雙子座', 'Cancer': '巨蟹座',
        'Leo': '獅子座', 'Virgo': '處女座', 'Libra': '天秤座', 'Scorpio': '天蠍座',
        'Sagittarius': '射手座', 'Capricorn': '摩羯座', 'Aquarius': '水瓶座', 'Pisces': '雙魚座'
    }

    TRANS_ASPECTS = {
        'Conjunction': '合相 (0°)',
        'Sextile': '六分相 (60°)',
        'Square': '四分相 (90°)',
        'Trine': '三分相 (120°)',
        'Opposition': '對分相 (180°)'
    }

    TRANS_HOUSES = {
        1: '第一宮 (命宮)',
        2: '第二宮',
        3: '第三宮',
        4: '第四宮',
        5: '第五宮',
        6: '第六宮',
        7: '第七宮',
        8: '第八宮',
        9: '第九宮',
        10: '第十宮',
        11: '第十一宮',
        12: '第十二宮'
    }

    def __init__(self):
        import os
        ephem_path = os.path.abspath('ephem')
        if os.path.exists(ephem_path):
            swe.set_ephe_path(ephem_path)
        else:
            common_paths = [
                '/usr/share/astrology/swisseph',
                '/usr/local/share/astrology/swisseph',
                os.path.expanduser('~/ephe'),
                './ephe'
            ]
            for path in common_paths:
                if os.path.exists(path):
                    swe.set_ephe_path(path)
                    break

    def get_location_coordinates(self, location_name):
        """
        Queries location coordinates with robust error handling.
        """
        try:
            geolocator = ArcGIS()
            location = geolocator.geocode(location_name, timeout=10)
            if location:
                return location.latitude, location.longitude
            return None
        except Exception:
            # Silently fail to allow manual coordinate input fallback
            return None

    def get_zodiac_sign(self, degree):
        sign_idx = int(degree // 30)
        sign_degree = degree % 30
        return sign_idx, sign_degree

    def degree_to_dms(self, degree):
        d = int(degree)
        m = int((degree - d) * 60)
        s = int((degree - d - m/60) * 3600)
        return d, m, s

    def calculate_equal_houses(self, asc_lon):
        """Generates 12 Equal Houses starting from ASC."""
        houses = []
        for i in range(12):
            house_lon = (asc_lon + i * 30) % 360
            sign_idx, sign_deg = self.get_zodiac_sign(house_lon)
            sign_const = const.LIST_SIGNS[sign_idx]
            house_id = i + 1
            
            ruler_const = self.RULERS.get(sign_const)
            ruler_name = self.TRANS_PLANETS.get(ruler_const, ruler_const)
            
            houses.append({
                'id': house_id,
                'id_str': self.TRANS_HOUSES.get(house_id, f"第{house_id}宮"),
                'lon': house_lon,
                'sign': self.TRANS_SIGNS.get(sign_const, sign_const),
                'degree': sign_deg,
                'ruler': ruler_name
            })
        return houses

    def get_house_of_lon(self, lon, houses):
        """Finds house index for a given longitude based on Equal House cusps."""
        h1_lon = houses[0]['lon']
        diff = (lon - h1_lon) % 360
        house_num = int(diff // 30) + 1
        return house_num

    def get_planets_data(self, chart, houses):
        """Returns localized planetary data including glyphs and house positions."""
        planets = [
            const.SUN, const.MOON, const.MERCURY, 
            const.VENUS, const.MARS, const.JUPITER, const.SATURN
        ]
        res = []
        for p_id in planets:
            p = chart.get(p_id)
            sign_idx, sign_deg = self.get_zodiac_sign(p.lon)
            d, m, s = self.degree_to_dms(sign_deg)
            
            retro = "Ⓡ" if p.lonspeed < 0 else ""
            house_num = self.get_house_of_lon(p.lon, houses)
            
            res.append({
                'symbol': self.PLANET_GLYPHS.get(p.id, ''),
                'name': self.TRANS_PLANETS.get(p.id, p.id),
                'sign': self.TRANS_SIGNS.get(p.sign, p.sign),
                'degree_str': f"{d}°{m}'{s}\"",
                'retro': retro,
                'house': self.TRANS_HOUSES.get(house_num, f"第{house_num}宮")
            })
        return res

    def get_aspects(self, chart):
        """Calculates major aspects using classical orbs."""
        aspects = []
        planets_to_check = [
            const.SUN, const.MOON, const.MERCURY, 
            const.VENUS, const.MARS, const.JUPITER, const.SATURN
        ]
        major_angles = {0: 'Conjunction', 60: 'Sextile', 90: 'Square', 120: 'Trine', 180: 'Opposition'}
        
        for i in range(len(planets_to_check)):
            for j in range(i + 1, len(planets_to_check)):
                p1_id, p2_id = planets_to_check[i], planets_to_check[j]
                p1, p2 = chart.get(p1_id), chart.get(p2_id)
                
                diff = abs(p1.lon - p2.lon)
                if diff > 180: diff = 360 - diff
                
                max_orb = (self.ORBS.get(p1_id, 0) + self.ORBS.get(p2_id, 0)) / 2.0
                
                for angle, name in major_angles.items():
                    if abs(diff - angle) <= max_orb:
                        p1_sym = self.PLANET_GLYPHS.get(p1_id, '')
                        p2_sym = self.PLANET_GLYPHS.get(p2_id, '')
                        aspects.append({
                            'p1': f"{p1_sym} {self.TRANS_PLANETS.get(p1_id, p1_id)}",
                            'p2': f"{p2_sym} {self.TRANS_PLANETS.get(p2_id, p2_id)}",
                            'aspect': self.TRANS_ASPECTS.get(name, name),
                            'orb': f"{round(abs(diff - angle), 2)}°"
                        })
        return aspects

    def calculate_profections(self, chart, houses, birth_dt_str, current_date=None):
        if current_date is None: current_date = date.today()
        birth_dt = datetime.strptime(birth_dt_str, '%Y/%m/%d')
        age = current_date.year - birth_dt.year
        if (current_date.month, current_date.day) < (birth_dt.month, birth_dt.day): age -= 1
        
        asc = chart.get(const.ASC)
        birth_asc_sign_idx = const.LIST_SIGNS.index(asc.sign)
        prof_sign_idx = (birth_asc_sign_idx + age) % 12
        prof_sign = const.LIST_SIGNS[prof_sign_idx]
        
        lord_id = self.RULERS[prof_sign]
        lord_planet = chart.get(lord_id)
        _, p_sign_deg = self.get_zodiac_sign(lord_planet.lon)
        d, m, s = self.degree_to_dms(p_sign_deg)
        
        return {
            'age': age,
            'prof_sign': self.TRANS_SIGNS.get(prof_sign, prof_sign),
            'prof_house_num': (prof_sign_idx - birth_asc_sign_idx) % 12 + 1,
            'lord_of_year': f"{self.PLANET_GLYPHS.get(lord_id, '')} {self.TRANS_PLANETS.get(lord_id, lord_id)}",
            'lord_pos': f"{self.TRANS_SIGNS.get(lord_planet.sign, lord_planet.sign)} {d}度{m}分"
        }

    def is_day_birth(self, chart, houses):
        """Checks if Sun is above the horizon (Houses 7-12)."""
        sun = chart.get(const.SUN)
        house_num = self.get_house_of_lon(sun.lon, houses)
        return 7 <= house_num <= 12

    def get_firdaria_data(self, birth_dt_str, is_day, current_date=None):
        """Calculates Firdaria periods and the currently active one."""
        if current_date is None: current_date = date.today()
        birth_dt = datetime.strptime(birth_dt_str, '%Y/%m/%d').date()
        
        # Firdaria Sequences
        day_seq = [
            (const.SUN, 10), (const.VENUS, 8), (const.MERCURY, 13), 
            (const.MOON, 9), (const.SATURN, 11), (const.JUPITER, 12), (const.MARS, 7),
            ('North Node', 3), ('South Node', 2)
        ]
        night_seq = [
            (const.MOON, 9), (const.SATURN, 11), (const.JUPITER, 12), (const.MARS, 7),
            (const.SUN, 10), (const.VENUS, 8), (const.MERCURY, 13), 
            ('North Node', 3), ('South Node', 2)
        ]
        
        seq = day_seq if is_day else night_seq
        
        # Sub-period planet order (excluding nodes)
        planets_order = [s[0] for s in seq if s[0] not in ['North Node', 'South Node']]
        
        timeline = []
        current_start = birth_dt
        
        active_major = None
        active_minor = None
        active_start = None
        active_end = None
        
        for major_lord, years in seq:
            major_end = current_start + pd.Timedelta(days=years * 365.25)
            
            # Sub-periods for planets only
            sub_periods = []
            if major_lord not in ['North Node', 'South Node']:
                # Find major lord in planets_order to start the minor lord sequence
                idx = planets_order.index(major_lord)
                ordered_minors = planets_order[idx:] + planets_order[:idx]
                
                sub_duration_days = (years * 365.25) / 7.0
                sub_start = current_start
                for minor_lord in ordered_minors:
                    sub_end = sub_start + pd.Timedelta(days=sub_duration_days)
                    
                    sub_data = {
                        'major': major_lord,
                        'minor': minor_lord,
                        'start': sub_start,
                        'end': sub_end
                    }
                    sub_periods.append(sub_data)
                    
                    # Check if active
                    if sub_start <= current_date < sub_end:
                        active_major = major_lord
                        active_minor = minor_lord
                        active_start = sub_start
                        active_end = sub_end
                    
                    sub_start = sub_end
            else:
                # Nodes don't have sub-periods
                if current_start <= current_date < major_end:
                    active_major = major_lord
                    active_minor = major_lord
                    active_start = current_start
                    active_end = major_end
                
                sub_periods.append({
                    'major': major_lord,
                    'minor': major_lord,
                    'start': current_start,
                    'end': major_end
                })
            
            timeline.append({
                'lord': major_lord,
                'start': current_start,
                'end': major_end,
                'subs': sub_periods
            })
            current_start = major_end
            
        return {
            'is_day': is_day,
            'active': {
                'major': active_major,
                'minor': active_minor,
                'start': active_start,
                'end': active_end
            },
            'timeline': timeline
        }
