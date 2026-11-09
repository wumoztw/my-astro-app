"""
classical_natal_core_logic.py
古典本命核心：四液氣質、生命主/壽主星/產前朔望、十二宮飛星與定位星鏈、七曜尊貴全表。
理論依據：William Lilly《Christian Astrology》Book 3、Dorian Greenbaum《Temperament》、Ptolemy《Tetrabiblos》。
"""
from typing import Dict, Any, List, Optional
from flatlib import const
from flatlib.chart import Chart

CLASSICAL = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN]

# (hot/cold, dry/moist, humor)
HUMOR_OF = {
    ('hot', 'dry'): 'choleric', ('hot', 'moist'): 'sanguine',
    ('cold', 'dry'): 'melancholic', ('cold', 'moist'): 'phlegmatic',
}
HUMOR_LABEL = {
    'choleric': '膽汁質 (Choleric - 熱乾火象)', 'sanguine': '多血質 (Sanguine - 熱濕風象)',
    'melancholic': '抑鬱質 (Melancholic - 冷乾土象)', 'phlegmatic': '黏液質 (Phlegmatic - 冷濕水象)',
}
HUMOR_TRAITS = {
    'choleric': '主動、果敢、急躁、野心旺盛', 'sanguine': '樂觀、社交、慷慨、情緒起伏快',
    'melancholic': '審慎、堅毅、內省、傾向憂慮', 'phlegmatic': '沉靜、敏感、適應力強、傾向被動',
}
ELEMENT_QUAL = {'Fire': ('hot', 'dry'), 'Earth': ('cold', 'dry'), 'Air': ('hot', 'moist'), 'Water': ('cold', 'moist')}
PLANET_QUAL = {
    const.SUN: ('hot', 'dry'), const.MOON: ('cold', 'moist'), const.MERCURY: ('cold', 'dry'),
    const.VENUS: ('cold', 'moist'), const.MARS: ('hot', 'dry'), const.JUPITER: ('hot', 'moist'),
    const.SATURN: ('cold', 'dry'),
}
QUARTER_QUAL = [('hot', 'moist'), ('hot', 'dry'), ('cold', 'dry'), ('cold', 'moist')]

# Lilly: 小年 / 中年 / 大年
PLANET_YEARS = {
    const.SATURN: (30, 43.5, 57), const.JUPITER: (12, 45.5, 79), const.MARS: (15, 40.5, 66),
    const.SUN: (19, 69.5, 120), const.VENUS: (8, 45, 82), const.MERCURY: (20, 48, 76),
    const.MOON: (25, 66.5, 108),
}
HYLEGICAL_HOUSES = [1, 10, 11, 7, 9]
PTOLEMAIC = [0, 60, 90, 120, 180]
ASPECT_ORB = 9.0

HOUSE_THEME = {
    1: '自我、身體與生命意志', 2: '財富、資源與自我價值', 3: '兄弟、溝通與短途旅行',
    4: '家庭、根基與晚年', 5: '子女、創造與愉悅', 6: '疾病、工作與僕役',
    7: '婚姻、伴侶與公開對手', 8: '死亡、共有資源與危機', 9: '信仰、遠行與高等學識',
    10: '事業、名望與公眾舞台', 11: '友誼、貴人與願望', 12: '隱藏敵人、孤立與靈性修煉',
}
HOUSE_NAMES = {1: '第一宮 (命宮)', 2: '第二宮', 3: '第三宮', 4: '第四宮', 5: '第五宮', 6: '第六宮',
               7: '第七宮', 8: '第八宮', 9: '第九宮', 10: '第十宮', 11: '第十一宮', 12: '第十二宮'}
FLY_OVERRIDES = {
    (1, 10): '個人意志與生命重心高度傾注於社會名望、事業成就與公眾舞台',
    (1, 7): '生命重心外放於伴侶與合作關係，透過他人定義自我',
    (1, 12): '意志易隱退於幕後，傾向孤獨、修行或為隱藏事務耗神',
}


class ClassicalNatalCoreLogic:
    def __init__(self, dignities, trans_planets=None, trans_signs=None, planet_glyphs=None):
        self.dignities = dignities
        self.tp = trans_planets or {}
        self.ts = trans_signs or {}
        self.glyphs = planet_glyphs or {}

    # ---------- helpers ----------
    def _pname(self, p):
        return self.tp.get(p, p)

    def _plabel(self, p):
        return f"{self.glyphs.get(p, '')} {self._pname(p)}".strip()

    @staticmethod
    def _house_of(lon, houses):
        return int(((lon - houses[0]['lon']) % 360) // 30) + 1

    @staticmethod
    def _sep(a, b):
        d = abs(a - b) % 360
        return 360 - d if d > 180 else d

    def _sign_const(self, lon):
        return const.LIST_SIGNS[int(lon % 360 // 30)]

    def _pos_str(self, lon):
        s = self._sign_const(lon)
        deg = lon % 30
        d = int(deg)
        m = int((deg - d) * 60)
        return f"{self.ts.get(s, s)} {d}°{m:02d}'"

    def _lords_at(self, lon, is_day):
        """回傳 lon 處五等尊貴主星 {dignity: planet}"""
        dg = self.dignities
        sc = self._sign_const(lon)
        deg = lon % 30
        tri = dg.TRIPLICITIES[dg.SIGN_ELEMENTS[sc]]
        term = next((r for mx, r in dg.TERMS[sc] if deg < mx), dg.TERMS[sc][-1][1])
        ex = dg.EXALTATIONS.get(sc)
        return {
            'domicile': dg.RULERS[sc], 'exaltation': ex[0] if ex else None,
            'triplicity': tri[0] if is_day else tri[1], 'triplicity_part': tri[2],
            'term': term, 'face': dg.FACES[sc][min(int(deg // 10), 2)],
            'tri_all': tri,
        }

    def _syzygy_lon(self, sun_lon, moon_lon):
        diff = (moon_lon - sun_lon) % 360
        d = diff if diff < 180 else diff - 180
        return (sun_lon - d * (0.9856 / 12.19)) % 360

    def _points(self, chart, houses, is_day):
        asc = chart.get(const.ASC).lon
        mc = chart.get(const.MC).lon
        sun = chart.get(const.SUN).lon
        moon = chart.get(const.MOON).lon
        pof = (asc + moon - sun) % 360 if is_day else (asc + sun - moon) % 360
        syz = self._syzygy_lon(sun, moon)
        return asc, mc, pof, syz

    # ---------- #1 ----------
    def calculate_temperament(self, chart: Chart, houses: List[Dict[str, Any]], is_day: bool,
                              almuten_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        dg = self.dignities
        asc = chart.get(const.ASC)
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        quals = {'hot': 0.0, 'cold': 0.0, 'dry': 0.0, 'moist': 0.0}
        humors = {'choleric': 0.0, 'sanguine': 0.0, 'melancholic': 0.0, 'phlegmatic': 0.0}
        factors = []

        def add(name, detail, qual, w):
            for q in qual:
                quals[q] += w
            humors[HUMOR_OF[qual]] += w
            factors.append({'factor': name, 'detail': detail, 'weight': w,
                            'qualities': f"{qual[0]}/{qual[1]}", 'humor': HUMOR_OF[qual]})

        asc_sign = self._sign_const(asc.lon)
        add('上升星座', self.ts.get(asc_sign, asc_sign), ELEMENT_QUAL[dg.SIGN_ELEMENTS[asc_sign]], 2.0)

        lord = dg.RULERS[asc_sign]
        lord_sign = self._sign_const(chart.get(lord).lon)
        add('命主星本性', self._pname(lord), PLANET_QUAL[lord], 1.0)
        add('命主星所在星座', self.ts.get(lord_sign, lord_sign), ELEMENT_QUAL[dg.SIGN_ELEMENTS[lord_sign]], 1.0)

        moon_sign = self._sign_const(moon.lon)
        add('月亮星座', self.ts.get(moon_sign, moon_sign), ELEMENT_QUAL[dg.SIGN_ELEMENTS[moon_sign]], 1.5)
        phase = (moon.lon - sun.lon) % 360
        q_idx = int(phase // 90) % 4
        add('月相', f"第 {q_idx + 1} 象限 ({phase:.1f}°)", QUARTER_QUAL[q_idx], 1.5)

        season_idx = int(sun.lon % 360 // 90)
        add('太陽季節', ['春', '夏', '秋', '冬'][season_idx], QUARTER_QUAL[[0, 1, 2, 3][season_idx]], 1.5)

        alm_id = (almuten_data or {}).get('almuten_id')
        if alm_id in PLANET_QUAL:
            add('全盤總御星', self._pname(alm_id), PLANET_QUAL[alm_id], 1.5)

        total = sum(humors.values()) or 1.0
        pct = {k: round(v / total * 100, 1) for k, v in humors.items()}
        ranked = sorted(humors, key=lambda k: humors[k], reverse=True)
        dom, sec = ranked[0], ranked[1]
        summary = (f"主導氣質為{HUMOR_LABEL[dom]}（{pct[dom]}%，{HUMOR_TRAITS[dom]}），"
                   f"次要氣質為{HUMOR_LABEL[sec]}（{pct[sec]}%）。"
                   f"熱 {quals['hot']:.1f} / 冷 {quals['cold']:.1f}，乾 {quals['dry']:.1f} / 濕 {quals['moist']:.1f}。")
        return {
            'dominant_temperament': HUMOR_LABEL[dom], 'secondary_temperament': HUMOR_LABEL[sec],
            'dominant_key': dom, 'secondary_key': sec,
            'qualities': {k: round(v, 2) for k, v in quals.items()},
            'humors': pct, 'factors': factors, 'summary': summary,
        }

    # ---------- #2 ----------
    def _aspects_from_rulers(self, lon, is_day, chart, exclude=None):
        lords = self._lords_at(lon, is_day)
        found = []
        seen = set()
        for kind in ('domicile', 'exaltation', 'triplicity', 'term', 'face'):
            p = lords[kind]
            if not p or p in seen or p == exclude:
                continue
            seen.add(p)
            sep = self._sep(chart.get(p).lon, lon)
            for asp in PTOLEMAIC:
                orb = abs(sep - asp)
                if orb <= ASPECT_ORB:
                    found.append({'planet': p, 'dignity': kind, 'aspect': asp, 'orb': round(orb, 2)})
                    break
        return found

    def calculate_hyleg_alcocoden_syzygy(self, chart: Chart, houses: List[Dict[str, Any]], is_day: bool) -> Dict[str, Any]:
        asc, mc, pof, syz = self._points(chart, houses, is_day)
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        is_new = (moon.lon - sun.lon) % 360 < 180
        syz_sign = self._sign_const(syz)
        syz_house = self._house_of(syz, houses)
        syzygy = {
            'type': '朔月 (New Moon)' if is_new else '望月 (Full Moon)',
            'syzygy_lon': syz, 'syzygy_sign': self.ts.get(syz_sign, syz_sign),
            'syzygy_degree_str': f"{int(syz % 30)}°{int((syz % 30 % 1) * 60):02d}'",
            'syzygy_house': syz_house, 'syzygy_ruler': self._pname(self.dignities.RULERS[syz_sign]),
            'syzygy_ruler_id': self.dignities.RULERS[syz_sign],
        }

        pts = {
            'Sun': ('太陽 (Sun)', sun.lon), 'Moon': ('月亮 (Moon)', moon.lon),
            'Asc': ('上升點 (Ascendant)', asc), 'Fortune': ('福德點 (Lot of Fortune)', pof),
            'Syzygy': ('產前朔望 (Prenatal Syzygy)', syz),
        }
        order = (['Sun', 'Moon', 'Asc', 'Fortune', 'Syzygy'] if is_day
                 else ['Moon', 'Sun', 'Fortune', 'Syzygy', 'Asc'])
        candidates = []
        hyleg_key = None
        for key in order:
            name, lon = pts[key]
            h = self._house_of(lon, houses)
            in_house = h in HYLEGICAL_HOUSES
            exclude = const.SUN if key == 'Sun' else const.MOON if key == 'Moon' else None
            asps = self._aspects_from_rulers(lon, is_day, chart, exclude) if key != 'Asc' else []
            ok = in_house and (key == 'Asc' or bool(asps))
            candidates.append({'key': key, 'name': name, 'lon': lon, 'position': self._pos_str(lon), 'house': h,
                               'in_hylegical_house': in_house, 'ruler_aspects': asps, 'qualifies': ok})
            if ok and hyleg_key is None:
                hyleg_key = key
        if hyleg_key is None:
            hyleg_key = 'Asc'
        h_name, h_lon = pts[hyleg_key]
        h_house = self._house_of(h_lon, houses)
        hyleg = {'key': hyleg_key, 'name': h_name, 'lon': h_lon, 'position': self._pos_str(h_lon),
                 'house': h_house, 'fallback_to_asc': hyleg_key == 'Asc' and not any(
                     c['qualifies'] and c['key'] != 'Asc' for c in candidates)}

        # Alcocoden
        lords = self._lords_at(h_lon, is_day)
        scored = []
        for p in CLASSICAL:
            s = self.dignities.calculate_essential_dignities(p, h_lon, is_day)['score']
            if s > 0 and p in (lords['domicile'], lords['exaltation'], lords['triplicity'],
                               lords['triplicity_part'], lords['term'], lords['face']):
                sep = self._sep(chart.get(p).lon, h_lon)
                asp = next((a for a in PTOLEMAIC if abs(sep - a) <= ASPECT_ORB), None)
                scored.append((s, asp is not None, p))
        aspecting = sorted([x for x in scored if x[1]], key=lambda x: -x[0])
        fallback = not aspecting
        alc_id = aspecting[0][2] if aspecting else lords['domicile']
        alc = chart.get(alc_id)
        alc_house = self._house_of(alc.lon, houses)
        alc_score = self.dignities.calculate_essential_dignities(alc_id, alc.lon, is_day)['score']
        minor, mean, major = PLANET_YEARS[alc_id]
        if alc_score >= 3 and alc_house in (1, 4, 7, 10, 2, 5, 8, 11):
            vitality, years = '強健 (傾向大年/中年)', major
        elif alc_score < 0 or alc_house in (6, 8, 12):
            vitality, years = '偏弱 (傾向小年)', minor
        else:
            vitality, years = '中等 (傾向中年)', mean
        alcocoden = {
            'planet_id': alc_id, 'planet': self._plabel(alc_id), 'position': self._pos_str(alc.lon),
            'house': alc_house, 'dignity_score': alc_score, 'fallback_to_domicile': fallback,
            'minor_years': minor, 'mean_years': mean, 'major_years': major,
            'vitality_status': vitality, 'indicative_years': years,
            'candidates': [{'planet': self._plabel(p), 'score': s, 'aspects_hyleg': a} for s, a, p in scored],
        }
        summary = (f"產前{syzygy['type']}於{syzygy['syzygy_sign']} {syzygy['syzygy_degree_str']}（第 {syz_house} 宮）；"
                   f"生命主為【{h_name}】（{hyleg['position']}，第 {h_house} 宮）；"
                   f"壽主星為【{self._pname(alc_id)}】（小/中/大年 {minor}/{mean}/{major}，{vitality}）。")
        return {'syzygy': syzygy, 'hyleg': hyleg, 'alcocoden': alcocoden, 'candidates': candidates, 'summary': summary}

    # ---------- #3 ----------
    def calculate_dispositorship_chain(self, chart: Chart, houses: List[Dict[str, Any]],
                                       planets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        dg = self.dignities
        fly = []
        for h in houses:
            n = h['id']
            sc = const.LIST_SIGNS[int(h['lon'] // 30) % 12]
            rid = dg.RULERS[sc]
            rl = chart.get(rid).lon
            to = self._house_of(rl, houses)
            if (n, to) in FLY_OVERRIDES:
                meaning = FLY_OVERRIDES[(n, to)]
            elif n == to:
                meaning = f"{HOUSE_THEME[n]}自成一體，主題自守、能量內聚"
            else:
                meaning = f"{HOUSE_THEME[n]}的能量導向{HOUSE_THEME[to]}，兩者主題緊密牽動"
            fly.append({
                'house_num': n, 'house_name': HOUSE_NAMES[n], 'sign': self.ts.get(sc, sc),
                'ruler_id': rid, 'ruler_name': self._pname(rid), 'flies_to_house': to,
                'ruler_sign': self.ts.get(self._sign_const(rl), self._sign_const(rl)),
                'ruler_dignity_score': dg.calculate_essential_dignities(rid, rl, True)['score'],
                'interpretation': f"第 {n} 宮主飛入第 {to} 宮：{meaning}",
            })

        edges = []
        nxt = {}
        for p in CLASSICAL:
            sc = self._sign_const(chart.get(p).lon)
            d = dg.RULERS[sc]
            nxt[p] = d
            edges.append({'planet_id': p, 'planet': self._plabel(p), 'dispositor_id': d,
                          'dispositor': self._plabel(d), 'self_dispositor': p == d,
                          'sign': self.ts.get(sc, sc)})

        terminals, loops = {}, []
        for p in CLASSICAL:
            path, cur = [], p
            while cur not in path:
                path.append(cur)
                cur = nxt[cur]
            cyc = path[path.index(cur):]
            terminals[p] = frozenset(cyc)
            canon = cyc[cyc.index(min(cyc)):] + cyc[:cyc.index(min(cyc))]
            if len(cyc) > 1 and canon not in loops:
                loops.append(canon)
        self_disp = [p for p in CLASSICAL if nxt[p] == p]
        ends = set(terminals.values())
        final = None
        if len(ends) == 1 and len(next(iter(ends))) == 1:
            final = next(iter(next(iter(ends))))
        mutual = [{'planets': [self._plabel(p) for p in lp], 'ids': lp,
                   'text': ' ⇄ '.join(self._pname(p) for p in lp + [lp[0]])} for lp in loops]
        if final:
            fsum = f"👑 唯一最終定位星：{self._plabel(final)}，七曜能量最終皆流向{self._pname(final)}。"
        elif mutual:
            fsum = "🔄 互容定位迴圈：" + "；".join(m['text'] for m in mutual) + "，無唯一最終定位星。"
        else:
            fsum = "無唯一最終定位星，定位鏈分流於多個自守定位星：" + "、".join(self._pname(p) for p in self_disp)
        return {
            'house_fly_chains': fly, 'planet_dispositor_edges': edges, 'self_dispositors': self_disp,
            'final_dispositor': final, 'final_dispositor_name': self._plabel(final) if final else None,
            'mutual_reception_loops': mutual, 'summary': fsum,
        }

    # ---------- #7 ----------
    def calculate_essential_dignities_matrix(self, chart: Chart, houses: List[Dict[str, Any]],
                                             is_day: bool) -> List[Dict[str, Any]]:
        dg = self.dignities
        asc, mc, pof, syz = self._points(chart, houses, is_day)
        rows = [(self._plabel(p), chart.get(p).lon, p) for p in CLASSICAL]
        rows += [('Ⓐ 上升點 (Ascendant)', asc, None), ('MC 天頂 (Midheaven)', mc, None),
                 ('⊗ 福德點 (Lot of Fortune)', pof, None), ('☌ 產前朔望 (Prenatal Syzygy)', syz, None)]
        out = []
        for label, lon, pid in rows:
            lords = self._lords_at(lon, is_day)
            sc = self._sign_const(lon)
            tri = lords['tri_all']
            det_fall = '—'
            net = None
            if pid:
                tags = []
                if dg.DETRIMENTS.get(sc) == pid:
                    tags.append('陷 (Detriment -5)')
                if dg.FALLS.get(sc) == pid:
                    tags.append('弱 (Fall -4)')
                det_fall = '、'.join(tags) or '—'
                net = dg.calculate_essential_dignities(pid, lon, is_day)['score']
            ex = lords['exaltation']
            out.append({
                'point': label, 'position': self._pos_str(lon), 'house': f"第 {self._house_of(lon, houses)} 宮",
                'domicile_lord': self._plabel(lords['domicile']),
                'exaltation_lord': self._plabel(ex) if ex else '—',
                'triplicity_lords': f"日 {self._plabel(tri[0])} / 夜 {self._plabel(tri[1])} / 共 {self._plabel(tri[2])}",
                'term_lord': self._plabel(lords['term']), 'face_lord': self._plabel(lords['face']),
                'detriment_fall': det_fall, 'net_score': net,
            })
        return out
