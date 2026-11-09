#!/usr/bin/env python3
"""
Thematic Reports Logic (三大精準專題深度報表)
封裝專為實戰諮詢設計的專題指標提取與結構化 Prompt 框架：
1. 💼 事業職涯與貴人格局專題 (Career & Status Analysis)
2. 💰 財富資產與偏財投資專題 (Wealth & Assets Analysis)
3. ❤️ 婚戀桃花與人際關係專題 (Romance & Relationship Analysis)
4. 📅 年度太陽返照盤與流年運勢專題 (Solar Return & Annual Forecast)
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
        elif topic == "synastry":
            syn = chart_data.get("synastry_data") or {}
            context.update({
                "person_a": syn.get("person_a", chart_data.get("name", "命盤主 A")),
                "person_b": syn.get("person_b", "合盤對象 B"),
                "asc_b_str": syn.get("asc_b_str", ""),
                "sun_b_str": syn.get("sun_b_str", ""),
                "moon_b_str": syn.get("moon_b_str", ""),
                "resonance_scores": syn.get("resonance_scores", {}),
                "receptions": syn.get("receptions", []),
                "b_in_a_overlays": syn.get("b_in_a_overlays", []),
                "a_in_b_overlays": syn.get("a_in_b_overlays", []),
                "cross_aspects": syn.get("cross_aspects", []),
                "h7": h_map.get(7, {}),
                "h5": h_map.get(5, {}),
                "h10": h_map.get(10, {}),
                "h1": h_map.get(1, {}),
            })

        elif topic == "health":
            context.update({
                "h6": h_map.get(6, {}),
                "h8": h_map.get(8, {}),
                "h12": h_map.get(12, {}),
                "h1": h_map.get(1, {}),
                "temperament": chart_data.get("natal_core", {}).get("temperament", {}),
                "hyleg": chart_data.get("natal_core", {}).get("hyleg_data", {}),
                "saturn": next((p for p in planets if p.get("id") in ("Saturn", "土星")), {}),
                "mars": next((p for p in planets if p.get("id") in ("Mars", "火星")), {}),
            })
        elif topic == "academics":
            context.update({
                "h9": h_map.get(9, {}),
                "h3": h_map.get(3, {}),
                "h10": h_map.get(10, {}),
                "mercury": next((p for p in planets if p.get("id") in ("Mercury", "水星")), {}),
                "jupiter": next((p for p in planets if p.get("id") in ("Jupiter", "木星")), {}),
                "lot_spirit": next((l for l in lots if "精神點" in l.get("name", "")), {}),
            })
        elif topic == "real_estate":
            context.update({
                "h4": h_map.get(4, {}),
                "h2": h_map.get(2, {}),
                "saturn": next((p for p in planets if p.get("id") in ("Saturn", "土星")), {}),
                "moon": next((p for p in planets if p.get("id") in ("Moon", "月亮")), {}),
                "venus": next((p for p in planets if p.get("id") in ("Venus", "金星")), {}),
            })

        return context

    @classmethod
    def generate_thematic_prompt(cls, chart_data: Dict[str, Any], topic: str) -> str:
        """依據專題生成高強度、無廢話的結構化 Prompt"""
        name = chart_data.get("name", "個案")
        ctx = cls.extract_thematic_context(chart_data, topic)
        clean_data = {k: v for k, v in chart_data.items() if k != 'chart'}

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
        elif topic == "synastry":
            syn = chart_data.get("synastry_data") or {}
            return (
                f"請以精深嚴謹的古典占星學理（托勒密《四書》Book 4、西頓的多羅修斯、威廉·里利《基督教占星學》Book 3 合盤與接納），"
                f"為【{ctx.get('person_a')}】與【{ctx.get('person_b')}】撰寫一份【💞 古典占星雙人合盤與宿命共鳴深度合參報告】。\n\n"
                f"⚠️【專題格式與解讀規範】：\n"
                f"1. 【字數與節奏】：總字數約 1,200 ~ 1,600 字，條理分明，直擊核心，禁止空泛心靈雞湯。\n"
                f"2. 【## 1. 雙人基本盤格與量化共鳴總評】：\n"
                f"   - 比較 A（上升 {chart_data.get('asc', '')}、太陽 {chart_data.get('sun', '')}、月亮 {chart_data.get('moon', '')}）"
                f"與 B（上升 {ctx.get('asc_b_str')}、太陽 {ctx.get('sun_b_str')}、月亮 {ctx.get('moon_b_str')}）的元素氣質相容度。\n"
                f"   - 解讀三項量化指數：事業協同指數、情感黏著指數、關係張力指數（{ctx.get('resonance_scores')}）。\n"
                f"3. 【## 2. 古典互容與接納深度解碼 (Mutual Reception & Dispositorship)】：\n"
                f"   - 分析 A、B 間的廟旺接納（{ctx.get('receptions')}）：誰欣賞、扶持、遷就誰，是否存在命運綁定的互容。\n"
                f"4. 【## 3. 十二整宮疊合效應 (Whole Sign House Overlays — 雙方落入彼此何宮)】：\n"
                f"   - 分析 B 的太陽、月亮、金星、火星、木星、土星、上升落入 A 整宮制各宮（b_in_a_overlays），以及 A 落入 B 各宮（a_in_b_overlays），"
                f"強調被引動的 1/7/5/4/10/2/8 宮人生領域。\n"
                f"5. 【## 4. 跨盤核心交角與吉凶張力 (Cross-Aspects: 日月共鳴、金火吸引與火土磨合)】：\n"
                f"   - 評估日月、金火、木星等吉相位與凶星刑沖（cross_aspects），指出具體的甜蜜點與摩擦觸發點。\n"
                f"6. 【## 5. 相處之道、合作/情感經營建議與避坑指南】：\n"
                f"   - 針對情感伴侶與事業合夥，各給出 3 項可落實的建議。\n"
                f"7. 【## 💡 延伸性問題建議（您可以直接複製詢問）】：\n"
                f"   1~3. 針對此組合最具張力的課題，設計 3 個引號標註的具體深度問題。\n"
                f"   4. ✍️ 自行輸入問題。\n\n"
                f"【合盤數據 (synastry_data)】：\n{syn}\n\n"
                f"【本命盤摘要】：\n{clean_data}"
            )
        elif topic == "solar_return":
            sr = chart_data.get("sr_data") or {}
            return (
                f"請以精深嚴謹的古典占星學理（Abu Ma'shar《論年度運轉》、Bonatti、William Lilly《基督教占星學》太陽返照盤），"
                f"為個案【{name}】撰寫一份【📅 年度太陽返照盤與流年運勢大合參報告】（{sr.get('target_year', '')} 年）。\n\n"
                f"⚠️【專題格式與解讀規範】：\n"
                f"1. 【字數與節奏】：總字數約 1,200 ~ 1,600 字，條理分明，直擊核心，禁止空泛心靈雞湯。\n"
                f"2. 【## 1. 年度主題定調】：\n"
                f"   - 返照時刻 {sr.get('sr_datetime_local', '')}，返照上升 {sr.get('sr_asc_str', '')}、天頂 {sr.get('sr_mc_str', '')}。\n"
                f"   - 返照上升落入本命第 {sr.get('sr_asc_in_natal_house', '')} 宮（{sr.get('sr_asc_natal_house_theme', '')}），"
                f"此為全年核心主題。\n"
                f"   - 返照年度主星（Lord of the Year）：{sr.get('sr_ruler_name', '')}，分析其在返照盤與本命盤的落宮、尊貴與相位。\n"
                f"3. 【## 2. 年度小限 (Annual Profection) 合參】：\n"
                f"   - 結合小限年度主星（{(chart_data.get('prof_info') or {}).get('lord_of_year', '')}）與返照年度主星，判斷兩者是否同星、互容或相位呼應。\n"
                f"4. 【## 3. 返照七曜與返照-本命緊密相位】：\n"
                f"   - 逐一解讀返照七曜落入返照宮與本命宮；重點分析 active_aspects（容許度 <= 2°）所引動的事件領域。\n"
                f"5. 【## 4. 法達星限與黃道釋放法 (ZR) 時間領主交叉驗證】：\n"
                f"   - 當前法達主運／副運：{(chart_data.get('f_data') or {}).get('active', {})}。\n"
                f"   - ZR 精神點 L1／L2 是否處於巔峰期或換宮跳躍 (LB)：{((chart_data.get('zr_data') or {}).get('spirit') or {}).get('active_l1', {})}。\n"
                f"   - 說明各時間領主與返照盤主題疊加後，全年吉凶強弱與關鍵月份。\n"
                f"6. 【## 5. 全年行動指南】：事業、財務、感情、健康各給出 1~2 項可落實的建議與需留意的時段。\n"
                f"7. 【## 💡 延伸性問題建議（您可以直接複製詢問）】：\n"
                f"   1~3. 針對該年度最具張力的課題，設計 3 個引號標註的具體深度問題。\n"
                f"   4. ✍️ 自行輸入問題。\n\n"
                f"【太陽返照盤數據 (sr_data)】：\n{sr}\n\n"
                f"【完整星盤與推運數據】：\n{clean_data}"
            )
        elif topic == "health":
            return (
                f"請以精深嚴謹的西洋古典占星學理（四液氣質學說、Hyleg 生命主、Alcocoden 壽主星、第 6/8/12 宮疾病防範），"
                f"為個案【{name}】撰寫一份條理清晰、直擊核心的【🏥 健康體質與身心精力平衡專題診斷報告】。\n\n"
                f"⚠️【專題格式與解讀規範】：\n"
                f"1. 【字數與節奏】：總字數約 1,000 ~ 1,400 字，著重預防性體質指引，禁止醫療診斷斷言。\n"
                f"2. 【## 1. 古典四液氣質 (Temperament) 與體質底色】：\n"
                f"   - 分析膽汁質 (Hot/Dry)、多血質 (Hot/Moist)、黏液質 (Cold/Moist)、抑鬱質 (Cold/Dry) 的主次比例與體能強弱。\n"
                f"3. 【## 2. 生命活力指標 (Hyleg/Alcocoden) 與耐受力】：\n"
                f"   - 分析本命第一宮（命宮身體）守護星狀態，評估整體元氣底蘊。\n"
                f"4. 【## 3. 潛在脆弱器官與慢性消耗預警】：\n"
                f"   - 第六宮（日常疾病/勞損）、第八宮（危機手術）、第十二宮（隱疾/心理慢性壓力/睡眠）之主星與落星。\n"
                f"   - 火星（炎熱急性）與土星（寒涼慢性積累）在本命的健康影響。\n"
                f"5. 【## 4. 身心調養與後天作息改善指南】：給出 2~3 項符合其體質特點的運動、飲食或作息建議。\n"
                f"6. 【## 💡 延伸性問題建議（您可以直接複製詢問）】：\n"
                f"   1~3. 針對該個案體能與壓力關鍵點，設計 3 個引號標註的具體深度問題。\n"
                f"   4. ✍️ 自行輸入問題。\n\n"
                f"【完整星盤與推運數據】：\n{chart_data}"
            )
        elif topic == "academics":
            return (
                f"請以精深嚴謹的古典與現代占星學理，為個案【{name}】撰寫一份條理清晰、直擊核心的【🎓 學業考運、進修出國與思維天賦專題診斷報告】。\n\n"
                f"⚠️【專題格式與解讀規範】：\n"
                f"1. 【字數與節奏】：總字數約 1,000 ~ 1,400 字，直擊學習方法與深造機遇。\n"
                f"2. 【## 1. 認知思維模式與大腦天賦優勢】：\n"
                f"   - 水星（邏輯/表達/記憶/吸收力）之星座、宮位與相位互容。\n"
                f"   - 第三宮（基礎學習/短期考試/技能證照）之吉凶配置。\n"
                f"3. 【## 2. 高等教育、國家考運與跨界遠行機遇】：\n"
                f"   - 第九宮（高等學府/深造碩博/留學出國/法律哲學）星座與守護星狀態。\n"
                f"   - 木星（學術貴人與智慧拓展）之助力。\n"
                f"4. 【## 3. 關鍵考試推運契機與高分窗口】：\n"
                f"   - 結合小限宮位、法達大運與太陽弧，判斷考運最旺盛或適合發表進修的時期。\n"
                f"5. 【## 4. 高效應試與自我精進策略】：給出 2~3 條專屬學習技巧與考場心態調整指引。\n"
                f"6. 【## 💡 延伸性問題建議（您可以直接複製詢問）】：\n"
                f"   1~3. 針對其考運或留學方向，設計 3 個引號標註的具體深度問題。\n"
                f"   4. ✍️ 自行輸入問題。\n\n"
                f"【完整星盤與推運數據】：\n{chart_data}"
            )
        elif topic == "real_estate":
            return (
                f"請以精深嚴謹的西洋古典占星學理，為個案【{name}】撰寫一份條理清晰、直擊核心的【🏡 田宅置產、居住風水與原生家庭根基專題診斷報告】。\n\n"
                f"⚠️【專題格式與解讀規範】：\n"
                f"1. 【字數與節奏】：總字數約 1,000 ~ 1,400 字，專注於不動產與安居決策。\n"
                f"2. 【## 1. 本命田宅格局與不動產守成能力】：\n"
                f"   - 第四宮（田宅宮/土地房產/晚年根基）星座與守護星狀態。\n"
                f"   - 土星（不動產自然象徵星）與月亮（居家安穩感）的配置。\n"
                f"3. 【## 2. 買房置產、自住 vs 投資適性與避坑指南】：\n"
                f"   - 買房時機是適合早年立業置產，還是中年後更穩健？\n"
                f"   - 第四宮與第二宮（財庫）、第八宮（貸款）之聯動關係，防範產權糾紛或房屋裝修瑕疵。\n"
                f"4. 【## 3. 居住環境磁場與居家風水建議】：\n"
                f"   - 適合居住於熱鬧市區、依山傍水安靜社區或具特定氣候特色的區域。\n"
                f"5. 【## 4. 近期買房/搬遷推運時間窗口】：\n"
                f"   - 次限/三限月亮引動第四宮或木星過境的吉利買屋搬遷時機。\n"
                f"6. 【## 💡 延伸性問題建議（您可以直接複製詢問）】：\n"
                f"   1~3. 針對買房、父母相處或租屋搬遷，設計 3 個引號標註的具體深度問題。\n"
                f"   4. ✍️ 自行輸入問題。\n\n"
                f"【完整星盤與推運數據】：\n{chart_data}"
            )
        else:
            return f"請針對個案【{name}】進行古典占星綜合解析。\n{chart_data}"
