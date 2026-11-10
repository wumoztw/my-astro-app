"""
Pure-Python classical astrology chart engine.

- render_lilly_square_chart_svg : William Lilly 1647 style square chart (default)
- render_interactive_chart_viewer : HTML/Canvas wrapper with copy / download PNG / SVG
"""
from datetime import datetime
import html
import re
from typing import Any, Dict, List, Optional

FONT = "'Noto Sans CJK TC','Noto Sans TC','PingFang TC','Microsoft JhengHei',sans-serif"
TEXT_VS = "︎"  # force text presentation so canvas export stays monochrome

SIGN_GLYPHS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
SIGN_NAMES = ["牡羊", "金牛", "雙子", "巨蟹", "獅子", "處女", "天秤", "天蠍", "射手", "魔羯", "水瓶", "雙魚"]
SIGN_ELEMENT = [0, 1, 2, 3] * 3  # fire, earth, air, water
ELEMENT_FILL = ["#FDE4D3", "#EFE9D2", "#DCEBF7", "#D5EEEA"]
PLANET_GLYPHS = {"Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀", "Mars": "♂", "Jupiter": "♃", "Saturn": "♄"}
PLANET_NAMES = {"Sun": "太陽", "Moon": "月亮", "Mercury": "水星", "Venus": "金星", "Mars": "火星", "Jupiter": "木星", "Saturn": "土星"}
CLASSICAL = list(PLANET_GLYPHS.keys())
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
CN_NUM = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]

THEMES = {
    "parchment": {
        "label": "🏛️ 古典羊皮紙", "paper": "#FAF6EE", "card": "#FFFDF8", "center_bg": "#F5EFE2",
        "ink": "#1E293B", "navy": "#0F172A", "muted": "#57534E", "gold": "#B45309",
        "horary_gold": "#D97706", "horary_fill": "#FEF3C7", "pos_score": "#15803D", "neg_score": "#B91C1C",
        "element_fill": ["#FDE4D3", "#EFE9D2", "#DCEBF7", "#D5EEEA"],
        "asc_col": "#B91C1C", "mc_col": "#1D4ED8", "ov_badge_bg": "#FFFFFF", "synastry": "#E11D48",
    },
    "starry_night": {
        "label": "🌌 皇家暗夜星空", "paper": "#0B1120", "card": "#111C33", "center_bg": "#0F172A",
        "ink": "#D4AF37", "navy": "#F8FAFC", "muted": "#94A3B8", "gold": "#FBBF24",
        "horary_gold": "#FDE047", "horary_fill": "#3B2F13", "pos_score": "#4ADE80", "neg_score": "#F87171",
        "element_fill": ["#3B1D1E", "#2D2A1E", "#17253B", "#132E32"],
        "asc_col": "#F87171", "mc_col": "#60A5FA", "ov_badge_bg": "#1E293B", "synastry": "#FB7185",
    },
}
DEFAULT_THEME = "parchment"
INK, GOLD, NAVY, PAPER, CARD = "#1E293B", "#B45309", "#0F172A", "#FAF6EE", "#FFFDF8"
HORARY_GOLD, HORARY_FILL = "#D97706", "#FEF3C7"

# ----------------------------------------------------------------- helpers
def _e(s: Any) -> str:
    return html.escape(str(s), quote=True)


def _dms(lon: float) -> str:
    d = lon % 30
    deg = int(d)
    return f"{deg}°{int((d - deg) * 60):02d}'"


def _sign_idx(lon: float) -> int:
    return int((lon % 360) // 30)


STAR_LONS = {
    'Algol (大陵五)': 56.52, 'Aldebaran (畢宿五)': 70.10, 'Rigel (參宿七)': 77.12,
    'Sirius (天狼星)': 104.38, 'Castor (北河二)': 110.47, 'Pollux (北河三)': 113.46,
    'Regulus (軒轅十四)': 150.32, 'Vindemiatrix (太微左垣四)': 190.30, 'Spica (角宿一)': 204.15,
    'Arcturus (大角星)': 204.47, 'Antares (心宿二)': 250.08, 'Vega (織女星)': 285.47,
    'Fomalhaut (北落師門)': 334.22, 'Scheat (室宿二)': 359.62,
}
LOT_DEFS = (("Fortuna", "⊗", "福德點"), ("Spirit", "⊕", "精神點"), ("Necessity", "⚷", "必要點"),
            ("Eros", "♡", "愛情點"), ("Courage", "⚔", "勇氣點"), ("Victory", "✵", "勝利點"))


def _star_short(name: str) -> str:
    m = re.search(r"\(([^)]+)\)", name)
    return m.group(1) if m else name


def _norm(report_data: Dict[str, Any], show_all_lots: bool = False) -> Dict[str, Any]:
    """Normalise report_data into plain chart primitives."""
    rd = report_data or {}
    houses = rd.get("houses") or []
    meta = rd.get("meta") or {}
    chart_type = meta.get("chart_type") or ("horary" if rd.get("horary_analysis") else "natal")

    chart = rd.get("chart")

    def _chart_lon(obj_id):
        try:
            return float(chart.get(obj_id).lon)
        except Exception:
            return None

    h1 = float(houses[0]["lon"]) if houses else 0.0
    asc = rd.get("asc_lon")
    if asc is None:
        asc = _chart_lon("Asc")
    if asc is None:
        asc = h1
    mc = rd.get("mc_lon")
    if mc is None:
        mc = _chart_lon("MC")
    if mc is None:
        mc = (asc + 270.0) % 360
    if not houses:
        houses = [{"id": i + 1, "lon": (_sign_idx(asc) + i) % 12 * 30.0, "ruler": ""} for i in range(12)]
        h1 = houses[0]["lon"]

    planets = []
    for p in rd.get("planets") or []:
        pid = p.get("id")
        lon = p.get("lon", p.get("longitude"))
        if pid not in PLANET_GLYPHS or lon is None:
            continue
        planets.append({
            "id": pid, "glyph": PLANET_GLYPHS[pid], "name": p.get("name") or PLANET_NAMES[pid],
            "lon": float(lon) % 360, "retro": bool(p.get("retro") or p.get("is_retrograde")),
            "score": (p.get("dignity") or {}).get("score"),
        })
    for p in planets:
        p["house"] = int(((p["lon"] - h1) % 360) // 30) + 1

    lots = []
    for i, lot in enumerate((rd.get("lots") or [])[:6 if show_all_lots else 2]):
        if lot.get("lon") is None:
            continue
        lon = float(lot["lon"]) % 360
        lots.append({"id": LOT_DEFS[i][0], "glyph": LOT_DEFS[i][1], "name": LOT_DEFS[i][2],
                     "lon": lon, "retro": False, "score": None,
                     "house": int(((lon - h1) % 360) // 30) + 1})

    almuten = rd.get("almuten") or {}
    fixed_stars = []
    for s in rd.get("fixed_stars") or []:
        slon = s.get("star_lon", STAR_LONS.get(s.get("star")))
        if slon is None:
            continue
        fixed_stars.append({"star": s["star"], "short_name": _star_short(s["star"]), "planet": s.get("planet", ""),
                            "orb": s.get("orb", ""), "lon": float(slon) % 360})

    ha = rd.get("horary_analysis") or {}
    perf = ha.get("perfection") or {}
    cls = ha.get("classification") or {}
    horary = None
    if chart_type == "horary":
        horary = {
            "lord_1": perf.get("lord_1_id"), "lord_q": perf.get("lord_q_id"),
            "lord_1_name": perf.get("lord_1_name", ""), "lord_q_name": perf.get("lord_q_name", ""),
            "q_house": cls.get("quesited_house") or perf.get("quesited_house_num") or 7,
            "verdict": perf.get("overall_verdict", ""), "question": cls.get("question", ""),
        }
        horary["sigs"] = {x for x in (horary["lord_1"], horary["lord_q"], "Moon") if x}

    return {"rd": rd, "meta": meta, "houses": houses, "h1": h1, "asc": float(asc) % 360, "mc": float(mc) % 360,
            "planets": planets, "lots": lots, "is_day": rd.get("is_day"), "type": chart_type, "horary": horary,
            "almuten_id": almuten.get("almuten_id"), "almuten_name": almuten.get("almuten_name", ""),
            "almuten_score": almuten.get("almuten_score", ""), "fixed_stars": fixed_stars}


def _almuten_line(n: Dict[str, Any]) -> str:
    if n["almuten_id"] and not n["horary"]:
        return f"👑 全盤總御星：{n['almuten_name']} ({n['almuten_score']}分)"
    return ""


def _stars_line(n: Dict[str, Any]) -> str:
    return "、".join(f"{s['short_name']}({s['planet']} {s['orb']})" for s in n["fixed_stars"])


def _theme(theme: str) -> Dict[str, Any]:
    return THEMES.get(theme) or THEMES[DEFAULT_THEME]


_STARS = [(0.04, 0.05, 1.6), (0.12, 0.03, 1.1), (0.2, 0.08, 0.9), (0.88, 0.04, 1.5), (0.95, 0.09, 1.0),
          (0.78, 0.02, 0.9), (0.03, 0.93, 1.4), (0.1, 0.97, 1.0), (0.06, 0.86, 0.9), (0.92, 0.95, 1.5),
          (0.97, 0.88, 1.0), (0.85, 0.97, 0.9)]


def _svg_open(width: int, height: int, t: Dict[str, Any]) -> List[str]:
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'font-family="{FONT}" role="img">',
           f'<rect x="0" y="0" width="{width}" height="{height}" fill="{t["paper"]}"/>']
    if t is THEMES["starry_night"]:
        for fx, fy, r in _STARS:
            out.append(f'<circle cx="{fx * width:.1f}" cy="{fy * height:.1f}" r="{r}" fill="#F8FAFC" '
                       f'opacity="0.35" class="star"/>')
    return out


def _text(x, y, s, size=12, fill="#1E293B", anchor="middle", weight="normal", extra="") -> str:
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" {extra}>{_e(s)}</text>')


def _meta_lines(n: Dict[str, Any]) -> Dict[str, str]:
    m = n["meta"]
    off = m.get("utc_offset_str", "")
    lat, lon = m.get("lat"), m.get("lon")
    coords = f"({lat:.2f}N, {lon:.2f}E)" if isinstance(lat, (int, float)) and isinstance(lon, (int, float)) else ""
    return {
        "date": f"{m.get('birth_date_str', '')} {m.get('birth_time_str', '')} (UTC{off})".strip(),
        "place": f"{m.get('location_city', '')} {coords}".strip(),
    }


def _angle_summary(n: Dict[str, Any]) -> List[str]:
    out = []
    for label, lon in (("ASC 上升", n["asc"]), ("MC 天頂", n["mc"]),
                       ("DSC 下降", (n["asc"] + 180) % 360), ("IC 天底", (n["mc"] + 180) % 360)):
        out.append(f"{label}  {SIGN_NAMES[_sign_idx(lon)]} {_dms(lon)}")
    return out


# ---------------------------------------------------------- square chart
_O = dict(TL=(30, 30), TM=(410, 30), TR=(790, 30), RM=(790, 410), BR=(790, 790), BM=(410, 790),
          BL=(30, 790), LM=(30, 410))
_I = dict(itl=(220, 220), itr=(600, 220), ibr=(600, 600), ibl=(220, 600))
HOUSE_POLYS = {
    1: [_O["LM"], _I["itl"], _I["ibl"]], 2: [_O["LM"], _O["BL"], _I["ibl"]],
    3: [_O["BL"], _O["BM"], _I["ibl"]], 4: [_O["BM"], _I["ibl"], _I["ibr"]],
    5: [_O["BM"], _O["BR"], _I["ibr"]], 6: [_O["BR"], _O["RM"], _I["ibr"]],
    7: [_O["RM"], _I["ibr"], _I["itr"]], 8: [_O["RM"], _O["TR"], _I["itr"]],
    9: [_O["TR"], _O["TM"], _I["itr"]], 10: [_O["TM"], _I["itr"], _I["itl"]],
    11: [_O["TM"], _O["TL"], _I["itl"]], 12: [_O["TL"], _O["LM"], _I["itl"]],
}


def _entry_label(p: Dict[str, Any]) -> str:
    s = f"{p['glyph']}{TEXT_VS} {p['name']} {_dms(p['lon'])}"
    if p.get("retro"):
        s += " Ⓡ"
    return s


def render_lilly_square_chart_svg(report_data: dict, show_lots: bool = True, theme: str = "parchment",
                                  show_all_lots: bool = False, show_stars: bool = True,
                                  show_antiscia: bool = False,
                                  show_aspect_bar: bool = False) -> str:
    t = _theme(theme)
    INK, GOLD, NAVY, PAPER, CARD = t["ink"], t["gold"], t["navy"], t["center_bg"], t["card"]
    HORARY_GOLD, HORARY_FILL, MUTED = t["horary_gold"], t["horary_fill"], t["muted"]
    n = _norm(report_data, show_all_lots)
    hor = n["horary"]
    if not show_stars:
        n["fixed_stars"] = []

    # Calculate aspects list for the integrated footer panel
    asp_list = n["rd"].get("aspects") or []
    if not asp_list and n["rd"].get("chart"):
        try:
            from aspects_logic import AspectsLogic
            asp_list = AspectsLogic().get_aspects(n["rd"]["chart"], PLANET_NAMES, PLANET_GLYPHS, {})
        except Exception:
            pass

    svg_h = 920 if (show_aspect_bar and asp_list) else 820
    out = _svg_open(820, svg_h, t)
    out.append(f'<rect x="30" y="30" width="760" height="760" fill="{CARD}" stroke="{INK}" stroke-width="2.5"/>')

    for hid, poly in HOUSE_POLYS.items():
        pts = " ".join(f"{x},{y}" for x, y in poly)
        hi = hor is not None and hid in (1, hor["q_house"])
        out.append(f'<polygon id="house-{hid}" points="{pts}" fill="{HORARY_FILL if hi else CARD}" '
                   f'stroke="{INK}" stroke-width="1.6"/>')
    out.append(f'<polyline points="30,410 410,30 790,410 410,790 30,410" fill="none" stroke="{INK}" stroke-width="1.6"/>')
    for a, b in (("TL", "itl"), ("TR", "itr"), ("BR", "ibr"), ("BL", "ibl")):
        out.append(f'<line x1="{_O[a][0]}" y1="{_O[a][1]}" x2="{_I[b][0]}" y2="{_I[b][1]}" '
                   f'stroke="{INK}" stroke-width="1.6"/>')

    entries_by_house: Dict[int, List[Dict[str, Any]]] = {i: [] for i in range(1, 13)}
    for p in n["planets"] + (n["lots"] if show_lots else []):
        entries_by_house[p["house"]].append(p)

    for hid, poly in HOUSE_POLYS.items():
        cx = sum(x for x, _ in poly) / 3.0
        cy = sum(y for _, y in poly) / 3.0
        hd = n["houses"][hid - 1]
        sidx = _sign_idx(hd["lon"])
        ents = sorted(entries_by_house[hid], key=lambda p: p["lon"] % 30)
        size = 12 if len(ents) <= 4 else 10.5
        lh = size + 4
        total_h = 3 * 15 + len(ents) * lh
        y = cy - total_h / 2 + 11
        out.append(f'<g id="house-content-{hid}">')
        out.append(_text(cx, y, f"{ROMAN[hid - 1]}  第{CN_NUM[hid - 1]}宮", 13, GOLD, weight="bold"))
        out.append(_text(cx, y + 15, f"{SIGN_GLYPHS[sidx]}{TEXT_VS} {SIGN_NAMES[sidx]} 0°00'", 12, NAVY))
        ruler = hd.get("ruler") or ""
        out.append(_text(cx, y + 30, f"主星 {ruler}", 10.5, MUTED))
        yy = y + 30 + lh
        for p in ents:
            is_sig = hor is not None and p["id"] in hor["sigs"]
            lbl = _entry_label(p)
            if p["id"] == n["almuten_id"] and not hor:
                lbl = "👑" + lbl
            if p.get("score") is not None:
                lbl += f" [{p['score']:+d}]" if isinstance(p["score"], int) else ""
            if is_sig:
                w = len(lbl) * size * 0.62
                out.append(f'<rect x="{cx - w / 2:.1f}" y="{yy - size:.1f}" width="{w:.1f}" height="{size + 4}" '
                           f'rx="4" fill="{HORARY_FILL}" stroke="{HORARY_GOLD}" stroke-width="1.8" '
                           f'class="sig-badge" data-planet="{_e(p["id"])}"/>')
            sc = p.get("score")
            color = t["pos_score"] if isinstance(sc, (int, float)) and sc > 0 else (
                t["neg_score"] if isinstance(sc, (int, float)) and sc < 0 else NAVY)
            out.append(_text(cx, yy, lbl, size, color, weight="bold" if is_sig else "normal"))
            yy += lh
        out.append("</g>")

    # centre card
    out.append(f'<rect x="220" y="220" width="380" height="380" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>')
    out.append(f'<rect x="230" y="230" width="360" height="360" fill="{CARD}" stroke="{GOLD}" stroke-width="1.2"/>')
    ml = _meta_lines(n)
    title = "古典卜卦占星盤 (Horary)" if hor else "古典占星本命星盤"
    y = 262
    out.append(_text(410, y, title, 20, NAVY, weight="bold"))
    y += 24
    sect = n["is_day"]
    if sect is not None:
        out.append(_text(410, y, "☀️ 日間盤 (Diurnal)" if sect else "🌙 夜間盤 (Nocturnal)", 13, GOLD, weight="bold"))
    y += 22
    out.append(_text(410, y, ml["date"], 12, INK))
    y += 18
    out.append(_text(410, y, ml["place"], 12, INK))
    y += 12
    out.append(f'<line x1="250" y1="{y}" x2="570" y2="{y}" stroke="{GOLD}" stroke-width="0.8"/>')
    y += 18
    for line in _angle_summary(n):
        out.append(_text(410, y, line, 12.5, NAVY))
        y += 18
    y += 4
    out.append(f'<line x1="250" y1="{y - 10}" x2="570" y2="{y - 10}" stroke="{GOLD}" stroke-width="0.8"/>')
    y += 8
    if hor:
        q = hor["question"]
        q = q if len(q) <= 22 else q[:21] + "…"
        out.append(_text(410, y, f"問題：{q}", 12, INK))
        y += 18
        out.append(_text(410, y, f"Lord 1 {hor['lord_1_name']} ⇄ Lord Q {hor['lord_q_name']} (第{hor['q_house']}宮)", 12, GOLD,
                         weight="bold"))
        y += 18
        out.append(_text(410, y, f"裁決：{hor['verdict']}", 12, NAVY, weight="bold"))
    else:
        by_id = {p["id"]: p for p in n["planets"]}
        for pid in ("Sun", "Moon"):
            if pid in by_id:
                p = by_id[pid]
                out.append(_text(410, y, f"{p['glyph']}{TEXT_VS} {p['name']}  {SIGN_NAMES[_sign_idx(p['lon'])]} {_dms(p['lon'])}", 12, INK))
                y += 17
        if _almuten_line(n):
            out.append(_text(410, y, _almuten_line(n), 12, GOLD, weight="bold"))
            y += 17
        if show_antiscia:
            ac = _antiscia_contacts(n)
            if ac:
                sl = "🪞 映點接觸：" + _antiscia_summary(ac, 3)
                out.append(_text(410, y, sl if len(sl) <= 34 else sl[:33] + "…", 11, "#8B5CF6" if theme != "starry_night" else "#C084FC",
                                 extra='class="antiscia-summary"'))
                y += 17
        if n["fixed_stars"]:
            sl = "★ 恆星合相：" + _stars_line(n)
            out.append(_text(410, y, sl if len(sl) <= 34 else sl[:33] + "…", 11, INK))
            y += 17
        if n["lots"]:
            f = n["lots"][0]
            out.append(_text(410, y, f"⊗ 福德點  {SIGN_NAMES[_sign_idx(f['lon'])]} {_dms(f['lon'])}", 12, INK))
            y += 17
        prof = n["rd"].get("prof_info") or {}
        if prof:
            out.append(_text(410, y, f"年度小限主星：{prof.get('lord_of_year', '')} ({prof.get('prof_sign', '')})", 11.5, INK))
            y += 17
        act = ((n["rd"].get("f_data") or {}).get("active")) or {}
        if act.get("major"):
            out.append(_text(410, y, f"法達：{PLANET_NAMES.get(act['major'], act['major'])} / {PLANET_NAMES.get(act.get('minor'), act.get('minor'))}", 11.5, INK))
            y += 17

    if show_aspect_bar and asp_list:
        # Integrated classical aspect panel within the image below the square chart
        out.append(f'<rect x="30" y="802" width="760" height="96" rx="4" fill="{CARD}" stroke="{GOLD}" stroke-width="1.2"/>')
        out.append(_text(410, 818, "✦ 托勒密行星主要交角與相位提示 (Ptolemaic Aspects & Orbs) ✦", 11.5, GOLD, weight="bold"))
        out.append(f'<line x1="45" y1="825" x2="775" y2="825" stroke="{t["muted"]}" stroke-width="0.6"/>')

        # Format items into 2 rows of up to 4 columns
        items = asp_list[:8]
        row1 = items[:4]
        row2 = items[4:8]

        asp_symbol_map = {
            "合相": "☌ 合相", "六分相": "⚹ 六合", "四分相": "□ 刑相",
            "三分相": "△ 拱相", "對分相": "☍ 衝相",
            "Conjunction": "☌ 合相", "Sextile": "⚹ 六合", "Square": "□ 刑相",
            "Trine": "△ 拱相", "Opposition": "☍ 衝相"
        }

        for r_idx, row in enumerate((row1, row2)):
            if not row:
                continue
            cols_count = len(row)
            col_w = 740 / max(1, cols_count)
            yy = 844 + r_idx * 22
            for c_idx, a in enumerate(row):
                cx = 40 + c_idx * col_w + col_w / 2
                p1_short = a.get("p1", "").split()
                p1_str = p1_short[0] if p1_short else ""
                p2_short = a.get("p2", "").split()
                p2_str = p2_short[0] if p2_short else ""
                raw_asp = a.get("aspect", "").split()[0]
                asp_sym = a.get("aspect_sym") or asp_symbol_map.get(raw_asp, raw_asp)
                orb_str = a.get("orb", "")
                reception_mark = " 🤝" if a.get("reception") else ""
                txt = f"{p1_str} {asp_sym} {p2_str} ({orb_str}{reception_mark})"
                out.append(_text(cx, yy, txt, 11, NAVY, weight="bold"))

        out.append(_text(410, 912, "William Lilly, Christian Astrology (1647) — Traditional Square Chart", 9.5, MUTED))
    else:
        out.append(_text(410, 806, "William Lilly, Christian Astrology (1647) — Traditional Square Chart", 10, MUTED))

    out.append("</svg>")
    return "\n".join(out)


def _angdiff(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return 360 - d if d > 180 else d


ANTISCIA_ORB = 2.0


def _antiscia_contacts(n: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Antiscion / Contra-Antiscion contacts (orb <= 2°) among classical planets and ASC/MC."""
    pts = [(p["id"], p["glyph"], p["lon"]) for p in n["planets"]]
    pts += [("Asc", "ASC", n["asc"] % 360), ("MC", "MC", n["mc"] % 360)]
    res = []
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            a, b = pts[i], pts[j]
            if a[0] in ("Asc", "MC") and b[0] in ("Asc", "MC"):
                continue
            for label, mirror in (("映點", (180.0 - a[2]) % 360), ("反映點", (360.0 - a[2]) % 360)):
                orb = _angdiff(mirror, b[2])
                if orb <= ANTISCIA_ORB:
                    res.append({"a": a[0], "b": b[0], "ga": a[1], "gb": b[1], "la": a[2], "lb": b[2],
                                "type": label, "orb": orb})
    return res


def _antiscia_summary(contacts: List[Dict[str, Any]], limit: int = 4) -> str:
    return "；".join(f"{c['ga']}-{c['gb']} {c['type']}({c['orb']:.1f}°)" for c in contacts[:limit])


# --------------------------------------------------------- viewer / export
_VIEWER_TMPL = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body{margin:0;font-family:__FONT__;background:transparent}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:4px 0 10px 0}
.bar button{background:#0F172A;color:#fff;border:1px solid #B45309;border-radius:8px;padding:8px 14px;font-size:14px;cursor:pointer}
.bar button:hover{background:#B45309}
#copy-status{font-size:13px;color:#15803D;min-height:18px}
.card{max-width:860px;margin:0 auto;border:1px solid #E2E8F0;border-radius:10px;box-shadow:0 2px 10px rgba(15,23,42,.12);background:__BG__;overflow:hidden}
.card svg{display:block;width:100%;height:auto}
</style></head><body>
<div class="bar">
<button id="btn-copy">📋 複製星盤圖片 (Copy PNG)</button>
<button id="btn-png">🖼️ 下載高畫質 PNG (Download PNG)</button>
<button id="btn-svg">📥 下載 SVG 向量檔 (Download SVG)</button>
<span id="copy-status"></span>
</div>
<div class="card" id="chart-card">__SVG__</div>
<script>
(function(){
var PREFIX = "__PREFIX__", SIZE = 1640, BG = "__BG__";
var statusEl = document.getElementById('copy-status');
function say(msg, bad){ statusEl.style.color = bad ? '#B91C1C' : '#15803D'; statusEl.textContent = msg; setTimeout(function(){statusEl.textContent='';}, 4000); }
function svgString(){
  var svg = document.querySelector('#chart-card svg').cloneNode(true);
  var vb = svg.getAttribute('viewBox').split(' ');
  svg.setAttribute('width', vb[2]); svg.setAttribute('height', vb[3]);
  return new XMLSerializer().serializeToString(svg);
}
function svgBlob(){ return new Blob([svgString()], {type:'image/svg+xml;charset=utf-8'}); }
function toCanvas(cb){
  var url = URL.createObjectURL(svgBlob()), img = new Image();
  img.onload = function(){
    var svgEl = document.querySelector('#chart-card svg');
    var vb = svgEl ? svgEl.getAttribute('viewBox').split(' ') : [0,0,820,820];
    var vw = parseFloat(vb[2]) || 820, vh = parseFloat(vb[3]) || 820;
    var c = document.createElement('canvas');
    c.width = SIZE;
    c.height = Math.round(SIZE * (vh / vw));
    var ctx = c.getContext('2d'); ctx.fillStyle = BG; ctx.fillRect(0,0,c.width,c.height);
    ctx.drawImage(img, 0, 0, c.width, c.height); URL.revokeObjectURL(url); cb(c);
  };
  img.onerror = function(){ say('⚠️ 圖片轉換失敗', true); };
  img.src = url;
}
function download(href, name){ var a = document.createElement('a'); a.href = href; a.download = name; document.body.appendChild(a); a.click(); document.body.removeChild(a); }
document.getElementById('btn-copy').onclick = function(){
  toCanvas(function(c){
    c.toBlob(function(pngBlob){
      try {
        navigator.clipboard.write([new ClipboardItem({'image/png': pngBlob})])
          .then(function(){ say('✅ 已複製圖片至剪貼簿！'); })
          .catch(function(){ say('⚠️ 瀏覽器阻擋剪貼簿，請改用下載 PNG', true); });
      } catch(e){ say('⚠️ 瀏覽器阻擋剪貼簿，請改用下載 PNG', true); }
    }, 'image/png');
  });
};
document.getElementById('btn-png').onclick = function(){
  toCanvas(function(c){ download(c.toDataURL('image/png'), PREFIX + '.png'); say('✅ 已開始下載 PNG！'); });
};
document.getElementById('btn-svg').onclick = function(){
  var u = URL.createObjectURL(svgBlob()); download(u, PREFIX + '.svg'); setTimeout(function(){URL.revokeObjectURL(u);}, 1000); say('✅ 已開始下載 SVG！');
};
})();
</script></body></html>"""


SIGN_EN = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
           "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
FIRDARIA_GLYPHS = dict(PLANET_GLYPHS, **{"North Node": "☊", "South Node": "☋"})
FIRDARIA_NAMES = dict(PLANET_NAMES, **{"North Node": "北交點", "South Node": "南交點"})
FIRDARIA_COLORS = {"Sun": "#B45309", "Moon": "#475569", "Mercury": "#0E7490", "Venus": "#BE185D",
                   "Mars": "#B91C1C", "Jupiter": "#6D28D9", "Saturn": "#374151",
                   "North Node": "#047857", "South Node": "#7C2D12"}
TIMELINE_MAX_AGE = 75


def _to_date(v: Any):
    from datetime import date as _date, datetime as _dt
    if hasattr(v, "to_pydatetime"):
        return v.floor("D").to_pydatetime().date()
    if isinstance(v, _dt):
        return v.date()
    if isinstance(v, _date):
        return v
    if isinstance(v, str):
        for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
            try:
                return _dt.strptime(v[:10], fmt).date()
            except ValueError:
                pass
    return None


def render_timeline_gantt_svg(report_data: dict, theme: str = "parchment") -> str:
    """75-year horizontal Gantt: Firdaria major/minor (top) x Zodiacal Releasing Spirit L1/L2 (bottom)."""
    from datetime import date as _date
    t = _theme(theme)
    INK, NAVY, MUTED, GOLD, CARD = t["ink"], t["navy"], t["muted"], t["gold"], t["card"]
    rd = report_data or {}
    f_data = rd.get("f_data") or {}
    timeline = f_data.get("timeline") or []
    spirit = (rd.get("zr_data") or {}).get("spirit") or {}
    meta = rd.get("meta") or {}

    birth = _to_date(timeline[0]["start"]) if timeline else _to_date(meta.get("birth_date_str"))
    birth = birth or _date(1990, 1, 1)
    target = _to_date(spirit.get("target_date")) or _date.today()
    now_age = max(0.0, (target - birth).days / 365.25)

    X0, X1 = 44.0, 892.0
    W_, H_ = 920, 440

    def ax(age: float) -> float:
        return X0 + max(0.0, min(float(TIMELINE_MAX_AGE), age)) / TIMELINE_MAX_AGE * (X1 - X0)

    def age_of(d) -> float:
        dd = _to_date(d)
        return (dd - birth).days / 365.25 if dd else 0.0

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W_} {H_}" font-family="{FONT}" role="img" '
           f'class="timeline-gantt">',
           f'<rect x="0" y="0" width="{W_}" height="{H_}" fill="{t["paper"]}"/>']

    def block(x_a, x_b, y, h, fill, label_lines, stroke=None, sw=1.0, cls="", title="", txt="#FFFFFF"):
        w = max(x_b - x_a, 0.5)
        out.append(f'<g class="{cls}"><rect x="{x_a:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="3" fill="{fill}" '
                   f'stroke="{stroke or INK}" stroke-width="{sw}"/>'
                   + (f'<title>{_e(title)}</title>' if title else "") + '</g>')
        n_l = len(label_lines)
        for i, (s, sz) in enumerate(label_lines):
            if s:
                out.append(_text((x_a + x_b) / 2, y + h / 2 + (i - (n_l - 1) / 2) * 13 + 4, s, sz, txt,
                                 weight="bold" if i == 0 else "normal"))

    out.append(_text(W_ / 2, 22, "法達星限 × 黃道釋放法 75 年生命時間軸", 15, NAVY, weight="bold"))
    # age axis
    for a in range(0, TIMELINE_MAX_AGE + 1, 5):
        x = ax(a)
        out.append(f'<line x1="{x:.1f}" y1="44" x2="{x:.1f}" y2="50" stroke="{INK}" stroke-width="1"/>')
        out.append(f'<line x1="{x:.1f}" y1="50" x2="{x:.1f}" y2="312" stroke="{MUTED}" stroke-width="0.4" '
                   f'stroke-dasharray="2 4" opacity="0.6"/>')
        out.append(_text(x, 36, f"{a}", 9.5, INK, weight="bold"))
        out.append(_text(x, 322, f"{birth.year + a}", 8.5, MUTED))
    out.append(_text(12, 36, "歲", 9, MUTED, anchor="start"))
    out.append(_text(12, 322, "年", 9, MUTED, anchor="start"))

    # --- Firdaria
    out.append(_text(X0, 60, "波斯法達星限 · 主運 (Major) 與當前主運七段副運 (Minor)", 11, GOLD, anchor="start", weight="bold"))
    active = f_data.get("active") or {}
    active_major_item = None
    for item in timeline:
        a0, a1 = age_of(item["start"]), age_of(item["end"])
        if a0 >= TIMELINE_MAX_AGE:
            continue
        lord = item["lord"]
        xa, xb = ax(a0), ax(a1)
        is_act = a0 <= now_age < a1
        if is_act:
            active_major_item = item
        yrs = round(a1 - a0)
        wide = xb - xa
        lines = [(FIRDARIA_GLYPHS.get(lord, "") + TEXT_VS, 15)]
        if wide >= 50:
            lines.append((FIRDARIA_NAMES.get(lord, lord), 10))
        lines.append((f"{round(a0)}–{round(a1)}", 8.5 if wide >= 34 else 7.5))
        block(xa, xb, 64, 46, FIRDARIA_COLORS.get(lord, "#475569"), lines,
              stroke=t["asc_col"] if is_act else INK, sw=2.4 if is_act else 1.0, cls="firdaria-major",
              title=f"{FIRDARIA_NAMES.get(lord, lord)} 主運 {yrs} 年 ({round(a0)}–{round(a1)} 歲)")
    if active_major_item:
        out.append(_text(X0, 126, f"當前主運 {FIRDARIA_NAMES.get(active_major_item['lord'], active_major_item['lord'])} 之七段副運：",
                         9.5, MUTED, anchor="start"))
        for sub in active_major_item.get("subs", []):
            a0, a1 = age_of(sub["start"]), age_of(sub["end"])
            minor = sub["minor"]
            is_act_sub = (sub["start"] == active.get("start")) or a0 <= now_age < a1
            lines = [(FIRDARIA_GLYPHS.get(minor, "") + TEXT_VS, 12)]
            block(ax(a0), ax(a1), 131, 30, FIRDARIA_COLORS.get(minor, "#475569"), lines,
                  stroke="#FACC15" if is_act_sub else INK, sw=2.8 if is_act_sub else 0.8, cls="firdaria-minor",
                  title=f"{FIRDARIA_NAMES.get(minor, minor)} 副運 {a0:.1f}–{a1:.1f} 歲" + (" ◀ 當前" if is_act_sub else ""))

    # --- Zodiacal Releasing
    out.append(f'<line x1="{X0}" y1="176" x2="{X1}" y2="176" stroke="{INK}" stroke-width="0.8"/>')
    out.append(_text(X0, 192, "希臘黃道釋放法 (ZR) · 精神點 L1 主運 與 當前 L1 之 L2 子運", 11, GOLD, anchor="start", weight="bold"))
    l1s = spirit.get("l1_periods") or []
    for p in l1s:
        a0, a1 = age_of(p["start"]), age_of(p["end"])
        if a0 >= TIMELINE_MAX_AGE:
            continue
        idx = SIGN_EN.index(p["sign_const"]) if p.get("sign_const") in SIGN_EN else 0
        peak_type = p.get("peak_type", "")
        if p.get("is_peak") and "Major" in peak_type:
            fill, txt, kind = "#F59E0B", "#1C1917", "巔峰期"
        elif p.get("is_peak"):
            fill, txt, kind = "#0D9488", "#FFFFFF", "角宮期"
        else:
            fill, txt, kind = "#64748B", "#FFFFFF", "一般期"
        is_act = a0 <= now_age < a1
        block(ax(a0), ax(a1), 198, 44, fill,
              [(f"{SIGN_GLYPHS[idx]}{TEXT_VS} {SIGN_NAMES[idx]}", 11), (f"{p.get('years', round(a1 - a0))}年 · {round(a0)}–{round(a1)}", 8.5)],
              stroke=t["asc_col"] if is_act else INK, sw=2.4 if is_act else 1.0, cls="zr-l1", txt=txt,
              title=f"{p.get('sign_name', SIGN_NAMES[idx])} L1 {kind} {p.get('start_date', '')}~{p.get('end_date', '')}")

    l2s = spirit.get("active_l2_periods") or []
    act_l1 = spirit.get("active_l1") or {}
    out.append(_text(X0, 262, f"當前 L1 ({act_l1.get('sign_name', '—')}) 之 L2 子運展開：", 9.5, MUTED, anchor="start"))
    for p in l2s:
        a0, a1 = age_of(p["start_date"]), age_of(p["end_date"])
        idx = SIGN_EN.index(p["sign_const"]) if p.get("sign_const") in SIGN_EN else 0
        is_act = a0 <= now_age < a1
        fill = "#0D9488" if p.get("is_peak") else "#94A3B8"
        wide = ax(a1) - ax(a0)
        block(ax(a0), ax(a1), 268, 30, fill, [(f"{SIGN_GLYPHS[idx]}{TEXT_VS}" if wide >= 14 else "", 11)],
              stroke="#FACC15" if is_act else INK, sw=2.8 if is_act else 0.7, cls="zr-l2", txt="#0F172A",
              title=f"L2 {SIGN_NAMES[idx]} {p['start_date']}~{p['end_date']}" + (" ⚡ LB 換宮跳躍" if p.get("is_lb") else ""))
        if p.get("is_lb"):
            bx = ax(a1)
            out.append(f'<g class="zr-lb"><rect x="{bx - 40:.1f}" y="300" width="80" height="14" rx="7" fill="#DC2626" '
                       f'stroke="#FACC15" stroke-width="1.2"/>' + _text(bx, 310, "⚡ LB 換宮跳躍", 8.5, "#FFFFFF", weight="bold")
                       + f'<line x1="{bx:.1f}" y1="298" x2="{bx:.1f}" y2="300" stroke="#DC2626" stroke-width="2"/></g>')

    # --- NOW cursor
    nx = ax(now_age)
    out.append(f'<g class="timeline-now-line"><line x1="{nx:.1f}" y1="42" x2="{nx:.1f}" y2="318" stroke="{t["asc_col"]}" '
               f'stroke-width="2.4"/><polygon points="{nx - 5:.1f},42 {nx + 5:.1f},42 {nx:.1f},50" fill="{t["asc_col"]}"/>'
               f'<rect x="{min(max(nx - 78, 4), W_ - 160):.1f}" y="330" width="156" height="17" rx="8" fill="{t["asc_col"]}"/>'
               + _text(min(max(nx, 82), W_ - 82), 342, f"NOW / 當前 {now_age:.1f} 歲 ({target.year})", 10, "#FFFFFF", weight="bold")
               + '</g>')

    # --- summary + legend
    act_l2 = spirit.get("active_l2") or {}
    summary = (f"此刻：法達 {FIRDARIA_NAMES.get(active.get('major'), active.get('major', '—'))} 主運 / "
               f"{FIRDARIA_NAMES.get(active.get('minor'), active.get('minor', '—'))} 副運　·　"
               f"ZR 精神點 L1 {act_l1.get('sign_name', '—')}（{act_l1.get('peak_type') or '一般期'}）/ L2 {act_l2.get('sign_name', '—')}")
    out.append(_text(X0, 372, summary, 10.5, NAVY, anchor="start", weight="bold"))
    lx = X0
    for fill, lbl in (("#F59E0B", "L1 巔峰期 (第十宮頂峰)"), ("#0D9488", "角宮期 / 角宮 L2"), ("#64748B", "一般期"),
                      ("#DC2626", "⚡ LB 換宮跳躍")):
        out.append(f'<rect x="{lx:.1f}" y="388" width="12" height="12" rx="2" fill="{fill}" stroke="{INK}" stroke-width="0.6"/>')
        out.append(_text(lx + 17, 398, lbl, 9.5, MUTED, anchor="start"))
        lx += 17 + len(lbl) * 9.5 + 22
    out.append(_text(X0, 420, "紅框＝當前主運/L1；金框＝當前副運/L2；縱向紅線＝當前年齡。時間軸以平均太陽年 365.25 日換算。", 9, MUTED, anchor="start"))
    out.append('</svg>')
    return "".join(out)


def render_interactive_chart_viewer(svg_str: str, filename_prefix: str = "astro_chart",
                                    bg_color: str = "#FAF6EE") -> str:
    m = re.search(r'<rect[^>]*\bfill="(#[0-9A-Fa-f]{3,8})"', svg_str or "")
    if m:
        bg_color = m.group(1)
    elif not re.fullmatch(r"#[0-9A-Fa-f]{3,8}", bg_color or ""):
        bg_color = "#FAF6EE"
    prefix = "".join(c for c in filename_prefix if c.isalnum() or c in "-_") or "astro_chart"
    return (_VIEWER_TMPL.replace("__FONT__", FONT.replace('"', "'"))
            .replace("__PREFIX__", prefix).replace("__BG__", bg_color).replace("__SVG__", svg_str))


_HUMOR_ROWS = [("choleric", "🔥 膽汁質 Choleric", "#DC2626"), ("sanguine", "💨 多血質 Sanguine", "#D97706"),
               ("melancholic", "🌍 抑鬱質 Melancholic", "#7C6F57"), ("phlegmatic", "💧 黏液質 Phlegmatic", "#2563EB")]


def _svg_canvas(w: int, h: int, t: Dict[str, Any], defs: str = "") -> List[str]:
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" font-family="{FONT}" role="img">',
            f'<defs>{defs}</defs>',
            f'<rect x="0" y="0" width="{w}" height="{h}" rx="10" fill="{t["paper"]}"/>']


def render_temperament_svg(temperament_data: Dict[str, Any], theme: str = "parchment") -> str:
    """四液氣質橫條 + 冷熱/乾濕菱形象限指示器 (viewBox 760x240)"""
    t = _theme(theme)
    td = temperament_data or {}
    humors, quals = td.get("humors", {}), td.get("qualities", {})
    out = _svg_canvas(760, 240, t)
    out.append(_text(20, 26, "古典四液氣質 Four Humors", 15, t["navy"], "start", "bold"))
    for i, (key, label, col) in enumerate(_HUMOR_ROWS):
        y = 40 + i * 36
        pct = max(0.0, min(100.0, float(humors.get(key, 0) or 0)))
        out.append(_text(20, y + 16, label, 13, t["ink"], "start"))
        out.append(f'<rect x="170" y="{y}" width="300" height="22" rx="6" fill="{t["card"]}" '
                   f'stroke="{t["muted"]}" stroke-width="0.8"/>')
        out.append(f'<rect class="humor-bar" x="170" y="{y}" width="{3.0 * pct:.1f}" height="22" rx="6" fill="{col}"/>')
        out.append(_text(480, y + 16, f"{pct:.1f}%", 13, t["navy"], "start", "bold"))
    cx, cy, r = 640, 112, 66
    out.append(f'<polygon points="{cx},{cy - r} {cx + r},{cy} {cx},{cy + r} {cx - r},{cy}" fill="{t["card"]}" '
               f'stroke="{t["gold"]}" stroke-width="1.5"/>')
    out.append(f'<line x1="{cx - r}" y1="{cy}" x2="{cx + r}" y2="{cy}" stroke="{t["muted"]}" stroke-width="0.6"/>')
    out.append(f'<line x1="{cx}" y1="{cy - r}" x2="{cx}" y2="{cy + r}" stroke="{t["muted"]}" stroke-width="0.6"/>')
    out.append(_text(cx + r + 4, cy + 4, "熱", 12, t["asc_col"], "start"))
    out.append(_text(cx - r - 4, cy + 4, "冷", 12, t["mc_col"], "end"))
    out.append(_text(cx, cy - r - 6, "濕", 12, t["muted"]))
    out.append(_text(cx, cy + r + 16, "乾", 12, t["muted"]))
    hot, cold = float(quals.get("hot", 0)), float(quals.get("cold", 0))
    dry, moist = float(quals.get("dry", 0)), float(quals.get("moist", 0))
    px = cx + r * 0.9 * (hot - cold) / ((hot + cold) or 1.0)
    py = cy - r * 0.9 * (moist - dry) / ((dry + moist) or 1.0)
    out.append(f'<circle class="temp-dot" cx="{px:.1f}" cy="{py:.1f}" r="6" fill="{t["gold"]}" '
               f'stroke="{t["navy"]}" stroke-width="1.2"/>')
    out.append(_text(20, 218, f"主導：{td.get('dominant_temperament', '')}", 12, t["gold"], "start", "bold"))
    out.append("</svg>")
    return "".join(out)


def render_dispositor_tree_svg(dispositor_data: Dict[str, Any], theme: str = "parchment") -> str:
    """七曜定位星有向圖：弧形箭頭、自守雙金環、互容雙向金箭頭 (viewBox 760x300)"""
    t = _theme(theme)
    dd = dispositor_data or {}
    nxt = {e["planet_id"]: e["dispositor_id"] for e in dd.get("planet_dispositor_edges", [])}
    final = dd.get("final_dispositor")
    defs = "".join(
        f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>'
        for mid, col in (("arrow", t["ink"]), ("arrow-gold", t["gold"])))
    out = _svg_canvas(760, 300, t, defs)
    out.append(_text(20, 24, "七曜定位星能量流向 Dispositor Graph", 14, t["navy"], "start", "bold"))
    pos = {p: (80 + i * 100, 160) for i, p in enumerate(CLASSICAL)}
    R = 24
    drawn = set()
    for p, d in nxt.items():
        if p == d or p not in pos or d not in pos or (d, p) in drawn:
            continue
        drawn.add((p, d))
        (x1, y1), (x2, y2) = pos[p], pos[d]
        mutual = nxt.get(d) == p
        up = -1 if (CLASSICAL.index(p) + CLASSICAL.index(d)) % 2 == 0 else 1
        ctrl_y = y1 + up * (30 + abs(x2 - x1) * 0.28)
        col, mk, sw = (t["gold"], "arrow-gold", 2.2) if mutual else (t["ink"], "arrow", 1.4)
        sx, ex = (x1 + R, x2 - R) if x2 > x1 else (x1 - R, x2 + R)
        start_mk = f' marker-start="url(#{mk})"' if mutual else ""
        out.append(f'<path class="disp-edge{" mutual" if mutual else ""}" '
                   f'd="M{sx:.1f},{y1} Q{(x1 + x2) / 2:.1f},{ctrl_y:.1f} {ex:.1f},{y2}" fill="none" '
                   f'stroke="{col}" stroke-width="{sw}" marker-end="url(#{mk})"{start_mk}/>')
    for p in CLASSICAL:
        x, y = pos[p]
        is_self = nxt.get(p) == p
        if is_self:
            out.append(f'<circle class="self-ring" cx="{x}" cy="{y}" r="{R + 6}" fill="none" '
                       f'stroke="{t["gold"]}" stroke-width="1.6"/>')
        out.append(f'<circle cx="{x}" cy="{y}" r="{R}" fill="{t["card"]}" '
                   f'stroke="{t["gold"] if is_self else t["muted"]}" stroke-width="{2.4 if is_self else 1.2}"/>')
        out.append(_text(x, y + 8, PLANET_GLYPHS[p] + TEXT_VS, 22, t["navy"]))
        out.append(_text(x, y + R + 24, PLANET_NAMES[p], 11, t["muted"]))
        if is_self:
            out.append(_text(x, y + R + 40, "👑 最終定位星" if p == final else "👑 自守廟星", 11, t["gold"],
                             "middle", "bold"))
    out.append(_text(20, 276, dd.get("summary", ""), 12, t["gold"], "start"))
    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------------- printable astro book
def _html_table(headers: List[str], rows: List[List[Any]]) -> str:
    if not rows:
        return ""
    head = "".join(f"<th>{_e(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{_e(c)}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def render_printable_astro_book_html(report_data: Dict[str, Any], theme: str = "parchment",
                                     ai_messages: Optional[List[Dict[str, str]]] = None) -> str:
    """Self-contained print-optimised HTML book (save as PDF via the browser print dialog)."""
    rd = report_data or {}
    t = _theme(theme)
    meta = rd.get("meta") or {}
    nc = rd.get("natal_core") or {}
    alm = rd.get("almuten") or {}
    sect = "☀️ 日間盤 (Diurnal)" if rd.get("is_day") else "🌙 夜間盤 (Nocturnal)"
    name = rd.get("person_name") or meta.get("person_name") or "命盤主"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    def svg_block(title, fn, note=""):
        try:
            note_html = f'<div class="chart-note">{_e(note)}</div>' if note else ""
            return f'<div class="chart"><h3>{_e(title)}</h3>{fn()}{note_html}</div>'
        except Exception as ex:
            return f'<div class="chart"><h3>{_e(title)}</h3><p>（繪製失敗：{_e(ex)}）</p></div>'

    # Classical ornate cover card
    cover_meta = [
        ("命盤主姓名", f"<b>{_e(name)}</b>"),
        ("生辰時間", f"{_e(meta.get('birth_date_str', ''))} {_e(meta.get('birth_time_str', ''))} (UTC{_e(meta.get('utc_offset_str', ''))})"),
        ("出生經緯地", f"{_e(meta.get('location_city', ''))} ({_e(meta.get('lat', ''))}, {_e(meta.get('lon', ''))})"),
        ("日夜盤屬性", sect),
        ("三要核心點", f"☉ 太陽 {_e(rd.get('sun', ''))} ｜ ☽ 月亮 {_e(rd.get('moon', ''))} ｜ 🧭 上升 {_e(rd.get('asc', ''))}"),
    ]
    if alm.get("almuten_name"):
        cover_meta.append(("全盤總御星 (Almuten)", f"👑 <b>{_e(alm.get('almuten_name'))}</b>（權重尊貴分：{_e(alm.get('almuten_score', ''))}）"))
    if nc.get("temperament"):
        cover_meta.append(("四液古典氣質", f"🧬 {_e(nc['temperament'].get('summary', ''))}"))
    if nc.get("hyleg_data"):
        cover_meta.append(("壽命三要點", f"🛡️ {_e(nc['hyleg_data'].get('summary', ''))}"))

    cover_table_rows = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in cover_meta)
    cover_html = f"""
    <section class="cover-page">
      <div class="cover-frame">
        <div class="cover-ornament">✦ ✠ ✦</div>
        <h1 class="cover-title">古典占星專業命書</h1>
        <div class="cover-subtitle">NATAL HOROSCOPE &amp; TRADITIONAL DELINEATION</div>
        <div class="cover-divider"></div>
        <table class="cover-meta-table">
          {cover_table_rows}
        </table>
        <div class="cover-footer-note">
          <p>依托勒密 (Ptolemy)、多羅修斯 (Dorotheus) 與威廉·莉莉 (William Lilly) 古典法則排盤計算</p>
          <p class="timestamp">報告生成時間：{now_str}</p>
        </div>
      </div>
    </section>
    """

    s1 = svg_block("William Lilly 傳統方形星盤", lambda: render_lilly_square_chart_svg(
        rd, show_lots=True, theme=theme, show_all_lots=True, show_stars=True, show_antiscia=True),
        note="※ 十二整宮、四正位、七政星、映點 (Antiscia) 與希臘阿拉伯點")

    s2 = ""
    if nc.get("temperament"):
        s2 += svg_block("古典四液氣質平衡 (Temperament Balance)", lambda: render_temperament_svg(nc["temperament"], theme),
                        note=f"質料狀態：{_e(nc['temperament'].get('dominant_qualities_str', ''))}｜體質傾向：{_e(nc['temperament'].get('dominant_temperaments_str', ''))}")
    if nc.get("dispositors"):
        s2 += svg_block("定位星能量流向階層圖 (Dispositor Tree)", lambda: render_dispositor_tree_svg(nc["dispositors"], theme),
                        note="自終極稟賦星/互容星向下遞移之支配關係")

    s3 = ""
    if rd.get("f_data") and meta.get("chart_type", "natal") != "horary":
        s3 = svg_block("75 年古典法達星限 (Firdaria) × 希臘黃道釋放法 (Zodiacal Releasing) 時間軸",
                       lambda: render_timeline_gantt_svg(rd, theme=theme),
                       note="甘特長條展示主星限與子運期，標記人生關鍵釋放與重大轉換轉折年份")

    tb = ["<h3>1. 七大古典行星與尊貴分 (Planetary Essential &amp; Accidental Dignities)</h3>" + _html_table(
        ["行星", "星座", "度數", "宮位", "尊貴分", "偶然尊貴"],
        [[p.get("name"), p.get("sign"), p.get("degree_str"), p.get("house"),
          (p.get("dignity") or {}).get("score"), "、".join(p.get("accidental") or [])]
         for p in rd.get("planets") or []])]
    if nc.get("dignities_matrix"):
        keys = ("point", "position", "house", "domicile_lord", "exaltation_lord",
                "triplicity_lords", "term_lord", "face_lord", "detriment_fall", "net_score")
        tb.append("<h3>2. 五等尊貴全表 (Five Essential Dignities Matrix)</h3>" + _html_table(
            ["星點", "位置", "宮位", "廟主", "旺主", "三分主", "界主", "面主", "落/陷", "淨分"],
            [[r.get(k, "") for k in keys] for r in nc["dignities_matrix"]]))
    tb.append("<h3>3. 十二整宮與宮主星 (Houses &amp; Domicile Lords)</h3>" + _html_table(
        ["宮位", "星座", "宮主星"],
        [[h.get("id_str", h.get("id")), h.get("sign", ""), h.get("ruler", "")] for h in rd.get("houses") or []]))
    chains = (nc.get("dispositors") or {}).get("house_fly_chains") or []
    if chains:
        tb.append("<h3>4. 十二宮位飛星連鎖 (House Rulers Fly Chains)</h3>" + _html_table(
            list(chains[0].keys()), [[str(v) for v in c.values()] for c in chains]))
    if rd.get("aspects"):
        tb.append("<h3>5. 托勒密古典相位 (Ptolemaic Major Aspects)</h3>" + _html_table(
            ["行星 1", "行星 2", "相位", "容許度", "入/出相位"],
            [[a.get("p1"), a.get("p2"), a.get("aspect"), a.get("orb"), a.get("applying")] for a in rd["aspects"]]))
    if rd.get("antiscia"):
        tb.append("<h3>6. 映點與映點合相 (Antiscia &amp; Contra-Antiscia)</h3>" + _html_table(
            list(rd["antiscia"][0].keys()), [[str(v) for v in a.values()] for a in rd["antiscia"]]))
    if rd.get("lots"):
        tb.append("<h3>7. 希臘赫密斯點 (Lots / Arabic Parts)</h3>" + _html_table(
            ["名稱", "星座", "度數", "宮位"],
            [[x.get("name"), x.get("sign"), x.get("degree"), x.get("house")] for x in rd["lots"]]))
    if rd.get("fixed_stars"):
        tb.append("<h3>8. 恆星合相 (Fixed Stars Conjunctions)</h3>" + _html_table(
            ["恆星", "行星", "容許度"], [[s.get("star"), s.get("planet"), s.get("orb")] for s in rd["fixed_stars"]]))
    sr = rd.get("sr_data")
    if sr:
        tb.append(f"<h3>9. 太陽返照盤 {_e(sr.get('target_year', ''))} (Solar Return)</h3><p>{_e(sr.get('summary', ''))}</p>")
    lr = rd.get("lr_data")
    if lr and lr.get("summary"):
        tb.append(f"<h3>10. 月亮返照盤 (Lunar Return)</h3><p>{_e(lr['summary'])}</p>")
    mp = rd.get("monthly_profections")
    if mp:
        tb.append("<h3>11. 12 個月小限輪動 (Monthly Profections)</h3>" + _html_table(
            ["月", "起", "迄", "宮位", "月主星", "主題"],
            [[r.get("month_index"), r.get("start_date"), r.get("end_date"), r.get("house_name"),
              r.get("lord_name"), r.get("focus_theme")] for r in mp]))
    syn = rd.get("synastry_data")
    if syn:
        sc = syn.get("resonance_scores") or {}
        tb.append(f"<h3>12. 雙人合盤：{_e(syn.get('person_a', ''))} × {_e(syn.get('person_b', ''))}</h3>"
                  f"<p>事業協同 {_e(sc.get('business_harmony_score', '-'))} ｜ 情感黏著 "
                  f"{_e(sc.get('romantic_harmony_score', '-'))} ｜ 關係張力 {_e(sc.get('tension_index', '-'))}</p>"
                  + _html_table(["A 行星", "B 行星", "相位", "容許度"],
                                [[a.get("planet_a_zh"), a.get("planet_b_zh"), a.get("aspect_name"), a.get("orb")]
                                 for a in syn.get("cross_aspects") or []]))

    # 13. 三大生活實戰專題核心評估指標 (健康、學業考運、田宅置產)
    if meta.get("chart_type", "natal") != "horary":
        health_hyleg = (nc.get("hyleg_data") or {}).get("summary", "命宮與第一宮守護星狀態正常")
        health_temp = (nc.get("temperament") or {}).get("summary", "氣質平衡")
        tb.append("<h3>13. 🏥 健康體質與身心精力平衡核心評估 (Health & Temperament)</h3>" + _html_table(
            ["健康評估項目", "古典學理依據", "本盤狀態與調養重點"],
            [
                ["四液氣質 (Temperament)", "Asc 星座、月亮與命主星之冷熱乾濕", _e(health_temp)],
                ["生命主與活力 (Hyleg)", "希臘托勒密生命主星與壽星評估", _e(health_hyleg)],
                ["慢性消耗與壓力宮位", "第 6 宮日常勞損、第 8 宮危機、第 12 宮隱匿壓力", "請參照 6/8/12 宮主星落入宮位與凶星刑沖情況進行後天作息調養"]
            ]
        ))

        mercury_p = next((p for p in (rd.get("planets") or []) if p.get("name") in ("水星", "Mercury")), {})
        m_pos = f"{mercury_p.get('sign', '')} {mercury_p.get('degree_str', '')} (第 {mercury_p.get('house', '')} 宮)" if mercury_p else "—"
        tb.append("<h3>14. 🎓 學業考運、進修出國與思維天賦評估 (Academics & Intellect)</h3>" + _html_table(
            ["考運與思維指標", "象徵宮位 / 自然主星", "本命盤座標配置"],
            [
                ["認知與表達邏輯", "水星 (Mercury)", _e(m_pos)],
                ["短期考試與技能證照", "第 3 宮 (兄弟宮 / 基礎教育)", f"第 3 宮主星與星體配置"],
                ["高等學術與留學深造", "第 9 宮 (遷移宮 / 高等智慧)", f"第 9 宮主星與木星助力評估"]
            ]
        ))

        h4_info = next((h for h in (rd.get("houses") or []) if str(h.get("id")) in ("4", "IV")), {})
        h4_str = f"{h4_info.get('sign', '')}，守護星：{h4_info.get('ruler', '')}" if h4_info else "—"
        tb.append("<h3>15. 🏡 田宅置產、居住風水與資產守成評估 (Real Estate & Property)</h3>" + _html_table(
            ["置產房地產指標", "象徵宮位 / 自然主星", "本命盤座標配置"],
            [
                ["田宅宮與不動產根基", "第 4 宮 (田宅宮 / 土地父母)", _e(h4_str)],
                ["土地自然象徵星", "土星 (Saturn) 與月亮 (居所安穩)", "評估土星尊貴分與月亮落宮"],
                ["買房置產與貸款連動", "第 2 宮 (自有財庫) × 第 8 宮 (銀行融資)", "評估 2/8 宮主星相位與田宅宮吉凶"]
            ]
        ))

    ai_html = ""
    replies = [m for m in (ai_messages or []) if m.get("role") == "assistant" and m.get("content")]
    if replies:
        ai_html = '<section class="page-break"><h2>Section 5 ✨ AI 大師深度解析記錄</h2>' + "".join(
            f'<div class="ai-bubble"><div class="ai-badge">✦ 大師研判筆記</div><div class="ai-body">{_e(m["content"])}</div></div>'
            for m in replies) + "</section>"

    css = f"""
@page {{
  size: A4;
  margin: 16mm 14mm 18mm 14mm;
  @top-center {{
    content: "古典占星專業命書 ｜ {_e(name)}";
    font-size: 9px;
    color: {t['muted']};
    border-bottom: 1px solid {t['muted']};
    padding-bottom: 4px;
    font-family: {FONT};
  }}
  @bottom-left {{
    content: "依托勒密、多羅修斯與威廉·莉莉古典法則推算";
    font-size: 9px;
    color: {t['muted']};
    font-family: {FONT};
  }}
  @bottom-right {{
    content: "第 " counter(page) " 頁";
    font-size: 9px;
    color: {t['muted']};
    font-family: {FONT};
  }}
}}
* {{ box-sizing: border-box; }}
body {{
  font-family: {FONT};
  background: {t['paper']};
  color: {t['navy']};
  margin: 0 auto;
  max-width: 960px;
  padding: 16px;
  line-height: 1.55;
  font-size: 13px;
}}
.no-print {{
  position: sticky;
  top: 0;
  text-align: center;
  padding: 12px;
  background: {t['card']};
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  border-radius: 6px;
  margin-bottom: 20px;
  z-index: 999;
}}
.no-print button {{
  background: {t['gold']};
  color: #fff;
  border: none;
  font-size: 14px;
  font-weight: bold;
  padding: 8px 20px;
  border-radius: 4px;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}}
.no-print button:hover {{ opacity: 0.9; }}

/* Cover Page Styling */
.cover-page {{
  min-height: 85vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30px 10px;
}}
.cover-frame {{
  width: 100%;
  border: 3px double {t['gold']};
  padding: 36px 28px;
  background: {t['card']};
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
  border-radius: 6px;
  text-align: center;
}}
.cover-ornament {{
  font-size: 18px;
  color: {t['gold']};
  letter-spacing: 6px;
  margin-bottom: 10px;
}}
.cover-title {{
  font-size: 28px;
  font-weight: bold;
  color: {t['gold']};
  margin: 6px 0;
  letter-spacing: 2px;
}}
.cover-subtitle {{
  font-size: 11px;
  color: {t['muted']};
  letter-spacing: 3px;
  margin-bottom: 18px;
}}
.cover-divider {{
  height: 2px;
  background: linear-gradient(to right, transparent, {t['gold']}, transparent);
  margin: 16px auto;
  width: 80%;
}}
.cover-meta-table {{
  width: 90%;
  margin: 20px auto;
  border-collapse: collapse;
  text-align: left;
  font-size: 13px;
}}
.cover-meta-table th {{
  width: 28%;
  padding: 8px 12px;
  border: 1px solid {t['muted']};
  background: {t['center_bg']};
  color: {t['navy']};
  font-weight: 600;
}}
.cover-meta-table td {{
  padding: 8px 12px;
  border: 1px solid {t['muted']};
  background: {t['paper']};
  color: {t['navy']};
}}
.cover-footer-note {{
  margin-top: 30px;
  font-size: 11px;
  color: {t['muted']};
  line-height: 1.6;
}}
.cover-footer-note .timestamp {{
  font-size: 10px;
  color: {t['muted']};
  margin-top: 4px;
}}

/* Section & Headers */
h2 {{
  font-size: 18px;
  color: {t['gold']};
  border-bottom: 2px solid {t['gold']};
  padding-bottom: 6px;
  margin-top: 24px;
  margin-bottom: 14px;
  page-break-after: avoid;
}}
h3 {{
  font-size: 14px;
  color: {t['navy']};
  margin-top: 18px;
  margin-bottom: 8px;
  page-break-after: avoid;
}}

/* Charts and Notes */
.chart {{
  text-align: center;
  margin: 16px 0;
  page-break-inside: avoid;
}}
.chart svg {{
  max-width: 100%;
  height: auto;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  border-radius: 4px;
}}
.chart-note {{
  font-size: 11px;
  color: {t['muted']};
  margin-top: 6px;
  text-align: center;
}}

/* Tables with zebra striping and page-break rules */
table {{
  border-collapse: collapse;
  width: 100%;
  font-size: 11.5px;
  margin-bottom: 16px;
  page-break-inside: auto;
}}
tr {{
  page-break-inside: avoid;
  page-break-after: auto;
}}
thead {{
  display: table-header-group;
}}
th {{
  background: {t['center_bg']};
  color: {t['navy']};
  border: 1px solid {t['muted']};
  padding: 4px 6px;
  text-align: left;
  font-weight: 600;
}}
td {{
  border: 1px solid {t['muted']};
  padding: 4px 6px;
  text-align: left;
}}
tbody tr:nth-child(even) {{
  background: {t['card']};
}}

/* AI Bubbles */
.ai-bubble {{
  border: 1px solid {t['muted']};
  border-left: 4px solid {t['gold']};
  background: {t['card']};
  border-radius: 4px;
  padding: 10px 14px;
  margin: 12px 0;
  page-break-inside: avoid;
}}
.ai-badge {{
  font-size: 11px;
  font-weight: bold;
  color: {t['gold']};
  margin-bottom: 4px;
}}
.ai-body {{
  white-space: pre-wrap;
  font-size: 12.5px;
  line-height: 1.6;
}}

/* Print-specific layout */
.page-break {{
  page-break-before: always;
}}
@media print {{
  .no-print {{ display: none !important; }}
  body {{
    background: #fff !important;
    color: #111 !important;
    padding: 0;
    max-width: 100%;
  }}
  .cover-frame {{
    border: 2px solid #888;
    background: #fff;
    box-shadow: none;
  }}
  .chart, table, .ai-bubble {{
    page-break-inside: avoid;
  }}
  th {{
    background: #f0f0f0 !important;
    color: #000 !important;
  }}
  tbody tr:nth-child(even) {{
    background: #fafafa !important;
  }}
}}
"""
    return ('<!DOCTYPE html><html lang="zh-TW"><head><meta charset="utf-8">'
            f'<title>古典占星專業命書 - {_e(name)}</title><style>{css}</style></head><body>'
            '<div class="no-print"><button onclick="window.print()">🖨️ 直接列印 / 另存為 PDF (Print to PDF)</button></div>'
            f'{cover_html}'
            f'<section class="page-break"><h2>Section 1 傳統星盤圖譜</h2>{s1}</section>'
            f'<section class="page-break"><h2>Section 2 氣質與定位星能量流向</h2>{s2}</section>'
            f'<section class="page-break"><h2>Section 3 法達星限 × ZR 時間軸</h2>{s3}</section>'
            f'<section class="page-break"><h2>Section 4 核心星盤與推運結構化報告</h2>{"".join(tb)}</section>'
            f'{ai_html}</body></html>')
