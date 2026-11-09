"""
Pure-Python classical astrology chart engine.

- render_lilly_square_chart_svg : William Lilly 1647 style square chart (default)
- render_circular_chart_svg     : Whole Sign circular wheel, optional bi-wheel overlays
- render_interactive_chart_viewer : HTML/Canvas wrapper with copy / download PNG / SVG
"""
import html
import math
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
OVERLAY_STYLE = {
    "synastry": ("#E11D48", "合盤伴侶/對象 (Synastry Partner)"),
    "solar_arc": ("#C2410C", "太陽弧推運 (Solar Arc)"),
    "secondary": ("#6D28D9", "次限推運 (Secondary)"),
    "tertiary": ("#0F766E", "三限推運 (Tertiary)"),
}
ASPECTS = {0: ("合", "#64748B"), 60: ("六分", "#2563EB"), 90: ("四分", "#DC2626"),
           120: ("三分", "#16A34A"), 180: ("對分", "#B91C1C")}


# ----------------------------------------------------------------- helpers
def _e(s: Any) -> str:
    return html.escape(str(s), quote=True)


def _dms(lon: float) -> str:
    d = lon % 30
    deg = int(d)
    return f"{deg}°{int((d - deg) * 60):02d}'"


def _sign_idx(lon: float) -> int:
    return int((lon % 360) // 30)


def spread_longitudes(lons: List[float], min_sep: float = 6.5, iterations: int = 300) -> List[float]:
    """Return display longitudes (same order as input) with circular gaps >= min_sep."""
    n = len(lons)
    if n < 2:
        return [l % 360 for l in lons]
    min_sep = min(min_sep, 360.0 / n - 1e-6)
    order = sorted(range(n), key=lambda i: lons[i] % 360)
    pos = [lons[i] % 360 for i in order]
    # unwrap so that pos is monotonically increasing; start the cycle after the largest gap
    gaps = [((pos[(k + 1) % n] - pos[k]) % 360) for k in range(n)]
    start = (max(range(n), key=lambda k: gaps[k]) + 1) % n
    pos = [pos[(start + k) % n] for k in range(n)]
    idx = [order[(start + k) % n] for k in range(n)]
    for k in range(1, n):
        while pos[k] < pos[k - 1]:
            pos[k] += 360
    for _ in range(iterations):
        moved = False
        for k in range(n):
            nxt = pos[k + 1] if k + 1 < n else pos[0] + 360
            gap = nxt - pos[k]
            if gap < min_sep - 1e-9:
                shift = (min_sep - gap) / 2.0
                pos[k] -= shift
                if k + 1 < n:
                    pos[k + 1] += shift
                else:
                    pos[0] += shift
                moved = True
        if not moved:
            break
    res = [0.0] * n
    for k in range(n):
        res[idx[k]] = pos[k] % 360
    return res


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


def _svg_open(size: int, t: Dict[str, Any]) -> List[str]:
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
           f'font-family="{FONT}" role="img">',
           f'<rect x="0" y="0" width="{size}" height="{size}" fill="{t["paper"]}"/>']
    if t is THEMES["starry_night"]:
        for fx, fy, r in _STARS:
            out.append(f'<circle cx="{fx * size:.1f}" cy="{fy * size:.1f}" r="{r}" fill="#F8FAFC" '
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
                                  show_antiscia: bool = False) -> str:
    t = _theme(theme)
    INK, GOLD, NAVY, PAPER, CARD = t["ink"], t["gold"], t["navy"], t["center_bg"], t["card"]
    HORARY_GOLD, HORARY_FILL, MUTED = t["horary_gold"], t["horary_fill"], t["muted"]
    n = _norm(report_data, show_all_lots)
    hor = n["horary"]
    if not show_stars:
        n["fixed_stars"] = []
    out = _svg_open(820, t)
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
    out.append(_text(410, 806, "William Lilly, Christian Astrology (1647) — Traditional Square Chart", 10, MUTED))
    out.append("</svg>")
    return "\n".join(out)


# --------------------------------------------------------- circular chart
CX = CY = 430.0


def _pt(lon: float, anchor: float, r: float):
    a = math.radians((180.0 - (lon - anchor)) % 360.0)
    return CX + r * math.cos(a), CY + r * math.sin(a)


def _sector(a0: float, a1: float, r_out: float, r_in: float, anchor: float) -> str:
    x0, y0 = _pt(a0, anchor, r_out)
    x1, y1 = _pt(a1, anchor, r_out)
    x2, y2 = _pt(a1, anchor, r_in)
    x3, y3 = _pt(a0, anchor, r_in)
    return (f"M{x0:.2f},{y0:.2f} A{r_out},{r_out} 0 0 0 {x1:.2f},{y1:.2f} "
            f"L{x2:.2f},{y2:.2f} A{r_in},{r_in} 0 0 1 {x3:.2f},{y3:.2f} Z")


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


def _overlay_planets(n: Dict[str, Any], mode: str) -> List[Dict[str, Any]]:
    key = {"solar_arc": "sa_data", "secondary": "sec_prog_data", "tertiary": "tert_prog_data",
           "synastry": "synastry_data"}.get(mode)
    data = n["rd"].get(key) or {}
    res = []
    for p in data.get("planets") or []:
        if p.get("id") in PLANET_GLYPHS and p.get("longitude") is not None:
            res.append({"id": p["id"], "glyph": PLANET_GLYPHS[p["id"]], "lon": float(p["longitude"]) % 360,
                        "retro": bool(p.get("is_retrograde"))})
    return res


def render_circular_chart_svg(report_data: dict, overlay_mode: str = "none",
                              show_lots: bool = True, show_aspects: bool = True,
                              theme: str = "parchment", show_all_lots: bool = False,
                              show_stars: bool = True, show_antiscia: bool = False) -> str:
    t = _theme(theme)
    INK, GOLD, NAVY, PAPER, CARD = t["ink"], t["gold"], t["navy"], t["center_bg"], t["card"]
    HORARY_GOLD, HORARY_FILL, MUTED = t["horary_gold"], t["horary_fill"], t["muted"]
    ELEMENT_FILL = t["element_fill"]
    n = _norm(report_data, show_all_lots)
    hor = n["horary"]
    if not show_stars:
        n["fixed_stars"] = []
    anchor = n["houses"][0]["lon"]
    overlay = overlay_mode if overlay_mode in OVERLAY_STYLE else "none"
    ov_color, ov_label = OVERLAY_STYLE.get(overlay, (INK, ""))
    if overlay == "synastry":
        ov_color = t["synastry"]
    ov_planets = _overlay_planets(n, overlay) if overlay != "none" else []
    syn = n["rd"].get("synastry_data") or {}
    name_a = syn.get("person_a") or "本命"
    name_b = syn.get("person_b") or "合盤對象"

    R_OUT, R_ZOD = 360.0, 322.0
    if overlay != "none":
        prog_outer, natal_outer = R_ZOD, R_ZOD - 50
    else:
        natal_outer = R_ZOD
    h_out = natal_outer - 58
    R_ASP = h_out - 32

    out = _svg_open(860, t)
    out.append(f'<circle cx="{CX}" cy="{CY}" r="{R_OUT + 6}" fill="{CARD}" stroke="{INK}" stroke-width="2"/>')

    # zodiac ring
    for i in range(12):
        out.append(f'<path d="{_sector(i * 30, (i + 1) * 30, R_OUT, R_ZOD, anchor)}" '
                   f'fill="{ELEMENT_FILL[SIGN_ELEMENT[i]]}" stroke="{INK}" stroke-width="1"/>')
        mx, my = _pt(i * 30 + 15, anchor, (R_OUT + R_ZOD) / 2)
        out.append(_text(mx, my + 2, f"{SIGN_GLYPHS[i]}{TEXT_VS}", 20, NAVY))
        nx, ny = _pt(i * 30 + 15, anchor, (R_OUT + R_ZOD) / 2 - 15)
        out.append(_text(nx, ny + 3, SIGN_NAMES[i], 9, MUTED))
    for d in range(0, 360, 5):
        ln = 9 if d % 10 == 0 else 5
        x1, y1 = _pt(d, anchor, R_ZOD)
        x2, y2 = _pt(d, anchor, R_ZOD - ln)
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{INK}" stroke-width="0.7"/>')

    # houses
    out.append(f'<circle cx="{CX}" cy="{CY}" r="{h_out}" fill="none" stroke="{INK}" stroke-width="1.2"/>')
    out.append(f'<circle cx="{CX}" cy="{CY}" r="{R_ASP}" fill="{PAPER}" stroke="{INK}" stroke-width="1.2"/>')
    for i in range(12):
        hi = hor is not None and (i + 1) in (1, hor["q_house"])
        if hi:
            out.append(f'<path d="{_sector(i * 30, (i + 1) * 30, h_out, R_ASP, anchor)}" fill="{HORARY_FILL}" '
                       f'stroke="none" class="house-hl"/>')
        x1, y1 = _pt(i * 30, anchor, R_ASP)
        x2, y2 = _pt(i * 30, anchor, R_ZOD)
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{INK}" stroke-width="1"/>')
        lx, ly = _pt(i * 30 + 15, anchor, (h_out + R_ASP) / 2)
        out.append(_text(lx, ly + 4, f"第{CN_NUM[i]}宮", 11, GOLD, weight="bold"))

    # angle axes
    for lbl, lon, col in (("ASC", n["asc"], t["asc_col"]), ("DSC", (n["asc"] + 180) % 360, t["asc_col"]),
                          ("MC", n["mc"], t["mc_col"]), ("IC", (n["mc"] + 180) % 360, t["mc_col"])):
        x1, y1 = _pt(lon, anchor, R_ASP)
        x2, y2 = _pt(lon, anchor, R_OUT)
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="2"/>')
        ax, ay = _pt(lon, anchor, R_OUT + 8)
        bx, by = _pt(lon + 1.6, anchor, R_OUT + 1)
        cx2, cy2 = _pt(lon - 1.6, anchor, R_OUT + 1)
        out.append(f'<polygon points="{ax:.1f},{ay:.1f} {bx:.1f},{by:.1f} {cx2:.1f},{cy2:.1f}" fill="{col}"/>')
        tx, ty = _pt(lon, anchor, R_OUT + 28)
        out.append(_text(tx, ty - 1, lbl, 11, col, weight="bold"))
        out.append(_text(tx, ty + 11, _dms(lon), 9.5, col))

    # natal planets
    items = list(n["planets"]) + (n["lots"] if show_lots else [])
    disp = spread_longitudes([p["lon"] for p in items], 6.5)
    node_pos: Dict[str, float] = {}
    for p, dl in zip(items, disp):
        sig = hor is not None and p["id"] in hor["sigs"]
        ex, ey = _pt(p["lon"], anchor, h_out)
        tx, ty = _pt(p["lon"], anchor, h_out + 7)
        lx, ly = _pt(dl, anchor, natal_outer - 44)
        out.append(f'<line x1="{ex:.1f}" y1="{ey:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" stroke="{NAVY}" stroke-width="1.6"/>')
        out.append(f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{lx:.1f}" y2="{ly:.1f}" stroke="{MUTED}" stroke-width="0.8"/>')
        gx, gy = _pt(dl, anchor, natal_outer - 17)
        if sig:
            out.append(f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="14" fill="{HORARY_FILL}" stroke="{HORARY_GOLD}" '
                       f'stroke-width="2.2" class="sig-badge" data-planet="{_e(p["id"])}"/>')
        out.append(_text(gx, gy + 7, f"{p['glyph']}{TEXT_VS}", 20, NAVY, weight="bold"))
        dx, dy = _pt(dl, anchor, natal_outer - 36)
        out.append(_text(dx, dy + 3, _dms(p["lon"]) + (" Ⓡ" if p.get("retro") else ""), 9, MUTED))
        sc = p.get("score")
        if show_stars and isinstance(sc, (int, float)):
            bx, by = _pt(dl, anchor, natal_outer - 48)
            col = t["pos_score"] if sc > 0 else (t["neg_score"] if sc < 0 else MUTED)
            out.append(f'<rect x="{bx - 11:.1f}" y="{by - 5:.1f}" width="22" height="11" rx="5.5" fill="{PAPER}" '
                       f'stroke="{col}" stroke-width="1" class="dignity-badge"/>')
            out.append(_text(bx, by + 3.5, f"[{int(sc):+d}]" if sc else "[0]", 8, col, weight="bold"))
        if p["id"] == n["almuten_id"] and not hor:
            rx, ry = _pt(dl, anchor, natal_outer - 17)
            out.append(f'<circle cx="{rx:.1f}" cy="{ry:.1f}" r="17" fill="none" stroke="{GOLD}" stroke-width="1.5" '
                       f'class="almuten-ring"/>')
            kx, ky = _pt(dl, anchor, natal_outer + 2)
            out.append(_text(kx, ky + 4, "👑", 12))
        if p["id"] in PLANET_GLYPHS:
            node_pos[p["id"]] = p["lon"]

    # fixed star conjunction markers on outer rim
    if show_stars and n["fixed_stars"]:
        sdisp = spread_longitudes([s["lon"] for s in n["fixed_stars"]], 6.5)
        for s, dl in zip(n["fixed_stars"], sdisp):
            x1, y1 = _pt(s["lon"], anchor, R_OUT)
            x2, y2 = _pt(dl, anchor, R_OUT + 14)
            lx2, ly2 = _pt(dl, anchor, R_OUT + 27)
            out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{GOLD}" '
                       f'stroke-width="0.9" stroke-dasharray="2 2"/>')
            out.append(f'<g class="fixed-star-marker" data-star="{_e(s["star"])}">'
                       + _text(x2, y2 + 4, "★", 13, GOLD, weight="bold")
                       + _text(lx2, ly2 + 3, f"★{s['short_name']}", 9, GOLD, weight="bold")
                       + '</g>')

    # progressed / directed outer ring
    if ov_planets:
        out.append(f'<circle cx="{CX}" cy="{CY}" r="{natal_outer}" fill="none" stroke="{ov_color}" '
                   f'stroke-width="1" stroke-dasharray="4 3"/>')
        pd_ = spread_longitudes([p["lon"] for p in ov_planets], 6.5)
        for p, dl in zip(ov_planets, pd_):
            ex, ey = _pt(p["lon"], anchor, R_ZOD)
            tx, ty = _pt(p["lon"], anchor, R_ZOD - 8)
            lx, ly = _pt(dl, anchor, R_ZOD - 14)
            out.append(f'<line x1="{ex:.1f}" y1="{ey:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" stroke="{ov_color}" stroke-width="1.6"/>')
            out.append(f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{lx:.1f}" y2="{ly:.1f}" stroke="{ov_color}" stroke-width="0.7"/>')
            gx, gy = _pt(dl, anchor, R_ZOD - 25)
            out.append(f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="11" fill="{t["ov_badge_bg"]}" stroke="{ov_color}" stroke-width="1.5" class="ov-badge"/>')
            out.append(_text(gx, gy + 6, f"{p['glyph']}{TEXT_VS}", 16, ov_color, weight="bold"))
            dx, dy = _pt(dl, anchor, R_ZOD - 43)
            out.append(_text(dx, dy + 3, _dms(p["lon"]), 8.5, ov_color))

    # aspect web
    if show_aspects:
        sigs = hor["sigs"] if hor else set()
        ids = [p["id"] for p in n["planets"]]
        by_id = {p["id"]: p for p in n["planets"]}
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = by_id[ids[i]], by_id[ids[j]]
                diff = _angdiff(a["lon"], b["lon"])
                for ang, (nm, col) in ASPECTS.items():
                    if ang == 0 or abs(diff - ang) > 6.0:
                        continue
                    x1, y1 = _pt(a["lon"], anchor, R_ASP - 2)
                    x2, y2 = _pt(b["lon"], anchor, R_ASP - 2)
                    key = a["id"] in sigs and b["id"] in sigs
                    if key:
                        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{HORARY_GOLD}" '
                                   f'stroke-width="3.5" class="asp-key"/>')
                    out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" '
                               f'stroke-width="1.2" class="asp"><title>{_e(a["name"])} {nm} {_e(b["name"])}</title></line>')
        for p in ov_planets:
            for nid, nlon in node_pos.items():
                diff = _angdiff(p["lon"], nlon)
                for ang in (0, 60, 90, 120, 180):
                    if abs(diff - ang) <= (5.0 if overlay == "synastry" else 1.5) and not (ang == 0 and p["id"] == nid):
                        x1, y1 = _pt(p["lon"], anchor, R_ASP - 2)
                        x2, y2 = _pt(nlon, anchor, R_ASP - 2)
                        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{ov_color}" '
                                   f'stroke-width="1.4" stroke-dasharray="5 3" class="trigger"/>')
        for pid, lon in node_pos.items():
            x, y = _pt(lon, anchor, R_ASP - 2)
            sig = pid in (hor["sigs"] if hor else ())
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{5 if sig else 3}" fill="{HORARY_GOLD if sig else NAVY}" '
                       f'stroke="{NAVY}" stroke-width="0.8"/>')

    # antiscia: solstice mirror axis, ghost points, contact chords
    if show_antiscia:
        ax_col = "#C084FC" if theme == "starry_night" else "#8B5CF6"
        gold_col = t["horary_gold"]
        sx1, sy1 = _pt(90.0, anchor, R_ZOD)
        sx2, sy2 = _pt(270.0, anchor, R_ZOD)
        out.append(f'<line x1="{sx1:.1f}" y1="{sy1:.1f}" x2="{sx2:.1f}" y2="{sy2:.1f}" '
                   f'stroke="{ax_col}" stroke-width="1.6" stroke-dasharray="6 4" class="solstice-axis"/>')
        for lon, lbl in ((90.0, "♋ 0° 夏至軸"), (270.0, "♑ 0° 冬至軸")):
            tx_, ty_ = _pt(lon, anchor, R_ZOD + 12)
            out.append(_text(tx_, ty_ + 4, lbl, 10, ax_col, weight="bold", extra='class="solstice-label"'))
        for p in n["planets"]:
            gx_, gy_ = _pt((180.0 - p["lon"]) % 360, anchor, h_out - 12)
            out.append(f'<g class="antiscia-point" opacity="0.65" data-planet="{_e(p["id"])}">'
                       + _text(gx_, gy_ + 5, f"{p['glyph']}{TEXT_VS}′", 13, ax_col, weight="bold")
                       + f'<title>{_e(p["name"])} 映點 {_dms((180.0 - p["lon"]) % 360)}</title></g>')
        a_contacts = _antiscia_contacts(n)
        for c in a_contacts:
            x1, y1 = _pt(c["la"], anchor, R_ASP - 2)
            x2, y2 = _pt(c["lb"], anchor, R_ASP - 2)
            mx_, my_ = (x1 + x2) / 2, (y1 + y2) / 2
            qx, qy = CX + (mx_ - CX) * 0.45, CY + (my_ - CY) * 0.45
            dash = "1 4" if c["type"] == "映點" else "5 2 1 2"
            d_attr = f"M{x1:.1f},{y1:.1f} Q{qx:.1f},{qy:.1f} {x2:.1f},{y2:.1f}"
            out.append(f'<path d="{d_attr}" fill="none" stroke="{gold_col}" stroke-width="3.2" stroke-linecap="round" '
                       f'stroke-dasharray="{dash}" class="antiscia-line"><title>{c["ga"]} {c["type"]} {c["gb"]}</title></path>')
            out.append(f'<path d="{d_attr}" fill="none" stroke="{ax_col}" stroke-width="1.2" '
                       f'stroke-dasharray="{dash}" class="antiscia-line"/>')
        if a_contacts:
            out.append(_text(14, 640, "🪞 映點接觸", 10.5, ax_col, anchor="start", weight="bold"))
            for k, c in enumerate(a_contacts[:3]):
                out.append(_text(14, 654 + k * 14, f"{c['ga']}-{c['gb']} {c['type']} {c['orb']:.1f}°", 10, MUTED, anchor="start"))

    # header / footer / legend
    ml = _meta_lines(n)
    title = "古典卜卦占星盤 (整宮制)" if hor else "古典占星本命星盤 (整宮制)"
    out.append(_text(CX, 20, title, 16, NAVY, weight="bold"))
    out.append(_text(CX, 846, f"{ml['date']}  ·  {ml['place']}", 11, MUTED))
    ly = 40
    if overlay != "none":
        out.append(f'<circle cx="22" cy="{ly - 4}" r="6" fill="{t["ov_badge_bg"]}" stroke="{ov_color}" stroke-width="2"/>')
        out.append(_text(34, ly, (f"外環：合盤對象 ({name_b})" if overlay == "synastry" else f"外環：{ov_label}"),
                         11, ov_color, anchor="start", weight="bold"))
        out.append(_text(34, ly + 16, (f"內環：本命 ({name_a})" if overlay == "synastry" else "內環：本命 (Natal)"),
                         11, NAVY, anchor="start"))
    if hor:
        out.append(_text(14, 830, f"★ Lord 1 {hor['lord_1_name']} · Lord Q {hor['lord_q_name']} · 月亮", 11, GOLD,
                         anchor="start", weight="bold"))
        out.append(_text(846, 830, f"裁決：{hor['verdict']}", 11, NAVY, anchor="end", weight="bold"))
    else:
        out.append(_text(846, 20, "☀️ 日間盤" if n["is_day"] else ("🌙 夜間盤" if n["is_day"] is not None else ""),
                         12, GOLD, anchor="end", weight="bold"))
    if not hor and _almuten_line(n):
        out.append(_text(846, 38, _almuten_line(n), 11, GOLD, anchor="end", weight="bold"))
    if show_stars and n["fixed_stars"]:
        out.append(_text(846, 810, "★ 恆星合相", 10.5, GOLD, anchor="end", weight="bold"))
        out.append(_text(846, 824, "；".join(f"{s['short_name']}-{s['planet']}" for s in n["fixed_stars"][:4]),
                         10, MUTED, anchor="end"))
    lx0 = 14
    for k, (ang, (nm, col)) in enumerate(a for a in ASPECTS.items() if a[0] != 0):
        out.append(f'<line x1="{lx0}" y1="{700 + k * 16}" x2="{lx0 + 18}" y2="{700 + k * 16}" stroke="{col}" stroke-width="2"/>')
        out.append(_text(lx0 + 24, 704 + k * 16, f"{nm} {ang}°", 10, MUTED, anchor="start"))
    out.append("</svg>")
    return "\n".join(out)


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
    var c = document.createElement('canvas'); c.width = SIZE; c.height = SIZE;
    var ctx = c.getContext('2d'); ctx.fillStyle = BG; ctx.fillRect(0,0,SIZE,SIZE);
    ctx.drawImage(img, 0, 0, SIZE, SIZE); URL.revokeObjectURL(url); cb(c);
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


def draw_circular_chart(user_data_or_report_data):
    """Backward-compatible wrapper: returns circular chart SVG, or None on failure."""
    try:
        if isinstance(user_data_or_report_data, dict) and "houses" in user_data_or_report_data:
            return render_circular_chart_svg(user_data_or_report_data)
    except Exception as exc:
        print(f"Error in draw_circular_chart: {exc}")
    return None
