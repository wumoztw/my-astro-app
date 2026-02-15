from flatlib import const
from datetime import datetime, date
import pandas as pd
from dignities_logic import DignitiesLogic

class TimeLordsLogic:
    # 這裡保留 RULERS 作為備援，或視專案架構改為完全引用 DignitiesLogic
    RULERS = {
        const.ARIES: const.MARS, const.TAURUS: const.VENUS, const.GEMINI: const.MERCURY,
        const.CANCER: const.MOON, const.LEO: const.SUN, const.VIRGO: const.MERCURY,
        const.LIBRA: const.VENUS, const.SCORPIO: const.MARS, const.SAGITTARIUS: const.JUPITER,
        const.CAPRICORN: const.SATURN, const.AQUARIUS: const.SATURN, const.PISCES: const.JUPITER
    }

    DAY_SEQ = [
        (const.SUN, 10), (const.VENUS, 8), (const.MERCURY, 13),
        (const.MOON, 9), (const.SATURN, 11), (const.JUPITER, 12), (const.MARS, 7),
        ('North Node', 3), ('South Node', 2)
    ]

    NIGHT_SEQ = [
        (const.MOON, 9), (const.SATURN, 11), (const.JUPITER, 12), (const.MARS, 7),
        (const.SUN, 10), (const.VENUS, 8), (const.MERCURY, 13),
        ('North Node', 3), ('South Node', 2)
    ]

    def calculate_profections(self, chart, trans_signs, planet_glyphs, trans_planets, birth_dt_str, current_date=None):
        """計算年小限及其年度主宰星。"""
        if current_date is None: 
            current_date = date.today()
        
        birth_dt = datetime.strptime(birth_dt_str, '%Y/%m/%d')
        
        # 計算足歲年齡
        age = current_date.year - birth_dt.year
        if (current_date.month, current_date.day) < (birth_dt.month, birth_dt.day): 
            age -= 1
        
        # 取得上升點並計算當前小限星座
        asc = chart.get(const.ASC)
        birth_asc_sign_idx = const.LIST_SIGNS.index(asc.sign)
        prof_sign_idx = (birth_asc_sign_idx + age) % 12
        prof_sign = const.LIST_SIGNS[prof_sign_idx]
        
        # 解決衝突：優先使用 DignitiesLogic 的守護星表
        try:
            lord_id = DignitiesLogic.RULERS[prof_sign]
        except (AttributeError, KeyError):
            # 如果 DignitiesLogic 未定義，則回退到本地 RULERS
            lord_id = self.RULERS[prof_sign]
            
        lord_planet = chart.get(lord_id)
        
        # 計算行星位置（度與分）
        p_sign_deg = lord_planet.lon % 30
        d = int(p_sign_deg)
        m = int((p_sign_deg - d) * 60)
        
        return {
            'age': age,
            'prof_sign': trans_signs.get(prof_sign, prof_sign),
            'prof_house_num': (prof_sign_idx - birth_asc_sign_idx) % 12 + 1,
            'lord_of_year': f"{planet_glyphs.get(lord_id, '')} {trans_planets.get(lord_id, lord_id)}",
            'lord_pos': f"{trans_signs.get(lord_planet.sign, lord_planet.sign)} {d}度{m}分"
        }

    def get_firdaria_data(self, birth_dt_str, is_day, current_date=None):
        """計算法達星限週期與當前活動週期。"""
        if current_date is None: 
            current_date = date.today()
            
        birth_dt = datetime.strptime(birth_dt_str, '%Y/%m/%d').date()
        
        # 根據日夜盤決定順序
        seq = self.DAY_SEQ if is_day else self.NIGHT_SEQ
        planets_order = [s[0] for s in seq if s[0] not in ['North Node', 'South Node']]
        
        timeline = []
        current_start = birth_dt
        
        active_major, active_minor, active_start, active_end = None, None, None, None
        
        for major_lord, years in seq:
            # 使用 pd.Timedelta 處理時間跨度 (365.25天/年)
            major_end = current_start + pd.Timedelta(days=years * 365.25)
            sub_periods = []
            
            # 處理行星的大運（有子運）
            if major_lord not in ['North Node', 'South Node']:
                idx = planets_order.index(major_lord)
                ordered_minors = planets_order[idx:] + planets_order[:idx]
                sub_duration_days = (years * 365.25) / 7.0
                sub_start = current_start
                
                for minor_lord in ordered_minors:
                    sub_end = sub_start + pd.Timedelta(days=sub_duration_days)
                    sub_data = {'major': major_lord, 'minor': minor_lord, 'start': sub_start, 'end': sub_end}
                    sub_periods.append(sub_data)
                    
                    # 檢查是否為當前活動運勢
                    if sub_start <= current_date < sub_end:
                        active_major, active_minor, active_start, active_end = major_lord, minor_lord, sub_start, sub_end
                    sub_start = sub_end
            # 處理南北交點的大運（無子運）
            else:
                if current_start <= current_date < major_end:
                    active_major, active_minor, active_start, active_end = major_lord, major_lord, current_start, major_end
                sub_periods.append({'major': major_lord, 'minor': major_lord, 'start': current_start, 'end': major_end})
            
            timeline.append({'lord': major_lord, 'start': current_start, 'end': major_end, 'subs': sub_periods})
            current_start = major_end
            
        return {
            'is_day': is_day,
            'active': {'major': active_major, 'minor': active_minor, 'start': active_start, 'end': active_end},
            'timeline': timeline
        }