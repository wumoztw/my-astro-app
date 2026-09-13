#!/usr/bin/env python3
"""
financial_astrology_logic.py
西洋金融占星與比特幣歷史週期統計共振引擎 (Financial Astrology & Bitcoin Cycle Correlation Engine)

理論與文獻依據：
1. 比特幣創世盤 (Bitcoin Genesis Chart)：
   - 2009 年 1 月 3 日 18:15:05 UTC (Satoshi mined Genesis Block #0, Chancellor on brink of second bailout).
   - 英國倫敦坐標 (51.5074, -0.1278)，整宮制 (Whole Sign House System)。
2. 比特幣歷史四年減半與宏觀牛熊量化數據庫 (2009 - 2026)。
3. 古典推運多維時限系統：
   - 年度小限 (Annual Profections) 輪值財富宮位 (2, 5, 8, 11 宮) 與年度主星 (Lord of the Year)。
   - 法達星限 (Firdaria) 大運與小運星體之落宮與守護財星。
   - 希臘黃道釋放法 (Zodiacal Releasing) 從福德點 (Lot of Fortune) 與精神點 (Lot of Spirit) 計算人生重大財富高峰 (Major Peaks)。
   - 外行星過運 (Outer Planet Transits - 木星擴張、土星考驗、天王星突發突破、冥王星重構)。
   - 命主與比特幣創世盤交叉合盤 (Synastry Resonance)。
4. 統計相關性打分與實證推論演算法 (Empirical Correlation Index)。
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
import math
import pandas as pd
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const

from time_lords_logic import TimeLordsLogic
from zodiacal_releasing_logic import ZodiacalReleasingLogic
from dignities_logic import DignitiesLogic
from aspects_logic import AspectsLogic
from lots_logic import LotsLogic


class FinancialAstrologyLogic:
    """
    金融占星量化引擎：
    負責比特幣創世天宮圖演算、宏觀牛熊週期歷史回測、個人推運多維時間切片對齊、
    以及同頻共振指數 (Resonance Index) 之量化統計打分。
    """

    # 比特幣創世盤常數 (Genesis Block #0)
    BTC_GENESIS_DT_STR = "2009/01/03"
    BTC_GENESIS_TIME_STR = "18:15:05"
    BTC_GENESIS_TZ_STR = "+00:00"
    BTC_GENESIS_LAT = 51.5074
    BTC_GENESIS_LON = -0.1278

    # 比特幣歷史四大宏觀牛熊週期量化數據表
    BTC_HISTORICAL_CYCLES = [
        {
            "id": "cycle_1",
            "name": "第一週期：初代拓荒與百倍奇蹟 (2011 - 2013)",
            "era": "2011 ~ 2015",
            "halving_date": "2012/11/28",
            "halving_price": 12.2,
            "peak_date": "2013/11/30",
            "peak_price": 1150.0,
            "trough_date": "2015/01/14",
            "trough_price": 152.0,
            "drawdown": "-86.8%",
            "multiplier": "約 94 倍",
            "macro_theme": "賽普勒斯金融危機爆發，密碼龐克去中心化貨幣首度走入大眾視野，突破千美元天花板。"
        },
        {
            "id": "cycle_2",
            "name": "第二週期：ICO狂潮與兩萬美元大頂 (2015 - 2017)",
            "era": "2015 ~ 2018",
            "halving_date": "2016/07/09",
            "halving_price": 650.0,
            "peak_date": "2017/12/17",
            "peak_price": 19783.0,
            "trough_date": "2018/12/15",
            "trough_price": 3120.0,
            "drawdown": "-84.2%",
            "multiplier": "約 30 倍",
            "macro_theme": "以太坊崛起與智能合約革命，全球散戶與加密基金大舉湧入，形成 19,783 美元狂潮與漫長寒冬。"
        },
        {
            "id": "cycle_3",
            "name": "第三週期：全球放水、機構進場與雙頂 (2019 - 2021)",
            "era": "2019 ~ 2022",
            "halving_date": "2020/05/11",
            "halving_price": 8600.0,
            "peak_date": "2021/11/10",
            "peak_price": 69000.0,
            "trough_date": "2022/11/21",
            "trough_price": 15500.0,
            "drawdown": "-77.5%",
            "multiplier": "約 8 倍",
            "macro_theme": "疫情全球無限 QE 放水，微策略、特斯拉機構大建倉，迎來 69,000 美元天頂，後續遭逢 Luna 與 FTX 清算暴雷。"
        },
        {
            "id": "cycle_4",
            "name": "第四週期：現貨ETF制度化與減半擴張 (2023 - 2026)",
            "era": "2023 ~ 2026",
            "halving_date": "2024/04/20",
            "halving_price": 64000.0,
            "peak_date": "2024/03/14",
            "peak_price": 73750.0,
            "trough_date": "2023/01/01",
            "trough_price": 16500.0,
            "drawdown": "宏觀進行中",
            "multiplier": "擴張進行中",
            "macro_theme": "美國華爾街正式發行比特幣現貨 ETF，傳統資本長驅直入，木天合相金牛座推動數位黃金制度化。"
        }
    ]

    TRADITIONAL_RULERS = {
        const.ARIES: const.MARS, const.TAURUS: const.VENUS, const.GEMINI: const.MERCURY,
        const.CANCER: const.MOON, const.LEO: const.SUN, const.VIRGO: const.MERCURY,
        const.LIBRA: const.VENUS, const.SCORPIO: const.MARS, const.SAGITTARIUS: const.JUPITER,
        const.CAPRICORN: const.SATURN, const.AQUARIUS: const.SATURN, const.PISCES: const.JUPITER
    }

    def __init__(self, trans_signs=None, trans_planets=None):
        self.time_lords = TimeLordsLogic()
        self.zr = ZodiacalReleasingLogic(trans_signs, trans_planets)
        self.dignities = DignitiesLogic()
        self.aspects = AspectsLogic()
        self.lots = LotsLogic()

        self.trans_signs = trans_signs or {
            const.ARIES: '牡羊座', const.TAURUS: '金牛座', const.GEMINI: '雙子座',
            const.CANCER: '巨蟹座', const.LEO: '獅子座', const.VIRGO: '處女座',
            const.LIBRA: '天秤座', const.SCORPIO: '天蠍座', const.SAGITTARIUS: '射手座',
            const.CAPRICORN: '摩羯座', const.AQUARIUS: '水瓶座', const.PISCES: '雙魚座'
        }
        self.trans_planets = trans_planets or {
            const.SUN: '太陽', const.MOON: '月亮', const.MERCURY: '水星',
            const.VENUS: '金星', const.MARS: '火星', const.JUPITER: '木星',
            const.SATURN: '土星', 'Uranus': '天王星', 'Neptune': '海王星', 'Pluto': '冥王星'
        }
        self.rev_planets = {v: k for k, v in self.trans_planets.items()}

    # -------------------------------------------------------------
    # 1. 比特幣創世盤演算 (Bitcoin Genesis Chart)
    # -------------------------------------------------------------
    def get_bitcoin_genesis_chart(self) -> Dict[str, Any]:
        """
        計算並回傳比特幣創世盤之主要星體坐標、整宮制宮位及核心特質。
        """
        dt = Datetime(self.BTC_GENESIS_DT_STR, self.BTC_GENESIS_TIME_STR, self.BTC_GENESIS_TZ_STR)
        pos = GeoPos(self.BTC_GENESIS_LAT, self.BTC_GENESIS_LON)
        chart = Chart(dt, pos, hsys=const.HOUSES_WHOLE_SIGN)

        planets_data = []
        for p_id in [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN]:
            try:
                p = chart.get(p_id)
                deg_in_sign = p.lon % 30
                d = int(deg_in_sign)
                m = int((deg_in_sign - d) * 60)
                planets_data.append({
                    "id": p_id,
                    "name": self.trans_planets.get(p_id, p_id),
                    "sign": self.trans_signs.get(p.sign, p.sign),
                    "sign_id": p.sign,
                    "lon": p.lon,
                    "degree_str": f"{d}°{m:02d}'",
                    "retro": p.lonspeed < 0
                })
            except Exception:
                pass

        return {
            "title": "比特幣創世天宮圖 (Bitcoin Genesis Chart)",
            "genesis_time_utc": f"{self.BTC_GENESIS_DT_STR} {self.BTC_GENESIS_TIME_STR} UTC",
            "genesis_block": 0,
            "headline": "Chancellor on brink of second bailout for banks",
            "chart_obj": chart,
            "planets": planets_data,
            "core_signatures": [
                {"name": "摩羯太陽 (13°)", "meaning": "反法幣通貨膨脹、追求數學代碼極致嚴謹度與硬通貨儲備地位。"},
                {"name": "處女逆行土星 (21°)", "meaning": "精密嚴苛的工作量證明 (Proof of Work) 與 2100 萬顆硬頂限制。"},
                {"name": "水瓶木星 (29°)", "meaning": "去中心化全球對等網絡、科技烏托邦與劃時代的金融平權變革。"},
                {"name": "摩羯冥王星 (2°)", "meaning": "舊式中心化銀行體系的信任崩解，以及全球主權財富的深層重組。"}
            ]
        }

    # -------------------------------------------------------------
    # 2. 個人命盤財星與財富宮位解構 (Native Wealth Archetype)
    # -------------------------------------------------------------
    def extract_native_wealth_profile(self, chart, houses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        從本命盤中提取正財 (2宮)、偏財投機 (8宮)、博弈風險 (5宮)、事業大發 (11宮) 及金木雙吉星之體系。
        """
        h_map = {h.get("id"): h for h in houses if isinstance(h, dict)}
        
        def get_house_ruler_info(h_num: int):
            h_info = h_map.get(h_num, {})
            sign = h_info.get("sign", "")
            ruler_name = h_info.get("ruler", "")
            ruler_id = h_info.get("ruler_id") or self.rev_planets.get(ruler_name, ruler_name)
            
            p_obj = None
            try:
                p_obj = chart.get(ruler_id)
            except Exception:
                pass
            
            return {
                "house_num": h_num,
                "sign": sign,
                "ruler_name": ruler_name,
                "ruler_id": ruler_id,
                "ruler_planet": p_obj,
                "ruler_lon": p_obj.lon if p_obj else 0.0,
                "ruler_retro": (p_obj.lonspeed < 0) if p_obj else False
            }

        lord_1 = get_house_ruler_info(1)   # 命宮 (Native)
        lord_2 = get_house_ruler_info(2)   # 正財 (Earned Liquid Assets)
        lord_5 = get_house_ruler_info(5)   # 投機博弈 (Speculation)
        lord_8 = get_house_ruler_info(8)   # 偏財/金融衍生/加密資產 (Shared & High-Risk Assets)
        lord_10 = get_house_ruler_info(10) # 事業名望 (Career/Status)
        lord_11 = get_house_ruler_info(11) # 事業巨額紅利/願望 (Gains & Windfall)

        venus_obj = chart.get(const.VENUS)
        jupiter_obj = chart.get(const.JUPITER)

        return {
            "lord_1": lord_1,
            "lord_2": lord_2,
            "lord_5": lord_5,
            "lord_8": lord_8,
            "lord_10": lord_10,
            "lord_11": lord_11,
            "venus": {
                "name": "金星 (小吉財星)",
                "sign": self.trans_signs.get(venus_obj.sign, venus_obj.sign),
                "lon": venus_obj.lon,
                "retro": venus_obj.lonspeed < 0
            },
            "jupiter": {
                "name": "木星 (大吉財星)",
                "sign": self.trans_signs.get(jupiter_obj.sign, jupiter_obj.sign),
                "lon": jupiter_obj.lon,
                "retro": jupiter_obj.lonspeed < 0
            }
        }

    # -------------------------------------------------------------
    # 3. 歷史週期個人推運切片計算 (Historical Timeline Slicing)
    # -------------------------------------------------------------
    def calculate_cycle_slice(
        self,
        chart,
        houses: List[Dict[str, Any]],
        birth_dt_str: str,
        is_day: bool,
        target_date_str: str
    ) -> Dict[str, Any]:
        """
        給定歷史特定日期 (如 2013/11/30 或 2017/12/17)，精算命主當下之：
        - 小限法 (Profection)：年齡、小限宮位、年度主星。
        - 法達星限 (Firdaria)：當前大限主星、小運副星。
        - 希臘黃道釋放 (ZR)：福德點釋放是否處於 Peak 高峰期。
        - 外行星過運 (Transits)：木星、土星、天王星當時黃經及對本命星體的相位。
        """
        target_dt = datetime.strptime(target_date_str, "%Y/%m/%d").date()
        clean_birth_dt = str(birth_dt_str).strip().split()[0].replace("-", "/")

        # 1. 小限計算
        prof = self.time_lords.calculate_profections(
            chart, self.trans_signs, {}, self.trans_planets, clean_birth_dt, target_dt
        )
        prof_house = prof.get("prof_house_num", 1)
        lord_of_year = prof.get("lord_of_year", "").strip()

        # 2. 法達星限計算
        firdaria_res = self.time_lords.get_firdaria_data(clean_birth_dt, is_day, target_dt)
        act = firdaria_res.get("active", {})
        major_lord = act.get("major", "")
        minor_lord = act.get("minor", "")
        major_lord_name = self.trans_planets.get(major_lord, major_lord)
        minor_lord_name = self.trans_planets.get(minor_lord, minor_lord)

        # 3. 黃道釋放法 (福德點 Lot of Fortune 財富釋放)
        zr_active_l1 = "未知"
        zr_active_l2 = "未知"
        is_zr_peak = False

        try:
            zr_all = self.zr.calculate_zr(chart, is_day, clean_birth_dt, current_date=target_dt)
            fortune_data = zr_all.get("fortune", {})
            act_l1 = fortune_data.get("active_l1", {})
            act_l2 = fortune_data.get("active_l2", {})
            if act_l1:
                zr_active_l1 = f"{act_l1.get('sign', '')} ({act_l1.get('ruler', '')})"
                if act_l1.get("is_peak"):
                    is_zr_peak = True
            if act_l2:
                zr_active_l2 = f"{act_l2.get('sign', '')} ({act_l2.get('ruler', '')})"
                if act_l2.get("is_peak"):
                    is_zr_peak = True
        except Exception:
            pass

        # 4. 外行星過運
        t_chart = None
        try:
            t_dt = Datetime(target_date_str, "12:00", "+00:00")
            t_pos = GeoPos(self.BTC_GENESIS_LAT, self.BTC_GENESIS_LON)
            t_chart = Chart(t_dt, t_pos, hsys=const.HOUSES_WHOLE_SIGN)
        except Exception:
            pass

        t_jupiter_sign = ""
        t_saturn_sign = ""
        transit_highlights = []

        if t_chart:
            try:
                tj = t_chart.get(const.JUPITER)
                ts = t_chart.get(const.SATURN)
                t_jupiter_sign = self.trans_signs.get(tj.sign, tj.sign)
                t_saturn_sign = self.trans_signs.get(ts.sign, ts.sign)

                h_map = {h.get("id"): h for h in houses if isinstance(h, dict)}
                h2_sign = h_map.get(2, {}).get("sign", "")
                h8_sign = h_map.get(8, {}).get("sign", "")
                h11_sign = h_map.get(11, {}).get("sign", "")

                if t_jupiter_sign == h2_sign:
                    transit_highlights.append("過運木星進駐本命第 2 宮 (正財庫大幅擴張)")
                elif t_jupiter_sign == h8_sign:
                    transit_highlights.append("過運木星進駐本命第 8 宮 (偏財/投資投機巨浪機遇)")
                elif t_jupiter_sign == h11_sign:
                    transit_highlights.append("過運木星進駐本命第 11 宮 (大發利市/宏觀紅利湧現)")

                if t_saturn_sign == h2_sign:
                    transit_highlights.append("過運土星壓境本命第 2 宮 (現金流受壓制與收縮考驗)")
                elif t_saturn_sign == h8_sign:
                    transit_highlights.append("過運土星進駐本命第 8 宮 (偏財考驗/嚴防槓桿爆倉)")

            except Exception:
                pass

        return {
            "date": target_date_str,
            "age": prof.get("age", 0),
            "profection_house": prof_house,
            "lord_of_year": lord_of_year,
            "firdaria_major": major_lord_name,
            "firdaria_minor": minor_lord_name,
            "zr_fortune_l1": zr_active_l1,
            "zr_fortune_l2": zr_active_l2,
            "is_zr_peak": is_zr_peak,
            "t_jupiter_sign": t_jupiter_sign,
            "t_saturn_sign": t_saturn_sign,
            "transit_highlights": transit_highlights
        }

    # -------------------------------------------------------------
    # 4. 統計相關性與共振演算法 (Statistical Correlation & Inference)
    # -------------------------------------------------------------
    def analyze_bitcoin_resonance(
        self,
        chart,
        houses: List[Dict[str, Any]],
        birth_dt_str: str,
        is_day: bool
    ) -> Dict[str, Any]:
        """
        全面比對命主歷史推運與比特幣四大牛熊週期，產出統計共振評分與白話推論報告。
        """
        wealth_profile = self.extract_native_wealth_profile(chart, houses)
        btc_genesis = self.get_bitcoin_genesis_chart()
        btc_chart = btc_genesis["chart_obj"]

        # 命主與比特幣創世盤交叉合盤吉星比對 (Genesis Synastry Affinity)
        genesis_affinity_points = 0
        affinity_aspects = []

        try:
            btc_sun = btc_chart.get(const.SUN)
            btc_jup = btc_chart.get(const.JUPITER)
            btc_sat = btc_chart.get(const.SATURN)

            for p_id in [const.SUN, const.MOON, const.VENUS, const.JUPITER, const.MERCURY]:
                p = chart.get(p_id)
                for b_p, b_label in [(btc_sun, "比特幣太陽"), (btc_jup, "比特幣木星"), (btc_sat, "比特幣土星")]:
                    diff = abs(p.lon - b_p.lon)
                    if diff > 180: diff = 360 - diff
                    for target_deg, asp_name, pts in [(0, "合相", 20), (120, "三分吉相", 15), (60, "六分吉相", 10)]:
                        if abs(diff - target_deg) <= 6.0:
                            genesis_affinity_points += pts
                            affinity_aspects.append(
                                f"本命{self.trans_planets.get(p_id, p_id)} 與 {b_label} 呈 {asp_name} (誤差 {round(abs(diff - target_deg), 1)}°)"
                            )
        except Exception:
            pass

        genesis_affinity_score = min(100, max(20, genesis_affinity_points))

        cycle_comparisons = []
        bull_scores = []
        bear_scores = []

        for cyc in self.BTC_HISTORICAL_CYCLES:
            peak_slice = self.calculate_cycle_slice(chart, houses, birth_dt_str, is_day, cyc["peak_date"])
            trough_slice = self.calculate_cycle_slice(chart, houses, birth_dt_str, is_day, cyc["trough_date"])

            b_score = 40
            if peak_slice["profection_house"] in (2, 8, 11):
                b_score += 25
            elif peak_slice["profection_house"] in (5, 10):
                b_score += 15
            
            if peak_slice["is_zr_peak"]:
                b_score += 15

            if any(k in peak_slice["firdaria_major"] for k in ("木星", "金星", "太陽")):
                b_score += 15

            if peak_slice["transit_highlights"]:
                b_score += 10

            b_score = min(100, b_score)
            bull_scores.append(b_score)

            t_score = 30
            if trough_slice["profection_house"] in (6, 8, 12):
                t_score += 30
            if any(k in trough_slice["firdaria_major"] for k in ("土星", "火星")):
                t_score += 20
            bear_scores.append(t_score)

            cycle_comparisons.append({
                "cycle_id": cyc["id"],
                "cycle_name": cyc["name"],
                "era": cyc["era"],
                "macro_summary": f"減半日 {cyc['halving_date']} (約 ${cyc['halving_price']:,.0f}) ➔ 大頂 {cyc['peak_date']} (${cyc['peak_price']:,.0f}) ➔ 寒冬底 {cyc['trough_date']} (${cyc['trough_price']:,.0f}，{cyc['drawdown']})",
                "bull_resonance_score": b_score,
                "peak_user_age": f"{peak_slice['age']} 歲",
                "peak_profection": f"第 {peak_slice['profection_house']} 宮 (年主星: {peak_slice['lord_of_year']})",
                "peak_firdaria": f"{peak_slice['firdaria_major']}運 ➔ {peak_slice['firdaria_minor']}小運",
                "peak_zr_fortune": f"{peak_slice['zr_fortune_l1']} (高峰: {'✅ 是' if peak_slice['is_zr_peak'] else '無'})",
                "peak_transits": "、".join(peak_slice["transit_highlights"]) if peak_slice["transit_highlights"] else "天象平穩推進",
                "trough_user_age": f"{trough_slice['age']} 歲",
                "trough_profection": f"第 {trough_slice['profection_house']} 宮",
                "trough_firdaria": f"{trough_slice['firdaria_major']}運"
            })

        avg_bull_resonance = int(sum(bull_scores) / len(bull_scores))
        overall_correlation_index = int(avg_bull_resonance * 0.6 + genesis_affinity_score * 0.4)

        if overall_correlation_index >= 80:
            resonance_type = "🌟 傳奇共振型 (Legendary Harmonic)"
            resonance_badge = "超高頻度完全呼應"
            verdict_desc = "命主的推運時限（法達大限、小限財富宮位與黃道釋放高峰）與比特幣歷史四年減半週期存在不可思議的高度重合！每逢比特幣宏觀主升浪頂峰，命主盤體皆同步被強烈吉星引動，具備接住加密超級紅利的先天時空氣運。"
        elif overall_correlation_index >= 65:
            resonance_type = "🚀 強度同頻型 (Highly Synchronized)"
            resonance_badge = "高度同頻共振"
            verdict_desc = "命主的財富推運走勢與比特幣宏觀週期具有顯著的正向呼應。特別是在歷史大型牛市的起漲與主升波段中，命主的正偏財宮位（2/8/11宮）頻繁出現關鍵呼應，是極具宏觀週期敏感度的體質。"
        elif overall_correlation_index >= 50:
            resonance_type = "⚖️ 選擇性共振型 (Selective Resonance)"
            resonance_badge = "階段性共振"
            verdict_desc = "命主與比特幣週期並非每一輪都完全齊步，而是呈現『特定大運波段深度共振、其餘時期平穩獨立』的節奏。需把握命主個人大運走入木星/金星或 2/8 宮年的疊合窗口。"
        else:
            resonance_type = "🛡️ 獨立自主型 (Decoupled & Independent)"
            resonance_badge = "獨立運作賽道"
            verdict_desc = "命主的個人財富成長曲線有其完全獨立的人生節奏，較不受外部加密貨幣四年週期的劇烈暴漲暴跌所制約，適合按部就班耕耘自身專業資產賽道。"

        current_and_future_slices = []
        for f_year in [2024, 2025, 2026, 2027, 2028]:
            f_slice = self.calculate_cycle_slice(chart, houses, birth_dt_str, is_day, f"{f_year}/10/01")
            is_gold_window = f_slice["profection_house"] in (2, 5, 8, 10, 11) or f_slice["is_zr_peak"]
            current_and_future_slices.append({
                "year": f_year,
                "age": f"{f_slice['age']} 歲",
                "profection": f"第 {f_slice['profection_house']} 宮 ({f_slice['lord_of_year']})",
                "firdaria": f"{f_slice['firdaria_major']} - {f_slice['firdaria_minor']}",
                "is_gold_window": is_gold_window,
                "strategy": "🎯 財富豐收/衝刺高點" if is_gold_window else "🛡️ 資本保全/防禦收斂"
            })

        return {
            "overall_correlation_index": overall_correlation_index,
            "resonance_type": resonance_type,
            "resonance_badge": resonance_badge,
            "verdict_desc": verdict_desc,
            "genesis_affinity_score": genesis_affinity_score,
            "genesis_affinity_aspects": affinity_aspects,
            "wealth_profile": wealth_profile,
            "cycle_comparisons": cycle_comparisons,
            "future_slices": current_and_future_slices,
            "btc_genesis_info": btc_genesis
        }
