import streamlit as st
import pandas as pd
import os
import traceback
from datetime import datetime, date, timedelta, timezone
from flatlib import const

import sys
import importlib

# Ensure fresh module reloading in Streamlit Cloud when git updates
for _mod_name in (
    'logic', 'horary_engine_logic', 'dignities_logic', 'aspects_logic', 'lots_logic', 
    'time_lords_logic', 'zodiacal_releasing_logic', 'solar_arc_logic', 'solar_return_logic', 'predictive_extensions_logic',
    'almuten_logic', 'classical_natal_core_logic', 'secondary_progressions_logic', 'tertiary_progressions_logic',
    'thematic_reports_logic', 'horary_prompt', 'natal_prompt', 'ai_logic'
):
    if _mod_name in sys.modules:
        try:
            importlib.reload(sys.modules[_mod_name])
        except Exception:
            pass

# Modular Imports
from logic import AstrologyLogic
from horary_prompt import HORARY_SYSTEM_PROMPT
from natal_prompt import NATAL_SYSTEM_PROMPT
from thematic_reports_logic import ThematicReportsLogic

import streamlit.components.v1 as components

# Initialize Logic
logic = AstrologyLogic()

st.set_page_config(page_title="古典占星命盤簡易排盤程式", layout="wide")

# Detect browser timezone for UTC offset (optional utility)
components.html(
    """
    <script>
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const urlParams = new URLSearchParams(window.parent.location.search);
    if (urlParams.get('tz') !== tz) {
        urlParams.set('tz', tz);
        window.parent.location.search = urlParams.toString();
    }
    </script>
    """,
    height=0,
)

# Read detected timezone (default to UTC if not yet synced)
browser_tz_name = st.query_params.get("tz", "UTC")

# --- Custom Styling (Classical Western Astrology Dashboard — Japanese Minimalist Muji Style) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&family=Noto+Sans+TC:wght@400;500&family=Noto+Serif+TC:wght@500;600;700&family=Noto+Serif:wght@500;600&display=swap');

    /* Global Background & Font */
    .stApp {
        background-color: #FAFAFC !important;
        color: #0B1C30 !important;
        font-family: 'Noto Sans TC', 'Inter', sans-serif !important;
        line-height: 1.6;
    }
    
    p, li, label, .stMarkdown p {
        font-family: 'Noto Sans TC', 'Inter', sans-serif !important;
        line-height: 1.6;
        color: #0B1C30;
    }

    /* Streamlit Material Icons & UI Control Icons Protection */
    [data-testid*="Icon"], [data-testid*="icon"], [class*="material-symbols"], [class*="icon"], [data-testid="stSidebarCollapsedControl"] *, [data-testid="stIconMaterial"], [data-testid="stExpanderToggleIcon"] *, summary svg, summary span {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
        font-style: normal !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Noto Serif TC', 'Noto Serif', serif !important;
        color: #0B1C30 !important;
        letter-spacing: 0.3px;
    }
    
    /* Degree, coordinates & numerical data font */
    .mono-data, code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Sidebar Aesthetics */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
        color: #0B1C30 !important;
        font-family: 'Noto Sans TC', 'Inter', sans-serif !important;
    }
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p {
        color: #0B1C30 !important;
        font-family: 'Noto Sans TC', 'Inter', sans-serif !important;
    }
    
    /* Input Design */
    .stTextInput input, .stNumberInput input, .stSelectbox select, .stDateInput input, .stTimeInput input {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        color: #0B1C30 !important;
        border-radius: 6px !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #1E3A8A !important;
        box-shadow: 0 0 0 1px #1E3A8A !important;
    }

    /* Buttons / Japanese Minimalist Indigo Accent & Touch Optimization */
    .stButton > button,
    .stButton > button *,
    .stButton > button p,
    .stButton > button div,
    .stButton > button span,
    section[data-testid="stSidebar"] .stButton button,
    section[data-testid="stSidebar"] .stButton button *,
    section[data-testid="stSidebar"] .stButton button p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-family: 'Noto Sans TC', 'Inter', sans-serif !important;
        letter-spacing: 0.5px !important;
    }
    .stButton > button {
        background-color: #1E3A8A !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        min-height: 40px !important;
        touch-action: manipulation !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover,
    .stButton > button:hover *,
    section[data-testid="stSidebar"] .stButton button:hover,
    section[data-testid="stSidebar"] .stButton button:hover * {
        background-color: #172554 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    }

    /* Containers */
    .stContainer {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        background: #FFFFFF;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    
    /* Summary Card (Big Three) */
    .summary-card {
        background: #FFFFFF;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .summary-title { 
        font-family: 'Noto Serif TC', 'Noto Serif', serif;
        font-size: 0.9rem; 
        color: #64748B; 
        margin-bottom: 6px; 
        letter-spacing: 0.5px;
    }
    .summary-value { 
        font-family: 'Noto Serif TC', 'Noto Serif', serif;
        font-size: 1.35rem; 
        font-weight: 600; 
        color: #1E3A8A;
    }

    /* Tabs Horizontal Scrolling */
    .stTabs [data-baseweb="tab-list"] {
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
        white-space: nowrap !important;
        scrollbar-width: none !important;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
        display: none !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.9rem !important;
        padding: 8px 14px !important;
        white-space: nowrap !important;
    }

    /* Table Horizontal Scroll & Responsive Container Protection */
    div[data-testid='stTable'], div.stDataFrame, table {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        max-width: 100% !important;
    }
    table {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 6px !important;
        width: 100% !important;
        min-width: 480px !important;
    }
    th {
        background-color: #F8FAFC !important;
        color: #0B1C30 !important;
        font-family: 'Noto Serif TC', 'Noto Serif', serif !important;
        border-bottom: 1px solid #E2E8F0 !important;
        padding: 10px !important;
    }
    td {
        color: #0B1C30 !important;
        border-bottom: 1px solid #F1F5F9 !important;
        padding: 8px 10px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.9rem !important;
    }
    tr:hover {
        background-color: #F8FAFC !important;
    }

    /* Mobile Responsive Media Query (max-width: 768px) */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.75rem !important;
            max-width: 100vw !important;
        }
        h1 {
            font-size: 1.45rem !important;
            line-height: 1.3 !important;
        }
        h2 {
            font-size: 1.2rem !important;
        }
        h3 {
            font-size: 1.05rem !important;
        }
        p, li, label, .stMarkdown p {
            font-size: 0.92rem !important;
            line-height: 1.55 !important;
        }
        /* Convert main content columns to single column on mobile */
        .main [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
            margin-bottom: 10px !important;
        }
        .summary-card {
            margin-bottom: 8px !important;
            padding: 12px 14px !important;
        }
        .summary-value {
            font-size: 1.25rem !important;
        }
        .stContainer {
            padding: 12px !important;
            margin-bottom: 12px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'report_data' not in st.session_state:
    st.session_state.report_data = None
if 'report_md' not in st.session_state:
    st.session_state.report_md = ""
if 'ai_analysis_triggered' not in st.session_state:
    st.session_state.ai_analysis_triggered = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'dynamic_models' not in st.session_state:
    st.session_state.dynamic_models = []
if 'last_key' not in st.session_state:
    st.session_state.last_key = ""
if 'last_provider' not in st.session_state:
    st.session_state.last_provider = ""
if 'chart_type' not in st.session_state:
    st.session_state.chart_type = "natal" # Default

# --- Sidebar Inputs ---
st.sidebar.header("時間與地點資料輸入")

from profiles_logic import ProfilesManager
if 'saved_profiles' not in st.session_state:
    st.session_state.saved_profiles = ProfilesManager.load_from_file()
for _k, _v in (("person_name", "命盤主"), ("date_input_raw", "1900/01/01"), ("time_input_raw", "12:00"),
               ("location_city", "台北市"), ("manual_lon", 121.50), ("manual_lat", 25.03), ("utc_offset", 8.0),
               ("partner_name", "合盤對象 B"), ("partner_date_raw", "1992/06/15"),
               ("partner_time_raw", "12:00"), ("partner_city", "台北市")):
    st.session_state.setdefault(_k, _v)

person_name = st.sidebar.text_input("命盤主姓名 / 稱呼", key="person_name")

# Date/Time Input via Text
date_input_raw = st.sidebar.text_input("日期 (YYYY/MM/DD)", key="date_input_raw")
try:
    birth_date = datetime.strptime(date_input_raw.strip(), '%Y/%m/%d').date()
except ValueError:
    st.sidebar.error("請依照 YYYY/MM/DD 格式輸入日期")
    st.stop()

time_input_raw = st.sidebar.text_input("時間 (HH:MM)", key="time_input_raw")
try:
    time_str = time_input_raw.replace('：', ':').strip()
    birth_time = datetime.strptime(time_str, '%H:%M').time()
except ValueError:
    st.sidebar.error("請依照 HH:MM 格式輸入時間")
    st.stop()

st.sidebar.markdown("---")

location_city = st.sidebar.text_input("輸入城市名稱", key="location_city")

with st.sidebar.expander("自行手動輸入經緯度與時區", expanded=False):
    manual_lon = st.number_input("經度 (Longitude)", key="manual_lon", format="%.2f")
    manual_lat = st.number_input("緯度 (Latitude)", key="manual_lat", format="%.2f")
    utc_offset = st.number_input("時區偏移 (UTC Offset)", key="utc_offset", step=0.5)

def _profile_names():
    return [p["name"] for p in st.session_state.saved_profiles]


def _load_profile_cb():
    p = next((p for p in st.session_state.saved_profiles if p["name"] == st.session_state.get("profile_pick")), None)
    if p:
        st.session_state.update(person_name=p["name"], date_input_raw=p["date"], time_input_raw=p["time"],
                                location_city=p["city"], manual_lat=p["lat"], manual_lon=p["lon"], utc_offset=p["tz"])


def _save_profile_cb():
    ss = st.session_state
    nm = (ss.person_name or "").strip()
    if not nm:
        return
    ss.saved_profiles = ProfilesManager.save_profile(ss.saved_profiles, nm, ss.date_input_raw.strip(),
                                                     ss.time_input_raw.strip(), ss.location_city.strip(),
                                                     ss.manual_lat, ss.manual_lon, ss.utc_offset)
    ProfilesManager.save_to_file(ss.saved_profiles)


def _delete_profile_cb():
    ss = st.session_state
    ss.saved_profiles = ProfilesManager.delete_profile(ss.saved_profiles, ss.get("profile_pick"))
    ProfilesManager.save_to_file(ss.saved_profiles)


def _partner_pick_cb():
    p = next((p for p in st.session_state.saved_profiles if p["name"] == st.session_state.get("partner_pick")), None)
    if p:
        st.session_state.update(partner_name=p["name"], partner_date_raw=p["date"],
                                partner_time_raw=p["time"], partner_city=p["city"])


with st.sidebar.expander("🗂️ 常用命盤書籤 / 案例快選", expanded=False):
    if st.session_state.saved_profiles:
        st.selectbox("選擇書籤", _profile_names(), key="profile_pick")
        bc1, bc2 = st.columns(2)
        bc1.button("📂 載入選中命盤", on_click=_load_profile_cb, use_container_width=True)
        bc2.button("🗑️ 刪除選中書籤", on_click=_delete_profile_cb, use_container_width=True)
    st.button("💾 儲存當前輸入至書籤", on_click=_save_profile_cb, use_container_width=True)
    st.download_button("📤 匯出書籤 JSON", data=ProfilesManager.export_profiles_json(st.session_state.saved_profiles),
                       file_name="saved_profiles.json", mime="application/json", use_container_width=True)
    _imp = st.file_uploader("匯入書籤 JSON", type=["json"], key="profiles_upload")
    _imp_txt = st.text_area("或貼上書籤 JSON", key="profiles_json_text", height=80)
    if st.button("📥 匯入書籤", use_container_width=True):
        try:
            _src = _imp.getvalue().decode("utf-8") if _imp else _imp_txt
            st.session_state.saved_profiles = ProfilesManager.import_profiles_json(st.session_state.saved_profiles, _src)
            ProfilesManager.save_to_file(st.session_state.saved_profiles)
            st.success("✅ 書籤匯入成功")
        except Exception as _ex:
            st.error(f"匯入失敗：{_ex}")

with st.sidebar.expander("📅 太陽返照盤 / 推運目標年份設定", expanded=False):
    sr_year = st.number_input("太陽返照盤目標年份 (Solar Return Year)", min_value=1900, max_value=2100,
                              value=datetime.now().year, step=1)
    sr_city = st.text_input("流年居住地城市 (預設同出生地)", value="")

with st.sidebar.expander("💑 雙人合盤設定 (選填 - 啟用合盤疊盤)", expanded=False):
    enable_synastry = st.checkbox("啟用雙人合盤 (Synastry)", value=False)
    st.selectbox("從常用書籤帶入對象資料", ["（手動輸入）"] + _profile_names(), key="partner_pick",
                 on_change=_partner_pick_cb)
    partner_name = st.text_input("對方姓名 / 稱呼", key="partner_name")
    partner_date_raw = st.text_input("對方出生日期 (YYYY/MM/DD)", key="partner_date_raw")
    partner_time_raw = st.text_input("對方出生時間 (HH:MM)", key="partner_time_raw")
    partner_city = st.text_input("對方出生城市", key="partner_city")

st.sidebar.markdown("---")
# Buttons for calculation
with st.sidebar.expander("🔮 卜卦占星問事設定", expanded=True):
    horary_presets = [
        "這件事會成功嗎？",
        "換工作 / 面試會錄取順利嗎？",
        "與對方的感情能復合 / 發展順利嗎？",
        "這筆投資 / 買賣能獲利嗎？",
        "遺失的物品 / 寵物能找回來嗎？",
        "病情 / 手術能平安康復嗎？"
    ]
    def _apply_horary_preset():
        chosen = st.session_state.get('horary_preset_select')
        if chosen and chosen != "（自訂輸入）":
            st.session_state.horary_question_input = chosen

    st.selectbox("常用卜卦情境範本", ["（自訂輸入）"] + horary_presets, key="horary_preset_select", on_change=_apply_horary_preset)
    horary_q_val = st.text_input("問卜具體問題 (Question)", 
                                 value=st.session_state.get('horary_question', '這件事會成功嗎？'), 
                                 key="horary_question_input",
                                 placeholder="請輸入您心中聚焦的問題...")

col1, col2 = st.sidebar.columns(2)
with col1:
    generate_btn = st.button("排本命盤", use_container_width=True)
with col2:
    horary_btn = st.button("🔮 卜卦占星", use_container_width=True, type="primary")

# --- Logic Processing ---
if generate_btn or horary_btn:
    # Reset AI analysis and chat history when a NEW chart is generated
    st.session_state.ai_analysis_triggered = False
    st.session_state.chat_history = []
    
    if generate_btn:
        st.session_state.chart_type = "natal"
    elif horary_btn:
        st.session_state.chart_type = "horary"
        # Store user's question from sidebar input
        q_text = st.session_state.get('horary_question_input', '').strip()
        st.session_state.horary_question = q_text if q_text else "這件事會成功嗎？"

    try:
        # Resolve location for the chart (essential for Houses)
        final_lat, final_lon = manual_lat, manual_lon
        if manual_lon == 121.50 and manual_lat == 25.03 and location_city != "台北市":
            coords = logic.get_location_coordinates(location_city)
            if coords:
                final_lat, final_lon = coords
            else:
                if not horary_btn: # For regular chart, show warning if city search fails
                    st.sidebar.warning("⚠️ 自動地點檢索暫時無法連線，請手動展開下方進階選項輸入經緯度。")

        # Basic parsing remains same, but we bypass any browser overrides
        birth_date_str = birth_date.strftime('%Y/%m/%d')
        birth_time_str = birth_time.strftime('%H:%M')
        
        # If horary button is clicked and default 1900/01/01 is left, cast for current moment
        if horary_btn and date_input_raw.strip() == "1900/01/01":
            now_dt = datetime.now()
            birth_date_str = now_dt.strftime('%Y/%m/%d')
            birth_time_str = now_dt.strftime('%H:%M')
        
        sign = '+' if utc_offset >= 0 else '-'
        abs_offset = abs(utc_offset)
        h, m = int(abs_offset), int((abs_offset - int(abs_offset)) * 60)
        offset_str = f"{sign}{h:02d}:{m:02d}"
        
        from flatlib.datetime import Datetime
        from flatlib.geopos import GeoPos
        from flatlib.chart import Chart
        
        dt = Datetime(birth_date_str, birth_time_str, offset_str)
        pos = GeoPos(final_lat, final_lon)
        chart = Chart(dt, pos, hsys=const.HOUSES_WHOLE_SIGN)
        
        # Calculations
        asc = chart.get(const.ASC)
        asc_sign = logic.TRANS_SIGNS.get(asc.sign, asc.sign)
        asc_deg, asc_min, _ = logic.degree_to_dms(asc.lon % 30)
        
        sun_p = chart.get(const.SUN)
        moon_p = chart.get(const.MOON)
        sun_sign = logic.TRANS_SIGNS.get(sun_p.sign, sun_p.sign)
        moon_sign = logic.TRANS_SIGNS.get(moon_p.sign, moon_p.sign)
        sun_deg, sun_min, _ = logic.degree_to_dms(sun_p.lon % 30)
        moon_deg, moon_min, _ = logic.degree_to_dms(moon_p.lon % 30)

        if hasattr(logic, 'calculate_whole_sign_houses'):
            houses = logic.calculate_whole_sign_houses(asc.lon)
        else:
            houses = logic.calculate_equal_houses(asc.lon)

        planets_data = logic.get_planets_data(chart, houses)

        # Determine target date for progressions and time lords based on system time
        target_date = datetime.now().date()

        prof_info = logic.calculate_profections(chart, houses, birth_date_str, current_date=target_date)
        aspects = logic.get_aspects(chart)
        antiscia = logic.get_antiscia(chart)
        is_day = logic.is_day_birth(chart, houses)
        f_data = logic.get_firdaria_data(birth_date_str, is_day, current_date=target_date)
        zr_data = logic.calculate_zodiacal_releasing(chart, is_day, birth_date_str, current_date=target_date) if hasattr(logic, 'calculate_zodiacal_releasing') else {}
        sa_data = logic.calculate_solar_arcs(chart, birth_date_str, birth_time_str, offset_str, final_lat, final_lon, target_date=target_date) if hasattr(logic, 'calculate_solar_arcs') else {}
        sec_prog_data = logic.calculate_secondary_progressions(chart, houses, birth_date_str, birth_time_str, offset_str, final_lat, final_lon, target_date=target_date) if hasattr(logic, 'calculate_secondary_progressions') else {}
        tert_prog_data = logic.calculate_tertiary_progressions(chart, houses, birth_date_str, birth_time_str, offset_str, final_lat, final_lon, target_date=target_date) if hasattr(logic, 'calculate_tertiary_progressions') else {}
        sr_data = {}
        try:
            sr_lat, sr_lon_v, sr_city_used = final_lat, final_lon, ""
            if sr_city.strip():
                sr_coords = logic.get_location_coordinates(sr_city.strip())
                if sr_coords:
                    sr_lat, sr_lon_v, sr_city_used = sr_coords[0], sr_coords[1], sr_city.strip()
                else:
                    st.warning(f"找不到流年居住地「{sr_city}」，太陽返照盤改用出生地。")
            sr_tz, sr_off = logic.get_timezone_info(sr_lat, sr_lon_v, datetime(int(sr_year), 7, 1, 12, 0))
            if sr_off is None:
                sr_off = utc_offset
            sr_data = logic.calculate_solar_return(chart, houses, birth_date_str, sr_off, sr_lat, sr_lon_v,
                                                   target_year=int(sr_year), sr_city=sr_city_used or location_city)
        except Exception as sr_err:
            st.warning(f"太陽返照盤計算失敗：{sr_err}")
        lr_data, transits_data, planetary_hours, monthly_profections = {}, {}, {}, []
        try:
            lr_data = logic.calculate_lunar_return(chart, houses, utc_offset, final_lat, final_lon,
                                                   target_date=target_date, lr_city=location_city)
            transits_data = logic.calculate_transits(chart, houses, utc_offset, final_lat, final_lon,
                                                     target_date=target_date, target_time_str=datetime.now().strftime('%H:%M'))
            monthly_profections = logic.calculate_monthly_profections_calendar(chart, houses, birth_date_str, int(sr_year))
            planetary_hours = logic.calculate_planetary_hours(birth_date_str, birth_time_str, utc_offset, final_lat, final_lon,
                                                              asc_sign_const=asc.sign)
        except Exception as pe_err:
            st.warning(f"預測擴充模組計算失敗：{pe_err}")
        lots = logic.calculate_lots(chart, houses, is_day)
        fixed_stars =logic.get_fixed_stars(chart)
        almuten_data = logic.calculate_almuten(chart, houses, is_day) if hasattr(logic, 'calculate_almuten') else {}
        natal_core = logic.calculate_natal_core(chart, houses, planets_data, is_day, almuten_data)

        # Build Markdown Report
        title_map = {'natal': '古典占星本命盤完整資料', 'horary': '古典占星卜卦盤解析資料'}
        current_title = title_map.get(st.session_state.chart_type, '古典占星命盤資料')
        
        md = f"# {current_title} (升級版)\n\n"
        md += f"產出時間：{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n\n"
        md += "---\n\n"
        md += "## 出生資訊\n\n"
        md += f"- 生日：{birth_date_str} {birth_time_str}\n"
        md += f"- 地點：{location_city} ({final_lat:.2f}N, {final_lon:.2f}E)\n"
        md += f"- 上升星座：{asc_sign} {asc_deg}°{asc_min}'\n"
        md += f"- 太陽星座：{sun_sign} {sun_deg}°{sun_min}'\n"
        md += f"- 月亮星座：{moon_sign} {moon_deg}°{moon_min}'\n\n"
        
        md += "## 行星狀態與本質力量\n\n"
        for p in planets_data:
            d = p['dignity']
            d_str = ", ".join(d['list']) if d['list'] else "無 (Peregrine)"
            acc_str = ", ".join(p['accidental'])
            md += f"### {p['symbol']} {p['name']}\n"
            md += f"- 位置：{p['sign']} {p['degree_str']} {p['retro']} | [{p['house']}]\n"
            md += f"- 本質力量：{d_str} (總分: {d['score']})\n"
            md += f"- 後天狀態：{acc_str}\n\n"
        
        md += "## 特殊點位與恆星\n\n"
        for lot in lots:
            md += f"- {lot['name']}：{lot['sign']} {lot['degree']} ({lot['house']})\n"
        for star in fixed_stars:
            md += f"- 恆星合相：{star['planet']} 合相 {star['star']} (誤差 {star['orb']})\n"
        md += "\n"

        md += "## 宮位資料\n\n"
        for h in houses:
            h_deg, h_min, _ = logic.degree_to_dms(h['degree'])
            md += f"- {h['id_str']}：{h['sign']} {h_deg}°{h_min}' (主：{h['ruler']})\n"
        md += "\n"
        
        md += "## 相位與接納\n\n"
        if aspects:
            for a in aspects:
                rec = f" | 接納：{a['reception']}" if a['reception'] else ""
                md += f"- {a['p1']} - {a['p2']}：{a['aspect']} (誤差 {a['orb']}){rec}\n"
        else:
            md += "無顯著相位。\n"
        md += "\n"

        md += "## 古典映點與反映點 (Antiscia & Contra-Antiscia)\n\n"
        if antiscia:
            for a in antiscia:
                md += f"- {a['p1']} - {a['p2']}：{a['type']} (誤差 {a['orb']})\n"
        else:
            md += "無顯著映點接觸。\n"
        md += "\n"

        if st.session_state.chart_type == 'natal':
            md += "## 推運資訊\n\n"
            md += f"- 小限分限：{prof_info.get('prof_sign')} (第 {prof_info.get('prof_house_num')} 宮)\n"
            md += f"- 當前年主星：{prof_info.get('lord_of_year')}\n\n"
            
            md += "### 未來 5 年小限主星預告\n"
            md += "| 預測西元年 | 年齡 | 小限宮位 | 年度主星 |\n"
            md += "|----------|------|----------|----------|\n"
            for i in range(1, 6):
                future_year = target_date.year + i
                try:
                    future_date = target_date.replace(year=future_year)
                except ValueError:
                    future_date = target_date.replace(year=future_year, day=28)
                fw_prof = logic.calculate_profections(chart, houses, birth_date_str, current_date=future_date)
                md += f"| {future_year} 年 | {fw_prof.get('age')} 歲 | {fw_prof.get('prof_sign')} (第 {fw_prof.get('prof_house_num')} 宮) | {fw_prof.get('lord_of_year')} |\n"
            md += "\n"
            
            act = f_data['active']
            m_n = logic.TRANS_PLANETS.get(act['major'], act['major'])
            mi_n = logic.TRANS_PLANETS.get(act['minor'], act['minor'])
            md += f"- 法達當前大運：{m_n}\n"
            md += f"- 法達當前小運：{mi_n}\n"
            md += f"- 下次換運日期：{act['end'].strftime('%Y/%m/%d')}\n\n"

            md += "### 完整法達星限時間表\n"
            md += "| 大運 | 小運 | 開始日期 | 結束日期 |\n"
            md += "|------|------|----------|----------|\n"
            for major in f_data['timeline']:
                for minor in major['subs']:
                    major_name = logic.TRANS_PLANETS.get(major['lord'], major['lord'])
                    minor_name = logic.TRANS_PLANETS.get(minor['minor'], minor['minor'])
                    start_str = minor['start'].strftime('%Y/%m/%d')
                    end_str = minor['end'].strftime('%Y/%m/%d')
                    md += f"| {major_name} | {minor_name} | {start_str} | {end_str} |\n"
            md += "\n"

            # Zodiacal Releasing (ZR)
            act_l1 = zr_data.get('spirit', {}).get('active_l1', {})
            act_l2 = zr_data.get('spirit', {}).get('active_l2', {})
            md += "### 希臘黃道釋放法 (Zodiacal Releasing - 精神點事業運)\n"
            md += f"- 當前 L1 主運：{act_l1.get('sign_name', '')} ({act_l1.get('ruler_name', '')}) 期間：{act_l1.get('start_date', '')} ~ {act_l1.get('end_date', '')} ｜ 巔峰屬性：{act_l1.get('peak_type', '普通時期')}\n"
            md += f"- 當前 L2 子運：{act_l2.get('sign_name', '')} ({act_l2.get('ruler_name', '')}) 期間：{act_l2.get('start_date', '')} ~ {act_l2.get('end_date', '')} ｜ 巔峰屬性：{act_l2.get('peak_type', '普通時期')}\n"
            if act_l2.get('is_lb'):
                md += f"- ⚠️ **注意**：當前處於換宮跳躍 (Losing of the Bond) 關鍵轉折大變動期！\n"
            md += "\n"

            # Solar Arc Directions (SAD)
            md += "### 現代事件占星：太陽弧推運 (Solar Arc Directions)\n"
            md += f"- 推進太陽弧度數：{sa_data.get('solar_arc_str', '')} (實歲 {sa_data.get('age_years', 0)} 歲)\n"
            sa_aspects = sa_data.get('active_aspects', [])
            if sa_aspects:
                md += f"- 當前活躍事件硬相位 (容許度 <= 1.0°)：\n"
                for sa_asp in sa_aspects:
                    sig = f" ➔ {sa_asp['significance']}" if sa_asp.get('significance') else ""
                    md += f"  * [SA {sa_asp['sa_planet_name']}] {sa_asp['aspect']} [Natal {sa_asp['natal_planet_name']}] (誤差 {sa_asp['orb_str']}){sig}\n"
            else:
                md += "- 目前無容許度 <= 1.0° 之重大事件硬相位。\n"
            md += "\n"

            # Secondary Progressions (一日一年)
            if sec_prog_data:
                md += "### 次限推運法 (Secondary Progressions 一日一年)\n"
                md += f"- 當前實歲年齡：{sec_prog_data.get('age_years', 0)} 歲 (次限推進日期：{sec_prog_data.get('progressed_date', '')})\n"
                p_moon = sec_prog_data.get('progressed_moon', {})
                if p_moon:
                    md += f"- 🌙 次限月亮：{p_moon.get('sign', '')} {p_moon.get('degree_str', '')} (落入本命 {p_moon.get('house_str', '')})\n"
                    md += f"  * 預計換座剩餘：約 {p_moon.get('months_left_in_sign', 0)} 個月\n"
                    md += f"  * 當前生活重心：{p_moon.get('theme', '')}\n"
                l_phase = sec_prog_data.get('lunar_phase', {})
                if l_phase:
                    md += f"- 🌗 次限 30 年月相週期：{l_phase.get('phase_name', '')} (日月角距 {l_phase.get('angle_str', '')}，{l_phase.get('stage', '')})\n"
                    md += f"  * 生命階段象徵：{l_phase.get('desc', '')}\n"
                sp_asps = sec_prog_data.get('active_aspects', [])
                if sp_asps:
                    md += "- 當前活躍次限對本命相位：\n"
                    for spa in sp_asps[:5]:
                        md += f"  * {spa['prog_planet']} {spa['aspect']} {spa['natal_planet']} (誤差 {spa['orb_str']}，{spa['duration']})\n"
                md += "\n"

            # Tertiary Progressions (一日一月)
            if tert_prog_data:
                md += "### 三限推運法 (Tertiary Progressions 一日一月)\n"
                md += f"- 當前實歲年齡：{tert_prog_data.get('age_years', 0)} 歲 (三限星曆時間：{tert_prog_data.get('tertiary_ephemeris_date', '')})\n"
                t_moon = tert_prog_data.get('tertiary_moon', {})
                if t_moon:
                    md += f"- 🌙 三限月亮焦點：{t_moon.get('sign', '')} {t_moon.get('degree_str', '')} (落入本命 {t_moon.get('house_str', '')})\n"
                    md += f"  * 預計換宮剩餘：約 {t_moon.get('weeks_left_in_sign', 0)} 週 ({t_moon.get('days_left_in_sign', 0)} 天)\n"
                    md += f"  * 當月生活重心：{t_moon.get('theme', '')}\n"
                tl_phase = tert_prog_data.get('lunar_phase', {})
                if tl_phase:
                    md += f"- 🌗 三限 2.5 年月相週期：{tl_phase.get('phase_name', '')} (第 {tl_phase.get('cycle_month', 0)} 個月，【{tl_phase.get('stage', '')}】)\n"
                tp_asps = tert_prog_data.get('active_aspects', [])
                if tp_asps:
                    md += "- 當月活躍三限對本命相位：\n"
                    for tpa in tp_asps[:5]:
                        md += f"  * {tpa['prog_planet']} {tpa['aspect']} {tpa['natal_planet']} (誤差 {tpa['orb_str']}，{tpa['duration']})\n"
                md += "\n"

        horary_analysis = None
        if st.session_state.chart_type == 'horary':
            cur_q = st.session_state.get('horary_question', '這件事會成功嗎？')
            horary_analysis = logic.analyze_horary_chart(chart, houses, cur_q, planets_data)
            
            c = horary_analysis.get('classification', {})
            p = horary_analysis.get('perfection', {})
            t = horary_analysis.get('timing', {})
            mf = horary_analysis.get('moon_flow', {})
            
            md += "## 🔮 古典卜卦成事診斷與應期 (William Lilly 1647 原典規範)\n\n"
            md += f"- **問卜問題**：{cur_q}\n"
            md += f"- **鎖定所屬宮位**：第 {c.get('quesited_house', 7)} 宮 ({c.get('house_meaning', '')}) ｜ 匹配關鍵字：`{c.get('matched_keyword', '')}`\n"
            md += f"- **問卜者守護星 (Lord 1)**：{c.get('querent_planet_name', '')}\n"
            md += f"- **所問事項守護星 (Lord Q)**：{c.get('quesited_planet_name', '')}\n"
            md += f"- **終局裁決**：**{p.get('overall_verdict', '')}**\n"
            md += f"  * 裁決說明：{p.get('verdict_desc', '')}\n"
            if p.get('direct_perfections'):
                for dp in p['direct_perfections']:
                    s_name = dp.get('source', '')
                    t_name = dp.get('target', '')
                    asp_name = dp.get('aspect', '')
                    d_deg = dp.get('delta_deg', '')
                    md += f"  * 直接入相位：{s_name} 與 {t_name} 呈 {asp_name} (剩餘 {d_deg}°)\n"
            if p.get('translation_of_light'):
                for tol in p['translation_of_light']:
                    t_name = tol.get('translator', '')
                    r_name = tol.get('receiver', tol.get('direction', ''))
                    md += f"  * 光線傳遞：{t_name} 傳遞光線予 {r_name}\n"
            if p.get('collection_of_light'):
                for col in p['collection_of_light']:
                    c_name = col.get('collector', '')
                    md += f"  * 光線收集：{c_name} 收集雙方光線\n"
            if p.get('reception_details'):
                for rec in p['reception_details']:
                    md += f"  * 互容關係：{rec['reception_type']} ({rec['meaning']})\n"
            if p.get('prohibitions'):
                for pro in p['prohibitions']:
                    md += f"  * ⚠️ 阻礙截胡：{pro['meaning']}\n"
            if p.get('refranations'):
                for ref in p['refranations']:
                    md += f"  * ⚠️ 逆行反悔：{ref['meaning']}\n"
            md += "\n"
            
            md += "### 🌙 月亮流動全景與應期時鐘\n"
            md += f"- **月亮當前狀態**：落於 {mf.get('moon_sign', '')} {mf.get('moon_deg_str', '')} ｜ {'⚠️ 空亡 (Void of Course)' if mf.get('is_voc') else '✅ 正常推進'}\n"
            if mf.get('last_separating_aspect'):
                lsa = mf['last_separating_aspect']
                md += f"- **離相位 (過去起因)**：月亮剛與 {lsa['target_planet']} 形成 {lsa['aspect_name']} (誤差 {lsa['orb']}°)\n"
            if mf.get('next_applying_aspect'):
                naa = mf['next_applying_aspect']
                md += f"- **次一入相位 (即刻發展)**：月亮即將與 {naa['target_planet']} 形成 {naa['aspect_name']} (誤差 {naa['orb']}°)\n"
            md += f"- **古典應期推估**：約 **{t.get('estimated_timeframe', '')}** (時間單位：{t.get('time_unit', '')}，剩餘度數：{t.get('delta_degrees', 0)}°)\n"
            md += f"  * 節奏動能：{t.get('pacing_description', '')}\n\n"

        if st.session_state.chart_type == 'natal' and sr_data:
            md += "---\n\n"
            md += f"## 📅 {sr_year} 年度太陽返照盤 (Solar Return)\n\n"
            md += f"- 返照時刻：{sr_data.get('sr_datetime_local', '')} ({sr_data.get('sr_city', '')})\n"
            md += f"- 返照上升：{sr_data.get('sr_asc_str', '')}｜返照天頂：{sr_data.get('sr_mc_str', '')}\n"
            md += f"- 返照上升落入本命第 {sr_data.get('sr_asc_in_natal_house', '')} 宮：{sr_data.get('sr_asc_natal_house_theme', '')}\n"
            md += f"- 年度主星 (Lord of the Year)：{sr_data.get('sr_ruler_name', '')}\n"
            for p in sr_data.get('planets', []):
                md += (f"  * 返照{p['name']}：{p['sign']} {p['degree_str']}{' Ⓡ' if p['is_retrograde'] else ''} "
                       f"(返照第 {p['sr_house_num']} 宮 / 本命第 {p['natal_house_num']} 宮)\n")
            for a in sr_data.get('active_aspects', [])[:10]:
                md += f"  * 返照{a['sr_planet_name']} {a['aspect']} 本命{a['natal_planet_name']} (容許度 {a['orb_str']})\n"
            md += "\n"

        if st.session_state.chart_type == 'natal' and (lr_data or transits_data or monthly_profections):
            md += "---\n\n## 🌕 月亮返照 / ⚡ 即時行運 / 📈 流月小限\n\n"
            if lr_data:
                md += f"- 月亮返照：{lr_data.get('summary', '')}\n"
            if transits_data:
                md += f"- 即時行運：{transits_data.get('summary', '')}\n"
            for r in monthly_profections:
                md += f"  * 流月 {r['month_index']:02d} ({r['start_date']}~{r['end_date']})：第 {r['house_num']} 宮 {r['sign']}，{r['lord_name']}｜{r['vitality_tag']}\n"
            md += "\n"
        if planetary_hours:
            md += f"- 行星時：{planetary_hours['day_ruler_name']}日，當下行星時主星 {planetary_hours['active_hour']['ruler_name']}；{planetary_hours.get('horary_radicality', '')}\n\n"

        _hd = natal_core['hyleg_data']
        md += "## 🧬 古典本命核心（演算法精算值）\n"
        md += f"* 四液氣質：{natal_core['temperament']['summary']}\n"
        md += f"* 生命主/壽主星/產前朔望：{_hd['summary']}\n"
        md += f"* 最終定位星：{natal_core['dispositors']['summary']}\n\n"

        md += "---\n\n"
        md += "## 🤖 AI 大師解盤提示詞說明\n"
        report_type = "本命盤" if st.session_state.chart_type == 'natal' else "卜卦占星盤"
        md += f"命盤資料已完整彙整完成（分析模式：**{report_type}**）。您可前往「🤖 AI 解盤提示詞與使用指引」分頁一鍵複製專用 Prompt，並轉貼至 ChatGPT、Claude 或 Gemini 等網頁版 AI 工具獲得深度古典解讀！\n\n"

        st.session_state.report_md = md
        st.session_state.report_data = {
            'chart': chart,
            'asc': f"{asc_sign} {asc_deg}°{asc_min}'",
            'sun': f"{sun_sign} {sun_deg}°{sun_min}'",
            'moon': f"{moon_sign} {moon_deg}°{moon_min}'",
            'planets': planets_data,
            'houses': houses,
            'aspects': aspects,
            'antiscia': antiscia,
            'prof_info': prof_info,
            'f_data': f_data,
            'zr_data': zr_data,
            'sa_data': sa_data,
            'sr_data': sr_data,
            'lr_data': lr_data,
            'transits_data': transits_data,
            'planetary_hours': planetary_hours,
            'monthly_profections': monthly_profections,
            'sec_prog_data': sec_prog_data,
            'tert_prog_data': tert_prog_data,
            'is_day': is_day,
            'lots': lots,
            'fixed_stars': fixed_stars,
            'almuten': almuten_data,
            'natal_core': natal_core,
            'horary_analysis': horary_analysis,
            'asc_lon': asc.lon,
            'mc_lon': chart.get(const.MC).lon,
            'meta': {
                'birth_date_str': birth_date_str,
                'birth_time_str': birth_time_str,
                'location_city': location_city,
                'lat': final_lat,
                'lon': final_lon,
                'utc_offset_str': offset_str,
                'chart_type': st.session_state.chart_type,
                'person_name': person_name.strip() or '命盤主'
            }
        }

        if generate_btn and enable_synastry:
            try:
                p_date = datetime.strptime(partner_date_raw.replace('-', '/').strip(), '%Y/%m/%d')
                p_time = datetime.strptime(partner_time_raw.replace('：', ':').strip(), '%H:%M')
                p_lat, p_lon = final_lat, final_lon
                p_city = partner_city.strip()
                if p_city and p_city != location_city:
                    p_coords = logic.get_location_coordinates(p_city)
                    if p_coords:
                        p_lat, p_lon = p_coords
                    else:
                        st.sidebar.warning("⚠️ 對方出生地檢索失敗，已改用本人出生地座標。")
                p_off = offset_str
                try:
                    _, p_utc = logic.get_timezone_info(p_lat, p_lon, p_date)
                    ps = '+' if p_utc >= 0 else '-'
                    p_off = f"{ps}{int(abs(p_utc)):02d}:{int((abs(p_utc) % 1) * 60):02d}"
                except Exception:
                    pass
                dt_b = Datetime(p_date.strftime('%Y/%m/%d'), p_time.strftime('%H:%M'), p_off)
                st.session_state.report_data['synastry_data'] = logic.synastry.generate_synastry_report(
                    "本人 A", dt, pos, partner_name.strip() or "合盤對象 B", dt_b, GeoPos(p_lat, p_lon))
                _syn = st.session_state.report_data['synastry_data']
                _sc = _syn.get('resonance_scores') or {}
                smd = "\n## 💑 古典雙人合盤分析資料 (Synastry)\n\n"
                smd += f"- 合盤對象：{_syn.get('person_b', '')}\n"
                smd += f"- 對象太陽 / 月亮 / 上升：{_syn.get('sun_b_str', '')} / {_syn.get('moon_b_str', '')} / {_syn.get('asc_b_str', '')}\n"
                smd += f"- 量化共鳴：事業協同 {_sc.get('business_harmony_score', '-')}｜情感黏著 {_sc.get('romantic_harmony_score', '-')}｜關係張力 {_sc.get('tension_index', '-')}\n"
                if _sc.get('summary'):
                    smd += f"- 總評：{_sc.get('summary')}\n"
                for hl in _sc.get('highlights') or []:
                    smd += f"  * {hl}\n"
                smd += "\n### 古典接納與互容\n"
                for r in _syn.get('receptions') or []:
                    smd += f"- {r.get('type', '')}：{r.get('description', '')}\n"
                smd += "\n### 宮位疊合 (B 行星落入 A 之宮位)\n"
                for o in _syn.get('b_in_a_overlays') or []:
                    smd += f"- {o.get('planet', '')} ({o.get('sign', '')} {o.get('degree', '')}) → 第 {o.get('overlay_house', '')} 宮\n"
                smd += "\n### 跨盤相位\n"
                for a in _syn.get('cross_aspects') or []:
                    smd += f"- {a.get('planet_a_zh', '')} {a.get('aspect_name', '')} {a.get('planet_b_zh', '')} (誤差 {a.get('orb', '')})\n"
                st.session_state.report_md += smd + "\n"
            except Exception as syn_err:
                st.sidebar.error(f"合盤計算錯誤: {syn_err}")
    except Exception as e:
        st.error(f"分析錯誤: {str(e)}")
        with st.expander("🔍 查看詳細錯誤追蹤 (Traceback)"):
            st.code(traceback.format_exc(), language="python")

# --- UI Layout ---
if st.session_state.report_data:
    d = st.session_state.report_data
    ui_title_map = {'natal': '古典占星本命盤資訊', 'horary': '古典占星卜卦盤資訊'}
    ui_title = ui_title_map.get(st.session_state.chart_type, '古典占星論命資訊')
    
    st.markdown(f"<h1 style='text-align: center; margin-bottom: 6px; color: #0B1C30;'>{ui_title}</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; font-size: 0.88rem; letter-spacing: 0.5px; margin-bottom: 24px;'>Professional Classical Astrology Analysis System</p>", unsafe_allow_html=True)
    
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(f"<div class='summary-card'><div class='summary-title'>太陽星座</div><div class='summary-value'>{d['sun']}</div></div>", unsafe_allow_html=True)
    with sc2:
        st.markdown(f"<div class='summary-card'><div class='summary-title'>月亮星座</div><div class='summary-value'>{d['moon']}</div></div>", unsafe_allow_html=True)
    with sc3:
        st.markdown(f"<div class='summary-card'><div class='summary-title'>上升星座</div><div class='summary-value'>{d['asc']}</div></div>", unsafe_allow_html=True)
    
    # --- UI Layout ---
    # Define tabs
    if st.session_state.chart_type == 'horary':
        tabs_list = [
            '🧭 星盤圖譜',
            '🪐 行星與本質力量',
            '📐 相位與接納關係',
            '🔮 卜卦檢意與成事診斷',
            '🌙 月亮流動與應期時鐘',
            '🤖 AI 解盤提示詞與使用指引'
        ]
    else:
        tabs_list = [
            '🧭 星盤圖譜',
            '行星與本質力量',
            '相位與接納',
            '特殊點位與恆星',
            '推運時間軸 (返照/太陽弧/次限/法達)',
            '🤖 AI 解盤提示詞與使用指引'
        ]
    
    all_tabs = st.tabs(tabs_list)
    
    # Tab 0: Chart graphics
    def _render_planetary_hours_table(ph):
        st.table(pd.DataFrame([{
            '時序': r['hour_index'], '晝夜': r['period'], '起': r['start_time'], '迄': r['end_time'],
            '時主星': f"{r['ruler_glyph']} {r['ruler_name']}", '擇日吉凶': r['electional_meaning'],
        } for r in ph.get('hours_table', [])]))

    with all_tabs[0]:
        from visuals import render_lilly_square_chart_svg, render_interactive_chart_viewer, THEMES
        _theme_bg = lambda key: THEMES[key]["paper"]
        theme_label = st.radio("🎨 視覺主題", ["🏛️ 古典羊皮紙", "🌌 皇家暗夜星空"], index=0, horizontal=True)
        theme_key = "starry_night" if "星空" in theme_label else "parchment"
        c_opt1, c_opt2 = st.columns(2)
        with c_opt1:
            show_lots = st.checkbox("顯示赫密斯點 (福德/精神)", value=True)
            show_all_lots = st.checkbox("展開全部 6 大赫密斯點", value=False) if show_lots else False
            show_aspect_bar = st.checkbox("星盤圖下方整合行星交角提示區塊", value=True, help="直接在星盤圖片底部面板內列出主要托勒密交角與接納關係，下載或複製圖片時一併包含")
        with c_opt2:
            show_stars = st.checkbox("顯示恆星合相與尊貴徽章", value=True)
            show_antiscia = st.checkbox("顯示映點接觸 (Antiscia)", value=False)
        try:
            chart_svg = render_lilly_square_chart_svg(d, show_lots=show_lots, theme=theme_key,
                                                      show_all_lots=show_all_lots, show_stars=show_stars,
                                                      show_antiscia=show_antiscia,
                                                      show_aspect_bar=show_aspect_bar)
            fname = "astro_lilly_square_chart"
            components.html(render_interactive_chart_viewer(chart_svg, fname, bg_color=_theme_bg(theme_key)), height=1010, scrolling=False)
            st.download_button("📥 下載 SVG 向量圖", data=chart_svg.encode("utf-8"),
                               file_name=f"{fname}.svg", mime="image/svg+xml")
        except Exception as e:
            st.error(f"星盤繪製錯誤: {e}")
            with st.expander("🔍 查看詳細錯誤追蹤 (Traceback)"):
                st.code(traceback.format_exc(), language="python")

        # --- 可列印命書下載 ---
        try:
            from visuals import render_printable_astro_book_html
            book_html = render_printable_astro_book_html(d, theme=theme_key, ai_messages=st.session_state.chat_history)
            st.download_button("📜 下載完整圖文命書 (HTML / 可列印 PDF)", data=book_html.encode("utf-8"),
                               file_name=f"Astro_Book_{datetime.now().strftime('%Y%m%d')}.html", mime="text/html",
                               use_container_width=True, key="book_dl_tab")
        except Exception as e:
            book_html = None
            st.error(f"命書匯出錯誤: {e}")

        syn = d.get("synastry_data")
        if syn:
            sc = syn.get("resonance_scores") or {}
            st.markdown(f"### 💑 古典合盤關係能量量化面板：{syn.get('person_a', '')} × {syn.get('person_b', '')}")
            st.caption(f"{syn.get('person_b', '')}：上升 {syn.get('asc_b_str', '')}｜太陽 {syn.get('sun_b_str', '')}｜月亮 {syn.get('moon_b_str', '')}")
            m1, m2, m3 = st.columns(3)
            m1.metric("💼 事業協同指數", sc.get("business_harmony_score", "-"))
            m2.metric("❤️ 情感黏著指數", sc.get("romantic_harmony_score", "-"))
            m3.metric("⚡ 關係張力指數", sc.get("tension_index", "-"))
            for hl in sc.get("highlights") or []:
                st.markdown(f"- {hl}")
            with st.expander("🤝 古典接納與互容 (Receptions)", expanded=False):
                recs = syn.get("receptions") or []
                if recs:
                    for r in recs:
                        st.markdown(f"- **{r.get('type', '')}**：{r.get('description', '')}")
                else:
                    st.write("未發現古典接納或互容關係。")
            with st.expander("🏠 宮位疊合表 (B 行星落入 A 之宮位)", expanded=False):
                rows = [{"對象行星": o["planet"], "星座": o["sign"], "度數": o["degree"], "落入 A 的宮位": f"第 {o['overlay_house']} 宮"}
                        for o in syn.get("b_in_a_overlays") or []]
                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            with st.expander("📐 跨盤相位表 (Cross-Aspects)", expanded=False):
                rows = [{"A 行星": a.get("planet_a_zh"), "B 行星": a.get("planet_b_zh"),
                         "相位": a.get("aspect_name"), "容許度": a.get("orb")}
                        for a in syn.get("cross_aspects") or []]
                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.write("無明顯跨盤相位。")

    # Tab 1: Planets
    with all_tabs[1]:
        st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
        st.subheader("行星本質與後天狀態")
        
        rows = []
        for p in d['planets']:
            dig = p['dignity']
            rows.append({
                '行星': f"{p['symbol']} {p['name']}",
                '位置': f"{p['sign']} {p['degree_str']} {p['retro']}",
                '宮位': p['house'],
                '本質力量': ", ".join(dig['list']) if dig['list'] else "無 (Peregrine)",
                '計分': dig['score'],
                '後天狀態': ", ".join(p['accidental'])
            })
        st.table(pd.DataFrame(rows))
        st.markdown("</div>", unsafe_allow_html=True)

        _nc = d.get('natal_core')
        if _nc:
            from visuals import render_temperament_svg, render_dispositor_tree_svg
            _nc_theme = locals().get('theme_key', 'parchment')
            with st.expander("📐 古典七曜與敏感點五等尊貴全表 (廟/旺/三分/埃及界/面)", expanded=False):
                _dm = pd.DataFrame(_nc['dignities_matrix']).fillna('—')
                st.table(_dm.rename(columns={
                    'point': '星點', 'position': '位置', 'house': '宮位', 'domicile_lord': '廟主 +5',
                    'exaltation_lord': '旺主 +4', 'triplicity_lords': '三分主 +3', 'term_lord': '埃及界主 +2',
                    'face_lord': '迦勒底面主 +1', 'detriment_fall': '落/陷', 'net_score': '淨分'}))
            with st.expander("🧬 古典四液氣質與寒熱乾濕量化儀 (Temperament) ＋ 👑 生命主 (Hyleg)、壽主星 (Alcocoden) 與產前朔望 (SAN)", expanded=False):
                _tp = _nc['temperament']
                components.html(render_temperament_svg(_tp, _nc_theme), height=300)
                st.markdown(_tp['summary'])
                st.table(pd.DataFrame(_tp['factors']).rename(columns={
                    'factor': '因子', 'detail': '內容', 'weight': '權重', 'qualities': '寒熱乾濕', 'humor': '氣質'}))
                _hd = _nc['hyleg_data']
                st.markdown(f"**{_hd['summary']}**")
                st.table(pd.DataFrame([{
                    '候選': c['name'], '位置': c['position'], '宮位': c['house'],
                    '位於生命宮': '是' if c['in_hylegical_house'] else '否',
                    '獲主星相位': len(c['ruler_aspects']), '採用': '✅' if c['qualifies'] else ''}
                    for c in _hd['candidates']]))
            with st.expander("🪐 十二宮飛星連鎖與最終定位星能量流向圖 (Dispositorship Chain)", expanded=False):
                _dp = _nc['dispositors']
                components.html(render_dispositor_tree_svg(_dp, _nc_theme), height=380)
                st.markdown(_dp['summary'])
                st.table(pd.DataFrame([{
                    '宮位': f['house_name'], '星座': f['sign'], '宮主星': f['ruler_name'],
                    '飛入': f"第 {f['flies_to_house']} 宮", '主星落座': f['ruler_sign'],
                    '尊貴分': f['ruler_dignity_score'], '解讀': f['interpretation']}
                    for f in _dp['house_fly_chains']]))

        st.subheader("十二宮位表")
        df_h = pd.DataFrame(d['houses'])
        col_map_h = {'id_str': '宮位名稱', 'sign': '對應星座', 'ruler': '宮位主星'}
        cols_h = [c for c in col_map_h if c in df_h.columns]
        st.table(df_h[cols_h].rename(columns=col_map_h))

    # Tab 2: Aspects
    with all_tabs[2]:
        st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
        st.subheader("行星相位與接納關係")
        if d['aspects']:
            df_a = pd.DataFrame(d['aspects'])
            col_map_a = {
                'p1': '行星 1',
                'p2': '行星 2',
                'aspect': '相位類型',
                'orb': '誤差',
                'applying': '入/離相位',
                'reception': '接納關係'
            }
            cols_a = [c for c in col_map_a if c in df_a.columns]
            st.table(df_a[cols_a].rename(columns=col_map_a))
        else:
            st.write("目前無顯著相位。")

        st.markdown("### 🪞 古典映點與反映點 (Antiscia & Contra-Antiscia — 巨蟹/摩羯至點鏡射)")
        if d.get('antiscia'):
            df_ant = pd.DataFrame(d['antiscia'])
            col_map_ant = {'p1': '行星 1', 'p2': '行星 2', 'type': '接觸類型', 'orb': '誤差'}
            st.table(df_ant[[c for c in col_map_ant if c in df_ant.columns]].rename(columns=col_map_ant))
        else:
            st.write("目前無顯著映點／反映點接觸。")
        with st.expander("📋 七大行星映點 (Antiscion) 與反映點 (Contra-Antiscion) 位置"):
            _sign_cn = ["牡羊", "金牛", "雙子", "巨蟹", "獅子", "處女", "天秤", "天蠍", "射手", "摩羯", "水瓶", "雙魚"]
            _fmt = lambda x: f"{_sign_cn[int(x % 360 // 30)]} {int(x % 30)}°{int((x % 1) * 60):02d}'"
            st.table(pd.DataFrame([{
                '行星': r['name'], '本命位置': _fmt(r['lon']),
                '映點 (Antiscion)': _fmt(r['antiscion']),
                '反映點 (Contra-Antiscion)': _fmt(r['contra_antiscion']),
            } for r in logic.get_antiscia_positions(d['chart'])]))
        st.markdown("</div>", unsafe_allow_html=True)

    # Tab 3: Lots & Stars (Natal) OR Radicality & Perfection (Horary)
    with all_tabs[3]:
        if st.session_state.chart_type == 'horary':
            ha = d.get('horary_analysis') or {}
            c = ha.get('classification', {})
            p = ha.get('perfection', {})
            t = ha.get('timing', {})
            mf = ha.get('moon_flow', {})

            # Helper to retrieve planet real positions and dignities
            def get_p_meta(p_name_or_id):
                for pl in d.get('planets', []):
                    if p_name_or_id and (pl.get('name') == p_name_or_id or pl.get('id') == p_name_or_id):
                        ret_mark = " ⚠️逆行" if pl.get('retro') else ""
                        dig_list = pl.get('dignity', {}).get('list', [])
                        dig_str = ", ".join(dig_list) if dig_list else "遊走 (Peregrine)"
                        h_num = pl.get('house_num')
                        h_label = f"第 {h_num} 宮" if h_num is not None and h_num != '' else pl.get('house', '')
                        return {
                            'name': pl.get('name', p_name_or_id),
                            'symbol': pl.get('symbol', '🪐'),
                            'pos': f"{pl.get('sign', '')} {pl.get('degree_str', '')}{ret_mark}",
                            'house': h_label,
                            'dignity': f"力量：{dig_str} (計分: {pl.get('dignity', {}).get('score', 0)})"
                        }
                return {
                    'name': p_name_or_id or '未定',
                    'symbol': '🪐',
                    'pos': '位置已排盤',
                    'house': '',
                    'dignity': '力量：正常'
                }

            p1_name = p.get('lord_1_name') or c.get('querent_planet_name') or p.get('lord_1_id') or '火星'
            pq_name = p.get('lord_q_name') or c.get('quesited_planet_name') or p.get('lord_q_id') or '金星'

            p1_meta = get_p_meta(p1_name)
            pq_meta = get_p_meta(pq_name)
            pm_meta = get_p_meta('月亮')

            # -------------------------------------------------------------
            # 1. 頂部問事對焦與三大徵象星全景卡片
            # -------------------------------------------------------------
            st.subheader("🎯 占卜議題與三大主徵象星對焦")
            
            cur_q_text = c.get('question', st.session_state.get('horary_question', '這件事會成功嗎？'))
            target_h_num = c.get('quesited_house', 7)
            target_h_desc = c.get('house_meaning') or c.get('topic_tag') or c.get('house_name') or '合作/關係/對方'
            target_kw = c.get('matched_keyword') or c.get('topic_tag') or '通用議題'
            
            q_col1, q_col2 = st.columns([4, 1])
            with q_col1:
                st.markdown(f"""
                <div style='background: #F1F5F9; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px; border-left: 4px solid #3B82F6;'>
                    <div style='font-size: 13px; color: #64748B; margin-bottom: 2px;'>當前占卜問題</div>
                    <div style='font-size: 19px; font-weight: 800; color: #0F172A; margin-bottom: 6px;'>「{cur_q_text}」</div>
                    <div style='font-size: 13px; color: #334155;'>
                        🎯 智能對焦領域：<b>第 {target_h_num} 宮（{target_h_desc}）</b> ｜ 匹配關鍵字：<span style='background:#E2E8F0; padding:2px 8px; border-radius:4px; font-weight:600;'>{target_kw}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with q_col2:
                with st.popover("✏️ 修改問題"):
                    new_q_tab = st.text_input("輸入新問題", value=cur_q_text, key="horary_modal_q_input")
                    if st.button("更新問題並重新研判", key="horary_update_q_btn", type="primary", use_container_width=True):
                        st.session_state.horary_question = new_q_tab.strip() or "這件事會成功嗎？"
                        st.session_state.horary_question_input = st.session_state.horary_question
                        st.rerun()

            sig_col1, sig_col2, sig_col3 = st.columns(3)
            with sig_col1:
                h_disp1 = f"（{p1_meta['house']}）" if p1_meta.get('house') else ""
                st.markdown(f"""
                <div style='background:#FFFFFF; border:1px solid #CBD5E1; border-radius:8px; padding:14px; box-shadow:0 1px 2px rgba(0,0,0,0.05); min-height:165px; height:100%; display:flex; flex-direction:column; justify-content:space-between; box-sizing:border-box;'>
                    <div>
                        <div style='font-size:11px; font-weight:700; color:#2563EB; margin-bottom:4px;'>🙋‍♂️ 問卜者代表 (Lord 1)</div>
                        <div style='font-size:1.3rem; font-weight:800; color:#0F172A; margin-bottom:4px;'>{p1_meta['symbol']} {p1_meta['name']}</div>
                        <div style='font-size:13px; color:#334155; margin-bottom:2px;'>📍 <b>{p1_meta['pos']}</b>{h_disp1}</div>
                    </div>
                    <div style='font-size:12px; color:#64748B; margin-top:8px; padding-top:6px; border-top:1px dashed #E2E8F0;'>⚡ {p1_meta['dignity']}</div>
                </div>
                """, unsafe_allow_html=True)
            with sig_col2:
                h_dispq = f"（{pq_meta['house']}）" if pq_meta.get('house') else ""
                st.markdown(f"""
                <div style='background:#FFFFFF; border:1px solid #CBD5E1; border-radius:8px; padding:14px; box-shadow:0 1px 2px rgba(0,0,0,0.05); min-height:165px; height:100%; display:flex; flex-direction:column; justify-content:space-between; box-sizing:border-box;'>
                    <div>
                        <div style='font-size:11px; font-weight:700; color:#D97706; margin-bottom:4px;'>🎯 所問事項代表 (Lord Q)</div>
                        <div style='font-size:1.3rem; font-weight:800; color:#0F172A; margin-bottom:4px;'>{pq_meta['symbol']} {pq_meta['name']}</div>
                        <div style='font-size:13px; color:#334155; margin-bottom:2px;'>📍 <b>{pq_meta['pos']}</b>{h_dispq}</div>
                    </div>
                    <div style='font-size:12px; color:#64748B; margin-top:8px; padding-top:6px; border-top:1px dashed #E2E8F0;'>⚡ {pq_meta['dignity']}</div>
                </div>
                """, unsafe_allow_html=True)
            with sig_col3:
                h_dispm = f"（{pm_meta['house']}）" if pm_meta.get('house') else ""
                moon_status_str = '⚠️ 空亡（事無進展）' if mf.get('is_voc') else '✅ 動能充沛（持續推動中）'
                st.markdown(f"""
                <div style='background:#FFFFFF; border:1px solid #CBD5E1; border-radius:8px; padding:14px; box-shadow:0 1px 2px rgba(0,0,0,0.05); min-height:165px; height:100%; display:flex; flex-direction:column; justify-content:space-between; box-sizing:border-box;'>
                    <div>
                        <div style='font-size:11px; font-weight:700; color:#059669; margin-bottom:4px;'>🌙 事態推進總發動機 (Co-Sig)</div>
                        <div style='font-size:1.3rem; font-weight:800; color:#0F172A; margin-bottom:4px;'>{pm_meta['symbol']} {pm_meta['name']}</div>
                        <div style='font-size:13px; color:#334155; margin-bottom:2px;'>📍 <b>{pm_meta['pos']}</b>{h_dispm}</div>
                    </div>
                    <div style='font-size:12px; color:#64748B; margin-top:8px; padding-top:6px; border-top:1px dashed #E2E8F0;'>{moon_status_str}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

            # -------------------------------------------------------------
            # 2. 終局成事裁決高亮大卡片 (Executive Verdict)
            # -------------------------------------------------------------
            st.subheader("🏆 終局成事裁決 (William Lilly 1647 原典診斷)")
            
            v_text = p.get('overall_verdict', '評估中')
            v_desc = p.get('verdict_desc', '')
            
            if p.get('is_perfected') and "阻礙" not in v_text and "逆行" not in v_text:
                v_bg = "#ECFDF5"
                v_border = "#10B981"
                v_title_color = "#065F46"
                v_badge_bg = "#10B981"
                v_badge_text = "#FFFFFF"
                v_badge_label = "成事有望 (PERFECTED)"
            elif "阻礙" in v_text or "逆行" in v_text:
                v_bg = "#FEF2F2"
                v_border = "#EF4444"
                v_title_color = "#991B1B"
                v_badge_bg = "#EF4444"
                v_badge_text = "#FFFFFF"
                v_badge_label = "阻礙變卦 (OBSTACLE)"
            elif "考驗" in v_text or "互容" in v_text:
                v_bg = "#FFFBEB"
                v_border = "#F59E0B"
                v_title_color = "#92400E"
                v_badge_bg = "#F59E0B"
                v_badge_text = "#FFFFFF"
                v_badge_label = "克服考驗成事"
            else:
                v_bg = "#F8FAFC"
                v_border = "#94A3B8"
                v_title_color = "#334155"
                v_badge_bg = "#64748B"
                v_badge_text = "#FFFFFF"
                v_badge_label = "缺乏推動力"

            st.markdown(f"""
            <div style='background: {v_bg}; border: 2px solid {v_border}; border-radius: 10px; padding: 18px 22px; margin-bottom: 20px;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
                    <span style='font-size: 22px; font-weight: 800; color: {v_title_color};'>{v_text}</span>
                    <span style='background: {v_badge_bg}; color: {v_badge_text}; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 20px;'>{v_badge_label}</span>
                </div>
                <div style='font-size: 15px; color: #1E293B; line-height: 1.6;'>{v_desc}</div>
            </div>
            """, unsafe_allow_html=True)

            # -------------------------------------------------------------
            # 3. 古典成事五大路徑結構化診斷總覽 (Executive Checklist)
            # -------------------------------------------------------------
            st.markdown("<h4 style='margin-bottom: 12px; color: #0F172A;'>📋 古典成事五大路徑檢測總覽</h4>", unsafe_allow_html=True)
            
            # Row 1: Direct Application
            if p.get('direct_perfections'):
                dp0 = p['direct_perfections'][0]
                dp_color = "#16A34A" if "四分" not in dp0['aspect'] and "對分" not in dp0['aspect'] else "#D97706"
                dp_bg = "#F0FDF4" if "四分" not in dp0['aspect'] and "對分" not in dp0['aspect'] else "#FFFBEB"
                st.markdown(f"""
                <div style='background:{dp_bg}; border:1px solid {dp_color}40; border-left:4px solid {dp_color}; border-radius:6px; padding:10px 14px; margin-bottom:8px;'>
                    <b>1. 直接入相位 (Direct Application)</b>：<span style='color:{dp_color}; font-weight:bold;'>【成立】</span> {dp0['source']} 與 {dp0['target']} 呈 <b>{dp0['aspect']}</b>（當前交角誤差 {dp0['orb']}°，剩餘推進度數 <b>{dp0['delta_deg']}°</b>）
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style='background:#F8FAFC; border:1px solid #E2E8F0; border-left:4px solid #94A3B8; border-radius:6px; padding:10px 14px; margin-bottom:8px; color:#475569;'>
                    <b>1. 直接入相位 (Direct Application)</b>：<span>【無直接入相】</span> 雙方主星在當前星座內無主要入相位交角。
                </div>
                """, unsafe_allow_html=True)

            # Row 2: Translation of Light
            if p.get('translation_of_light'):
                tol0 = p['translation_of_light'][0]
                t_src = tol0.get('source', '')
                t_recv = tol0.get('receiver', '')
                t_dir = tol0.get('direction', '')
                t_desc = f"從 {t_src} 離相，奔向與 {t_recv} 成相" if (t_src and t_recv) else t_dir
                st.markdown(f"""
                <div style='background:#F0FDF4; border:1px solid #86EFAC; border-left:4px solid #16A34A; border-radius:6px; padding:10px 14px; margin-bottom:8px;'>
                    <b>2. 光線傳遞 (Translation of Light)</b>：<span style='color:#16A34A; font-weight:bold;'>【成立 - 熱心貴人】</span> 第三方星體 <b>{tol0.get('translator', '')}</b> {t_desc}，從中撮合！
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style='background:#F8FAFC; border:1px solid #E2E8F0; border-left:4px solid #94A3B8; border-radius:6px; padding:10px 14px; margin-bottom:8px; color:#475569;'>
                    <b>2. 光線傳遞 (Translation of Light)</b>：<span>【無光線傳遞】</span> 無第三方星體於雙方之間傳遞光線。
                </div>
                """, unsafe_allow_html=True)

            # Row 3: Collection of Light
            if p.get('collection_of_light'):
                col0 = p['collection_of_light'][0]
                st.markdown(f"""
                <div style='background:#F0FDF4; border:1px solid #86EFAC; border-left:4px solid #16A34A; border-radius:6px; padding:10px 14px; margin-bottom:8px;'>
                    <b>3. 光線收集 (Collection of Light)</b>：<span style='color:#16A34A; font-weight:bold;'>【成立 - 權威仲裁】</span> 權威星體 <b>{col0['collector']}</b> 同時接納雙方入相位，機構/司法裁決協調成事！
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style='background:#F8FAFC; border:1px solid #E2E8F0; border-left:4px solid #94A3B8; border-radius:6px; padding:10px 14px; margin-bottom:8px; color:#475569;'>
                    <b>3. 光線收集 (Collection of Light)</b>：<span>【無光線收集】</span> 無高階星體同時接納雙方入相。
                </div>
                """, unsafe_allow_html=True)

            # Row 4: Mutual Reception
            if p.get('reception_details'):
                rec0 = p['reception_details'][0]
                st.markdown(f"""
                <div style='background:#EEF2FF; border:1px solid #C7D2FE; border-left:4px solid #6366F1; border-radius:6px; padding:10px 14px; margin-bottom:8px;'>
                    <b>4. 古典廟旺互容 (Mutual Reception)</b>：<span style='color:#4F46E5; font-weight:bold;'>【成立 - 退讓妥協】</span> {rec0['reception_type']} ➔ 雙方願各退一步共同促成協議。
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style='background:#F8FAFC; border:1px solid #E2E8F0; border-left:4px solid #94A3B8; border-radius:6px; padding:10px 14px; margin-bottom:8px; color:#475569;'>
                    <b>4. 古典廟旺互容 (Mutual Reception)</b>：<span>【無互容】</span> 雙方主星未落入彼此廟旺尊貴位。
                </div>
                """, unsafe_allow_html=True)

            # Row 5: Prohibitions & Refranations
            has_intervener = bool(p.get('prohibitions') or p.get('refranations'))
            if has_intervener:
                pro_msgs = []
                if p.get('prohibitions'):
                    for pro in p['prohibitions']:
                        pro_msgs.append(f"⚠️ <b>阻礙截胡</b>：{pro['meaning']}")
                if p.get('refranations'):
                    for ref in p['refranations']:
                        pro_msgs.append(f"⚠️ <b>逆行反悔</b>：{ref['meaning']}")
                pro_text = "<br>".join(pro_msgs)
                st.markdown(f"""
                <div style='background:#FEF2F2; border:1px solid #FECACA; border-left:4px solid #DC2626; border-radius:6px; padding:10px 14px; margin-bottom:8px;'>
                    <b>5. 阻礙截胡與反悔 (Prohibition & Refranation)</b>：<span style='color:#DC2626; font-weight:bold;'>【出現警示】</span><br>{pro_text}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style='background:#F0FDF4; border:1px solid #86EFAC; border-left:4px solid #16A34A; border-radius:6px; padding:10px 14px; margin-bottom:8px;'>
                    <b>5. 阻礙截胡與反悔 (Prohibition & Refranation)</b>：<span style='color:#16A34A; font-weight:bold;'>【路徑暢通】</span> 無第三方星體搶先截胡插隊，亦無主星逆行反悔。
                </div>
                """, unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

            # -------------------------------------------------------------
            # 4. William Lilly 1647 盤體檢意審查 (Considerations Dashboard)
            # -------------------------------------------------------------
            st.subheader("⚖️ 盤體有效性檢驗 (Considerations Before Judgment)")
            asc_deg_f = (d['chart'].get(const.ASC).lon % 30) if 'chart' in d else 15.0
            is_early = asc_deg_f < 3.0
            is_late = asc_deg_f > 27.0
            is_m_voc = mf.get('is_voc', False)
            saturn_h = next((p_item['house_num'] for p_item in d['planets'] if p_item.get('id') == 'Saturn'), 0)
            
            c_r1, c_r2, c_r3, c_r4 = st.columns(4)
            card_style_base = "border-radius:6px;padding:10px;text-align:center;min-height:75px;display:flex;flex-direction:column;justify-content:center;box-sizing:border-box;"
            with c_r1:
                if is_early:
                    st.markdown(f"<div style='background:#FFFBEB;border:1px solid #FCD34D;{card_style_base}'><b>上升過早</b><br><span style='color:#D97706;font-size:12px;'>{round(asc_deg_f,1)}° < 3° (事未成熟)</span></div>", unsafe_allow_html=True)
                elif is_late:
                    st.markdown(f"<div style='background:#FEF2F2;border:1px solid #FCA5A5;{card_style_base}'><b>上升過晚</b><br><span style='color:#DC2626;font-size:12px;'>{round(asc_deg_f,1)}° > 27° (大局已定)</span></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background:#F0FDF4;border:1px solid #86EFAC;{card_style_base}'><b>上升度數良好</b><br><span style='color:#16A34A;font-size:12px;'>{round(asc_deg_f,1)}° (3°~27° 適判)</span></div>", unsafe_allow_html=True)
            with c_r2:
                if is_m_voc:
                    st.markdown(f"<div style='background:#FEF2F2;border:1px solid #FCA5A5;{card_style_base}'><b>月亮空亡 (VOC)</b><br><span style='color:#DC2626;font-size:12px;'>換座前無入相 (動能停滯)</span></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background:#F0FDF4;border:1px solid #86EFAC;{card_style_base}'><b>月亮推進正常</b><br><span style='color:#16A34A;font-size:12px;'>具備實質入相發展動能</span></div>", unsafe_allow_html=True)
            with c_r3:
                if saturn_h == 1:
                    st.markdown(f"<div style='background:#FFFBEB;border:1px solid #FCD34D;{card_style_base}'><b>土星落入 1 宮</b><br><span style='color:#D97706;font-size:12px;'>問卜者焦慮或阻力沉重</span></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background:#F0FDF4;border:1px solid #86EFAC;{card_style_base}'><b>土星無落 1 宮</b><br><span style='color:#16A34A;font-size:12px;'>落第 {saturn_h} 宮 (問卜無受克)</span></div>", unsafe_allow_html=True)
            with c_r4:
                if saturn_h == 7:
                    st.markdown(f"<div style='background:#FFFBEB;border:1px solid #FCD34D;{card_style_base}'><b>土星落入 7 宮</b><br><span style='color:#D97706;font-size:12px;'>占斷研判易受干擾</span></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background:#F0FDF4;border:1px solid #86EFAC;{card_style_base}'><b>土星無落 7 宮</b><br><span style='color:#16A34A;font-size:12px;'>落第 {saturn_h} 宮 (客觀明朗)</span></div>", unsafe_allow_html=True)
            ph_d = d.get('planetary_hours') or {}
            if ph_d:
                rad_txt = ph_d.get('horary_radicality', '')
                ah = ph_d.get('active_hour', {})
                rad_ok = rad_txt.startswith("✅")
                st.markdown(f"<div style='background:{'#F0FDF4' if rad_ok else '#FFFBEB'};border:1px solid {'#86EFAC' if rad_ok else '#FCD34D'};border-radius:6px;padding:10px;margin-top:10px;'>"
                            f"<b>🗓️ 迦勒底行星時真卦檢驗 (Planetary Hour Radicality)</b><br>"
                            f"<span style='font-size:13px;'>{ph_d.get('day_ruler_name', '')}日 · 當下行星時：{ah.get('ruler_glyph', '')} {ah.get('ruler_name', '')} "
                            f"({ah.get('start_time', '')}-{ah.get('end_time', '')})<br>{rad_txt}</span></div>", unsafe_allow_html=True)
                with st.expander("🗓️ 查看當日 24 小時迦勒底行星時與擇日吉凶表"):
                    st.caption(f"日出 {ph_d.get('sunrise_str', '')} / 日落 {ph_d.get('sunset_str', '')}")
                    _render_planetary_hours_table(ph_d)
            st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
            st.subheader("希臘阿拉伯點 (Lots)")
            if d.get('lots'):
                df_l = pd.DataFrame(d['lots'])
                col_map_l = {
                    'name': '點位名稱',
                    'sign': '星座',
                    'degree': '度數',
                    'house': '宮位',
                    'description': '象徵意義'
                }
                cols_l = [c for c in col_map_l if c in df_l.columns]
                st.table(df_l[cols_l].rename(columns=col_map_l))
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
            st.subheader("重要恆星合相 (Fixed Stars)")
            if d['fixed_stars']:
                df_s = pd.DataFrame(d['fixed_stars'])
                col_map_s = {'planet': '行星', 'star': '恆星', 'orb': '誤差'}
                cols_s = [c for c in col_map_s if c in df_s.columns]
                st.table(df_s[cols_s].rename(columns=col_map_s))
            else:
                st.write("目前無行星與重要恆星合相。")
            st.markdown("</div>", unsafe_allow_html=True)

    # Tab 4: Time Lords (Natal) OR Moon Flow & Timing Clock (Horary)
    with all_tabs[4]:
        if st.session_state.chart_type == 'horary':
            ha = d.get('horary_analysis') or {}
            mf = ha.get('moon_flow', {})
            t = ha.get('timing', {})

            # -------------------------------------------------------------
            # 1. 應期時鐘高亮儀表板 (Headline Timing Result)
            # -------------------------------------------------------------
            st.subheader("⏳ 古典應期時鐘 (William Lilly Timing Dashboard)")
            st.caption("依據 William Lilly 應期計算法：以成相剩餘度數差 $\\Delta\\theta$ 為基礎，結合推進星所處星座 (開創/變動/固定) 與落入宮位 (角宮/續宮/落宮) 之速度矩陣權重換算。")

            timeframe_val = t.get('estimated_timeframe', '需進一步觀測')
            time_unit_val = t.get('time_unit', '待推算')
            delta_deg_val = t.get('delta_degrees', 0.0)
            active_p_val = t.get('active_planet', '')
            active_s_val = t.get('active_sign', '')
            sign_spd_val = t.get('sign_speed', '')
            house_spd_val = t.get('house_speed', '')
            pacing_desc_val = t.get('pacing_description', '')

            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); border-radius: 12px; padding: 22px 24px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);'>
                <div style='font-size: 12px; letter-spacing: 1.5px; color: #94A3B8; text-transform: uppercase; margin-bottom: 4px;'>預估成事時間 (TIMING ESTIMATE)</div>
                <div style='font-size: 2.2rem; font-weight: 800; color: #38BDF8; margin-bottom: 6px;'>{timeframe_val}</div>
                <div style='font-size: 13px; color: #CBD5E1;'>時間尺度單位：<b>{time_unit_val}</b> ｜ 成相剩餘交角差：<b>{delta_deg_val}°</b></div>
            </div>
            """, unsafe_allow_html=True)

            t_c1, t_c2, t_c3 = st.columns(3)
            with t_c1:
                st.markdown(f"""
                <div style='background:#FFFFFF; border:1px solid #CBD5E1; border-radius:8px; padding:14px; text-align:center; min-height:115px; height:100%; display:flex; flex-direction:column; justify-content:space-between; box-sizing:border-box;'>
                    <div>
                        <div style='font-size:11px; font-weight:700; color:#64748B; margin-bottom:4px;'>🎯 推進核心星體</div>
                        <div style='font-size:1.15rem; font-weight:800; color:#0F172A; margin-bottom:2px;'>{active_p_val}</div>
                    </div>
                    <div style='font-size:12px; color:#475569; border-top:1px dashed #E2E8F0; padding-top:4px;'>落於 {active_s_val} ｜ 需跑 {delta_deg_val}°</div>
                </div>
                """, unsafe_allow_html=True)
            with t_c2:
                st.markdown(f"""
                <div style='background:#FFFFFF; border:1px solid #CBD5E1; border-radius:8px; padding:14px; text-align:center; min-height:115px; height:100%; display:flex; flex-direction:column; justify-content:space-between; box-sizing:border-box;'>
                    <div>
                        <div style='font-size:11px; font-weight:700; color:#64748B; margin-bottom:4px;'>⚡ 星座動能速度</div>
                        <div style='font-size:1.15rem; font-weight:800; color:#0F172A; margin-bottom:2px;'>{sign_spd_val}</div>
                    </div>
                    <div style='font-size:12px; color:#475569; border-top:1px dashed #E2E8F0; padding-top:4px;'>開創 (極快) / 變動 (適中) / 固定 (沉緩)</div>
                </div>
                """, unsafe_allow_html=True)
            with t_c3:
                st.markdown(f"""
                <div style='background:#FFFFFF; border:1px solid #CBD5E1; border-radius:8px; padding:14px; text-align:center; min-height:115px; height:100%; display:flex; flex-direction:column; justify-content:space-between; box-sizing:border-box;'>
                    <div>
                        <div style='font-size:11px; font-weight:700; color:#64748B; margin-bottom:4px;'>🏛️ 宮位動能速度</div>
                        <div style='font-size:1.15rem; font-weight:800; color:#0F172A; margin-bottom:2px;'>{house_spd_val}</div>
                    </div>
                    <div style='font-size:12px; color:#475569; border-top:1px dashed #E2E8F0; padding-top:4px;'>角宮 (迅速) / 續宮 (適中) / 落宮 (延宕)</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style='background:#F0F9FF; border:1px solid #BAE6FD; border-left:4px solid #0284C7; border-radius:6px; padding:12px 16px; margin-top:16px; margin-bottom:24px; color:#0369A1; font-size:14px; line-height:1.6;'>
                <b>💡 節奏動能評述：</b> {pacing_desc_val}
            </div>
            """, unsafe_allow_html=True)

            # -------------------------------------------------------------
            # 2. 月亮流動全景三階段時間軸 (Past ➔ Present ➔ Future)
            # -------------------------------------------------------------
            st.subheader("🌙 月亮流動全景三階段時間軸 (Moon's Temporal Flow)")
            st.caption("古典占星學中，月亮是全宇宙事態具象化的總發動機。月亮離相位代表『過去起因』，落宮代表『當下處境』，入相位代表『即刻發展』。")

            m_sign_val = mf.get('moon_sign', '')
            m_deg_val = mf.get('moon_deg_str', '')
            is_voc_val = mf.get('is_voc', False)
            lsa_val = mf.get('last_separating_aspect')
            naa_val = mf.get('next_applying_aspect')

            # Three temporal columns: Past -> Present -> Future
            flow_c1, flow_c2, flow_c3 = st.columns(3)
            with flow_c1:
                if lsa_val:
                    lsa_title = f"{lsa_val['target_planet']} 形成 {lsa_val['aspect_name']}"
                    lsa_orb = f"交角誤差：{lsa_val['orb']}°"
                    lsa_desc = "象徵事件爆發前之背景、過去原由與問卜者在提問前的經歷。"
                else:
                    lsa_title = "無近期緊密離相位"
                    lsa_orb = "—"
                    lsa_desc = "過去事態相對平緩或無特殊劇烈引動事件。"

                st.markdown(f"""
                <div style='background:#FFFFFF; border:1px solid #CBD5E1; border-top:4px solid #64748B; border-radius:8px; padding:14px; min-height:185px; height:100%; display:flex; flex-direction:column; justify-content:space-between; box-sizing:border-box;'>
                    <div>
                        <div style='font-size:11px; font-weight:700; color:#64748B; margin-bottom:4px;'>⏪ 第一階段：過去起因 (離相)</div>
                        <div style='font-size:1.15rem; font-weight:800; color:#0F172A; margin-bottom:4px;'>{lsa_title}</div>
                        <div style='font-size:12px; color:#475569; margin-bottom:6px;'>{lsa_orb}</div>
                    </div>
                    <div style='font-size:12px; color:#64748B; line-height:1.5; border-top:1px dashed #E2E8F0; padding-top:6px;'>{lsa_desc}</div>
                </div>
                """, unsafe_allow_html=True)

            with flow_c2:
                voc_label = "⚠️ 空亡 (動能停滯)" if is_voc_val else "✅ 推進正常"
                voc_color = "#DC2626" if is_voc_val else "#16A34A"
                st.markdown(f"""
                <div style='background:#FFFFFF; border:1px solid #CBD5E1; border-top:4px solid #2563EB; border-radius:8px; padding:14px; min-height:185px; height:100%; display:flex; flex-direction:column; justify-content:space-between; box-sizing:border-box;'>
                    <div>
                        <div style='font-size:11px; font-weight:700; color:#2563EB; margin-bottom:4px;'>⏸️ 第二階段：當前處境 (月相)</div>
                        <div style='font-size:1.15rem; font-weight:800; color:#0F172A; margin-bottom:4px;'>月亮落於 {m_sign_val}</div>
                        <div style='font-size:12px; color:#475569; margin-bottom:6px;'>度數：{m_deg_val} ｜ <span style='color:{voc_color}; font-weight:bold;'>{voc_label}</span></div>
                    </div>
                    <div style='font-size:12px; color:#64748B; line-height:1.5; border-top:1px dashed #E2E8F0; padding-top:6px;'>反映問卜者當前的心境焦點與局勢所處的客觀環境氛圍。</div>
                </div>
                """, unsafe_allow_html=True)

            with flow_c3:
                if naa_val:
                    naa_title = f"{naa_val['target_planet']} 形成 {naa_val['aspect_name']}"
                    naa_orb = f"剩餘推進度數：{naa_val['orb']}°"
                    naa_desc = "象徵事態接下來最直接迎來的關鍵引動點或消息，為未來的最主要推力！"
                else:
                    naa_title = "換座前已無入相位"
                    naa_orb = "處於空亡狀態"
                    naa_desc = "事件恐無實質後續進展或容易無疾而終。"

                st.markdown(f"""
                <div style='background:#FFFFFF; border:1px solid #CBD5E1; border-top:4px solid #16A34A; border-radius:8px; padding:14px; min-height:185px; height:100%; display:flex; flex-direction:column; justify-content:space-between; box-sizing:border-box;'>
                    <div>
                        <div style='font-size:11px; font-weight:700; color:#16A34A; margin-bottom:4px;'>⏩ 第三階段：即刻未來 (入相)</div>
                        <div style='font-size:1.15rem; font-weight:800; color:#0F172A; margin-bottom:4px;'>{naa_title}</div>
                        <div style='font-size:12px; color:#475569; margin-bottom:6px;'>{naa_orb}</div>
                    </div>
                    <div style='font-size:12px; color:#64748B; line-height:1.5; border-top:1px dashed #E2E8F0; padding-top:6px;'>{naa_desc}</div>
                </div>
                """, unsafe_allow_html=True)

            with st.expander("📋 查看月亮在此星座的完整相位歷程清單"):
                if mf.get('all_applying'):
                    st.markdown("**即將迎來的入相位清單**：")
                    st.table(pd.DataFrame(mf['all_applying']).rename(columns={'target_planet': '目標星體', 'aspect_name': '相位類型', 'orb': '剩餘交角差', 'is_applying': '入相標記'}))
                if mf.get('all_separating'):
                    st.markdown("**剛脫離的離相位清單**：")
                    st.table(pd.DataFrame(mf['all_separating']).rename(columns={'target_planet': '目標星體', 'aspect_name': '相位類型', 'orb': '脫離交角差', 'is_applying': '入相標記'}))
        else:
            # 1. 推運資訊摘要
            st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
            st.subheader("推運資訊摘要")
            pi = d['prof_info']
            st.write(f"當前年齡：{pi.get('age')} 歲")
            st.write(f"小限走到：{pi.get('prof_sign')} (第 {pi.get('prof_house_num')} 宮)")
            st.write(f"年度主星：{pi.get('lord_of_year')}")
            st.markdown("---")

            # 2. 年度太陽返照盤 (Solar Return Chart) 深度指標
            st.subheader("📅 年度太陽返照盤 (Solar Return Chart) 深度指標")
            srd = d.get('sr_data') or {}
            if srd:
                st.info(f"**{srd.get('target_year')} 年太陽返照時刻**：`{srd.get('sr_datetime_local')}` ({srd.get('sr_city', '')})")
                sr_c1, sr_c2, sr_c3 = st.columns(3)
                sr_c1.metric("返照上升 (SR ASC)", srd.get('sr_asc_str', ''))
                sr_c2.metric("返照天頂 (SR MC)", srd.get('sr_mc_str', ''))
                sr_c3.metric("年度主星 (Year Ruler)", srd.get('sr_ruler_name', ''))
                st.success(f"**返照上升落入本命第 {srd.get('sr_asc_in_natal_house')} 宮**：{srd.get('sr_asc_natal_house_theme', '')}")
                st.table(pd.DataFrame([{
                    '星體': p['name'], '星座': p['sign'], '度數': p['degree_str'],
                    '逆行': 'Ⓡ' if p['is_retrograde'] else '',
                    '返照宮位': p['sr_house_num'], '本命宮位': p['natal_house_num']
                } for p in srd.get('planets', [])]))
                if srd.get('active_aspects'):
                    st.markdown("**返照-本命緊密相位 (容許度 <= 2°)**：")
                    st.table(pd.DataFrame([{
                        '返照星': a['sr_planet_name'], '相位': a['aspect'],
                        '本命星': a['natal_planet_name'], '誤差': a['orb_str']
                    } for a in srd['active_aspects']]))
                else:
                    st.write("目前無容許度 <= 2° 之返照-本命相位。")
            else:
                st.write("尚無太陽返照盤資料，請重新點擊「排本命盤」。")
            st.markdown("---")

            # 2-1. 年度 12 個月流月小限日曆
            with st.expander("📈 年度 12 個月流月小限日曆 (Monthly Profections 12-Month Calendar)", expanded=True):
                mp = d.get('monthly_profections') or []
                if mp:
                    st.table(pd.DataFrame([{
                        '月序': r['month_index'], '起': r['start_date'], '迄': r['end_date'],
                        '小限宮位': r['house_name'], '星座': r['sign'], '月主星': r['lord_name'],
                        '吉凶能量': r['vitality_tag'], '主題': r['focus_theme'],
                    } for r in mp]))
                else:
                    st.write("尚無流月小限資料。")

            # 2-2. 當月月亮返照盤
            with st.expander("🌕 當月月亮返照盤 (Lunar Return Chart) 深度指標"):
                lrd = d.get('lr_data') or {}
                if lrd:
                    st.info(lrd.get('summary', ''))
                    lc1, lc2, lc3 = st.columns(3)
                    lc1.metric("返照上升 (LR ASC)", lrd.get('lr_asc_str', ''))
                    lc2.metric("返照天頂 (LR MC)", lrd.get('lr_mc_str', ''))
                    lc3.metric("當月主星", lrd.get('lr_ruler_name', ''))
                    st.table(pd.DataFrame([{
                        '星體': p['name'], '星座': p['sign'], '度數': p['degree_str'],
                        '逆行': 'Ⓡ' if p['is_retrograde'] else '',
                        '返照宮位': p['lr_house_num'], '本命宮位': p['natal_house_num'],
                    } for p in lrd.get('planets', [])]))
                    if lrd.get('active_aspects'):
                        st.table(pd.DataFrame([{
                            '返照星': a['lr_planet_name'], '相位': a['aspect'],
                            '本命星': a['natal_planet_name'], '誤差': a['orb_str'],
                        } for a in lrd['active_aspects']]))
                else:
                    st.write("尚無月亮返照盤資料。")

            # 2-3. 即時流年行運
            with st.expander("⚡ 即時流年行運 (Real-Time Transits) 過境宮位與觸發相位表"):
                trd = d.get('transits_data') or {}
                if trd:
                    st.info(trd.get('summary', ''))
                    st.table(pd.DataFrame([{
                        '行運星': p['name'], '星座': p['sign'], '度數': p['degree_str'],
                        '逆行': 'Ⓡ' if p['is_retrograde'] else '', '過境宮位': p['natal_house_str'],
                    } for p in trd.get('planets', [])]))
                    if trd.get('active_aspects'):
                        st.table(pd.DataFrame([{
                            '行運星': a['transit_planet_name'], '相位': a['aspect'],
                            '本命星': a['natal_planet_name'], '誤差': a['orb_str'], '古典解讀': a['meaning'],
                        } for a in trd['active_aspects']]))
                else:
                    st.write("尚無即時行運資料。")

            # 2-4. 當日 24 小時古典行星時與擇日吉時良辰表
            with st.expander("🗓️ 當日 24 小時古典行星時與擇日吉時良辰表 (Planetary Hours)"):
                phd = d.get('planetary_hours') or {}
                if phd:
                    st.caption(f"{phd.get('day_ruler_name', '')}日 · 日出 {phd.get('sunrise_str', '')} / 日落 {phd.get('sunset_str', '')}")
                    _render_planetary_hours_table(phd)
                else:
                    st.write("尚無行星時資料。")
            st.markdown("---")

            # 3. 現代事件占星：太陽弧推運 (Solar Arc Directions)
            st.subheader("現代事件占星：太陽弧推運 (Solar Arc Directions)")
            sa = d.get('sa_data', {})
            if sa:
                st.info(f"**推進太陽弧**：`{sa.get('solar_arc_str')}` (當前年齡：{sa.get('age_years')} 歲)")
                sa_aspects = sa.get('active_aspects', [])
                if sa_aspects:
                    st.markdown("**當前活躍重大硬相位 (0°/90°/180°，誤差 <= 1.0°)**：")
                    sa_rows = []
                    for asp in sa_aspects:
                        sa_rows.append({
                            '推運星 (SA)': asp['sa_planet_name'],
                            '相位': asp['aspect'],
                            '本命星 (Natal)': asp['natal_planet_name'],
                            '誤差': asp['orb_str'],
                            '核心事件象徵': asp.get('significance', '重大人生結構重組')
                        })
                    st.table(pd.DataFrame(sa_rows))
                else:
                    st.write("目前無容許度 <= 1.0° 之重大事件硬相位（處於相對穩定期）。")
            st.markdown("---")

            # 4. 次限推運法 (Secondary Progressions - 一日一年)
            st.subheader("次限推運法 (Secondary Progressions - 一日一年)")
            sp = d.get('sec_prog_data', {})
            if sp:
                p_moon = sp.get('progressed_moon', {})
                l_phase = sp.get('lunar_phase', {})
            
                sp_col1, sp_col2 = st.columns(2)
                with sp_col1:
                    st.markdown(f"**🌙 次限月亮焦點**：`{p_moon.get('sign', '')} {p_moon.get('degree_str', '')}` ({p_moon.get('house_str', '')})")
                    st.caption(f"生活重心：{p_moon.get('theme', '')}")
                    st.caption(f"預計換座剩餘：約 {p_moon.get('months_left_in_sign', 0)} 個月")
                with sp_col2:
                    st.markdown(f"**🌗 30 年月相大週期**：`{l_phase.get('phase_name', '')}`")
                    st.caption(f"人生階段：【{l_phase.get('stage', '')}】(日月角距 {l_phase.get('angle_str', '')})")
                    st.caption(f"{l_phase.get('desc', '')}")

                # 30 年次限月相視覺進度軸
                angle_val = l_phase.get('angle', 0.0)
                progress_ratio = min(1.0, max(0.0, angle_val / 360.0))
                cycle_year = round(progress_ratio * 29.5, 1)
                st.progress(progress_ratio, text=f"30年月相進程：{round(progress_ratio * 100, 1)}% (約第 {cycle_year} 年 / 29.5 年週期)")

                phase_stages = [
                    ("新月", "🌑", "0°~45°", "播種期"),
                    ("蛾眉月", "🌒", "45°~90°", "萌芽期"),
                    ("上弦月", "🌓", "90°~135°", "突破期"),
                    ("盈凸月", "🌔", "135°~180°", "精進期"),
                    ("滿月", "🌕", "180°~225°", "巔峰期"),
                    ("散播月", "🌖", "225°~270°", "分享期"),
                    ("下弦月", "🌗", "270°~315°", "重組期"),
                    ("香脂月", "🌘", "315°~360°", "休整期")
                ]
                cur_pname = l_phase.get('phase_name', '')
                badges_html = "<div style='display: flex; justify-content: space-between; margin-top: 4px; margin-bottom: 12px; gap: 4px; overflow-x: auto;'>"
                for name, icon, deg_range, stage in phase_stages:
                    is_active = (name in cur_pname)
                    bg_col = "#1E293B" if is_active else "#F1F5F9"
                    text_col = "#38BDF8" if is_active else "#475569"
                    border = "2px solid #38BDF8" if is_active else "1px solid #CBD5E1"
                    badges_html += f"<div style='flex: 1; min-width: 65px; text-align: center; background: {bg_col}; color: {text_col}; border: {border}; border-radius: 6px; padding: 6px 2px; font-size: 11px;'>"
                    badges_html += f"<div style='font-size: 16px; margin-bottom: 2px;'>{icon}</div><b>{stage}</b><div style='font-size: 9px; opacity: 0.8;'>{deg_range}</div></div>"
                badges_html += "</div>"
                st.markdown(badges_html, unsafe_allow_html=True)
            
                sp_aspects = sp.get('active_aspects', [])
                if sp_aspects:
                    st.markdown("**當前活躍次限相位 (對本命盤)**：")
                    sp_rows = []
                    for asp in sp_aspects:
                        sp_rows.append({
                            '次限星 (Prog)': asp['prog_planet'],
                            '相位': asp['aspect'],
                            '本命星 (Natal)': asp['natal_planet'],
                            '誤差': asp['orb_str'],
                            '持續引動期': asp['duration']
                        })
                    st.table(pd.DataFrame(sp_rows))
                else:
                    st.write("目前無容許度內之活躍次限對本命相位。")
            st.markdown("---")

            # 5. 法達大限 (Firdaria) 時間表
            st.subheader("法達大限 (Firdaria) 時間表")
            act = d['f_data']['active']
            st.info(f"**當前大運**：{logic.TRANS_PLANETS.get(act['major'], act['major'])} | **當前小運**：{logic.TRANS_PLANETS.get(act['minor'], act['minor'])} (直到 {act['end'].strftime('%Y/%m/%d')})")
        
            with st.expander("查看完整法達星限時間表"):
                f_rows = []
                for major in d['f_data']['timeline']:
                    for minor in major['subs']:
                        f_rows.append({
                            '大運': logic.TRANS_PLANETS.get(major['lord'], major['lord']),
                            '小運': logic.TRANS_PLANETS.get(minor['minor'], minor['minor']),
                            '開始日期': minor['start'].strftime('%Y/%m/%d'),
                            '結束日期': minor['end'].strftime('%Y/%m/%d')
                        })
                st.table(pd.DataFrame(f_rows))
            st.markdown("---")

            # 6. 古典生時校正小助手
            st.subheader("⏱️ 古典生時校正小助手 (Astrological Rectification)")
            st.markdown(
                "藉由過去人生發生的重大客觀事件（如婚戀、升遷、子女出生、重大手術、置產等），"
                "以小限宮位主星、法達星期、原級推進度數進行**逆向多維度碰撞評分**，鎖定最吻合之出生精準分秒。"
            )
            with st.expander("🛠️ 展開生時校正逆向比對面板", expanded=False):
                from rectification_logic import rectify_birth_time, EVENT_TYPES
                
                rect_win = st.slider("生時搜索窗口 (前後 ± 分鐘)", min_value=5, max_value=45, value=15, step=5)
                rect_step = st.select_slider("步長 (分鐘)", options=[1, 2, 3, 5], value=2)
                
                st.markdown("**請輸入 2～4 個過去重大生活事件**：")
                ev_c1, ev_c2, ev_c3 = st.columns([2, 3, 1])
                
                if 'rect_events' not in st.session_state:
                    st.session_state.rect_events = [
                        {"date": "2015-06-15", "type": "career_promotion"},
                        {"date": "2020-10-01", "type": "marriage"}
                    ]
                
                with ev_c1:
                    new_ev_date = st.date_input("事件發生日期", value=date(2018, 6, 1))
                with ev_c2:
                    new_ev_type = st.selectbox("事件性質", options=list(EVENT_TYPES.keys()),
                                               format_func=lambda k: EVENT_TYPES[k]["name"])
                with ev_c3:
                    st.write("")
                    st.write("")
                    if st.button("➕ 加入事件"):
                        st.session_state.rect_events.append({"date": new_ev_date.strftime("%Y-%m-%d"), "type": new_ev_type})
                        st.rerun()

                if st.session_state.rect_events:
                    st.write("已加入之檢驗事件：")
                    ev_del_cols = st.columns(len(st.session_state.rect_events))
                    for idx, ev_item in enumerate(st.session_state.rect_events):
                        st.caption(f"事件 {idx+1}: {ev_item['date']} ｜ {EVENT_TYPES.get(ev_item['type'], {}).get('name', ev_item['type'])}")

                    if st.button("🚀 開始生時逆向校正比對", type="primary"):
                        with st.spinner("正在逐分鐘遞推星盤並計算原級弧度與小限吻合度..."):
                            def _chart_calc(d_str, t_str, off_str, lat_f, lon_f):
                                dt_obj, _ = logic.validate_and_parse_datetime(d_str, t_str, off_str.replace("UTC", "").replace("+", ""))
                                return logic.calculate_chart(dt_obj, lat_f, lon_f, d['meta']['location_city'])['chart']

                            candidates = rectify_birth_time(
                                _chart_calc,
                                d['meta']['birth_date_str'],
                                d['meta']['birth_time_str'],
                                search_window_mins=rect_win,
                                step_minutes=rect_step,
                                utc_offset_str=d['meta']['utc_offset_str'],
                                lat=d['meta']['lat'],
                                lon=d['meta']['lon'],
                                city=d['meta']['location_city'],
                                events_list=st.session_state.rect_events
                            )
                            st.session_state.rect_candidates = candidates

                    if st.session_state.get('rect_candidates'):
                        cands = st.session_state.rect_candidates
                        st.success(f"校正比對完成！共評估 {len(cands)} 組候選生時，依吻合度排序如下：")
                        top_rows = []
                        for c in cands[:8]:
                            top_rows.append({
                                '候選出生時間': c['candidate_time'],
                                '吻合置信度': f"{c['confidence_score']:.1f} %",
                                '上升星座': f"{c['asc_sign']} ({c['asc_deg_str']})",
                                '天頂星座': f"{c['mc_sign']} ({c['mc_deg_str']})"
                            })
                        st.table(pd.DataFrame(top_rows))
                        best = cands[0]
                        st.markdown(f"🏆 **最佳候選生時**：`{best['candidate_time']}`（吻合度 **{best['confidence_score']}%**，上升點：{best['asc_sign']} {best['asc_deg_str']}）")
                        st.markdown("**各事件吻合原因剖析**：")
                        for ev_res in best['evaluations']:
                            st.markdown(f"- **{ev_res['event_date']} ({ev_res['event_name']})** ➔ 得分 {ev_res['score']} 分")
                            for r in ev_res['reasons']:
                                st.markdown(f"  - {r}")

            st.markdown("</div>", unsafe_allow_html=True)

    # Tab 5: AI Prompt Generator & Browser AI Guide
    def _render_copy_prompt_box(prompt_text: str, element_id: str, box_label: str = "Prompt 內容"):
        import json as _json
        p_json = _json.dumps(prompt_text)
        st.caption(box_label)
        components.html(
            f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin-bottom: 10px;">
                <button id="btn_{element_id}" onclick="copyText_{element_id}()" style="
                    background: #2563EB; color: white; border: none; border-radius: 6px;
                    padding: 8px 16px; font-size: 14px; font-weight: 600; cursor: pointer;
                    display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                    transition: all 0.2s ease;
                ">
                    📋 一鍵複製 Prompt 到剪貼簿
                </button>
                <span id="msg_{element_id}" style="margin-left: 12px; font-size: 13px; color: #16A34A; font-weight: 600; display: none;">
                    ✅ 已成功複製到剪貼簿！請至 AI 聊天室按 Ctrl+V 貼上
                </span>
            </div>
            <script>
                function copyText_{element_id}() {{
                    const text = {p_json};
                    if (navigator.clipboard && window.isSecureContext) {{
                        navigator.clipboard.writeText(text).then(showSuccess_{element_id}).catch(fallbackCopy_{element_id});
                    }} else {{
                        fallbackCopy_{element_id}();
                    }}
                }}
                function fallbackCopy_{element_id}() {{
                    const text = {p_json};
                    const textArea = document.createElement("textarea");
                    textArea.value = text;
                    textArea.style.position = "fixed";
                    textArea.style.left = "-999999px";
                    document.body.appendChild(textArea);
                    textArea.focus();
                    textArea.select();
                    try {{
                        document.execCommand('copy');
                        showSuccess_{element_id}();
                    }} catch (err) {{
                        alert("複製失敗，請手動選取下方文字框內容按 Ctrl+C 複製");
                    }}
                    document.body.removeChild(textArea);
                }}
                function showSuccess_{element_id}() {{
                    const btn = document.getElementById("btn_{element_id}");
                    const msg = document.getElementById("msg_{element_id}");
                    btn.style.background = "#16A34A";
                    btn.innerHTML = "✅ 已複製！";
                    msg.style.display = "inline";
                    setTimeout(() => {{
                        btn.style.background = "#2563EB";
                        btn.innerHTML = "📋 一鍵複製 Prompt 到剪貼簿";
                        msg.style.display = "none";
                    }}, 3500);
                }}
            </script>
            """,
            height=46,
            scrolling=False
        )
        st.text_area("文本預覽（可手動選取複製）：", value=prompt_text, height=240, key=f"area_{element_id}")

    with all_tabs[5]:
        st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
        st.subheader("🤖 AI 大師解盤提示詞（Prompt）與轉貼指引")
        st.markdown("""
        現在市面上的網頁版 AI（如 **ChatGPT**、**Claude**、**Google Gemini**）具備極強的邏輯推理能力！<br>
        本程式已替您將全盤精確數據（包含宮位、七曜尊貴分、相位互容、小限、法達大運、太陽弧與卜卦判據）轉化為純正 1647 年 William Lilly 古典大師 Prompt。
        您可以直接**一鍵複製提示詞**，貼到您慣用的 AI 網頁版，即可開始一對一深度論命與追問！
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🚀 三步驟快速轉貼教學")
        step_c1, step_c2, step_c3 = st.columns(3)
        with step_c1:
            st.markdown("""
            <div style='background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px; height:100%;'>
                <div style='font-weight:700; color:#2563EB; margin-bottom:4px;'>Step 1. 選擇主題並複製</div>
                <div style='font-size:13px; color:#475569;'>在下方挑選「全盤總論」或「事業/財運/婚戀/流年」專題，點擊<b>「一鍵複製」</b>藍色按鈕。</div>
            </div>
            """, unsafe_allow_html=True)
        with step_c2:
            st.markdown("""
            <div style='background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px; height:100%;'>
                <div style='font-weight:700; color:#059669; margin-bottom:4px;'>Step 2. 開啟 AI 網站</div>
                <div style='font-size:13px; color:#475569;'>點擊下方按鈕前往 ChatGPT、Claude 或 Gemini 官方聊天網頁。</div>
            </div>
            """, unsafe_allow_html=True)
        with step_c3:
            st.markdown("""
            <div style='background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px; height:100%;'>
                <div style='font-weight:700; color:#7C3AED; margin-bottom:4px;'>Step 3. 貼上並自由追問</div>
                <div style='font-size:13px; color:#475569;'>按 <kbd>Ctrl+V</kbd> 貼上並送出，AI 將化身 William Lilly 親傳大師為您深度斷言，可隨意多輪追問！</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 🌐 常用網頁版 AI 工具快速跳轉")
        ai_link1, ai_link2, ai_link3, ai_link4 = st.columns(4)
        with ai_link1:
            st.link_button("🟢 前往 ChatGPT (OpenAI)", "https://chatgpt.com", use_container_width=True)
        with ai_link2:
            st.link_button("🟠 前往 Claude (Anthropic)", "https://claude.ai", use_container_width=True)
        with ai_link3:
            st.link_button("🔵 前往 Google Gemini", "https://gemini.google.com", use_container_width=True)
        with ai_link4:
            st.link_button("🟣 前往 DeepSeek (深度求索)", "https://chat.deepseek.com", use_container_width=True)

        st.markdown("---")
        with st.expander("💡 讓 AI 大師解盤更神準的「提問追問小技巧」 (Tips)", expanded=False):
            st.markdown("""
            在 AI 產出初步解析後，您可以將以下語句直接複製貼給 AI，獲得更具實戰意義的回答：
            1. **趨吉避凶與具體解方**：「*請從本命盤中力量最強、最尊貴的吉星與宮位切入，告訴我如何透過後天具體行動來化解凶星帶來的張力？*」
            2. **精確應期與轉折年**：「*請比對小限宮位與法達星限的交集，列出我未來 3 年內最關鍵的人生轉折年份與月份？*」
            3. **事業天命與創業適性**：「*依據我的第 10 宮天頂與精神點狀態，我更適合自立創業、專業技術合夥，還是大型機構體系？*」
            4. **感情正緣伴侶畫像**：「*請依據我的第 7 宮主星、飛宮與接納互容，具體描述我未來正緣伴侶的性格、職業背景與相識契機？*」
            5. **健康精力與慢性消耗預防**：「*請根據我的四液氣質與第 6/12 宮弱點，提醒我生活作息中應特別防範的臟腑與精力透支時段？*」
            6. **大考考運與出國深造契機**：「*我近期是否有考取專業證照、公職考試或出國留學發展的強勢星象加持？最佳衝刺時間點為何？*」
            7. **田宅房產與置產時機**：「*以我的第 4 宮田宅與財庫格局，近期適合買房置產嗎？在貸款或簽約時有什麼隱藏風險需要防範？*」
            8. **重要決定擇日避坑**：「*如果我近期有重大合約簽署或轉換工作，應避開哪些凶險星象（如逆行、燃燒、月亮空亡）？*」
            """)

        st.markdown("#### 📋 專題 Prompt 提示詞生成器")

        # Prepare prompts
        if st.session_state.chart_type == 'horary':
            cur_q_hor = st.session_state.get('horary_question', '這件事會成功嗎？')
            active_prompt = (
                f"{HORARY_SYSTEM_PROMPT}\n\n"
                "--- 以下是卜卦星盤數據 ---\n\n"
                f"{st.session_state.report_md}\n\n"
                f"--- 問卜具體問題 ---\n問題內容：{cur_q_hor}\n\n"
                "請嚴格依據 1647 年 William Lilly 古典卜卦占星法則，直接給予成事判斷、阻礙分析與預期應期！"
            )
            st.info(f"🔮 當前問卜問題：**「{cur_q_hor}」**")
            _render_copy_prompt_box(active_prompt, "horary_q", "專用卜卦成事診斷 Prompt (已整合 1647 原典規格與盤體數據)")
            st.download_button(
                "📥 下載此卜卦專用 Prompt 文字檔 (.txt)",
                data=active_prompt,
                file_name=f"Horary_Prompt_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            prompt_tabs = [
                "🌟 全盤大師總論",
                "💼 事業職涯",
                "💰 財富資產",
                "❤️ 婚戀關係",
                "🏥 健康體質",
                "🎓 學業考運",
                "🏡 田宅置產",
                "📅 流年返照合參"
            ]
            if st.session_state.report_data.get('synastry_data'):
                prompt_tabs.append("💑 雙人合盤深度合參")
            
            p_tab_objs = st.tabs(prompt_tabs)
            
            # Tab 1: Full Natal
            with p_tab_objs[0]:
                full_natal_prompt = (
                    f"{NATAL_SYSTEM_PROMPT}\n\n"
                    "--- 以下是本命星盤數據 ---\n\n"
                    f"{st.session_state.report_md}\n\n"
                    "請依據 1647 年《Christian Astrology》Book 3，為命盤主提供全面的人生格局、生命主星、氣質、十二宮位與重要推運時機之深度剖析。"
                )
                _render_copy_prompt_box(full_natal_prompt, "full_natal", "全盤深度診斷 Prompt (涵蓋全盤生命主、壽主星、氣質、十二宮與大運時間軸之宏觀診斷)")
                st.download_button(
                    "📥 下載全盤診斷 Prompt (.txt)",
                    data=full_natal_prompt,
                    file_name=f"Natal_Full_Prompt_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_full_natal_prompt"
                )

            # Tab 2: Career
            with p_tab_objs[1]:
                career_p = ThematicReportsLogic.generate_thematic_prompt(st.session_state.report_data, "career")
                _render_copy_prompt_box(career_p, "career", "事業職涯專題 Prompt (鎖定第 10 宮事業天頂、第 6 宮工作、第 11 宮貴人、精神點與黃道釋放法)")
                st.download_button(
                    "📥 下載事業專題 Prompt (.txt)",
                    data=career_p,
                    file_name=f"Career_Prompt_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_career_prompt"
                )

            # Tab 3: Wealth
            with p_tab_objs[2]:
                wealth_p = ThematicReportsLogic.generate_thematic_prompt(st.session_state.report_data, "wealth")
                _render_copy_prompt_box(wealth_p, "wealth", "財富資產專題 Prompt (鎖定第 2 宮財庫、第 8 宮偏財、第 4 宮不動產、福德點與資產避坑)")
                st.download_button(
                    "📥 下載財富專題 Prompt (.txt)",
                    data=wealth_p,
                    file_name=f"Wealth_Prompt_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_wealth_prompt"
                )

            # Tab 4: Romance
            with p_tab_objs[3]:
                romance_p = ThematicReportsLogic.generate_thematic_prompt(st.session_state.report_data, "romance")
                _render_copy_prompt_box(romance_p, "romance", "婚戀關係專題 Prompt (鎖定第 7 宮夫妻、第 5 宮戀愛桃花、金星/火星與伴侶原型)")
                st.download_button(
                    "📥 下載婚戀專題 Prompt (.txt)",
                    data=romance_p,
                    file_name=f"Romance_Prompt_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_romance_prompt"
                )

            # Tab 5: Health
            with p_tab_objs[4]:
                health_p = ThematicReportsLogic.generate_thematic_prompt(st.session_state.report_data, "health")
                _render_copy_prompt_box(health_p, "health", "健康體質專題 Prompt (四液氣質、Hyleg 生命主、第 6/8/12 宮慢性消耗與作息調理)")
                st.download_button(
                    "📥 下載健康專題 Prompt (.txt)",
                    data=health_p,
                    file_name=f"Health_Prompt_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_health_prompt"
                )

            # Tab 6: Academics
            with p_tab_objs[5]:
                academics_p = ThematicReportsLogic.generate_thematic_prompt(st.session_state.report_data, "academics")
                _render_copy_prompt_box(academics_p, "academics", "學業考運專題 Prompt (水星思維天賦、第 9 宮深造出國、國家考試與發表窗口)")
                st.download_button(
                    "📥 下載考運專題 Prompt (.txt)",
                    data=academics_p,
                    file_name=f"Academics_Prompt_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_academics_prompt"
                )

            # Tab 7: Real Estate
            with p_tab_objs[6]:
                re_p = ThematicReportsLogic.generate_thematic_prompt(st.session_state.report_data, "real_estate")
                _render_copy_prompt_box(re_p, "real_estate", "田宅置產專題 Prompt (第 4 宮田宅、買房時機、自住 vs 投資適性與居住環境)")
                st.download_button(
                    "📥 下載田宅專題 Prompt (.txt)",
                    data=re_p,
                    file_name=f"Real_Estate_Prompt_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_re_prompt"
                )

            # Tab 8: Solar Return
            with p_tab_objs[7]:
                sr_p = ThematicReportsLogic.generate_thematic_prompt(st.session_state.report_data, "solar_return")
                _render_copy_prompt_box(sr_p, "solar_return", "年度流年專題 Prompt (整合年度太陽返照盤、小限、法達星限與黃道釋放法之流年大合參)")
                st.download_button(
                    "📥 下載流年專題 Prompt (.txt)",
                    data=sr_p,
                    file_name=f"Solar_Return_Prompt_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_sr_prompt"
                )

            # Tab 9: Synastry (if present)
            if st.session_state.report_data.get('synastry_data') and len(prompt_tabs) > 8:
                with p_tab_objs[8]:
                    syn_p = ThematicReportsLogic.generate_thematic_prompt(st.session_state.report_data, "synastry")
                    _render_copy_prompt_box(syn_p, "synastry", "雙人合盤專題 Prompt (雙人古典合盤能量共振、跨盤相位與接納互容深度合參)")
                    st.download_button(
                        "📥 下載雙人合盤專題 Prompt (.txt)",
                        data=syn_p,
                        file_name=f"Synastry_Prompt_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key="dl_syn_prompt"
                    )

        st.markdown("---")
        with st.expander("📢 好物推薦與免責聲明 (Share & Disclaimer)", expanded=False):
            st.markdown("""
            - **📢 分享推薦**：如果本排盤系統與 AI 大師提示詞對您有所啟發，歡迎將本站網址分享給身邊對古典占星、命理規劃感興趣的親友或社群夥伴！
            - **⚖️ 諮詢免責聲明**：古典占星為象徵哲學、文化遺產與個人生涯規劃之參考工具。本程式與 AI 提供之分析僅供個人探索與自我覺察，不構成任何醫療、法律、財務投資之絕對保證或指令。重要人生抉擇請結合現實理性判斷。
            """)

        st.markdown("</div>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("---")
        st.subheader("下載文字版本命盤資訊")
        st.download_button(
            label="點擊下載",
            data=st.session_state.report_md,
            file_name=f"Chart_Report_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            use_container_width=True
        )
        if book_html:
            st.download_button("📜 下載完整圖文命書 (HTML / 可列印 PDF)", data=book_html.encode("utf-8"),
                               file_name=f"Astro_Book_{datetime.now().strftime('%Y%m%d')}.html", mime="text/html",
                               use_container_width=True, key="book_dl_side")

else:
    st.markdown("<br><br><div style='text-align: center; padding: 20px;'>", unsafe_allow_html=True)
    st.markdown("<h1 style='font-size: 1.75rem; color: #0B1C30;'>古典占星命盤簡易排盤程式</h1>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top: 15px; color: #64748B; font-size: 0.95rem; line-height: 1.6;'>手機使用者請點擊左上角 <b>「>」</b> 按鈕即可展開輸入時間與地點側邊欄進行排盤。</p>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top: 10px; color: #64748B;'>請於側邊欄輸入出生日期與時間以開始分析</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
