import swisseph as swe
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from datetime import datetime, date
import pandas as pd
import html
from geopy.geocoders import ArcGIS

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
    ephem_path = os.path.abspath("ephem")
    if os.path.exists(ephem_path):
        swe.set_ephe_path(ephem_path)
    return True


@st.cache_data
def get_location_coords(location_name):
    """
    Perform geocoding for a location name and cache the results.
    This prevents redundant network requests and UI freezes.
    """
    try:
        geolocator = ArcGIS()
        location = geolocator.geocode(location_name, timeout=10)
        return (location.latitude, location.longitude) if location else None
    except Exception:
        return None


class AstrologyLogic:
    # Localization Dictionaries (Shared)
    TRANS_PLANETS = {
        const.SUN: "太陽",
        const.MOON: "月亮",
        const.MERCURY: "水星",
        const.VENUS: "金星",
        const.MARS: "火星",
        const.JUPITER: "木星",
        const.SATURN: "土星",
        const.ASC: "上升點",
        "Sun": "太陽",
        "Moon": "月亮",
        "Mercury": "水星",
        "Venus": "金星",
        "Mars": "火星",
        "Jupiter": "木星",
        "Saturn": "土星",
        "Asc": "上升點",
        "Ascendant": "上升點",
    }

    PLANET_GLYPHS = {
        const.SUN: "☉",
        const.MOON: "☽",
        const.MERCURY: "☿",
        const.VENUS: "♀",
        const.MARS: "♂",
        const.JUPITER: "♃",
        const.SATURN: "♄",
        const.ASC: "Ⓐ",
        "Sun": "☉",
        "Moon": "☽",
        "Mercury": "☿",
        "Venus": "♀",
        "Mars": "♂",
        "Jupiter": "♃",
        "Saturn": "♄",
        "Asc": "Ⓐ",
        "Ascendant": "Ⓐ",
    }

    TRANS_SIGNS = {
        const.ARIES: "牡羊座",
        const.TAURUS: "金牛座",
        const.GEMINI: "雙子座",
        const.CANCER: "巨蟹座",
        const.LEO: "獅子座",
        const.VIRGO: "處女座",
        const.LIBRA: "天秤座",
        const.SCORPIO: "天蠍座",
        const.SAGITTARIUS: "射手座",
        const.CAPRICORN: "摩羯座",
        const.AQUARIUS: "水瓶座",
        const.PISCES: "雙魚座",
        "Aries": "牡羊座",
        "Taurus": "金牛座",
        "Gemini": "雙子座",
        "Cancer": "巨蟹座",
        "Leo": "獅子座",
        "Virgo": "處女座",
        "Libra": "天秤座",
        "Scorpio": "天蠍座",
        "Sagittarius": "射手座",
        "Capricorn": "摩羯座",
        "Aquarius": "水瓶座",
        "Pisces": "雙魚座",
    }

    TRANS_ASPECTS = {
        "Conjunction": "合相 (0°)",
        "Sextile": "六分相 (60°)",
        "Square": "四分相 (90°)",
        "Trine": "三分相 (120°)",
        "Opposition": "對分相 (180°)",
    }

    TRANS_HOUSES = {
        1: "第一宮 (命宮)",
        2: "第二宮",
        3: "第三宮",
        4: "第四宮",
        5: "第五宮",
        6: "第六宮",
        7: "第七宮",
        8: "第八宮",
        9: "第九宮",
        10: "第十宮",
        11: "第十一宮",
        12: "第十二宮",
    }

    def __init__(self):
        # Cache initialization
        init_ephemeris()

        # Initialize Logic Modules
        self.dignities = DignitiesLogic()
        self.aspects = AspectsLogic()
        self.lots = LotsLogic()
        self.time_lords = TimeLordsLogic()

    def get_location_coordinates(self, location_name):
        return get_location_coords(location_name)

    def degree_to_dms(self, degree):
        d = int(degree)
        m = int((degree - d) * 60)
        s = int((degree - d - m / 60) * 3600)
        return d, m, s

    def calculate_equal_houses(self, asc_lon):
        houses = []
        for i in range(12):
            house_lon = (asc_lon + i * 30) % 360
            sign_idx = int(house_lon // 30)
            sign_const = const.LIST_SIGNS[sign_idx]
            house_id = i + 1
            ruler_const = self.dignities.RULERS.get(sign_const)
            houses.append(
                {
                    "id": house_id,
                    "id_str": self.TRANS_HOUSES.get(house_id, f"第{house_id}宮"),
                    "lon": house_lon,
                    "sign": self.TRANS_SIGNS.get(sign_const, sign_const),
                    "degree": house_lon % 30,
                    "ruler": self.TRANS_PLANETS.get(ruler_const, ruler_const),
                }
            )
        return houses

    def get_house_of_lon(self, lon, houses):
        h1_lon = houses[0]["lon"]
        diff = (lon - h1_lon) % 360
        return int(diff // 30) + 1

    def is_day_birth(self, chart, houses):
        sun = chart.get(const.SUN)
        house_num = self.get_house_of_lon(sun.lon, houses)
        return 7 <= house_num <= 12

    def get_planets_data(self, chart, houses):
        planets = [
            const.SUN,
            const.MOON,
            const.MERCURY,
            const.VENUS,
            const.MARS,
            const.JUPITER,
            const.SATURN,
        ]
        res = []
        is_day = self.is_day_birth(chart, houses)
        sun_lon = chart.get(const.SUN).lon

        for p_id in planets:
            p = chart.get(p_id)
            d, m, s = self.degree_to_dms(p.lon % 30)
            house_num = self.get_house_of_lon(p.lon, houses)

            # Use Modular Logic
            dig = self.dignities.calculate_essential_dignities(p.id, p.lon, is_day)
            acc = self.dignities.get_accidental_dignities(
                p.id, p.lon, house_num, sun_lon, p.lonspeed < 0
            )

            res.append(
                {
                    "id": p.id,
                    "symbol": self.PLANET_GLYPHS.get(p.id, ""),
                    "name": self.TRANS_PLANETS.get(p.id, p.id),
                    "sign": self.TRANS_SIGNS.get(p.sign, p.sign),
                    "degree_str": f"{d}°{m}'{s}\"",
                    "retro": "Ⓡ" if p.lonspeed < 0 else "",
                    "lon": p.lon,
                    "house": self.TRANS_HOUSES.get(house_num, f"第{house_num}宮"),
                    "house_num": house_num,
                    "dignity": dig,
                    "accidental": acc,
                }
            )
        return res

    def get_aspects(self, chart):
        return self.aspects.get_aspects(
            chart, self.TRANS_PLANETS, self.PLANET_GLYPHS, self.TRANS_ASPECTS
        )

    def calculate_lots(self, chart, houses, is_day):
        return self.lots.calculate_lots(
            chart, houses, is_day, self.TRANS_SIGNS, self.TRANS_HOUSES
        )

    def get_fixed_stars(self, chart):
        return self.lots.get_fixed_stars(chart, self.TRANS_PLANETS)

    def calculate_profections(self, chart, houses, birth_dt_str, current_date=None):
        return self.time_lords.calculate_profections(
            chart,
            self.TRANS_SIGNS,
            self.PLANET_GLYPHS,
            self.TRANS_PLANETS,
            birth_dt_str,
            current_date,
        )

    def get_firdaria_data(self, birth_dt_str, is_day, current_date=None):
        return self.time_lords.get_firdaria_data(birth_dt_str, is_day, current_date)

    def run_analysis(self, birth_date, birth_time, lat, lon, utc_offset):
        """
        Runs the full astrological analysis and returns a dictionary of results.
        """
        birth_date_str = birth_date.strftime("%Y/%m/%d")
        birth_time_str = birth_time.strftime("%H:%M")

        sign = "+" if utc_offset >= 0 else "-"
        abs_offset = abs(utc_offset)
        h, m = int(abs_offset), int((abs_offset - int(abs_offset)) * 60)
        offset_str = f"{sign}{h:02d}:{m:02d}"

        dt = Datetime(birth_date_str, birth_time_str, offset_str)
        pos = GeoPos(lat, lon)
        chart = Chart(dt, pos)

        # Calculations
        asc = chart.get(const.ASC)
        asc_sign = self.TRANS_SIGNS.get(asc.sign, asc.sign)
        asc_deg, asc_min, _ = self.degree_to_dms(asc.lon % 30)

        sun_p = chart.get(const.SUN)
        moon_p = chart.get(const.MOON)
        sun_sign = self.TRANS_SIGNS.get(sun_p.sign, sun_p.sign)
        moon_sign = self.TRANS_SIGNS.get(moon_p.sign, moon_p.sign)
        sun_deg, sun_min, _ = self.degree_to_dms(sun_p.lon % 30)
        moon_deg, moon_min, _ = self.degree_to_dms(moon_p.lon % 30)

        houses = self.calculate_equal_houses(asc.lon)
        planets_data = self.get_planets_data(chart, houses)
        prof_info = self.calculate_profections(chart, houses, birth_date_str)
        aspects = self.get_aspects(chart)
        is_day = self.is_day_birth(chart, houses)
        f_data = self.get_firdaria_data(birth_date_str, is_day)
        lots = self.calculate_lots(chart, houses, is_day)
        fixed_stars = self.get_fixed_stars(chart)

        return {
            "birth_date_str": birth_date_str,
            "birth_time_str": birth_time_str,
            "lat": lat,
            "lon": lon,
            "asc": f"{asc_sign} {asc_deg}°{asc_min}'",
            "sun": f"{sun_sign} {sun_deg}°{sun_min}'",
            "moon": f"{moon_sign} {moon_deg}°{moon_min}'",
            "planets": planets_data,
            "houses": houses,
            "aspects": aspects,
            "prof_info": prof_info,
            "f_data": f_data,
            "is_day": is_day,
            "lots": lots,
            "fixed_stars": fixed_stars,
        }

    def generate_markdown_report(self, data, location_city):
        """
        Generates a Markdown report from the analysis data.
        """
        lines = []
        lines.append("# 古典占星命盤完整資料 (升級版)\n\n")
        lines.append(f"產出時間：{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n\n")
        lines.append("---\n\n")
        lines.append("## 出生資訊\n\n")
        lines.append(f"- 生日：{data['birth_date_str']} {data['birth_time_str']}\n")
        lines.append(
            f"- 地點：{html.escape(location_city)} ({data['lat']:.2f}N, {data['lon']:.2f}E)\n"
        )
        lines.append(f"- 上升星座：{data['asc']}\n")
        lines.append(f"- 太陽星座：{data['sun']}\n")
        lines.append(f"- 月亮星座：{data['moon']}\n\n")

        lines.append("## 行星狀態與本質力量\n\n")
        for p in data["planets"]:
            d = p["dignity"]
            d_str = ", ".join(d["list"]) if d["list"] else "無 (Peregrine)"
            acc_str = ", ".join(p["accidental"])
            lines.append(f"### {p['symbol']} {p['name']}\n")
            lines.append(
                f"- 位置：{p['sign']} {p['degree_str']} {p['retro']} | [{p['house']}]\n"
            )
            lines.append(f"- 本質力量：{d_str} (總分: {d['score']})\n")
            lines.append(f"- 後天狀態：{acc_str}\n\n")

        lines.append("## 特殊點位與恆星\n\n")
        for lot in data["lots"]:
            lines.append(f"- {lot['name']}：{lot['sign']} {lot['degree']} ({lot['house']})\n")
        for star in data["fixed_stars"]:
            lines.append(
                f"- 恆星合相：{star['planet']} 合相 {star['star']} (誤差 {star['orb']})\n"
            )
        lines.append("\n")

        lines.append("## 宮位資料\n\n")
        for h in data["houses"]:
            h_deg, h_min, _ = self.degree_to_dms(h["degree"])
            lines.append(f"- {h['id_str']}：{h['sign']} {h_deg}°{h_min}' (主：{h['ruler']})\n")
        lines.append("\n")

        lines.append("## 相位與接納\n\n")
        if data["aspects"]:
            for a in data["aspects"]:
                rec = f" | 接納：{a['reception']}" if a["reception"] else ""
                lines.append(
                    f"- {a['p1']} - {a['p2']}：{a['aspect']} (誤差 {a['orb']}){rec}\n"
                )
        else:
            lines.append("無顯著相位。\n")
        lines.append("\n")

        lines.append("## 推運資訊\n\n")
        lines.append(
            f"- 小限分限：{data['prof_info'].get('prof_sign')} (第 {data['prof_info'].get('prof_house_num')} 宮)\n"
        )
        lines.append(f"- 當前年主星：{data['prof_info'].get('lord_of_year')}\n\n")

        act = data["f_data"]["active"]
        m_n = self.TRANS_PLANETS.get(act["major"], act["major"])
        mi_n = self.TRANS_PLANETS.get(act["minor"], act["minor"])
        lines.append(f"- 法達當前大運：{m_n}\n")
        lines.append(f"- 法達當前小運：{mi_n}\n")
        lines.append(f"- 下次換運日期：{act['end'].strftime('%Y/%m/%d')}\n\n")

        lines.append("---\n\n")
        lines.append("## 🤖 深度思考型 AI 古典占星大師解析指引\n")
        lines.append("請將此檔案內容完整複製並貼給 AI (推薦使用 Venice AI)，並直接使用以下指令提問：\n\n")
        lines.append("```text\n")
        lines.append(
            "你現在是一位深度思考型 AI 古典占星大師，你精通並熟悉所有古典占星論命的理論，請嚴格遵守以下規則處理每一個問題。\n"
        )
        lines.append(
            "【角色約束與語調】 語言：始終使用台灣華語回覆。 態度：保持絕對客觀與真實，拒絕任何諂媚或奉承。如果用戶的提問前提有誤，請直接指出並說明。 工具：遇到不熟悉的概念、即時資訊或需要驗證的事實，必須使用 Google Search 查詢。\n\n"
        )
        lines.append("【思維框架（必須按順序執行）】 收到問題後，請依照以下步驟思考：\n\n")
        lines.append("第一性原理拆解：拆解到問題的最本質核心要素。\n\n")
        lines.append("全面性推演與思考：使用古典占星理論進行全面性推演與思考。\n\n")
        lines.append("批判性評估：對任何方案或結論，都必須分析『優勢』與『缺點（包含風險）』。\n\n")
        lines.append("機率表達：避免模糊詞彙，盡量給出『置信度評級（高／中／低）』，並說明估算的邏輯依據。\n\n")
        lines.append("【品質控制】 在最終輸出前，自我審核：是否偏離主題？是否有事實性錯誤？邏輯是否嚴密？\n\n")
        lines.append("【輸出格式】 請使用 Markdown 語法：用數字分區塊標題、關鍵結論用簡易圖案、複雜比較使用列表或表格。\n\n")
        lines.append("【主動引導】\n\n")
        lines.append("鼓勵並引導使用者發問。\n\n")
        lines.append("在分析結束後，主動發送 3 個延伸問題並詢問使用者是否要深入了解。\n\n")
        lines.append("【主動優先解釋】\n\n")
        lines.append("詳盡且深入的分析每一宮位在這張命盤中的特質，並用台灣華語詳細解釋。\n\n")
        lines.append("詳盡且深入的分析每一個行星在這張命盤中的特質，並解釋行星與行星的交角在這張命盤中的含意。\n")
        lines.append("```\n\n")
        lines.append(
            "**Venice AI 推薦連結：[https://venice.ai/chat?ref=XmvhLM](https://venice.ai/chat?ref=XmvhLM)**\n"
        )

        return "".join(lines)
