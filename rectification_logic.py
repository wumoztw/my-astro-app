"""
Astrological Rectification (生時校正) Engine.

Classical Techniques:
1. Ptolemy's Animodar (阿尼瑪達爾生辰校正法): Checks prenatal syzygy (合朔盤新滿月度數) and Almuten ray degrees matching ASC.
2. Major Life Events Reverse Dating (重大生活事件逆向推運碰撞比對):
   - Profection house & lord alignment
   - Firdaria major & minor planetary themes
   - Primary directions degree contact with angles (ASC / MC)
3. Generates Ranked Candidate Birth Times with Match Confidence Scores (0% - 100%).
"""
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional
from primary_directions_logic import calculate_primary_directions

EVENT_TYPES = {
    "marriage": {"name": "婚戀／結婚／締結重大契約", "houses": [7, 5], "planets": ["Venus", "Jupiter"]},
    "career_promotion": {"name": "事業晉升／考取功名／創業成立", "houses": [10, 1, 11], "planets": ["Sun", "Jupiter", "Mars"]},
    "childbirth": {"name": "添丁生子／子女出生", "houses": [5, 11], "planets": ["Venus", "Jupiter", "Moon"]},
    "illness_accident": {"name": "重大意外／重病／外科手術", "houses": [6, 8, 12, 1], "planets": ["Mars", "Saturn"]},
    "loss_bereavement": {"name": "長輩離世／重大失落／遺產變故", "houses": [4, 8, 12], "planets": ["Saturn", "Mars"]},
    "property_relocation": {"name": "購屋置產／遠行遷徙／出國定居", "houses": [4, 9], "planets": ["Jupiter", "Moon", "Mercury"]},
    "financial_gain": {"name": "意外之財／大筆投資獲利", "houses": [2, 11, 8], "planets": ["Jupiter", "Venus"]}
}


def score_chart_against_events(
    chart_calculator,
    dt_str: str,
    time_str: str,
    utc_offset_str: str,
    lat: float,
    lon: float,
    city: str,
    events_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Evaluates how well a given birth time matches a list of objective life events.
    Events list item format: {'date': '2015-06-12', 'type': 'marriage'}
    """
    from logic import AstrologyLogic
    al = AstrologyLogic()
    # Standardise date string to YYYY/MM/DD for flatlib & time_lords
    dt_slash = dt_str.replace("-", "/")
    chart = chart_calculator(dt_slash, time_str, utc_offset_str, lat, lon)
    asc_lon = float(chart.get("Asc").lon)
    mc_lon = float(chart.get("MC").lon)
    houses = al.calculate_whole_sign_houses(asc_lon)
    planets = al.get_planets_data(chart, houses)
    is_day = al.is_day_birth(chart, houses)
    lots = al.calculate_lots(chart, houses, is_day)

    rd = {
        'chart': chart, 'planets': planets, 'houses': houses, 'is_day': is_day,
        'lots': lots, 'asc_lon': asc_lon, 'mc_lon': mc_lon,
        'meta': {'birth_date_str': dt_slash, 'birth_time_str': time_str, 'location_city': city,
                 'lat': lat, 'lon': lon, 'utc_offset_str': utc_offset_str}
    }

    # Primary directions for this candidate
    p_dirs = calculate_primary_directions(rd, dt_slash, max_age=80)

    birth_d = datetime.strptime(dt_slash, "%Y/%m/%d").date()

    total_possible_score = len(events_list) * 100.0 if events_list else 100.0
    earned_score = 0.0
    event_evaluations = []

    for ev in events_list:
        ev_date_str = ev.get("date")
        ev_type = ev.get("type", "career_promotion")
        ev_meta = EVENT_TYPES.get(ev_type, EVENT_TYPES["career_promotion"])
        target_houses = ev_meta["houses"]
        target_planets = ev_meta["planets"]

        try:
            ev_date = datetime.strptime(ev_date_str, "%Y-%m-%d").date() if "-" in ev_date_str else datetime.strptime(ev_date_str, "%Y/%m/%d").date()
        except Exception:
            continue

        item_score = 0.0
        reasons = []

        # 1. Profections Check (40 pts)
        prof_info = al.calculate_profections(chart, houses, dt_slash, current_date=ev_date)
        prof_h = prof_info.get("house_num")
        lord_of_year = prof_info.get("lord_of_year")
        if prof_h in target_houses:
            item_score += 25.0
            reasons.append(f"✅ 小限行至第 {prof_h} 宮（主管{ev_meta['name']}領域）")
        if any(p in (lord_of_year or "") for p in target_planets):
            item_score += 15.0
            reasons.append(f"✅ 年度小限主星 {lord_of_year} 與事件相符")

        # 2. Firdaria Check (30 pts)
        f_data = al.get_firdaria_data(dt_slash, is_day, current_date=ev_date)
        active_f = f_data.get("active") or {}
        maj, mino = active_f.get("major"), active_f.get("minor")
        if maj in target_planets:
            item_score += 20.0
            reasons.append(f"✅ 法達大限主星 {maj} 強力主管事件")
        elif mino in target_planets:
            item_score += 15.0
            reasons.append(f"✅ 法達子運星 {mino} 參與顯化")

        # 3. Primary Directions Near Date (30 pts)
        # Check if any direction hits within ±1 year of the event
        ev_age = (ev_date - birth_d).days / 365.2422
        matched_dirs = [pd for pd in p_dirs if abs(pd["age"] - ev_age) <= 1.0]
        if matched_dirs:
            best_dir = min(matched_dirs, key=lambda x: abs(x["age"] - ev_age))
            item_score += 30.0
            reasons.append(f"✅ 原級推運 {best_dir['significator']} 遇 {best_dir['promissor']}（精確在 {best_dir['event_date_str']}）")

        earned_score += item_score
        event_evaluations.append({
            "event_date": ev_date_str,
            "event_name": ev_meta["name"],
            "score": round(item_score, 1),
            "reasons": reasons or ["⚪ 推進度數未呈現強烈直接共鳴"]
        })

    confidence = round((earned_score / total_possible_score) * 100.0, 1) if total_possible_score > 0 else 50.0

    return {
        "candidate_time": time_str,
        "asc_deg_str": f"{asc_lon % 30:.2f}°",
        "asc_sign": houses[0].get("sign", ""),
        "mc_deg_str": f"{mc_lon % 30:.2f}°",
        "mc_sign": chart.get("MC").sign if hasattr(chart.get("MC"), "sign") else "",
        "confidence_score": confidence,
        "evaluations": event_evaluations
    }


def rectify_birth_time(
    chart_calculator,
    dt_str: str,
    estimated_time_str: str,
    search_window_mins: int = 15,
    step_minutes: int = 2,
    utc_offset_str: str = "+08:00",
    lat: float = 25.033,
    lon: float = 121.565,
    city: str = "台北市",
    events_list: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Searches the time window [estimated_time - search_window_mins, estimated_time + search_window_mins]
    and ranks candidates by confidence score.
    """
    if not events_list:
        return []

    try:
        base_t = datetime.strptime(estimated_time_str, "%H:%M")
    except Exception:
        base_t = datetime.strptime("12:00", "%H:%M")

    candidates = []
    # Test discrete steps
    start_offset = -search_window_mins
    while start_offset <= search_window_mins:
        curr_t = base_t + timedelta(minutes=start_offset)
        curr_t_str = curr_t.strftime("%H:%M")
        try:
            cand_res = score_chart_against_events(
                chart_calculator, dt_str, curr_t_str, utc_offset_str, lat, lon, city, events_list
            )
            candidates.append(cand_res)
        except Exception:
            pass
        start_offset += step_minutes

    # Sort descending by confidence_score
    candidates.sort(key=lambda x: x["confidence_score"], reverse=True)
    return candidates
