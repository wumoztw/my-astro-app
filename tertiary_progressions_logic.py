#!/usr/bin/env python3
"""
Tertiary Progressions Engine (三限推運法 - 一日一月)
依據正統西方預測占星學理與天體力學：
1. 實歲年齡經過之總天數 D，以熱帶月 (Tropical Month, 27.321582 日) 推進：
   三限推進星曆天數 = D / 27.321582 (A Day for a Month)。
2. 計算三限月亮 (Tertiary Moon)：
   三限月亮在現實中約 2.27 個月 (約 68 天) 走過一個星座/宮位，
   專門用來捕捉「具體月份」的心境轉折、焦點生活場景與當月情緒波動。
3. 計算三限 2.5 年月相週期 (Tertiary Lunar Phase, 約 29.53 個月循環一次)。
4. 篩選三限星體對本命星體的當月活躍緊密相位 (影響約 2~4 週)。
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
import pandas as pd
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

class TertiaryProgressionsLogic:
    """三限推運法 (一日一月) 獨立核心演算法"""

    TROPICAL_MONTH_DAYS = 27.321582  # 恆星/熱帶月平均日數

    CORE_PLANETS = [
        const.SUN, const.MOON, const.MERCURY, const.VENUS,
        const.MARS, const.JUPITER, const.SATURN,
        const.URANUS, const.NEPTUNE, const.PLUTO
    ]

    LUNAR_PHASES = [
        {"name": "三限新月", "min_angle": 0.0, "max_angle": 45.0, "stage": "月度播種期",
         "desc": "開啟 2.5 年內在微週期之新起點，萌生新想法，適合規劃未來數月方向。"},
        {"name": "三限蛾眉月", "min_angle": 45.0, "max_angle": 90.0, "stage": "萌芽試探期",
         "desc": "新計畫開始落實於日常生活中，需要克服起步時的小阻力與慣性。"},
        {"name": "三限上弦月", "min_angle": 90.0, "max_angle": 135.0, "stage": "行動突破期",
         "desc": "面對具體現實事件考驗，需要果斷決策，確立行動方案與時間表。"},
        {"name": "三限盈凸月", "min_angle": 135.0, "max_angle": 180.0, "stage": "精進校準期",
         "desc": "細部調整與資源整合期，蓄勢待發，準備迎接接下來數週的高峰收成。"},
        {"name": "三限滿月", "min_angle": 180.0, "max_angle": 225.0, "stage": "成果巔峰期",
         "desc": "2.5 年微週期最高潮，事情結果明朗化、情緒強烈顯化或重要人際確立。"},
        {"name": "三限散播月", "min_angle": 225.0, "max_angle": 270.0, "stage": "分享回饋期",
         "desc": "享受事情告一段落的成果，適合交流傳遞經驗、整合資源。"},
        {"name": "三限下弦月", "min_angle": 270.0, "max_angle": 315.0, "stage": "反思重整期",
         "desc": "對過去數月行事進行反省檢討，去除不必要的事務與人際負擔。"},
        {"name": "三限香脂月", "min_angle": 315.0, "max_angle": 360.0, "stage": "休整沉澱期",
         "desc": "微週期尾聲，適合休養生息、身心放鬆，等待下一次新月帶來新動能。"}
    ]

    HOUSE_THEMES = {
        1: "自我形象重塑、個人主動出擊、身體活力與展現自我的 2 個月",
        2: "正財收入、財務收支調度、物質資源評估與消費理財之月",
        3: "密集學習、溝通出差、短途拜訪、合約簽署與資訊交流之月",
        4: "家庭事務、住所環境改善、不動產關注與內在安全感沉澱之月",
        5: "創意靈感爆發、投資理財投機、戀愛桃花熱烈或娛樂休閒之月",
        6: "職場專注工作、細部技能磨練、健康飲食生活作息調理之月",
        7: "重要合約談判、伴侶相處互動、一對一商業合夥與關鍵人際對話之月",
        8: "偏財借貸、保險稅務、共有資產整合與深層心理蛻變之月",
        9: "長途遠行出國、高等進修學習、法律諮詢或人生哲學開拓之月",
        10: "事業舞台高光、主管客戶青睞、職涯晉升或社會形象受矚目之月",
        11: "朋友圈社交熱絡、團隊組織合作、擴大貴人人脈資源之月",
        12: "心靈療癒休養、幕後策劃構思、避免過勞與釋放情緒包袱之月"
    }

    def __init__(self, trans_signs: Dict[str, str], trans_planets: Dict[str, str]):
        self.trans_signs = trans_signs
        self.trans_planets = trans_planets

    def _degree_to_dms_str(self, deg: float) -> str:
        sign_deg = deg % 30
        d = int(sign_deg)
        m = int((sign_deg - d) * 60)
        return f"{d}°{m:02d}'"

    def calculate_progressed_time(
        self,
        birth_dt_str: str,
        birth_time_str: str,
        target_date: Optional[Any] = None
    ) -> tuple:
        """
        三限法一日一月法則：計算實歲經歷天數與三限星曆推進時間點。
        """
        if target_date is None:
            target_date = date.today()
        elif isinstance(target_date, datetime):
            target_date = target_date.date()
        elif isinstance(target_date, str):
            clean_td = target_date.strip().replace('/', '-')
            if len(clean_td) == 4 and clean_td.isdigit():
                target_date = datetime.strptime(f"{clean_td}-06-15", "%Y-%m-%d").date()
            else:
                target_date = datetime.strptime(clean_td[:10], "%Y-%m-%d").date()

        clean_birth_str = birth_dt_str.replace('-', '/')
        birth_d = datetime.strptime(clean_birth_str, '%Y/%m/%d').date()
        age_days = max(0, (target_date - birth_d).days)
        age_years = age_days / 365.2422

        # 三限推進星曆天數 = 總經歷天數 / 27.321582
        tertiary_prog_days = age_days / self.TROPICAL_MONTH_DAYS

        birth_dt = datetime.strptime(f"{clean_birth_str} {birth_time_str}", "%Y/%m/%d %H:%M")
        prog_dt = birth_dt + pd.Timedelta(days=tertiary_prog_days)
        return age_years, tertiary_prog_days, prog_dt, target_date

    def calculate_tertiary_chart(
        self,
        birth_dt_str: str,
        birth_time_str: str,
        utc_offset_str: str,
        lat: float,
        lon: float,
        target_date: Optional[Any] = None
    ) -> tuple:
        """建立三限盤 (Chart)"""
        age_years, tert_days, prog_dt, eval_target_date = self.calculate_progressed_time(
            birth_dt_str, birth_time_str, target_date
        )
        prog_date_str = prog_dt.strftime("%Y/%m/%d")
        prog_time_str = prog_dt.strftime("%H:%M")

        dt_prog = Datetime(prog_date_str, prog_time_str, utc_offset_str)
        pos = GeoPos(lat, lon)
        chart_prog = Chart(dt_prog, pos, hsys=const.HOUSES_WHOLE_SIGN)
        return chart_prog, age_years, tert_days, prog_dt, eval_target_date

    def calculate_tertiary_moon(
        self,
        chart_prog: Chart,
        houses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        計算三限月亮核心數據：星座、度數、落入本命宮位、換宮倒數與當月生活主題。
        """
        moon = chart_prog.get(const.MOON)
        moon_lon = moon.lon
        sign_idx = int(moon_lon // 30)
        sign_const = const.LIST_SIGNS[sign_idx]
        sign_name = self.trans_signs.get(sign_const, sign_const)
        deg_in_sign = moon_lon % 30
        deg_str = self._degree_to_dms_str(moon_lon)

        # 判定落入本命哪一宮 (以古典整宮制 houses[0]['lon'] 為基準)
        h1_lon = houses[0]['lon'] if houses else 0.0
        house_num = int(((moon_lon - h1_lon) % 360) // 30) + 1
        house_str = f"第 {house_num} 宮"

        # 換座/換宮倒數估算：
        # 三限月亮在現實人生中平均每 68.3 天 (約 2.27 個月) 走一個星座 (30°)
        # 換算現實天速度：約 30° / 68.3 天 ≈ 0.439° / 天 (約每週走 3.07°)
        degrees_left = 30.0 - deg_in_sign
        days_left = round(degrees_left / 0.439, 1)
        weeks_left = round(days_left / 7.0, 1)

        theme = self.HOUSE_THEMES.get(house_num, "當月關鍵生活場景與情緒焦點")

        return {
            "sign": sign_name,
            "sign_const": sign_const,
            "degree_str": deg_str,
            "longitude": round(moon_lon, 2),
            "degree_in_sign": round(deg_in_sign, 2),
            "house_num": house_num,
            "house_str": house_str,
            "days_left_in_sign": days_left,
            "weeks_left_in_sign": weeks_left,
            "theme": theme,
            "summary": f"三限月亮現位於【{sign_name} {deg_str}】，落入本命【{house_str}】。預計約 {weeks_left} 週（{days_left} 天）後換宮。當前月度核心重心：{theme}。"
        }

    def calculate_tertiary_lunar_phase(self, chart_prog: Chart) -> Dict[str, Any]:
        """
        計算三限 2.5 年月相八大週期 (Tertiary Lunar Phase)
        """
        sun_lon = chart_prog.get(const.SUN).lon
        moon_lon = chart_prog.get(const.MOON).lon
        angle = (moon_lon - sun_lon) % 360

        current_phase = self.LUNAR_PHASES[0]
        for p in self.LUNAR_PHASES:
            if p["min_angle"] <= angle < p["max_angle"]:
                current_phase = p
                break

        # 三限月相週期為 29.53 個月 (約 2.46 年)
        cycle_month = round((angle / 360.0) * 29.53, 1)

        return {
            "phase_name": current_phase["name"],
            "stage": current_phase["stage"],
            "angle": round(angle, 2),
            "angle_str": f"{round(angle, 1)}°",
            "cycle_month": cycle_month,
            "desc": current_phase["desc"],
            "summary": f"三限當前處於【{current_phase['name']}】（日月角距 {round(angle, 1)}°，約處於 2.5 年微週期之第 {cycle_month} 個月，【{current_phase['stage']}】）。{current_phase['desc']}"
        }

    def calculate_tertiary_aspects(
        self,
        chart_prog: Chart,
        chart_natal: Chart,
        max_orb: float = 1.0,
        moon_max_orb: float = 1.5
    ) -> List[Dict[str, Any]]:
        """
        計算三限星體對本命星體的當月活躍相位 (影響約 2~4 週)
        """
        major_aspects = {
            0: "合相 (0°)",
            60: "六分相 (60°)",
            90: "四分相 (90°)",
            120: "三分相 (120°)",
            180: "對分相 (180°)"
        }

        active_aspects = []

        for p_id in self.CORE_PLANETS:
            try:
                p_prog = chart_prog.get(p_id)
            except Exception:
                continue

            prog_lon = p_prog.lon
            prog_name = self.trans_planets.get(p_id, p_id)
            allowed_orb = moon_max_orb if p_id == const.MOON else max_orb

            for n_id in self.CORE_PLANETS:
                try:
                    p_nat = chart_natal.get(n_id)
                except Exception:
                    continue

                nat_lon = p_nat.lon
                nat_name = self.trans_planets.get(n_id, n_id)

                diff = abs(prog_lon - nat_lon) % 360
                if diff > 180:
                    diff = 360 - diff

                for asp_deg, asp_name in major_aspects.items():
                    orb = abs(diff - asp_deg)
                    if orb <= allowed_orb:
                        active_aspects.append({
                            "prog_planet": f"三限{prog_name}",
                            "aspect": asp_name,
                            "natal_planet": f"本命{nat_name}",
                            "orb": round(orb, 2),
                            "orb_str": f"{round(orb, 2)}°",
                            "duration": "約 2~4 週 (月度聚焦引動)"
                        })

        active_aspects.sort(key=lambda x: x["orb"])
        return active_aspects

    def calculate_tertiary_progressions(
        self,
        chart_natal: Chart,
        houses: List[Dict[str, Any]],
        birth_dt_str: str,
        birth_time_str: str,
        utc_offset_str: str,
        lat: float,
        lon: float,
        target_date: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        三限推運法整合計算介面
        """
        chart_prog, age_years, tert_days, prog_dt, eval_target_date = self.calculate_tertiary_chart(
            birth_dt_str, birth_time_str, utc_offset_str, lat, lon, target_date
        )

        tert_moon = self.calculate_tertiary_moon(chart_prog, houses)
        lunar_phase = self.calculate_tertiary_lunar_phase(chart_prog)
        aspects = self.calculate_tertiary_aspects(chart_prog, chart_natal)

        return {
            "age_years": round(age_years, 2),
            "target_date": str(eval_target_date),
            "tertiary_ephemeris_date": prog_dt.strftime("%Y/%m/%d %H:%M"),
            "tertiary_moon": tert_moon,
            "lunar_phase": lunar_phase,
            "active_aspects": aspects,
            "summary": (
                f"【三限推運 (一日一月)】聚焦於當前月份（實歲 {round(age_years, 1)} 歲）。\n"
                f"- 🌙 **三限月亮**：{tert_moon['summary']}\n"
                f"- 🌗 **三限 2.5 年月相**：{lunar_phase['summary']}\n"
                f"- ⚡ **當月活躍三限對本命相位**：共 {len(aspects)} 組緊密觸發。"
            )
        }
