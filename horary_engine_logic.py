#!/usr/bin/env python3
"""
Horary Engine Logic (古典占星卜卦核心演算法模組)
依據 William Lilly 1647《Christian Astrology》Book II 與第一性原理實作：
1. 問題意圖分類與目標宮位 (Quesited House) 自動鎖定
2. 天體成事五大路徑 (Perfection of Matter: Direct, Translation, Collection, Reception, Prohibition)
3. 應期時鐘 (Timing Estimation: 剩餘度數差與星座宮位速度矩陣)
4. 月亮流動全景 (Moon's Separating & Applying Aspects)
"""

from typing import Dict, Any, List, Optional
from flatlib import const
from dignities_logic import DignitiesLogic

class HoraryEngineLogic:
    """古典占星卜卦專業演算法引擎"""

    # Classical Planetary Orbs (William Lilly CA 1647)
    PLANET_ORBS = {
        const.SUN: 15.0,
        const.MOON: 12.0,
        const.MERCURY: 7.0,
        const.VENUS: 7.0,
        const.MARS: 8.0,
        const.JUPITER: 9.0,
        const.SATURN: 9.0,
    }

    # Average Daily Speeds (degrees per day) for relative velocity
    PLANET_AVERAGE_SPEEDS = {
        const.MOON: 13.176,
        const.MERCURY: 1.20,
        const.VENUS: 1.00,
        const.SUN: 0.9856,
        const.MARS: 0.524,
        const.JUPITER: 0.083,
        const.SATURN: 0.033,
    }

    MAJOR_ASPECTS = {
        0: '合相 (Conjunction)',
        60: '六分相 (Sextile)',
        90: '四分相 (Square)',
        120: '三分相 (Trine)',
        180: '對分相 (Opposition)',
    }

    CARDINAL_SIGNS = {const.ARIES, const.CANCER, const.LIBRA, const.CAPRICORN}
    FIXED_SIGNS = {const.TAURUS, const.LEO, const.SCORPIO, const.AQUARIUS}
    MUTABLE_SIGNS = {const.GEMINI, const.VIRGO, const.SAGITTARIUS, const.PISCES}

    ANGULAR_HOUSES = {1, 4, 7, 10}
    SUCCEDENT_HOUSES = {2, 5, 8, 11}
    CADENT_HOUSES = {3, 6, 9, 12}

    def __init__(self, trans_signs: Optional[Dict[str, str]] = None, trans_planets: Optional[Dict[str, str]] = None):
        self.dignities = DignitiesLogic()
        self.trans_signs = trans_signs or {
            const.ARIES: '牡羊座', const.TAURUS: '金牛座', const.GEMINI: '雙子座',
            const.CANCER: '巨蟹座', const.LEO: '獅子座', const.VIRGO: '處女座',
            const.LIBRA: '天秤座', const.SCORPIO: '天蠍座', const.SAGITTARIUS: '射手座',
            const.CAPRICORN: '摩羯座', const.AQUARIUS: '水瓶座', const.PISCES: '雙魚座'
        }
        self.trans_planets = trans_planets or {
            const.SUN: '太陽', const.MOON: '月亮', const.MERCURY: '水星',
            const.VENUS: '金星', const.MARS: '火星', const.JUPITER: '木星',
            const.SATURN: '土星'
        }
        self.rev_planets = {v: k for k, v in self.trans_planets.items()}


    # -------------------------------------------------------------
    # 1. 問題意圖與目標宮位 (Quesited House) 自動分類
    # -------------------------------------------------------------
    def classify_quesited_house(self, question: str) -> Dict[str, Any]:
        """
        根據問卜者提問內容，自動對焦主要所問事項所屬之古典宮位與關鍵象徵。
        """
        q = question.lower() if question else ""

        rel_keywords = (
            "感情", "戀愛", "婚姻", "伴侶", "老公", "老婆", "男友", "女友",
            "對象", "曖昧", "復合", "分手", "桃花", "喜歡我", "在乎我",
            "合作", "合夥", "簽約", "合約", "合約談成", "生意夥伴", "客戶",
            "打官司", "官司", "訴訟", "對手", "競爭對手"
        )
        career_keywords = (
            "工作", "事業", "求職", "錄取", "面試", "新工作", "升遷", "升職",
            "轉正", "創業", "開公司", "職涯", "主管", "老闆", "官位", "名譽",
            "考上", "公職", "審查", "官方審批"
        )
        wealth_2h_keywords = (
            "薪水", "加薪", "待遇", "正財", "收入", "錢包", "存款",
            "值不值錢", "能不能賣掉", "開價"
        )
        wealth_8h_keywords = (
            "投資", "股票", "虛擬幣", "偏財", "借錢", "借貸", "貸款", "還錢",
            "融資", "保險理賠", "遺產", "債務", "賠錢", "賺錢"
        )
        home_4h_keywords = (
            "買房", "賣房", "房子", "房屋", "租屋", "租房", "房東", "搬家",
            "不動產", "家庭", "父母", "父親", "失物", "遺失物", "遺失", "找回",
            "丟了", "掉了", "不見了", "不見", "皮夾", "找得回", "找不找得到"
        )
        child_5h_keywords = (
            "懷孕", "小孩", "孩子", "生男生女", "受孕", "子女", "彩券",
            "中獎", "賭博", "投機"
        )
        health_6h_keywords = (
            "生病", "疾病", "健康", "手術", "看醫生", "康復", "病因", "診斷",
            "寵物", "貓", "狗", "下屬", "部屬", "員工"
        )
        travel_9h_keywords = (
            "留學", "出國", "簽證", "移民", "旅行", "出差", "研究所",
            "考研究所", "博士", "信仰", "出版", "寫書"
        )
        friend_11h_keywords = (
            "願望", "能實現嗎", "希望", "貴人", "朋友", "人脈", "社群",
            "團隊支持", "合唱團", "協會"
        )
        comm_3h_keywords = (
            "兄弟", "姊妹", "鄰居", "駕照", "買車", "開車", "短程", "溝通", "通訊"
        )

        matched_house = 7
        matched_name = "第 7 宮 (婚姻伴侶 / 合作交易 / 公開對手)"
        topic_tag = "一對一關係與契約"
        desc = "問事涉及感情關係、對象心態、合夥合作、談判交易或訴訟對造。"
        matched_kw = "通用議題"

        groups = [
            (career_keywords, 10, "第 10 宮 (事業功名 / 求職升遷 / 官方成就)", "事業工作與名望", "問事涉及求職面試錄取、事業升遷、創業開展或主管長官審批。"),
            (wealth_8h_keywords, 8, "第 8 宮 (偏財投資 / 借貸債務 / 共有資源)", "偏財投資與融資", "問事涉及投資投機、股票獲利、借貸融資或他人合夥資產。"),
            (wealth_2h_keywords, 2, "第 2 宮 (正財薪資 / 個人資產 / 物質價值)", "正財薪資與動產", "問事涉及薪資報酬、加薪調薪、買賣利潤或個人財物。"),
            (home_4h_keywords, 4, "第 4 宮 (不動產房產 / 家庭父母 / 終局落點)", "房地產與家庭", "問事涉及購屋租屋、房屋買賣、搬遷、家庭長輩或失物所在地點。"),
            (health_6h_keywords, 6, "第 6 宮 (疾病健康 / 日常工作 / 寵物員工)", "健康疾病與勞務", "問事涉及疾病康復、醫療手術、日常繁雜勞動或寵物健康。"),
            (child_5h_keywords, 5, "第 5 宮 (懷孕生育 / 子女後代 / 投機娛樂)", "懷孕子女與投機", "問事涉及懷孕受孕、子女教養、投機遊戲或創作娛樂。"),
            (travel_9h_keywords, 9, "第 9 宮 (出國留學 / 長途遠行 / 高階學術)", "出國深造與遠行", "問事涉及海外出國、留學簽證、遠途旅行或高等學術論文。"),
            (friend_11h_keywords, 11, "第 11 宮 (願望達成 / 朋友社群 / 貴人提攜)", "願望與貴人人脈", "問事涉及個人願望能否實現、貴人支持或社群組織。"),
            (comm_3h_keywords, 3, "第 3 宮 (短程交通 / 考試溝通 / 兄弟手足)", "日常溝通與短行", "問事涉及短途出差、考駕照、通訊合約或兄弟親屬。"),
            (rel_keywords, 7, "第 7 宮 (婚姻伴侶 / 合作交易 / 公開對手)", "一對一關係與契約", "問事涉及感情伴侶、婚姻復合、合作商業夥伴或官司訴訟對手。")
        ]

        for kw_list, h_num, h_name, t_tag, h_desc in groups:
            for k in kw_list:
                if k in q:
                    matched_house = h_num
                    matched_name = h_name
                    topic_tag = t_tag
                    desc = h_desc
                    matched_kw = k
                    break
            if matched_kw != "通用議題":
                break

        return {
            "quesited_house": matched_house,
            "house_name": matched_name,
            "house_meaning": topic_tag,
            "topic_tag": topic_tag,
            "matched_keyword": matched_kw,
            "description": desc,
            "question": question
        }

    # -------------------------------------------------------------
    # 2. 天體幾何輔助計算 (入相位判定與度數差)
    # -------------------------------------------------------------
    def calculate_aspect_details(self, p1, p2) -> Optional[Dict[str, Any]]:
        """
        精算兩星體之古典交角、目前誤差、是否入相位 (Applying) 以及精確成相剩餘度數差 (delta_deg)。
        """
        diff = abs(p1.lon - p2.lon)
        if diff > 180:
            diff = 360 - diff

        max_orb = (self.PLANET_ORBS.get(p1.id, 8.0) + self.PLANET_ORBS.get(p2.id, 8.0)) / 2.0

        for angle, aspect_name in self.MAJOR_ASPECTS.items():
            diff_from_aspect = abs(diff - angle)
            if diff_from_aspect <= max_orb:
                v1 = getattr(p1, 'lonspeed', None)
                v2 = getattr(p2, 'lonspeed', None)
                if v1 is None: v1 = self.PLANET_AVERAGE_SPEEDS.get(p1.id, 1.0)
                if v2 is None: v2 = self.PLANET_AVERAGE_SPEEDS.get(p2.id, 0.5)

                if abs(v1) > abs(v2):
                    faster, slower = p1, p2
                    vf, vs = v1, v2
                else:
                    faster, slower = p2, p1
                    vf, vs = v2, v1

                step = 0.01
                f_next = faster.lon + vf * step
                s_next = slower.lon + vs * step
                diff_next_raw = abs(f_next - s_next)
                if diff_next_raw > 180:
                    diff_next_raw = 360 - diff_next_raw
                diff_next = abs(diff_next_raw - angle)

                is_applying = diff_next < diff_from_aspect

                rel_speed = abs(vf - vs)
                if rel_speed <= 0.001:
                    rel_speed = 0.001

                delta_deg = round(diff_from_aspect, 2)

                return {
                    "p1_id": p1.id,
                    "p2_id": p2.id,
                    "faster_id": faster.id,
                    "slower_id": slower.id,
                    "aspect_angle": angle,
                    "aspect_name": aspect_name,
                    "orb": delta_deg,
                    "is_applying": is_applying,
                    "status_str": "入相位 (Applying)" if is_applying else "離相位 (Separating)",
                    "delta_degrees": delta_deg,
                    "rel_speed": round(rel_speed, 3)
                }
        return None

    # -------------------------------------------------------------
    # 3. 古典成事五大路徑 (Perfection of Matter) 硬核運算
    # -------------------------------------------------------------
    def analyze_perfection(
        self,
        chart,
        houses: List[Dict[str, Any]],
        quesited_house_num: int,
        planets_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        全面分析 William Lilly 1647 古典成事五大路徑：
        1. 直接入相位 (Direct Application)
        2. 光線傳遞 (Translation of Light)
        3. 光線收集 (Collection of Light)
        4. 古典互容 (Mutual Reception)
        5. 中途阻礙與截胡 (Prohibition & Refranation)
        """
        h_map = {h.get("id"): h for h in houses if isinstance(h, dict)}
        lord_1_raw = h_map.get(1, {}).get("ruler_id") or h_map.get(1, {}).get("ruler", const.MARS)
        lord_q_raw = h_map.get(quesited_house_num, {}).get("ruler_id") or h_map.get(quesited_house_num, {}).get("ruler", const.VENUS)

        lord_1_id = self.rev_planets.get(lord_1_raw, lord_1_raw)
        lord_q_id = self.rev_planets.get(lord_q_raw, lord_q_raw)

        p_objects = {}
        for p_id in [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN]:
            try:
                p_objects[p_id] = chart.get(p_id)
            except Exception:
                pass

        lord_1 = p_objects.get(lord_1_id)
        lord_q = p_objects.get(lord_q_id)
        moon = p_objects.get(const.MOON)

        lord_1_name = self.trans_planets.get(lord_1_id, lord_1_id)
        lord_q_name = self.trans_planets.get(lord_q_id, lord_q_id)

        same_ruler = (lord_1_id == lord_q_id)

        # 1. 直接入相位
        direct_perfections = []
        if not same_ruler and lord_1 and lord_q:
            asp_1_q = self.calculate_aspect_details(lord_1, lord_q)
            if asp_1_q and asp_1_q["is_applying"]:
                direct_perfections.append({
                    "type": "Lord 1 ➔ Lord Q",
                    "source": lord_1_name,
                    "target": lord_q_name,
                    "aspect": asp_1_q["aspect_name"],
                    "angle": asp_1_q["aspect_angle"],
                    "orb": asp_1_q["orb"],
                    "delta_deg": asp_1_q["delta_degrees"],
                    "faster_id": asp_1_q["faster_id"],
                    "slower_id": asp_1_q["slower_id"]
                })

        if moon and lord_q and (const.MOON != lord_q_id):
            asp_moon_q = self.calculate_aspect_details(moon, lord_q)
            if asp_moon_q and asp_moon_q["is_applying"]:
                direct_perfections.append({
                    "type": "Moon ➔ Lord Q",
                    "source": "月亮",
                    "target": lord_q_name,
                    "aspect": asp_moon_q["aspect_name"],
                    "angle": asp_moon_q["aspect_angle"],
                    "orb": asp_moon_q["orb"],
                    "delta_deg": asp_moon_q["delta_degrees"],
                    "faster_id": asp_moon_q["faster_id"],
                    "slower_id": asp_moon_q["slower_id"]
                })

        # 2. 光線傳遞 (Translation of Light)
        translation_of_light = []
        for trans_p_id, trans_p in p_objects.items():
            if trans_p_id in (lord_1_id, lord_q_id):
                continue
            if lord_1 and lord_q:
                asp_to_1 = self.calculate_aspect_details(trans_p, lord_1)
                asp_to_q = self.calculate_aspect_details(trans_p, lord_q)

                if asp_to_1 and not asp_to_1["is_applying"] and asp_to_q and asp_to_q["is_applying"]:
                    trans_name = self.trans_planets.get(trans_p_id, trans_p_id)
                    translation_of_light.append({
                        "translator": trans_name,
                        "translator_id": trans_p_id,
                        "direction": f"{trans_name} 離開 {lord_1_name} ({asp_to_1['aspect_name']}) ➔ 奔向 {lord_q_name} ({asp_to_q['aspect_name']})",
                        "applying_aspect": asp_to_q["aspect_name"],
                        "orb": asp_to_q["orb"],
                        "delta_deg": asp_to_q["delta_degrees"],
                        "meaning": f"【貴人/中間人牽線促成】：象徵有第三方媒介（{trans_name}）在問卜者與所問事項間撮合斡旋，可獲圓滿解決。"
                    })
                elif asp_to_q and not asp_to_q["is_applying"] and asp_to_1 and asp_to_1["is_applying"]:
                    trans_name = self.trans_planets.get(trans_p_id, trans_p_id)
                    translation_of_light.append({
                        "translator": trans_name,
                        "translator_id": trans_p_id,
                        "direction": f"{trans_name} 離開 {lord_q_name} ({asp_to_q['aspect_name']}) ➔ 奔向 {lord_1_name} ({asp_to_1['aspect_name']})",
                        "applying_aspect": asp_to_1["aspect_name"],
                        "orb": asp_to_1["orb"],
                        "delta_deg": asp_to_1["delta_degrees"],
                        "meaning": f"【回饋牽線促成】：所問事項之資源或消息透過第三方（{trans_name}）傳遞帶回給問卜者。"
                    })

        # 3. 光線收集 (Collection of Light)
        collection_of_light = []
        if not direct_perfections and lord_1 and lord_q and not same_ruler:
            for col_id, col_p in p_objects.items():
                if col_id in (lord_1_id, lord_q_id, const.MOON):
                    continue
                v_col = getattr(col_p, 'lonspeed', self.PLANET_AVERAGE_SPEEDS.get(col_id, 0.05))
                v_1 = getattr(lord_1, 'lonspeed', self.PLANET_AVERAGE_SPEEDS.get(lord_1_id, 0.5))
                v_q = getattr(lord_q, 'lonspeed', self.PLANET_AVERAGE_SPEEDS.get(lord_q_id, 0.5))

                if abs(v_col) <= abs(v_1) and abs(v_col) <= abs(v_q):
                    asp_1_col = self.calculate_aspect_details(lord_1, col_p)
                    asp_q_col = self.calculate_aspect_details(lord_q, col_p)

                    if asp_1_col and asp_1_col["is_applying"] and asp_q_col and asp_q_col["is_applying"]:
                        col_name = self.trans_planets.get(col_id, col_id)
                        collection_of_light.append({
                            "collector": col_name,
                            "collector_id": col_id,
                            "aspect_1": asp_1_col["aspect_name"],
                            "aspect_q": asp_q_col["aspect_name"],
                            "orb_1": asp_1_col["orb"],
                            "orb_q": asp_q_col["orb"],
                            "delta_deg": max(asp_1_col["delta_degrees"], asp_q_col["delta_degrees"]),
                            "meaning": f"【權威/法官仲裁成事】：雙方無直接聯繫，但同時奔向更具權威之第三方大老、長輩或仲裁機構（{col_name}），藉其力量成事。"
                        })

        # 4. 古典互容 (Mutual Reception)
        reception_details = []
        if lord_1 and lord_q and not same_ruler:
            r_str = self.check_classical_reception(lord_1_id, lord_1.lon, lord_q_id, lord_q.lon)
            if r_str:
                reception_details.append({
                    "reception_type": r_str,
                    "meaning": "【互容互信】：問卜者與所問事項守護星彼此互有尊貴好感，代表雙方願意各退一步、共同促成和解或協議。"
                })

        # 5. 中途阻礙與截胡 (Prohibition & Refranation)
        prohibitions = []
        refranations = []

        for cand in [lord_1, lord_q]:
            if cand:
                speed = getattr(cand, 'lonspeed', 1.0)
                if speed < 0:
                    cand_name = self.trans_planets.get(cand.id, cand.id)
                    refranations.append({
                        "planet": cand_name,
                        "meaning": f"【徵象星逆行反悔】：{cand_name} 目前處於逆行狀態，象徵該方可能臨陣退縮、猶豫變卦或進度大幅拖延。"
                    })

        if direct_perfections:
            primary_perf = direct_perfections[0]
            target_orb = primary_perf["delta_deg"]
            src_id = primary_perf.get("faster_id")
            src_p = p_objects.get(src_id)

            if src_p:
                for other_id, other_p in p_objects.items():
                    if other_id in (lord_1_id, lord_q_id, src_id):
                        continue
                    asp_intervene = self.calculate_aspect_details(src_p, other_p)
                    if asp_intervene and asp_intervene["is_applying"]:
                        if asp_intervene["delta_degrees"] < target_orb:
                            other_name = self.trans_planets.get(other_id, other_id)
                            prohibitions.append({
                                "intervener": other_name,
                                "aspect": asp_intervene["aspect_name"],
                                "intervene_orb": asp_intervene["delta_degrees"],
                                "target_orb": target_orb,
                                "meaning": f"【半路截胡/突發阻礙 (Prohibition)】：在與目標成相前，{other_name} 將在 {asp_intervene['delta_degrees']}° 處搶先與推進星交角，恐有程咬金介入或突發事件打斷！"
                            })

        # 綜合終局裁決
        if prohibitions:
            overall_verdict = "⚠️ 阻礙截胡 (PROHIBITED)"
            verdict_desc = "雖有成相趨勢，但中途有第三方強行介入干擾，易功虧一簣或橫生波折。"
            is_perfected = False
        elif refranations and not direct_perfections:
            overall_verdict = "⚠️ 逆行反悔 (REFRANATION)"
            verdict_desc = "主徵象星逆行後退，象徵某方態度動搖或反悔變卦，需防破局。"
            is_perfected = False
        elif direct_perfections:
            p_aspect = direct_perfections[0]["aspect"]
            if "四分" in p_aspect or "對分" in p_aspect:
                overall_verdict = "⚡ 歷經考驗而成事 (PERFECTED WITH HARDSHIP)"
                verdict_desc = f"主徵象星以【{p_aspect}】入相位，事情最終可成，但必須克服劇烈壓力、代價或妥協拆夥。"
            else:
                overall_verdict = "🎉 順利成事 (DIRECT PERFECTION)"
                verdict_desc = f"主徵象星以吉相【{p_aspect}】直接入相位，事態水到渠成，按部就班可順利達成目標！"
            is_perfected = True
        elif translation_of_light:
            overall_verdict = "🤝 貴人牽線成事 (TRANSLATION OF LIGHT)"
            verdict_desc = f"雙方無直接吉相，但有【{translation_of_light[0]['translator']}】從中傳遞光線牽線，仰賴第三方媒介促成！"
            is_perfected = True
        elif collection_of_light:
            overall_verdict = "⚖️ 仲裁協調成事 (COLLECTION OF LIGHT)"
            verdict_desc = f"雙方共同奔向【{collection_of_light[0]['collector']}】，透過權威第三方或法律機構裁決協調成事！"
            is_perfected = True
        elif reception_details:
            overall_verdict = "🤝 互容妥協成事 (MUTUAL RECEPTION)"
            verdict_desc = "雙方雖無緊密入相位，但有強烈互容好感，彼此願意退讓妥協，事情仍有希望推進。"
            is_perfected = True
        else:
            overall_verdict = "❌ 無成事相位 (NO PERFECTION)"
            verdict_desc = "問卜者徵象星與所問事項守護星既無直接入相位，亦無光線傳遞或收集，事態缺乏推動力，恐無實質進展。"
            is_perfected = False

        return {
            "quesited_house_num": quesited_house_num,
            "lord_1_id": lord_1_id,
            "lord_1_name": lord_1_name,
            "lord_q_id": lord_q_id,
            "lord_q_name": lord_q_name,
            "same_ruler": same_ruler,
            "is_perfected": is_perfected,
            "overall_verdict": overall_verdict,
            "verdict_desc": verdict_desc,
            "direct_perfections": direct_perfections,
            "translation_of_light": translation_of_light,
            "collection_of_light": collection_of_light,
            "reception_details": reception_details,
            "prohibitions": prohibitions,
            "refranations": refranations,
        }

    # -------------------------------------------------------------
    # 4. 古典應期時鐘 (Timing Estimation)
    # -------------------------------------------------------------
    def calculate_timing(
        self,
        chart,
        houses: List[Dict[str, Any]],
        perfection_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根據主要成事入相位之剩餘度數差 (delta_deg)，結合推進星之星座與宮位速度屬性，精算具體現實應期。
        """
        delta_deg = 0.0
        active_planet_id = const.MOON

        direct = perfection_analysis.get("direct_perfections", [])
        trans = perfection_analysis.get("translation_of_light", [])
        col = perfection_analysis.get("collection_of_light", [])

        if direct:
            delta_deg = direct[0]["delta_deg"]
            active_planet_id = direct[0].get("faster_id", const.MOON)
        elif trans:
            delta_deg = trans[0]["delta_deg"]
            active_planet_id = trans[0].get("translator_id", const.MOON)
        elif col:
            delta_deg = col[0]["delta_deg"]
            active_planet_id = perfection_analysis.get("lord_1_id", const.MOON)
        else:
            moon_flow = self.get_moon_flow(chart)
            next_asp = moon_flow.get("next_applying_aspect")
            if next_asp:
                delta_deg = next_asp.get("orb", 3.0)
            else:
                delta_deg = 3.0

        delta_deg = max(0.1, float(delta_deg))

        try:
            active_planet = chart.get(active_planet_id)
            sign_const = active_planet.sign
            h_num = self.get_planet_house_num(active_planet.lon, houses)
        except Exception:
            sign_const = const.ARIES
            h_num = 1

        if sign_const in self.CARDINAL_SIGNS:
            sign_speed = "快 (開創星座 Cardinal)"
            sign_score = 1
        elif sign_const in self.MUTABLE_SIGNS:
            sign_speed = "中 (變動星座 Mutable)"
            sign_score = 2
        else:
            sign_speed = "慢 (固定星座 Fixed)"
            sign_score = 3

        if h_num in self.ANGULAR_HOUSES:
            house_speed = f"最快 (四正角宮 第 {h_num} 宮)"
            house_score = 1
        elif h_num in self.SUCCEDENT_HOUSES:
            house_speed = f"中等 (續宮 第 {h_num} 宮)"
            house_score = 2
        else:
            house_speed = f"緩慢/延遲 (落宮 第 {h_num} 宮)"
            house_score = 3

        combined_score = sign_score + house_score

        num_units = round(delta_deg, 1)
        if num_units < 1.0:
            num_units = round(delta_deg * 2, 1)

        if combined_score <= 2:
            time_unit = "天 (Days)"
            timeframe_str = f"約 {max(1, int(round(num_units)))} ~ {int(round(num_units * 1.5))} 天內"
            pacing_desc = "極為迅捷，天象星動毫無阻滯，預計數日內即見真章。"
        elif combined_score == 3:
            time_unit = "週 (Weeks)"
            timeframe_str = f"約 {max(1, int(round(num_units)))} ~ {int(round(num_units * 1.5))} 週內"
            pacing_desc = "節奏緊湊明快，事情在未來數週之內將有明確推進或階段性結果。"
        elif combined_score == 4:
            time_unit = "月 (Months)"
            timeframe_str = f"約 {max(1, int(round(num_units)))} ~ {int(round(num_units * 1.5))} 個月內"
            pacing_desc = "按部就班發展，需歷經一至數個月之週期醞釀與手續推進。"
        elif combined_score == 5:
            time_unit = "數月至半年 (Months to Year)"
            timeframe_str = f"約 {max(2, int(round(num_units * 1.5)))} ~ {int(round(num_units * 3))} 個月"
            pacing_desc = "進度相對緩慢，牽涉較多客觀體制、法規或多方磋商，需保持耐心。"
        else:
            time_unit = "年或大幅延宕 (Prolonged / Years)"
            timeframe_str = "超過 1 年或極為漫長之拉鋸"
            pacing_desc = "星氣沉滯落入深層僵局，短期內恐難以定案，建議做好長期抗戰準備。"

        active_planet_name = self.trans_planets.get(active_planet_id, active_planet_id)

        return {
            "delta_degrees": round(delta_deg, 2),
            "active_planet": active_planet_name,
            "active_sign": self.trans_signs.get(sign_const, sign_const),
            "sign_speed": sign_speed,
            "house_speed": house_speed,
            "combined_score": combined_score,
            "time_unit": time_unit,
            "estimated_timeframe": timeframe_str,
            "pacing_description": pacing_desc
        }

    # -------------------------------------------------------------
    # 5. 月亮流動全景 (Moon's Separating & Applying Aspects)
    # -------------------------------------------------------------
    def get_moon_flow(self, chart) -> Dict[str, Any]:
        """
        計算月亮最近剛脫離的相位 (代表事件起因/過去狀態)
        以及即將進入的次一主要相位 (代表即刻將發生的事態演變)。
        """
        try:
            moon = chart.get(const.MOON)
        except Exception:
            return {}

        planets_to_check = [const.SUN, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN]

        separating_aspects = []
        applying_aspects = []

        for p_id in planets_to_check:
            try:
                p = chart.get(p_id)
                asp = self.calculate_aspect_details(moon, p)
                if asp:
                    target_name = self.trans_planets.get(p_id, p_id)
                    asp_summary = {
                        "target_planet": target_name,
                        "aspect_name": asp["aspect_name"],
                        "orb": asp["orb"],
                        "is_applying": asp["is_applying"]
                    }
                    if asp["is_applying"]:
                        applying_aspects.append(asp_summary)
                    else:
                        separating_aspects.append(asp_summary)
            except Exception:
                pass

        separating_aspects.sort(key=lambda x: x["orb"])
        applying_aspects.sort(key=lambda x: x["orb"])

        last_sep = separating_aspects[0] if separating_aspects else None
        next_app = applying_aspects[0] if applying_aspects else None

        is_voc = (len(applying_aspects) == 0)

        return {
            "moon_sign": self.trans_signs.get(moon.sign, moon.sign),
            "moon_deg_str": f"{int(moon.lon % 30)}°{int((moon.lon % 1) * 60):02d}'",
            "is_voc": is_voc,
            "last_separating_aspect": last_sep,
            "next_applying_aspect": next_app,
            "all_applying": applying_aspects,
            "all_separating": separating_aspects
        }

    # -------------------------------------------------------------
    # 輔助方法：互容檢查與落宮定位
    # -------------------------------------------------------------
    def check_classical_reception(self, p1_id, p1_lon, p2_id, p2_lon) -> str:
        s1_const = const.LIST_SIGNS[int(p1_lon // 30)]
        s2_const = const.LIST_SIGNS[int(p2_lon // 30)]

        p1_in_p2_dom = self.dignities.RULERS.get(s1_const) == p2_id
        p1_in_p2_exalt = self.dignities.EXALTATIONS.get(s1_const, (None,))[0] == p2_id

        p2_in_p1_dom = self.dignities.RULERS.get(s2_const) == p1_id
        p2_in_p1_exalt = self.dignities.EXALTATIONS.get(s2_const, (None,))[0] == p1_id

        if (p1_in_p2_dom or p1_in_p2_exalt) and (p2_in_p1_dom or p2_in_p1_exalt):
            return "雙向互容 (Mutual Reception - 廟旺互換)"
        elif p1_in_p2_dom or p1_in_p2_exalt:
            return f"{self.trans_planets.get(p2_id, p2_id)} 接納 {self.trans_planets.get(p1_id, p1_id)}"
        elif p2_in_p1_dom or p2_in_p1_exalt:
            return f"{self.trans_planets.get(p1_id, p1_id)} 接納 {self.trans_planets.get(p2_id, p2_id)}"
        return ""

    def get_planet_house_num(self, lon: float, houses: List[Dict[str, Any]]) -> int:
        for h in houses:
            if isinstance(h, dict):
                start = h.get("lon", 0.0)
                end = (start + 30.0) % 360.0
                if start < end:
                    if start <= lon < end:
                        return h.get("id", 1)
                else:
                    if lon >= start or lon < end:
                        return h.get("id", 1)
        return 1
