from flatlib import const
from datetime import datetime, date
import pandas as pd

class TimeLordsLogic:
    def calculate_profections(self, chart, trans_signs, planet_glyphs, trans_planets, birth_dt_str, current_date=None):
        if current_date is None: current_date = date.today()
        if isinstance(current_date, datetime): current_date = current_date.date()
        
        birth_dt = datetime.strptime(birth_dt_str, '%Y/%m/%d')
        birth_d = birth_dt.date()
        age = current_date.year - birth_d.year
        if (current_date.month, current_date.day) < (birth_d.month, birth_d.day): age -= 1
        if age < 0: age = 0  # Handle future births (horary)
        
        asc = chart.get(const.ASC)
        birth_asc_sign_idx = const.LIST_SIGNS.index(asc.sign)
        prof_sign_idx = (birth_asc_sign_idx + age) % 12
        prof_sign = const.LIST_SIGNS[prof_sign_idx]
        
        # This needs a ruler table - ideally passed or accessed via shared logic
        # For simplicity in this standalone module, we'll re-define traditional rulers
        RULERS = {
            const.ARIES: const.MARS, const.TAURUS: const.VENUS, const.GEMINI: const.MERCURY,
            const.CANCER: const.MOON, const.LEO: const.SUN, const.VIRGO: const.MERCURY,
            const.LIBRA: const.VENUS, const.SCORPIO: const.MARS, const.SAGITTARIUS: const.JUPITER,
            const.CAPRICORN: const.SATURN, const.AQUARIUS: const.SATURN, const.PISCES: const.JUPITER
        }
        
        lord_id = RULERS[prof_sign]
        lord_planet = chart.get(lord_id)
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
        """Calculates Firdaria periods and the currently active one."""
        if current_date is None: current_date = date.today()
        # Ensure current_date is a pandas Timestamp for consistent comparison
        target_ts = pd.Timestamp(current_date)
        
        birth_dt = pd.Timestamp(datetime.strptime(birth_dt_str, '%Y/%m/%d')).normalize()
        
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
        planets_order = [s[0] for s in seq if s[0] not in ['North Node', 'South Node']]
        
        timeline = []
        current_start = birth_dt
        
        active_major, active_minor, active_start, active_end = None, None, None, None
        
        for major_lord, years in seq:
            major_end = current_start + pd.Timedelta(days=years * 365.25)
            sub_periods = []
            if major_lord not in ['North Node', 'South Node']:
                idx = planets_order.index(major_lord)
                ordered_minors = planets_order[idx:] + planets_order[:idx]
                sub_duration_days = (years * 365.25) / 7.0
                sub_start = current_start
                for minor_lord in ordered_minors:
                    sub_end = sub_start + pd.Timedelta(days=sub_duration_days)
                    sub_data = {'major': major_lord, 'minor': minor_lord, 'start': sub_start, 'end': sub_end}
                    sub_periods.append(sub_data)
                    if sub_start <= target_ts < sub_end:
                        active_major, active_minor, active_start, active_end = major_lord, minor_lord, sub_start, sub_end
                    sub_start = sub_end
            else:
                if current_start <= target_ts < major_end:
                    active_major, active_minor, active_start, active_end = major_lord, major_lord, current_start, major_end
                sub_periods.append({'major': major_lord, 'minor': major_lord, 'start': current_start, 'end': major_end})
            
            timeline.append({'lord': major_lord, 'start': current_start, 'end': major_end, 'subs': sub_periods})
            current_start = major_end

        # Fallback for future-dated horary charts
        if active_major is None and timeline:
            first_p = timeline[0]['subs'][0]
            active_major, active_minor, active_start, active_end = first_p['major'], first_p['minor'], first_p['start'], first_p['end']
            
        return {
            'is_day': is_day,
            'active': {'major': active_major, 'minor': active_minor, 'start': active_start, 'end': active_end},
            'timeline': timeline
        }
