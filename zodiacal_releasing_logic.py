"""
zodiacal_releasing_logic.py
古典占星希臘黃道釋放推運模組 (Hellenistic Zodiacal Releasing, ZR Engine)
文獻依據：Vettius Valens《Anthologies》Book IV、Chris Brennan《Hellenistic Astrology》
核心功能：
1. 計算希臘精神點 (Lot of Spirit) 與 幸運點 (Lot of Fortune)。
2. 計算以精神點（事業志業）或幸運點（健康體質）出發之 L1、L2 時間軸。
3. 判定相對幸運點之四角宮（1, 4, 7, 10 宮）巔峰期 (Peak Periods)，尤以第 10 宮為頂峰。
4. 支援換宮跳躍 (Losing of the Bond, LB) 標記。
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
import pandas as pd
from flatlib import const

class ZodiacalReleasingLogic:
    # 希臘行星年數 (Minor Years of the Planetary Rulers)
    SIGN_YEARS = {
        const.ARIES: 15,        # 牡羊 (Mars): 15年
        const.TAURUS: 8,        # 金牛 (Venus): 8年
        const.GEMINI: 20,       # 雙子 (Mercury): 20年
        const.CANCER: 25,       # 巨蟹 (Moon): 25年
        const.LEO: 19,          # 獅子 (Sun): 19年
        const.VIRGO: 20,        # 處女 (Mercury): 20年
        const.LIBRA: 8,         # 天秤 (Venus): 8年
        const.SCORPIO: 15,      # 天蠍 (Mars): 15年
        const.SAGITTARIUS: 12,  # 射手 (Jupiter): 12年
        const.CAPRICORN: 27,    # 摩羯 (Saturn): 27年
        const.AQUARIUS: 30,     # 水瓶 (Saturn): 30年
        const.PISCES: 12        # 雙魚 (Jupiter): 12年
    }

    TRADITIONAL_RULERS = {
        const.ARIES: 'Mars', const.TAURUS: 'Venus', const.GEMINI: 'Mercury',
        const.CANCER: 'Moon', const.LEO: 'Sun', const.VIRGO: 'Mercury',
        const.LIBRA: 'Venus', const.SCORPIO: 'Mars', const.SAGITTARIUS: 'Jupiter',
        const.CAPRICORN: 'Saturn', const.AQUARIUS: 'Saturn', const.PISCES: 'Jupiter'
    }

    DAYS_PER_YEAR = 365.2422

    def __init__(self, trans_signs=None, trans_planets=None):
        self.trans_signs = trans_signs or {
            const.ARIES: '牡羊座', const.TAURUS: '金牛座', const.GEMINI: '雙子座',
            const.CANCER: '巨蟹座', const.LEO: '獅子座', const.VIRGO: '處女座',
            const.LIBRA: '天秤座', const.SCORPIO: '天蠍座', const.SAGITTARIUS: '射手座',
            const.CAPRICORN: '摩羯座', const.AQUARIUS: '水瓶座', const.PISCES: '雙魚座'
        }
        self.trans_planets = trans_planets or {
            'Sun': '太陽', 'Moon': '月亮', 'Mercury': '水星', 'Venus': '金星',
            'Mars': '火星', 'Jupiter': '木星', 'Saturn': '土星'
        }

    def calculate_lots(self, chart, is_day: bool) -> Dict[str, Any]:
        """計算幸運點與精神點黃經與星座"""
        asc_lon = chart.get(const.ASC).lon
        sun_lon = chart.get(const.SUN).lon
        moon_lon = chart.get(const.MOON).lon

        if is_day:
            fortune_lon = (asc_lon + moon_lon - sun_lon) % 360
            spirit_lon = (asc_lon + sun_lon - moon_lon) % 360
        else:
            fortune_lon = (asc_lon + sun_lon - moon_lon) % 360
            spirit_lon = (asc_lon + moon_lon - sun_lon) % 360

        f_sign_idx = int(fortune_lon // 30)
        s_sign_idx = int(spirit_lon // 30)

        return {
            'fortune_lon': fortune_lon,
            'fortune_sign': const.LIST_SIGNS[f_sign_idx],
            'fortune_sign_idx': f_sign_idx,
            'spirit_lon': spirit_lon,
            'spirit_sign': const.LIST_SIGNS[s_sign_idx],
            'spirit_sign_idx': s_sign_idx
        }

    def calculate_zr(self, chart, is_day: bool, birth_dt_str: str, current_date: Optional[Any] = None) -> Dict[str, Any]:
        """
        完整計算希臘黃道釋放法 (Zodiacal Releasing)
        主推：精神點 (Lot of Spirit) 代表事業志業、名望與人生方向
        輔推：福德點 (Lot of Fortune) 代表身體健康、物質機遇
        """
        lots = self.calculate_lots(chart, is_day)
        fortune_idx = lots['fortune_sign_idx']
        spirit_sign = lots['spirit_sign']
        fortune_sign = lots['fortune_sign']

        spirit_res = self.calculate_releasing(
            birth_dt_str, spirit_sign, fortune_idx, target_date=current_date
        )
        fortune_res = self.calculate_releasing(
            birth_dt_str, fortune_sign, fortune_idx, target_date=current_date
        )

        return {
            'lots': {
                'fortune': {
                    'sign': self.trans_signs.get(fortune_sign, fortune_sign),
                    'lon': round(lots['fortune_lon'], 2)
                },
                'spirit': {
                    'sign': self.trans_signs.get(spirit_sign, spirit_sign),
                    'lon': round(lots['spirit_lon'], 2)
                }
            },
            'spirit': spirit_res,
            'fortune': fortune_res
        }

    def get_peak_signs_info(self, fortune_sign_idx: int) -> Dict[str, Any]:
        """
        以幸運點為基準，計算四正位（角宮）巔峰星座：
        1st (基石峰), 10th (最高頂峰), 7th (合作峰), 4th (根基峰)
        """
        peak_1 = fortune_sign_idx
        peak_10 = (fortune_sign_idx + 9) % 12
        peak_7 = (fortune_sign_idx + 6) % 12
        peak_4 = (fortune_sign_idx + 3) % 12

        mapping = {
            const.LIST_SIGNS[peak_10]: "Major Peak (頂峰之頂 - 聲望與成就最高點)",
            const.LIST_SIGNS[peak_1]: "Peak (基石之峰 - 新章與核心開端)",
            const.LIST_SIGNS[peak_7]: "Peak (對外/夥伴合作之峰)",
            const.LIST_SIGNS[peak_4]: "Peak (根基/整合收斂之峰)"
        }
        return mapping

    def calculate_releasing(
        self,
        birth_dt_str: str,
        start_sign_const: str,
        fortune_sign_idx: int,
        target_date: Optional[Any] = None,
        max_age: int = 100
    ) -> Dict[str, Any]:
        """
        核心釋放計算 (L1 與 L2)
        start_sign_const: 釋放起始星座（精神點或幸運點）
        """
        if target_date is None:
            target_date = date.today()
        if isinstance(target_date, datetime):
            target_date = target_date.date()
        target_ts = pd.Timestamp(target_date)

        clean_birth_str = birth_dt_str.replace('-', '/')
        birth_dt = pd.Timestamp(datetime.strptime(clean_birth_str, '%Y/%m/%d')).normalize()
        peak_map = self.get_peak_signs_info(fortune_sign_idx)

        start_sign_idx = const.LIST_SIGNS.index(start_sign_const)
        l1_periods = []
        cur_l1_start = birth_dt
        cur_sign_idx = start_sign_idx

        active_l1 = None
        active_l2 = None
        upcoming_peaks = []

        total_years_accum = 0
        while total_years_accum < max_age:
            sign_const = const.LIST_SIGNS[cur_sign_idx]
            years = self.SIGN_YEARS[sign_const]
            l1_duration_days = years * self.DAYS_PER_YEAR
            cur_l1_end = cur_l1_start + pd.Timedelta(days=l1_duration_days)

            ruler = self.TRADITIONAL_RULERS[sign_const]
            is_peak = sign_const in peak_map
            peak_type = peak_map.get(sign_const, "")

            # 計算當前 L1 內部的 L2 子篇章 (L2 單位為月，1 L1 年 = 1 L2 月)
            l2_periods = []
            cur_l2_start = cur_l1_start
            cur_l2_sign_idx = cur_sign_idx
            initial_l2_sign_idx = cur_sign_idx
            has_lb_occurred = False

            while cur_l2_start < cur_l1_end:
                l2_sign = const.LIST_SIGNS[cur_l2_sign_idx]
                l2_months = self.SIGN_YEARS[l2_sign]
                l2_duration_days = (l2_months / 12.0) * self.DAYS_PER_YEAR
                cur_l2_end = cur_l2_start + pd.Timedelta(days=l2_duration_days)

                if cur_l2_end > cur_l1_end:
                    cur_l2_end = cur_l1_end

                l2_ruler = self.TRADITIONAL_RULERS[l2_sign]
                l2_is_peak = l2_sign in peak_map
                l2_peak_type = peak_map.get(l2_sign, "")

                l2_info = {
                    'level': 2,
                    'sign': self.trans_signs.get(l2_sign, l2_sign),
                    'sign_const': l2_sign,
                    'ruler': self.trans_planets.get(l2_ruler, l2_ruler),
                    'start': cur_l2_start,
                    'end': cur_l2_end,
                    'is_peak': l2_is_peak,
                    'peak_type': l2_peak_type,
                    'is_lb': False
                }
                l2_periods.append(l2_info)

                if cur_l2_start <= target_ts < cur_l2_end:
                    active_l2 = l2_info

                if l2_is_peak and cur_l2_end > target_ts and len(upcoming_peaks) < 5:
                    upcoming_peaks.append({
                        'level': 'L2',
                        'sign': self.trans_signs.get(l2_sign, l2_sign),
                        'peak_type': l2_peak_type,
                        'start': cur_l2_start.strftime('%Y/%m/%d'),
                        'end': cur_l2_end.strftime('%Y/%m/%d')
                    })

                cur_l2_start = cur_l2_end

                # 準備下一個 L2 星座
                next_l2_idx = (cur_l2_sign_idx + 1) % 12
                # Losing of the Bond (LB 換宮跳躍)：當在同一 L1 中循環回到 L1 原起始星座時跳到對宮 (+6)
                if not has_lb_occurred and next_l2_idx == initial_l2_sign_idx and cur_l2_start < cur_l1_end:
                    next_l2_idx = (next_l2_idx + 6) % 12
                    has_lb_occurred = True
                    if l2_periods:
                        l2_periods[-1]['is_lb'] = True

                cur_l2_sign_idx = next_l2_idx

            l1_info = {
                'level': 1,
                'sign': self.trans_signs.get(sign_const, sign_const),
                'sign_name': self.trans_signs.get(sign_const, sign_const),
                'sign_const': sign_const,
                'ruler': self.trans_planets.get(ruler, ruler),
                'ruler_name': self.trans_planets.get(ruler, ruler),
                'years': years,
                'start': cur_l1_start,
                'start_date': cur_l1_start.strftime('%Y/%m/%d'),
                'end': cur_l1_end,
                'end_date': cur_l1_end.strftime('%Y/%m/%d'),
                'is_peak': is_peak,
                'peak_type': peak_type,
            }
            l1_periods.append(l1_info)

            if cur_l1_start <= target_ts < cur_l1_end:
                active_l1 = l1_info

            total_years_accum += years
            cur_l1_start = cur_l1_end
            cur_sign_idx = (cur_sign_idx + 1) % 12

        return {
            'start_sign': self.trans_signs.get(start_sign_const, start_sign_const),
            'target_date': str(target_date),
            'active_l1': {
                'sign': active_l1['sign'] if active_l1 else "",
                'sign_name': active_l1['sign'] if active_l1 else "",
                'ruler': active_l1['ruler'] if active_l1 else "",
                'ruler_name': active_l1['ruler'] if active_l1 else "",
                'start': active_l1['start'].strftime('%Y/%m/%d') if active_l1 else "",
                'start_date': active_l1['start'].strftime('%Y/%m/%d') if active_l1 else "",
                'end': active_l1['end'].strftime('%Y/%m/%d') if active_l1 else "",
                'end_date': active_l1['end'].strftime('%Y/%m/%d') if active_l1 else "",
                'is_peak': active_l1['is_peak'] if active_l1 else False,
                'peak_type': active_l1['peak_type'] if active_l1 else ""
            },
            'active_l2': {
                'sign': active_l2['sign'] if active_l2 else "",
                'sign_name': active_l2['sign'] if active_l2 else "",
                'ruler': active_l2['ruler'] if active_l2 else "",
                'ruler_name': active_l2['ruler'] if active_l2 else "",
                'start': active_l2['start'].strftime('%Y/%m/%d') if active_l2 else "",
                'start_date': active_l2['start'].strftime('%Y/%m/%d') if active_l2 else "",
                'end': active_l2['end'].strftime('%Y/%m/%d') if active_l2 else "",
                'end_date': active_l2['end'].strftime('%Y/%m/%d') if active_l2 else "",
                'is_peak': active_l2['is_peak'] if active_l2 else False,
                'peak_type': active_l2['peak_type'] if active_l2 else "",
                'is_lb': active_l2['is_lb'] if active_l2 else False
            },
            'peak_signs': [
                f"{self.trans_signs.get(s, s)} ({desc})"
                for s, desc in peak_map.items()
            ],
            'upcoming_peaks': upcoming_peaks,
            'l1_periods': l1_periods
        }
