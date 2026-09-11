"""
almuten_logic.py
古典占星全盤總御星 (Almuten Figuris / Lord of Geniture) 計算引擎
理論依據：Abraham Ibn Ezra《The Beginning of Wisdom》、Guido Bonatti、William Lilly (1647)

核心邏輯：
1. 計算五大發光根位 (Five Hylegical Points)：
   - 太陽 (Sun)
   - 月亮 (Moon)
   - 上升點 (Ascendant)
   - 福德點 (Lot of Fortune)
   - 產前朔望月 (Pre-natal Syzygy, SAN)
2. 針對五大根位評定七曜之五等本質尊貴得分：
   - 廟 (Domicile): +5 分
   - 旺 (Exaltation): +4 分
   - 三分 (Triplicity): +3 分
   - 界 (Term): +2 分
   - 面 (Face): +1 分
3. 後天宮位強弱加分 (Accidental House Placement)：
   - 第 1 宮 (+12), 第 10 宮 (+10), 第 4 宮 (+9), 第 7 宮 (+8)
   - 第 11 宮 (+7), 第 5 宮 (+6), 第 2 宮 (+5), 第 9 宮 (+4)
   - 第 8 宮 (+3), 第 3 宮 (+2), 第 12 宮 (+1), 第 6 宮 (+1)
4. 七曜依總分排名，得分最高者即為「全盤總御星 (Almuten Figuris)」，象徵命主的靈魂守護星與人生核心驅動力。
"""

from typing import Dict, Any, List, Optional
from flatlib import const
from flatlib.chart import Chart
from dignities_logic import DignitiesLogic

class AlmutenLogic:
    HOUSE_SCORES = {
        1: 12, 10: 10, 4: 9, 7: 8,
        11: 7, 5: 6, 2: 5, 9: 4,
        8: 3, 3: 2, 12: 1, 6: 1
    }

    CLASSICAL_PLANETS = [
        const.SUN, const.MOON, const.MERCURY, const.VENUS,
        const.MARS, const.JUPITER, const.SATURN
    ]

    def __init__(self, dignities_logic: Optional[DignitiesLogic] = None, trans_planets=None, trans_signs=None):
        self.dignities = dignities_logic or DignitiesLogic()
        self.trans_planets = trans_planets or {
            const.SUN: '太陽', const.MOON: '月亮', const.MERCURY: '水星',
            const.VENUS: '金星', const.MARS: '火星', const.JUPITER: '木星',
            const.SATURN: '土星'
        }
        self.trans_signs = trans_signs or {
            const.ARIES: '牡羊座', const.TAURUS: '金牛座', const.GEMINI: '雙子座',
            const.CANCER: '巨蟹座', const.LEO: '獅子座', const.VIRGO: '處女座',
            const.LIBRA: '天秤座', const.SCORPIO: '天蠍座', const.SAGITTARIUS: '射手座',
            const.CAPRICORN: '摩羯座', const.AQUARIUS: '水瓶座', const.PISCES: '雙魚座'
        }

    def _get_prenatal_syzygy_lon(self, sun_lon: float, moon_lon: float) -> float:
        """
        計算產前朔望月 (Pre-natal Syzygy) 黃經。
        若月亮處於漸盈 (Moon ahead of Sun < 180°)，產前為新月 (朔)；
        若月亮處於漸虧 (Moon ahead of Sun >= 180°)，產前為滿月 (望)。
        以出生當下的日月交角推算最近一次朔望的位置。
        """
        diff = (moon_lon - sun_lon) % 360
        if diff < 180:
            return (sun_lon - (diff * (0.9856 / 12.19))) % 360
        else:
            diff_from_opp = (diff - 180) % 360
            return (sun_lon - (diff_from_opp * (0.9856 / 12.19))) % 360

    def calculate_almuten_figuris(
        self,
        chart: Chart,
        houses: List[Dict[str, Any]],
        is_day: bool
    ) -> Dict[str, Any]:
        """
        計算全盤總御星 (Almuten Figuris) 與七曜得分表。
        """
        asc_lon = chart.get(const.ASC).lon
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)

        # 1. 幸運點 (Fortune)
        if is_day:
            pof_lon = (asc_lon + moon.lon - sun.lon) % 360
        else:
            pof_lon = (asc_lon + sun.lon - moon.lon) % 360

        # 2. 產前朔望月 (Syzygy)
        san_lon = self._get_prenatal_syzygy_lon(sun.lon, moon.lon)

        points = [
            ("太陽 (Sun)", sun.lon),
            ("月亮 (Moon)", moon.lon),
            ("上升點 (Ascendant)", asc_lon),
            ("福德點 (Fortune)", pof_lon),
            ("產前朔望 (Syzygy)", san_lon)
        ]

        scores = {p: 0 for p in self.CLASSICAL_PLANETS}
        breakdown = {p: {'essential': 0, 'accidental': 0, 'total': 0, 'details': []} for p in self.CLASSICAL_PLANETS}

        for pt_name, pt_lon in points:
            sign_idx = int(pt_lon // 30)
            sign_const = const.LIST_SIGNS[sign_idx]
            sign_deg = pt_lon % 30
            element = self.dignities.SIGN_ELEMENTS[sign_const]

            # 廟 (Domicile +5)
            dom_ruler = self.dignities.RULERS.get(sign_const)
            if dom_ruler in scores:
                scores[dom_ruler] += 5
                breakdown[dom_ruler]['essential'] += 5
                breakdown[dom_ruler]['details'].append(f"{pt_name} 廟主星 (+5)")

            # 旺 (Exaltation +4)
            exalt_info = self.dignities.EXALTATIONS.get(sign_const)
            if exalt_info:
                exalt_ruler = exalt_info[0]
                if exalt_ruler in scores:
                    scores[exalt_ruler] += 4
                    breakdown[exalt_ruler]['essential'] += 4
                    breakdown[exalt_ruler]['details'].append(f"{pt_name} 旺主星 (+4)")

            # 三分 (Triplicity +3)
            tri_lords = self.dignities.TRIPLICITIES.get(element, [])
            if tri_lords:
                tri_ruler = tri_lords[0] if is_day else tri_lords[1]
                if tri_ruler in scores:
                    scores[tri_ruler] += 3
                    breakdown[tri_ruler]['essential'] += 3
                    breakdown[tri_ruler]['details'].append(f"{pt_name} 三分主星 (+3)")

            # 界 (Term +2)
            terms = self.dignities.TERMS.get(sign_const, [])
            for max_deg, t_ruler in terms:
                if sign_deg < max_deg:
                    if t_ruler in scores:
                        scores[t_ruler] += 2
                        breakdown[t_ruler]['essential'] += 2
                        breakdown[t_ruler]['details'].append(f"{pt_name} 界主星 (+2)")
                    break

            # 面 (Face +1)
            faces = self.dignities.FACES.get(sign_const, [])
            face_idx = int(sign_deg // 10)
            if face_idx < len(faces):
                f_ruler = faces[face_idx]
                if f_ruler in scores:
                    scores[f_ruler] += 1
                    breakdown[f_ruler]['essential'] += 1
                    breakdown[f_ruler]['details'].append(f"{pt_name} 面主星 (+1)")

        # 後天宮位得分
        h1_lon = houses[0]['lon']
        for p_id in self.CLASSICAL_PLANETS:
            p_obj = chart.get(p_id)
            p_house = int(((p_obj.lon - h1_lon) % 360) // 30) + 1
            h_score = self.HOUSE_SCORES.get(p_house, 1)
            scores[p_id] += h_score
            breakdown[p_id]['accidental'] += h_score
            breakdown[p_id]['details'].append(f"落第 {p_house} 宮 (+{h_score})")
            breakdown[p_id]['total'] = scores[p_id]

        sorted_planets = sorted(self.CLASSICAL_PLANETS, key=lambda p: scores[p], reverse=True)
        almuten_id = sorted_planets[0]
        almuten_score = scores[almuten_id]
        almuten_name = self.trans_planets.get(almuten_id, almuten_id)

        alm_obj = chart.get(almuten_id)
        alm_sign_idx = int(alm_obj.lon // 30)
        alm_sign = self.trans_signs.get(const.LIST_SIGNS[alm_sign_idx], "")
        alm_deg = int(alm_obj.lon % 30)
        alm_min = int(((alm_obj.lon % 30) - alm_deg) * 60)
        alm_house = int(((alm_obj.lon - h1_lon) % 360) // 30) + 1

        ranking = []
        for rank, p_id in enumerate(sorted_planets, start=1):
            ranking.append({
                'rank': rank,
                'planet_id': p_id,
                'planet_name': self.trans_planets.get(p_id, p_id),
                'total_score': scores[p_id],
                'essential_score': breakdown[p_id]['essential'],
                'accidental_score': breakdown[p_id]['accidental'],
                'details': breakdown[p_id]['details']
            })

        significance_map = {
            const.SUN: "👑 權威榮耀、自我實現、精神光源、追求頂峰與獨立人格",
            const.MOON: "🌊 直覺洞察、公眾共鳴、情感滋養、生活適應與世俗人緣",
            const.MERCURY: "🧠 卓越智識、商業談判、分析批判、精密邏輯與多線運作",
            const.VENUS: "🌸 美感和諧、人際魅力、社交資源、藝術創造與價值整合",
            const.MARS: "⚔️ 勇武開創、突破重圍、決策魄力、抗壓競爭與行動戰力",
            const.JUPITER: "🏛️ 宏觀願景、財富擴張、哲學智慧、貴人庇佑與精神導引",
            const.SATURN: "⏳ 沉穩架構、歷史沉澱、專注耐力、深謀遠慮與長線根基"
        }

        return {
            'almuten_id': almuten_id,
            'almuten_name': almuten_name,
            'almuten_score': almuten_score,
            'position': f"{alm_sign} {alm_deg}°{alm_min:02d}'",
            'house': f"第 {alm_house} 宮",
            'spiritual_significance': significance_map.get(almuten_id, "綜合守護"),
            'ranking': ranking,
            'summary': f"本命盤全盤總御星為【{almuten_name}】（總得分 {almuten_score} 分，落入 {alm_sign} 第 {alm_house} 宮），代表盤主的核心天賦在於 {significance_map.get(almuten_id, '')}。"
        }
