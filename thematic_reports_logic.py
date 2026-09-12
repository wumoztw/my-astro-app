#!/usr/bin/env python3
"""
Thematic Reports Logic (三大精準專題深度報表)
封裝專為實戰諮詢設計的專題指標提取與結構化 Prompt 框架：
1. 💼 事業職涯與貴人格局專題 (Career & Status Analysis)
2. 💰 財富資產與偏財投資專題 (Wealth & Assets Analysis)
3. ❤️ 婚戀桃花與人際關係專題 (Romance & Relationship Analysis)
"""

from typing import Dict, Any, Optional

class ThematicReportsLogic:
    """專題占星深度報表框架生成器"""

    @staticmethod
    def extract_thematic_context(chart_data: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """從排盤原始資料中提煉專題核心指標"""
        houses = chart_data.get("houses", [])
        planets = chart_data.get("planets", [])
        lots = chart_data.get("lots", [])
        almuten = chart_data.get("almuten", {})

        h_map = {h.get("id"): h for h in houses if isinstance(h, dict)}
        lot_map = {l.get("name"): l for l in lots if isinstance(l, dict)}

        context = {
            "topic": topic,
            "name": chart_data.get("name", "個案"),
            "birth_date": chart_data.get("birth_date", ""),
            "birth_time": chart_data.get("birth_time", ""),
            "location": chart_data.get("location", ""),
            "is_day": chart_data.get("is_day_chart", True),
            "asc_sign": houses[0].get("sign", "") if houses else "",
            "lord_1": houses[0].get("ruler", "") if houses else "",
            "almuten": almuten.get("almuten_name", ""),
            "almuten_score": almuten.get("almuten_score", 0),
        }

        if topic == "career":
            context.update({
                "h10": h_map.get(10, {}),
                "h6": h_map.get(6, {}),
                "h11": h_map.get(11, {}),
                "h1": h_map.get(1, {}),
                "lot_spirit": next((l for l in lots if "精神點" in l.get("name", "")), {}),
                "lot_victory": next((l for l in lots if "勝利點" in l.get("name", "")), {}),
                "zr": chart_data.get("zodiacal_releasing", {}),
                "sa": chart_data.get("solar_arcs", {}),
                "sec_moon": chart_data.get("secondary_progressions", {}).get("progressed_moon", {}),
                "tert_moon": chart_data.get("tertiary_progressions", {}).get("tertiary_moon", {}),
            })
        elif topic == "wealth":
            context.update({
                "h2": h_map.get(2, {}),
                "h8": h_map.get(8, {}),
                "h4": h_map.get(4, {}),
                "h10": h_map.get(10, {}),
                "lot_fortune": next((l for l in lots if "幸運點" in l.get("name", "") or "福德點" in l.get("name", "")), {}),
                "lot_necessity": next((l for l in lots if "必要點" in l.get("name", "")), {}),
                "venus": next((p for p in planets if p.get("id") in ("Venus", "金星")), {}),
                "jupiter": next((p for p in planets if p.get("id") in ("Jupiter", "木星")), {}),
                "sec_moon": chart_data.get("secondary_progressions", {}).get("progressed_moon", {}),
                "tert_moon": chart_data.get("tertiary_progressions", {}).get("tertiary_moon", {}),
            })
        elif topic == "romance":
            context.update({
                "h7": h_map.get(7, {}),
                "h5": h_map.get(5, {}),
                "h1": h_map.get(1, {}),
                "lot_eros": next((l for l in lots if "愛情點" in l.get("name", "")), {}),
                "venus": next((p for p in planets if p.get("id") in ("Venus", "金星")), {}),
                "mars": next((p for p in planets if p.get("id") in ("Mars", "火星")), {}),
                "moon": next((p for p in planets if p.get("id") in ("Moon", "月亮")), {}),
                "sun": next((p for p in planets if p.get("id") in ("Sun", "太陽")), {}),
                "sec_moon": chart_data.get("secondary_progressions", {}).get("progressed_moon", {}),
                "tert_moon": chart_data.get("tertiary_progressions", {}).get("tertiary_moon", {}),
            })

        return context

    @classmethod
    def generate_thematic_prompt(cls, chart_data: Dict[str, Any], topic: str) -> str:
        """依據專題生成高強度、無廢話的結構化 Prompt"""
        name = chart_data.get("name", "個案")
        ctx = cls.extract_thematic_context(chart_data, topic)

        if topic == "career":
            return (
                f"請以精深嚴謹的西洋古典與現代占星學理，為個案【{name}】撰寫一份條理清晰、直擊核心的【💼 事業職涯與貴人格局專題深度診斷報告】。\n\n"
                f"⚠️【專題格式與解讀規範】：\n"
                f"1. 【字數與節奏】：總字數約 1,000 ~ 1,400 字，去蕪存菁，以清晰的小標題與條列陳述，切忌籠統模稜兩可。\n"
                f"2. 【## 1. 職涯天命座標與核心天賦格局】：\n"
                f"   - 第十宮（官祿宮/社會成就）星座與宮位主星狀態。\n"
                f"   - 全盤總御星（Almuten Figuris：{ctx.get('almuten')} 得分 {ctx.get('almuten_score')}分）代表的底層天賦與權能優勢。\n"
                f"   - 適合走體制內高管、獨立創業、專業技術專家或跨界多元發展之定位判定。\n"
                f"3. 【## 2. 職場貴人、組織團隊與阻力防範】：\n"
                f"   - 第十一宮（社群人脈/願景貴人）與第六宮（職場日常/執行力/部屬關係）之吉凶互容接納。\n"
                f"   - 希臘精神點與勝利點之指引。\n"
                f"4. 【## 3. 當前與未來關鍵推運契機 (月度精確引動)】：\n"
                f"   - 黃道釋放法 (ZR 精神點) 之巔峰期或轉折點。\n"
                f"   - 次限月亮（2.5 年生活重心）與三限月亮（當前 2 個月具體月份重心）對事業宮位的推進時機。\n"
                f"5. 【## 4. 具體決策行動指南】：給出 2~3 項立即可落實的職場進退、談判或轉換跑道建議。\n"
                f"6. 【## 💡 延伸性問題建議（您可以直接複製詢問）】：\n"
                f"   1~3. 針對該個案職涯最具張力的關鍵點，設計 3 個引號標註的具體深度問題。\n"
                f"   4. ✍️ 自行輸入問題（若您有其他特定關心的公司、合夥人或轉職疑慮，歡迎直接輸入提問）。\n\n"
                f"【完整星盤與推運數據】：\n{chart_data}"
            )
        elif topic == "wealth":
            return (
                f"請以精深嚴謹的西洋古典與現代占星學理，為個案【{name}】撰寫一份條理清晰、直擊核心的【💰 財富資產與偏財投資專題深度診斷報告】。\n\n"
                f"⚠️【專題格式與解讀規範】：\n"
                f"1. 【字數與節奏】：總字數約 1,000 ~ 1,400 字，直擊財務本質，禁止廢話。\n"
                f"2. 【## 1. 本命財富格局與金錢容器診斷】：\n"
                f"   - 第二宮（正財/薪資收入/動產儲蓄）星座與宮位守護星。\n"
                f"   - 第八宮（偏財/投資/借貸/遺產/商業共有資產）格局。\n"
                f"   - 福德點（Lot of Fortune）與必要點之財富密碼。\n"
                f"3. 【## 2. 財富來源結構與漏財風險破局】：\n"
                f"   - 金星與木星吉凶狀態。\n"
                f"   - 正財穩健 vs 偏財投機的適性比例。\n"
                f"   - 第四宮（田宅不動產/守成基石）之累積潛力。\n"
                f"4. 【## 3. 當前財運推運時機與月份高能觸發點】：\n"
                f"   - 次限月亮在正財/偏財宮位的進展。\n"
                f"   - 三限月亮與吉凶星相位在近 2~4 個月的財運起伏提醒。\n"
                f"5. 【## 4. 實戰理財與投資避坑指引】：給出 2~3 條具體資金配置與風險管控建議。\n"
                f"6. 【## 💡 延伸性問題建議（您可以直接複製詢問）】：\n"
                f"   1~3. 針對該個案財運特質，設計 3 個引號標註的具體深度問題。\n"
                f"   4. ✍️ 自行輸入問題（若您有特定想評估的投資標的、買房置產或創業資金疑惑，歡迎直接輸入提問）。\n\n"
                f"【完整星盤與推運數據】：\n{chart_data}"
            )
        elif topic == "romance":
            return (
                f"請以精深嚴謹的西洋古典與現代占星學理，為個案【{name}】撰寫一份條理清晰、直擊核心的【❤️ 婚戀桃花與人際關係專題深度診斷報告】。\n\n"
                f"⚠️【專題格式與解讀規範】：\n"
                f"1. 【字數與節奏】：總字數約 1,000 ~ 1,400 字，情感洞察深刻，避免心靈雞湯。\n"
                f"2. 【## 1. 本命情感特質與靈魂伴侶原型】：\n"
                f"   - 第七宮（夫妻/一對一伴侶）星座與第七宮守護星之狀態與落宮。\n"
                f"   - 伴侶特質原型（個性、外表氣質、相處模式）。\n"
                f"   - 愛情點（Lot of Eros）之情感渴望與心靈共鳴點。\n"
                f"3. 【## 2. 戀愛互動模式與關係盲點剖析】：\n"
                f"   - 第五宮（戀愛桃花/熱情歡愉）與金星/火星之互動張力。\n"
                f"   - 在親密關係中容易遭遇的溝通卡點或相處挑戰。\n"
                f"4. 【## 3. 近期桃花機遇與感情推運時間窗口】：\n"
                f"   - 次限月亮過境宮位與金星推進。\n"
                f"   - 三限月亮在近 2~4 個月是否引動五宮或七宮桃花契機。\n"
                f"5. 【## 4. 幸福關係經營指引】：給出 2~3 條專屬的感情經營或脫單/化解摩擦建議。\n"
                f"6. 【## 💡 延伸性問題建議（您可以直接複製詢問）】：\n"
                f"   1~3. 針對該個案感情關鍵課題，設計 3 個引號標註的具體深度問題。\n"
                f"   4. ✍️ 自行輸入問題（若您有特定對象、合盤困擾或感情抉擇，歡迎直接輸入提問）。\n\n"
                f"【完整星盤與推運數據】：\n{chart_data}"
            )
        else:
            return f"請針對個案【{name}】進行古典占星綜合解析。\n{chart_data}"
