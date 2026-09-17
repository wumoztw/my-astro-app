import streamlit as st
import pandas as pd
import os
from datetime import datetime, date, timedelta, timezone
from flatlib import const

import sys
import importlib

# Ensure fresh module reloading in Streamlit Cloud when git updates
for _mod_name in (
    'logic', 'horary_engine_logic', 'dignities_logic', 'aspects_logic', 'lots_logic', 
    'time_lords_logic', 'zodiacal_releasing_logic', 'solar_arc_logic', 
    'almuten_logic', 'secondary_progressions_logic', 'tertiary_progressions_logic',
    'thematic_reports_logic', 'horary_prompt', 'natal_prompt', 'ai_logic',
    'github_forum_exporter'
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
from ai_logic import AIAssistant
from github_forum_exporter import generate_discussion_payload, REPO_URL

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

# --- Custom Styling (Minimalist Clean Theme) ---
st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background-color: #FFFFFF;
    }
    
    /* Sidebar Aesthetics */
    section[data-testid="stSidebar"] {
        background-color: #F8F9FA !important;
        border-right: 1px solid #DEE2E6;
    }
    section[data-testid="stSidebar"] label {
        color: #212529 !important;
        font-weight: 600 !important;
    }
    
    /* Input Design */
    .stTextInput input, .stNumberInput input {
        border: 1px solid #CED4DA !important;
        border-radius: 4px !important;
    }
    
    /* Typography */
    h1, h2, h3 {
        color: #212529 !important;
    }
    .stMarkdown, p {
        color: #212529;
    }
    
    /* Simple Container */
    .stContainer {
        border: 1px solid #E9ECEF;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: #FFFFFF;
    }
    
    /* Summary Card (Big Three) */
    .summary-card {
        background: #F8F9FA;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        border: 1px solid #DEE2E6;
    }
    .summary-title { font-size: 0.9rem; opacity: 0.8; margin-bottom: 5px; }
    .summary-value { font-size: 1.4rem; font-weight: bold; }
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

# Date/Time Input via Text
date_input_raw = st.sidebar.text_input("日期 (YYYY/MM/DD)", value="1900/01/01")
try:
    birth_date = datetime.strptime(date_input_raw.strip(), '%Y/%m/%d').date()
except ValueError:
    st.sidebar.error("請依照 YYYY/MM/DD 格式輸入日期")
    st.stop()

time_input_raw = st.sidebar.text_input("時間 (HH:MM)", value="12:00")
try:
    time_str = time_input_raw.replace('：', ':').strip()
    birth_time = datetime.strptime(time_str, '%H:%M').time()
except ValueError:
    st.sidebar.error("請依照 HH:MM 格式輸入時間")
    st.stop()

st.sidebar.markdown("---")

location_city = st.sidebar.text_input("輸入城市名稱", "台北市")

with st.sidebar.expander("自行手動輸入經緯度與時區", expanded=False):
    manual_lon = st.number_input("經度 (Longitude)", value=121.50, format="%.2f")
    manual_lat = st.number_input("緯度 (Latitude)", value=25.03, format="%.2f")
    utc_offset = st.number_input("時區偏移 (UTC Offset)", value=8.0, step=0.5)

@st.dialog("取得免費 API Key", width="large")
def show_api_keys_dialog():
    st.markdown("""
    如果你還沒有 API Key，可以前往以下平台免費註冊並取得：
    - **Google Gemini**: [Google AI Studio](https://aistudio.google.com/app/apikey) (推薦，每天有高額免費額度)
    - **Groq**: [GroqCloud](https://console.groq.com/keys) (推薦，提供速度極快的開源模型，免費額度高)
    - **OpenRouter**: [OpenRouter API](https://openrouter.ai/keys) (推薦，可以使用多款頂尖的開源免費模型，如 Llama 3)
    - **OpenAI**: [OpenAI Platform](https://platform.openai.com/api-keys) (需綁定信用卡，無免費額度)
    
    *取得 Key 後，請複製並貼上到左側的輸入框中，即可開始使用 AI 自動解析功能！*
    """)

st.sidebar.markdown("---")
st.sidebar.header("AI 設定 (不輸入也可排盤)")

ai_provider = st.sidebar.selectbox("AI 供應商", ["Gemini", "Groq", "OpenAI", "OpenRouter"])

# Key label changes based on provider
key_label = f"{ai_provider} API Key"
ai_api_key = st.sidebar.text_input(key_label, type="password", help=f"請輸入您的 {ai_provider} API Key")

if st.sidebar.button("👉 點此查閱如何取得免費 API Key", type="tertiary", help="查看各大平台的免費 API Key 註冊教學"):
    show_api_keys_dialog()

# Trigger dynamic model discovery if key or provider changed
if (ai_api_key != st.session_state.get('last_key') or ai_provider != st.session_state.get('last_provider')):
    st.session_state.last_key = ai_api_key
    st.session_state.last_provider = ai_provider
    # Initialize a temp assistant to fetch models
    with st.sidebar:
        with st.spinner("🔍 正在探索可用模型..."):
            temp_assistant = AIAssistant(provider=ai_provider, api_key=ai_api_key)
            st.session_state.dynamic_models = temp_assistant.fetch_available_models()
    st.rerun()

# Default fallback if discovery failed or key empty
if not st.session_state.dynamic_models:
    temp_assistant = AIAssistant(provider=ai_provider)
    st.session_state.dynamic_models = temp_assistant.get_model_list(ai_provider)

ai_model = st.sidebar.selectbox("AI 模型", st.session_state.dynamic_models)

# Initialize AI Assistant with correct parameters
ai_assistant = AIAssistant(provider=ai_provider, api_key=ai_api_key, model_name=ai_model)

st.sidebar.markdown("---")
# Buttons for calculation
col1, col2 = st.sidebar.columns(2)
with col1:
    generate_btn = st.button("排本命盤", use_container_width=True)
with col2:
    horary_btn = st.button("卜卦占星", use_container_width=True)

# --- Logic Processing ---
if generate_btn or horary_btn:
    # Reset AI analysis and chat history when a NEW chart is generated
    st.session_state.ai_analysis_triggered = False
    st.session_state.chat_history = []
    
    if generate_btn:
        st.session_state.chart_type = "natal"
    elif horary_btn:
        st.session_state.chart_type = "horary"

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
        is_day = logic.is_day_birth(chart, houses)
        f_data = logic.get_firdaria_data(birth_date_str, is_day, current_date=target_date)
        zr_data = logic.calculate_zodiacal_releasing(chart, is_day, birth_date_str, current_date=target_date) if hasattr(logic, 'calculate_zodiacal_releasing') else {}
        sa_data = logic.calculate_solar_arcs(chart, birth_date_str, birth_time_str, offset_str, final_lat, final_lon, target_date=target_date) if hasattr(logic, 'calculate_solar_arcs') else {}
        sec_prog_data = logic.calculate_secondary_progressions(chart, houses, birth_date_str, birth_time_str, offset_str, final_lat, final_lon, target_date=target_date) if hasattr(logic, 'calculate_secondary_progressions') else {}
        tert_prog_data = logic.calculate_tertiary_progressions(chart, houses, birth_date_str, birth_time_str, offset_str, final_lat, final_lon, target_date=target_date) if hasattr(logic, 'calculate_tertiary_progressions') else {}
        lots = logic.calculate_lots(chart, houses, is_day)
        fixed_stars = logic.get_fixed_stars(chart)

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
                    md += f"  * 直接入相位：{dp['source']} 與 {dp['target']} 呈 {dp['aspect']} (剩餘 {dp['delta_deg']}°)\n"
            if p.get('translation_of_light'):
                for tol in p['translation_of_light']:
                    md += f"  * 光線傳遞：{tol['translator']} 傳遞光線予 {tol['receiver']}\n"
            if p.get('collection_of_light'):
                for col in p['collection_of_light']:
                    md += f"  * 光線收集：{col['collector']} 收集雙方光線\n"
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

        md += "---\n\n"
        md += "## 🤖 AI 自動解析已就緒\n"
        report_type = "本命盤" if st.session_state.chart_type == 'natal' else "卜卦占星盤"
        md += f"目前的分析模式為：**{report_type}**。請點擊側邊欄的「🚀 啟動 AI 深度解析」開始互動。\n\n"

        st.session_state.report_md = md
        st.session_state.report_data = {
            'chart': chart,
            'asc': f"{asc_sign} {asc_deg}°{asc_min}'",
            'sun': f"{sun_sign} {sun_deg}°{sun_min}'",
            'moon': f"{moon_sign} {moon_deg}°{moon_min}'",
            'planets': planets_data,
            'houses': houses,
            'aspects': aspects,
            'prof_info': prof_info,
            'f_data': f_data,
            'zr_data': zr_data,
            'sa_data': sa_data,
            'sec_prog_data': sec_prog_data,
            'tert_prog_data': tert_prog_data,
            'is_day': is_day,
            'lots': lots,
            'fixed_stars': fixed_stars,
            'horary_analysis': horary_analysis
        }
    except Exception as e:
        st.error(f"分析錯誤: {str(e)}")

# --- AI Integration Processing (Specialized Modules) ---
if st.session_state.report_data and ai_assistant.is_configured:
    with st.sidebar:
        st.markdown("---")
        st.subheader("🤖 AI 自動解析")
        
        if st.session_state.chart_type == 'horary':
            # --- Specialized Horary AI Module ---
            horary_question = st.text_input("📌 請輸入您想占卜的問題：", value=st.session_state.get('horary_question', '這件事會成功嗎？'), help="例如：我會不會順利錄取這份工作？")
            st.session_state.horary_question = horary_question
            
            if st.button("🔮 啟動卜卦盤 AI 邏輯分析引擎", use_container_width=True, type="primary"):
                st.session_state.ai_analysis_triggered = True
                
                question_block = f"\n\n--- 用戶想占卜的問題 (非常重要) ---\n問題內容：{horary_question}\n" if horary_question.strip() else ""
                
                initial_user_msg = (
                    f"{HORARY_SYSTEM_PROMPT}\n\n"
                    "--- 以下是卜卦星盤數據 ---\n\n"
                    f"{st.session_state.report_md}"
                    f"{question_block}"
                )
                st.session_state.chat_history = [{"role": "user", "content": initial_user_msg}]
        else:
            # --- Specialized Natal AI Module ---
            if st.button("🚀 啟動本命盤 AI 大師深度解析", use_container_width=True, type="primary"):
                st.session_state.ai_analysis_triggered = True
                initial_user_msg = (
                    f"{NATAL_SYSTEM_PROMPT}\n\n"
                    "--- 以下是本命星盤數據 ---\n\n"
                    f"{st.session_state.report_md}"
                )
                st.session_state.chat_history = [{"role": "user", "content": initial_user_msg}]

            st.markdown("---")
            st.markdown("🎯 **三大專題深度診斷**")
            thm_col1, thm_col2, thm_col3 = st.columns(3)
            with thm_col1:
                if st.button("💼 事業", use_container_width=True, help="事業職涯、貴人格局與天命專題"):
                    st.session_state.ai_analysis_triggered = True
                    p_msg = ThematicReportsLogic.generate_thematic_prompt(st.session_state.report_data, "career")
                    st.session_state.chat_history = [{"role": "user", "content": p_msg}]
            with thm_col2:
                if st.button("💰 財富", use_container_width=True, help="財富資產、正偏財與投資避坑專題"):
                    st.session_state.ai_analysis_triggered = True
                    p_msg = ThematicReportsLogic.generate_thematic_prompt(st.session_state.report_data, "wealth")
                    st.session_state.chat_history = [{"role": "user", "content": p_msg}]
            with thm_col3:
                if st.button("❤️ 婚戀", use_container_width=True, help="婚戀桃花、伴侶原型與關係經營專題"):
                    st.session_state.ai_analysis_triggered = True
                    p_msg = ThematicReportsLogic.generate_thematic_prompt(st.session_state.report_data, "romance")
                    st.session_state.chat_history = [{"role": "user", "content": p_msg}]

# --- UI Layout ---
if st.session_state.report_data:
    d = st.session_state.report_data
    ui_title_map = {'natal': '古典占星本命盤資訊', 'horary': '古典占星卜卦盤資訊'}
    ui_title = ui_title_map.get(st.session_state.chart_type, '古典占星論命資訊')
    
    st.markdown(f"<h1 style='text-align: center; margin-bottom: 5px; color: #000;'>{ui_title}</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-style: italic; color: #666; margin-bottom: 30px;'>Professional Classical Astrology Analysis System</p>", unsafe_allow_html=True)
    
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(f"<div class='summary-card'><div class='summary-title'>太陽星座</div><div class='summary-value'>{d['sun']}</div></div>", unsafe_allow_html=True)
    with sc2:
        st.markdown(f"<div class='summary-card'><div class='summary-title'>月亮星座</div><div class='summary-value'>{d['moon']}</div></div>", unsafe_allow_html=True)
    with sc3:
        st.markdown(f"<div class='summary-card'><div class='summary-title'>上升星座</div><div class='summary-value'>{d['asc']}</div></div>", unsafe_allow_html=True)
    
    # --- UI Layout ---
    # Define tabs dynamically
    if st.session_state.chart_type == 'horary':
        tabs_list = [
            '🪐 行星與本質力量',
            '📐 相位與接納關係',
            '🔮 卜卦檢意與成事診斷',
            '🌙 月亮流動與應期時鐘'
        ]
        if st.session_state.get('ai_analysis_triggered'):
            tabs_list.append('✨ AI 卜卦深度解析報告')
    else:
        tabs_list = [
            '行星與本質力量',
            '相位與接納',
            '特殊點位與恆星',
            '推運時間軸 (法達/小限/ZR/太陽弧)'
        ]
        if st.session_state.get('ai_analysis_triggered'):
            tabs_list.append('✨ AI 深度解析報告')
    
    # Always append Community Forum Tab at the end
    tabs_list.append('🏛️ 占星社群論壇')
    
    all_tabs = st.tabs(tabs_list)
    
    # Tab 1: Planets
    with all_tabs[0]:
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
        
        st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
        st.subheader("十二宮位表")
        df_h = pd.DataFrame(d['houses'])
        col_map_h = {'id_str': '宮位名稱', 'sign': '對應星座', 'ruler': '宮位主星'}
        cols_h = [c for c in col_map_h if c in df_h.columns]
        st.table(df_h[cols_h].rename(columns=col_map_h))
        st.markdown("</div>", unsafe_allow_html=True)

    # Tab 2: Aspects
    with all_tabs[1]:
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
        st.markdown("</div>", unsafe_allow_html=True)

    # Tab 3: Lots & Stars (Natal) OR Radicality & Perfection (Horary)
    with all_tabs[2]:
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
            
            st.markdown(f"""
            <div style='background: #F1F5F9; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px; border-left: 4px solid #3B82F6;'>
                <div style='font-size: 13px; color: #64748B; margin-bottom: 2px;'>當前占卜問題</div>
                <div style='font-size: 19px; font-weight: 800; color: #0F172A; margin-bottom: 6px;'>「{cur_q_text}」</div>
                <div style='font-size: 13px; color: #334155;'>
                    🎯 智能對焦領域：<b>第 {target_h_num} 宮（{target_h_desc}）</b> ｜ 匹配關鍵字：<span style='background:#E2E8F0; padding:2px 8px; border-radius:4px; font-weight:600;'>{target_kw}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

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
                st.markdown(f"""
                <div style='background:#F0FDF4; border:1px solid #86EFAC; border-left:4px solid #16A34A; border-radius:6px; padding:10px 14px; margin-bottom:8px;'>
                    <b>2. 光線傳遞 (Translation of Light)</b>：<span style='color:#16A34A; font-weight:bold;'>【成立 - 熱心貴人】</span> 第三方星體 <b>{tol0['translator']}</b> 從 {tol0['source']} 離相，奔向與 {tol0['receiver']} 成相，從中撮合！
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
    with all_tabs[3]:
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
            st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
            st.subheader("推運資訊摘要")
            pi = d['prof_info']
            st.write(f"當前年齡：{pi.get('age')} 歲")
            st.write(f"小限走到：{pi.get('prof_sign')} (第 {pi.get('prof_house_num')} 宮)")
            st.write(f"年度主星：{pi.get('lord_of_year')}")
            st.markdown("---")
        
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

            # --- Zodiacal Releasing (ZR) Section ---
            st.subheader("希臘黃道釋放法 (Zodiacal Releasing - 精神點)")
            zr = d.get('zr_data', {}).get('spirit', {})
            if zr:
                act_l1 = zr.get('active_l1', {})
                act_l2 = zr.get('active_l2', {})
                z_col1, z_col2 = st.columns(2)
                with z_col1:
                    st.markdown(f"**L1 主運**：`{act_l1.get('sign_name')}` ({act_l1.get('ruler_name')})")
                    st.caption(f"區間：{act_l1.get('start_date')} ~ {act_l1.get('end_date')} ｜ {act_l1.get('peak_type', '普通時期')}")
                with z_col2:
                    st.markdown(f"**L2 子運**：`{act_l2.get('sign_name')}` ({act_l2.get('ruler_name')})")
                    st.caption(f"區間：{act_l2.get('start_date')} ~ {act_l2.get('end_date')} ｜ {act_l2.get('peak_type', '普通時期')}")
                if act_l2.get('is_lb'):
                    st.warning("⚠️ 當前處於換宮跳躍 (Losing of the Bond) 關鍵轉折大變動期！")

                with st.expander("查看黃道釋放法 L1 完整時間軸"):
                    l1_list = []
                    for p in zr.get('l1_periods', []):
                        l1_list.append({
                            '星座': p['sign_name'],
                            '主星': p['ruler_name'],
                            '黃道年數': p['years'],
                            '開始時間': p['start_date'],
                            '結束時間': p['end_date'],
                            '巔峰屬性': p['peak_type']
                        })
                    st.table(pd.DataFrame(l1_list))
            st.markdown("---")

            # --- Solar Arc Directions (SAD) Section ---
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

            # --- Secondary Progressions (一日一年) Section ---
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

                # --- Tertiary Progressions (一日一月) Section ---
                st.subheader("三限推運法 (Tertiary Progressions - 一日一月)")
                st.caption("推進法則：以地球自轉一日對應熱帶月（約 27.32 日），精準捕捉以「月份/週」為尺度的生活場景轉移與情緒心理焦點。")
                tp = d.get('tert_prog_data', {})
                if tp:
                    t_moon = tp.get('tertiary_moon', {})
                    tl_phase = tp.get('lunar_phase', {})
                
                    tp_col1, tp_col2 = st.columns(2)
                    with tp_col1:
                        st.markdown(f"**🌙 三限月亮當月焦點**：`{t_moon.get('sign', '')} {t_moon.get('degree_str', '')}` ({t_moon.get('house_str', '')})")
                        st.caption(f"當月生活重心：{t_moon.get('theme', '')}")
                        st.caption(f"預計換宮剩餘：約 {t_moon.get('weeks_left_in_sign', 0)} 週 ({t_moon.get('days_left_in_sign', 0)} 天)")
                    with tp_col2:
                        st.markdown(f"**🌗 2.5 年月相週期**：`{tl_phase.get('phase_name', '')}`")
                        st.caption(f"階段進程：【{tl_phase.get('stage', '')}】(第 {tl_phase.get('cycle_month', 0)} 個月 / 29.5 個月週期)")
                        st.caption(f"{tl_phase.get('desc', '')}")

                    # 2.5 年三限月相進度軸
                    t_angle_val = tl_phase.get('angle', 0.0)
                    t_prog_ratio = min(1.0, max(0.0, t_angle_val / 360.0))
                    st.progress(t_prog_ratio, text=f"2.5年月相循環：{round(t_prog_ratio * 100, 1)}% (約第 {tl_phase.get('cycle_month', 0)} 個月 / 29.5 個月週期)")

                    cur_tpname = tl_phase.get('phase_name', '')
                    tp_badges_html = "<div style='display: flex; justify-content: space-between; margin-top: 4px; margin-bottom: 12px; gap: 4px; overflow-x: auto;'>"
                    for name, icon, deg_range, stage in phase_stages:
                        is_active = (name in cur_tpname)
                        bg_col = "#1E293B" if is_active else "#F1F5F9"
                        text_col = "#38BDF8" if is_active else "#475569"
                        border = "2px solid #38BDF8" if is_active else "1px solid #CBD5E1"
                        tp_badges_html += f"<div style='flex: 1; min-width: 65px; text-align: center; background: {bg_col}; color: {text_col}; border: {border}; border-radius: 6px; padding: 6px 2px; font-size: 11px;'>"
                        tp_badges_html += f"<div style='font-size: 16px; margin-bottom: 2px;'>{icon}</div><b>{stage}</b><div style='font-size: 9px; opacity: 0.8;'>{deg_range}</div></div>"
                    tp_badges_html += "</div>"
                    st.markdown(tp_badges_html, unsafe_allow_html=True)

                    tp_aspects = tp.get('active_aspects', [])
                    if tp_aspects:
                        st.markdown("**當月活躍三限相位 (對本命盤，持續約 2~4 週)**：")
                        tp_rows = []
                        for asp in tp_aspects:
                            tp_rows.append({
                                '三限星 (Tert)': asp['prog_planet'],
                                '相位': asp['aspect'],
                                '本命星 (Natal)': asp['natal_planet'],
                                '誤差': asp['orb_str'],
                                '持續引動期': asp['duration']
                            })
                        st.table(pd.DataFrame(tp_rows))
                    else:
                        st.write("目前無容許度內之活躍三限對本命相位。")
            st.markdown("</div>", unsafe_allow_html=True)

    # Tab 5: AI Analysis (Dynamic Chat)
    if st.session_state.get('ai_analysis_triggered'):
        with all_tabs[4]:
            st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
            if st.session_state.chart_type == "natal":
                st.subheader("✨ AI 大師深度分析報告與對話 (本命盤專用)")
            else:
                st.subheader("🔮 AI 邏輯分析引擎報告與對話 (卜卦盤專用)")
            
            # Display chat history
            for msg in st.session_state.chat_history:
                # Skip the very first bulky data message to keep UI clean, or show a summary
                if msg == st.session_state.chat_history[0]:
                    with st.chat_message("user"):
                        st.write("📊 *已上傳命盤數據進行解析...*")
                    continue
                
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            # Handle first generation if history only has the initial user message
            if len(st.session_state.chat_history) == 1:
                with st.chat_message("assistant"):
                    # Select correct specialized prompt
                    current_prompt = HORARY_SYSTEM_PROMPT if st.session_state.chart_type == 'horary' else NATAL_SYSTEM_PROMPT
                    full_response = ""
                    resp_container = st.empty()
                    for chunk in ai_assistant.generate_chat_stream(current_prompt, st.session_state.chat_history):
                        full_response += chunk
                        resp_container.markdown(full_response)
                    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                    st.rerun()

            # Chat input for follow-up
            if prompt := st.chat_input("對這張命盤有什麼想追問的嗎？"):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                with st.chat_message("assistant"):
                    # Select correct specialized prompt for follow-up
                    current_prompt = HORARY_SYSTEM_PROMPT if st.session_state.chart_type == 'horary' else NATAL_SYSTEM_PROMPT
                    full_response = ""
                    resp_container = st.empty()
                    for chunk in ai_assistant.generate_chat_stream(current_prompt, st.session_state.chat_history):
                        full_response += chunk
                        resp_container.markdown(full_response)
                    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

    # Tab: GitHub Discussions Community Forum
    with all_tabs[-1]:
        st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
        st.subheader("🏛️ GitHub 原生古典占星社群論壇 (Discussions)")
        st.markdown(
            "歡迎將此命盤發布至 GitHub 開源討論區進行深度研討！\n\n"
            "發布後，我們的 **AI 駐站古典掌門（William Lilly 1647 原典體系）** 將透過 **Groq LPU (openai/gpt-oss-120b)** "
            "在 2 秒內於討論串底下自動提供第一道深度體檢、徵象星診斷與成事路徑分析。"
        )

        q_or_theme = st.session_state.get('horary_question', '') if st.session_state.chart_type == 'horary' else "古典本命格局與推運研討"
        forum_notes = st.text_area(
            "📝 想向社群易友說明的背景或問題細節（選填）：",
            placeholder="例如：目前正在考慮是否接受外商 Offer、想探討 ZR 精神點 L2 換宮轉折的具體生活印證...",
            key="forum_custom_notes"
        )

        f_payload = generate_discussion_payload(
            chart_type=st.session_state.chart_type,
            question_or_theme=q_or_theme,
            report_data=st.session_state.report_data,
            report_md=st.session_state.report_md,
            extra_notes=forum_notes
        )

        st.markdown("---")
        st.info(
            "💡 **極簡發布 2 步驟**：\n"
            "1. 點擊下方內容框右上角的 **「複製 (Copy)」** 圖示（已包含完整命盤、七政度數、相位與推運報告）。\n"
            "2. 點擊 **「🌐 前往 GitHub Discussions 發布」** ➔ 貼上標題與內容 ➔ 點擊 **Start discussion** 送出！"
        )

        st.text_input("📌 貼文標題 (Title)：", value=f_payload['title'], help="可複製此標題填入 GitHub 討論串標題欄")

        st.markdown("#### 📋 完整命盤發布內容 (點右上角一鍵複製)：")
        st.code(f_payload['full_markdown_body'], language="markdown")

        f_col1, f_col2 = st.columns([1, 1])
        with f_col1:
            st.link_button(
                "🌐 前往 GitHub Discussions 發布 (貼上即發)",
                f"{REPO_URL}/discussions/new?category={f_payload['category_slug']}",
                use_container_width=True,
                type="primary"
            )
        with f_col2:
            st.link_button(
                "📚 瀏覽論壇現有所有案例討論",
                f_payload['repo_discussions_url'],
                use_container_width=True
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # Re-declare tabs (Handled above now)

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
        st.markdown("---")
        st.subheader("🏛️ 社群論壇交流")
        st.link_button(
            "🌐 前往 GitHub 占星論壇",
            f"{REPO_URL}/discussions",
            use_container_width=True
        )

else:
    st.markdown("<br><br><div style='text-align: center;'>", unsafe_allow_html=True)
    st.markdown("<h1 style='font-size: 2.5rem;'>古典占星命盤簡易排盤程式</h1>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top: 50px;'>請於側邊欄輸入出生日期與時間以開始分析</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
