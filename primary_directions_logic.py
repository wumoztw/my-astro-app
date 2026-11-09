"""
Primary Directions (原級推運 / 赤道主向推運) Logic Engine.

Based on Ptolemy's Key and classical semi-arc spherical principles:
- Ptolemy's Key: 1° of equatorial arc of direction (approx. 4 mins of sidereal diurnal rotation) = 1 solar tropical year (Naibod / Ptolemy 1° = 1.000 year, Naibod 1° = 1.0146 years).
- Significators: Ascendant (ASC), Midheaven (MC), Sun, Moon, Fortuna (Part of Fortune).
- Promissors: 7 Classical Planets (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn) and their 5 Ptolemaic major aspects (Conjunction 0°, Sextile 60°, Square 90°, Trine 120°, Opposition 180°).
"""
import math
from datetime import datetime, date
from typing import Any, Dict, List, Optional

PLANET_NAMES_ZH = {
    "Sun": "太陽", "Moon": "月亮", "Mercury": "水星",
    "Venus": "金星", "Mars": "火星", "Jupiter": "木星", "Saturn": "土星"
}
PLANET_GLYPHS = {
    "Sun": "☉", "Moon": "☽", "Mercury": "☿",
    "Venus": "♀", "Mars": "♂", "Jupiter": "♃", "Saturn": "♄"
}
SIGN_NAMES_ZH = [
    "牡羊", "金牛", "雙子", "巨蟹", "獅子", "處女",
    "天秤", "天蠍", "射手", "魔羯", "水瓶", "雙魚"
]
ASPECT_ANGLES = {
    0: ("合相 (Conjunction)", "☌", "強烈融合／開創重大新週期"),
    60: ("六合 (Sextile)", "⚹", "機遇浮現、貴人提攜、環境助力"),
    90: ("刑相 (Square)", "□", "重大阻礙、衝突壓力、強迫轉型"),
    120: ("拱相 (Trine)", "△", "順遂豐收、名利成就、平安吉慶"),
    180: ("衝相 (Opposition)", "☍", "對立危機、合作破裂、極端考驗")
}

# Standard obliquity of ecliptic (approx. 23.44°)
EPSILON_RAD = math.radians(23.44)


def ecliptic_to_equatorial(lon_deg: float, lat_deg: float = 0.0) -> tuple:
    """Converts ecliptic longitude (and latitude) to right ascension (RA) and declination (Decl)."""
    lam = math.radians(lon_deg % 360)
    beta = math.radians(lat_deg)
    sin_delta = math.sin(beta) * math.cos(EPSILON_RAD) + math.cos(beta) * math.sin(EPSILON_RAD) * math.sin(lam)
    decl_rad = math.asin(max(-1.0, min(1.0, sin_delta)))
    y = math.sin(lam) * math.cos(EPSILON_RAD) - math.tan(beta) * math.sin(EPSILON_RAD)
    x = math.cos(lam)
    ra_rad = math.atan2(y, x)
    ra_deg = (math.degrees(ra_rad) + 360.0) % 360.0
    decl_deg = math.degrees(decl_rad)
    return ra_deg, decl_deg


def calculate_primary_directions(
    chart_data: Dict[str, Any],
    birth_date_str: str,
    max_age: int = 80,
    direction_key: str = "ptolemy"  # 'ptolemy' (1° = 1.0 yr) or 'naibod' (1° = 1.0146 yr)
) -> List[Dict[str, Any]]:
    """
    Computes direct Primary Directions from birth to max_age.
    Significators: ASC, MC, Sun, Moon, Fortuna.
    Promissors: 7 classical planets (body & 5 aspects).
    """
    birth_dt = None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            birth_dt = datetime.strptime(birth_date_str, fmt).date()
            break
        except Exception:
            pass
    if not birth_dt:
        birth_dt = date(1990, 1, 1)

    # Degree to year rate
    deg_per_year = 1.0 if direction_key == "ptolemy" else (360.0 / 365.2422)

    planets = chart_data.get("planets") or []
    planet_map = {}
    for p in planets:
        pid = p.get("id")
        lon = p.get("lon", p.get("longitude"))
        if pid in PLANET_NAMES_ZH and lon is not None:
            ra, decl = ecliptic_to_equatorial(float(lon))
            planet_map[pid] = {
                "id": pid,
                "name": p.get("name") or PLANET_NAMES_ZH[pid],
                "glyph": PLANET_GLYPHS.get(pid, ""),
                "lon": float(lon) % 360,
                "ra": ra,
                "decl": decl
            }

    # Significators
    asc_lon = chart_data.get("asc_lon")
    mc_lon = chart_data.get("mc_lon")
    if asc_lon is None and chart_data.get("asc"):
        try:
            asc_lon = float(chart_data["chart"].get("Asc").lon)
        except Exception:
            asc_lon = 0.0
    if mc_lon is None and chart_data.get("mc"):
        try:
            mc_lon = float(chart_data["chart"].get("MC").lon)
        except Exception:
            mc_lon = (float(asc_lon or 0.0) + 270.0) % 360.0

    significators = []
    if asc_lon is not None:
        ra, decl = ecliptic_to_equatorial(float(asc_lon))
        significators.append({"id": "ASC", "name": "上升點 (ASC)", "glyph": "🧭", "lon": float(asc_lon), "ra": ra, "role": "生命／健康／自我定位"})
    if mc_lon is not None:
        ra, decl = ecliptic_to_equatorial(float(mc_lon))
        significators.append({"id": "MC", "name": "天頂 (MC)", "glyph": "👑", "lon": float(mc_lon), "ra": ra, "role": "事業／名聲／社會地位"})
    if "Sun" in planet_map:
        significators.append({**planet_map["Sun"], "role": "本質光芒／尊貴／權柄"})
    if "Moon" in planet_map:
        significators.append({**planet_map["Moon"], "role": "身心感知／公眾人緣／家庭"})

    lots = chart_data.get("lots") or []
    if lots and lots[0].get("lon") is not None:
        f_lon = float(lots[0]["lon"]) % 360
        ra, decl = ecliptic_to_equatorial(f_lon)
        significators.append({"id": "Fortuna", "name": "福德點 (Lot of Fortune)", "glyph": "⊗", "lon": f_lon, "ra": ra, "role": "財富福祿／肉身受用"})

    events: List[Dict[str, Any]] = []

    # Calculate Arc of Direction (Direct: Promissor advances eastward in diurnal motion towards Significator's position)
    # Arc = (RA_promissor - RA_significator) mod 360
    for sig in significators:
        sig_ra = sig["ra"]
        for p_id, prom in planet_map.items():
            if p_id == sig.get("id"):
                continue  # Skip self
            
            # Check 5 major Ptolemaic aspect rays of promissor
            for angle, (asp_name, asp_sym, asp_desc) in ASPECT_ANGLES.items():
                # Promissor ray longitude
                for sign_mult in (-1, 1):
                    if angle == 0 and sign_mult == -1:
                        continue
                    if angle == 180 and sign_mult == -1:
                        continue
                    ray_lon = (prom["lon"] + sign_mult * angle) % 360.0
                    ray_ra, _ = ecliptic_to_equatorial(ray_lon)
                    
                    # Direct direction arc: promissor ray towards significator
                    arc = (ray_ra - sig_ra) % 360.0
                    if 0.1 <= arc <= (max_age * deg_per_year):
                        age = arc / deg_per_year
                        event_year = birth_dt.year + int(age)
                        event_month = int((age - int(age)) * 12) + 1
                        if event_month > 12:
                            event_month = 12
                            event_year += 1
                        
                        # Interpret nature
                        benefic = p_id in ("Jupiter", "Venus", "Sun")
                        malefic = p_id in ("Saturn", "Mars")
                        is_hard = angle in (90, 180)
                        
                        tone = "吉相亨通" if (benefic and not is_hard) or (benefic and angle == 120) else (
                            "凶險磨難" if (malefic and is_hard) else (
                                "考驗與轉型" if is_hard else "中性顯化"
                            )
                        )

                        events.append({
                            "age": round(age, 2),
                            "event_date_str": f"{event_year} 年 {event_month:02d} 月",
                            "significator": sig["name"],
                            "significator_glyph": sig.get("glyph", ""),
                            "promissor": prom["name"],
                            "promissor_glyph": prom["glyph"],
                            "aspect_name": asp_name,
                            "aspect_symbol": asp_sym,
                            "arc_deg": round(arc, 2),
                            "nature": tone,
                            "meaning": f"【{sig['name']} 遇 {prom['glyph']} {prom['name']} {asp_sym} {asp_name}】：{asp_desc}。影響領域聚焦於：{sig['role']}。"
                        })

    # Sort events by age
    events.sort(key=lambda x: x["age"])
    return events
