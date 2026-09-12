#!/usr/bin/env python3
"""
Secondary Progressions Engine (次限推運法 - 一日一年)
依據正統西方推運占星學理與天體力學：
1. 實歲 N 歲對應出生後第 N 天之真實天球天體座標 (A Day for a Year)。
2. 計算次限月亮 (Progressed Moon) 當前星座、度數、落入本命宮位與換座預警 (約 2.5 年生命焦點)。
3. 計算次限 30 年月相八大週期 (Progressed Lunar Phase Cycle)。
4. 篩選次限星體對本命星體的重大活躍相位 (Progressed-to-Natal Aspects)。
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
import pandas as pd
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

class SecondaryProgressionsLogic:
    """次限推運法 (一日一年) 獨立核心演算法"""

    CORE_PLANETS = [
        const.SUN, const.MOON, const.MERCURY, const.VENUS,
        const.MARS, const.JUPITER, const.SATURN,
        const.URANUS, const.NEPTUNE, const.PLUTO
    ]

    LUNAR_PHASES = [
        {"name": "次限新月 (New Moon)", "min_angle": 0.0, "max_angle": 45.0,
         "stage": "生命播種期", "desc": "開啟全新 30 年生命宏觀大篇章，萌生新志向與願景，適合奠定基礎與探索種子。"},
        {"name": "次限蛾眉月 (Crescent Moon)", "min_angle": 45.0, "max_angle": 90.0,
         "stage": "萌芽突破期", "desc": "突破既有慣性與阻力，將新芽推進現實世界，需要毅力與主動開拓精神。"},
        {"name": "次限上弦月 (First Quarter)", "min_angle": 90.0, "max_angle": 135.0,
         "stage": "行動考驗期", "desc": "面對外在結構考驗與決策轉折點，必須付諸果決行動，確立明確架構與邊界。"},
        {"name": "次限盈凸月 (Gibbous Moon)", "min_angle": 135.0, "max_angle": 180.0,
         "stage": "微調精進期", "desc": "技能磨礪與細節校準期，蓄勢待發，準備迎接即將到來的生命滿月收成。"},
        {"name": "次限滿月 (Full Moon)", "min_angle": 180.0, "max_angle": 225.0,
         "stage": "巔峰顯化期", "desc": "人生 30 年能量頂峰，成果全面顯化與曝光，伴隨強烈的意識覺醒與關係明朗。"},
        {"name": "次限散播月 (Disseminating Moon)", "min_angle": 225.0, "max_angle": 270.0,
         "stage": "分享傳播期", "desc": "享受實質成果並回饋社會，適合傳授經驗、傳播理念與擴大社會影響力。"},
        {"name": "次限下弦月 (Last Quarter)", "min_angle": 270.0, "max_angle": 315.0,
         "stage": "意識重組期", "desc": "價值觀深刻反思與轉型，需要斷捨離不再適用的外在模式，去蕪存菁。"},
        {"name": "次限香脂月 (Balsamic Moon)", "min_angle": 315.0, "max_angle": 360.0,
         "stage": "沉澱休整期", "desc": "30 年大週期尾聲，清理未解業力與執著，休養生息，在寧靜中孕育下一次新月。"}
    ]

    HOUSE_THEMES = {
        1: "自我重塑、個人主體性開拓與人生新形象建立",
        2: "財務架構、資產累積、正財收入與自我價值重新評估",
        3: "學習溝通、資訊傳播、日常交通與身邊手足鄰里圈互動",
        4: "家庭基石、內在安全感、不動產置產與心理沉澱歸宿",
        5: "創造力爆發、自我表現、投資冒險、戀愛桃花與子女緣份",
        6: "職場工作節奏、日常技能精進、身心健康與生活作息調校",
        7: "重要一對一關係、商業合夥協議、婚姻伴侶與公開對手",
        8: "深層資源整合、偏財借貸、心理轉化重生與隱私信任",
        9: "高等學識、哲學信仰、跨國遠行、出版名望與人生視野開闊",
        10: "社會名望、事業最高成就、職涯晉升與公眾形象焦點",
        11: "社群網路、團隊組織合作、社會願景與人脈資源流動",
        12: "心靈療癒、隱退休整、幕後籌備、身心解碼與業力釋放"
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
        一日一年法則：計算實歲年齡與次限星曆推進時間點。
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
        age_days = (target_date - birth_d).days
        age_years = max(0.0, age_days / 365.2422)

        birth_dt = datetime.strptime(f"{clean_birth_str} {birth_time_str}", "%Y/%m/%d %H:%M")
        prog_dt = birth_dt + pd.Timedelta(days=age_years)
        return age_years, prog_dt, target_date

    def calculate_progressed_chart(
        self,
        birth_dt_str: str,
        birth_time_str: str,
        utc_offset_str: str,
        lat: float,
        lon: float,
        target_date: Optional[Any] = None
    ) -> tuple:
        """建立次限盤 (Chart)"""
        age_years, prog_dt, eval_target_date = self.calculate_progressed_time(
            birth_dt_str, birth_time_str, target_date
        )
        prog_date_str = prog_dt.strftime("%Y/%m/%d")
        prog_time_str = prog_dt.strftime("%H:%M")

        dt_prog = Datetime(prog_date_str, prog_time_str, utc_offset_str)
        pos = GeoPos(lat, lon)
        chart_prog = Chart(dt_prog, pos, hsys=const.HOUSES_WHOLE_SIGN)
        return chart_prog, age_years, prog_dt, eval_target_date

    def calculate_progressed_moon(
        self,
        chart_prog: Chart,
        houses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        計算次限月亮核心數據：星座、度數、落入本命宮位、換座預警與生活主題。
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

        # 換座換宮倒數估算
        # 次限月亮天球日速 (lonspeed) 對應年速，換算每個月平均推進度數
        daily_speed = abs(moon.lonspeed) if hasattr(moon, 'lonspeed') and moon.lonspeed else 13.18
        monthly_speed = daily_speed / 12.0
        degrees_left = 30.0 - deg_in_sign
        months_left = round(degrees_left / max(monthly_speed, 0.5), 1)

        theme = self.HOUSE_THEMES.get(house_num, "生命關鍵轉型與內在心境焦點")

        return {
            "sign": sign_name,
            "sign_const": sign_const,
            "degree_str": deg_str,
            "longitude": round(moon_lon, 2),
            "degree_in_sign": round(deg_in_sign, 2),
            "house_num": house_num,
            "house_str": house_str,
            "months_left_in_sign": months_left,
            "theme": theme,
            "summary": f"次限月亮現位於【{sign_name} {deg_str}】，落入本命【{house_str}】。預計約 {months_left} 個月後進入下一個宮位。當前生活與心理核心焦點：{theme}。"
        }

    def calculate_progressed_lunar_phase(self, chart_prog: Chart) -> Dict[str, Any]:
        """
        計算次限 30 年月相八大週期 (Progressed Lunar Phase Cycle)
        """
        sun_lon = chart_prog.get(const.SUN).lon
        moon_lon = chart_prog.get(const.MOON).lon
        angle = (moon_lon - sun_lon) % 360

        current_phase = self.LUNAR_PHASES[0]
        for p in self.LUNAR_PHASES:
            if p["min_angle"] <= angle < p["max_angle"]:
                current_phase = p
                break

        return {
            "phase_name": current_phase["name"],
            "stage": current_phase["stage"],
            "angle": round(angle, 2),
            "angle_str": f"{round(angle, 1)}°",
            "desc": current_phase["desc"],
            "sun_lon": round(sun_lon, 2),
            "moon_lon": round(moon_lon, 2),
            "summary": f"當前處於【{current_phase['name']}】（日月角距 {round(angle, 1)}°），象徵人生 30 年週期之【{current_phase['stage']}】。{current_phase['desc']}"
        }

    def calculate_progressed_planets_list(
        self,
        chart_prog: Chart,
        houses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """提取次限全星體位置與順逆行狀態"""
        h1_lon = houses[0]['lon'] if houses else 0.0
        planets = []

        for p_id in self.CORE_PLANETS:
            try:
                p = chart_prog.get(p_id)
                p_lon = p.lon
                sign_idx = int(p_lon // 30)
                sign_const = const.LIST_SIGNS[sign_idx]
                sign_name = self.trans_signs.get(sign_const, sign_const)
                p_name = self.trans_planets.get(p_id, p_id)
                house_num = int(((p_lon - h1_lon) % 360) // 30) + 1
                deg_str = self._degree_to_dms_str(p_lon)
                speed = getattr(p, 'lonspeed', 1.0)
                is_retro = bool(speed < 0)

                planets.append({
                    "id": p_id,
                    "name": p_name,
                    "sign": sign_name,
                    "degree_str": deg_str,
                    "house_num": house_num,
                    "house_str": f"第 {house_num} 宮",
                    "longitude": round(p_lon, 2),
                    "is_retrograde": is_retro,
                    "speed": round(speed, 4)
                })
            except Exception:
                continue

        return planets

    def calculate_progressed_aspects(
        self,
        chart_prog: Chart,
        chart_natal: Chart,
        max_orb: float = 1.0,
        moon_max_orb: float = 1.5
    ) -> List[Dict[str, Any]]:
        """
        計算次限星體對本命星體的重大活躍相位 (Progressed-to-Natal Aspects)
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
                        active_duration = "約 2~3 個月 (月亮快速引動)" if p_id == const.MOON else "約 1~2 年 (年度重大深層趨勢)"
                        active_aspects.append({
                            "prog_planet": f"次限{prog_name}",
                            "aspect": asp_name,
                            "natal_planet": f"本命{nat_name}",
                            "orb": round(orb, 2),
                            "orb_str": f"{round(orb, 2)}°",
                            "duration": active_duration
                        })

        active_aspects.sort(key=lambda x: x["orb"])
        return active_aspects

    def calculate_secondary_progressions(
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
        次限推運法整合計算介面
        """
        chart_prog, age_years, prog_dt, eval_target_date = self.calculate_progressed_chart(
            birth_dt_str, birth_time_str, utc_offset_str, lat, lon, target_date
        )

        prog_moon = self.calculate_progressed_moon(chart_prog, houses)
        lunar_phase = self.calculate_progressed_lunar_phase(chart_prog)
        planets_list = self.calculate_progressed_planets_list(chart_prog, houses)
        aspects = self.calculate_progressed_aspects(chart_prog, chart_natal)

        return {
            "age_years": round(age_years, 2),
            "target_date": str(eval_target_date),
            "progressed_date": prog_dt.strftime("%Y/%m/%d %H:%M"),
            "progressed_moon": prog_moon,
            "lunar_phase": lunar_phase,
            "planets": planets_list,
            "active_aspects": aspects,
            "summary": (
                f"【次限推運 (一日一年)】當前年齡 {round(age_years, 1)} 歲。\n"
                f"- 🌙 **次限月亮**：{prog_moon['summary']}\n"
                f"- 🌗 **次限月相**：{lunar_phase['summary']}\n"
                f"- ⚡ **活躍次限對本命相位**：共 {len(aspects)} 組高能相位觸發。"
            )
        }
