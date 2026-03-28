import streamlit as st
import pandas as pd
import os
from datetime import datetime, date, timedelta, timezone
from flatlib import const

# Modular Imports
from logic import AstrologyLogic
from horary_prompt import HORARY_SYSTEM_PROMPT
from natal_prompt import NATAL_SYSTEM_PROMPT
from ai_logic import AIAssistant

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
    .stMarkdown, p, span, div {
        color: #212529 !important;
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
        
        sign = '+' if utc_offset >= 0 else '-'
        abs_offset = abs(utc_offset)
        h, m = int(abs_offset), int((abs_offset - int(abs_offset)) * 60)
        offset_str = f"{sign}{h:02d}:{m:02d}"
        
        from flatlib.datetime import Datetime
        from flatlib.geopos import GeoPos
        from flatlib.chart import Chart
        
        dt = Datetime(birth_date_str, birth_time_str, offset_str)
        pos = GeoPos(final_lat, final_lon)
        chart = Chart(dt, pos)
        
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

        houses = logic.calculate_equal_houses(asc.lon)
        planets_data = logic.get_planets_data(chart, houses)

        # Determine target date for progressions and time lords based on system time
        target_date = datetime.now().date()

        prof_info = logic.calculate_profections(chart, houses, birth_date_str, current_date=target_date)
        aspects = logic.get_aspects(chart)
        is_day = logic.is_day_birth(chart, houses)
        f_data = logic.get_firdaria_data(birth_date_str, is_day, current_date=target_date)
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

        md += "---\n\n"
        md += "## 🤖 AI 自動解析已就緒\n"
        report_type = "本命盤" if st.session_state.chart_type == 'natal' else "卜卦占星盤"
        md += f"目前的分析模式為：**{report_type}**。請點擊側邊欄的「🚀 啟動 AI 深度解析」開始互動。\n\n"



        st.session_state.report_md = md
        st.session_state.report_data = {
            'asc': f"{asc_sign} {asc_deg}°{asc_min}'",
            'sun': f"{sun_sign} {sun_deg}°{sun_min}'",
            'moon': f"{moon_sign} {moon_deg}°{moon_min}'",
            'planets': planets_data,
            'houses': houses,
            'aspects': aspects,
            'prof_info': prof_info,
            'f_data': f_data,
            'is_day': is_day,
            'lots': lots,
            'fixed_stars': fixed_stars
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
            horary_question = st.text_input("📌 請輸入您想占卜的問題：", help="例如：我會不會順利錄取這份工作？")
            
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
    tabs_list = ['行星與本質力量', '相位與接納', '特殊點位與恆星', '法達星限與小限']
    if st.session_state.get('ai_analysis_triggered'):
        tabs_list.append('✨ AI 深度解析報告')
    
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
        df_h_disp = df_h[['id_str', 'sign', 'ruler']].copy()
        df_h_disp.columns = ['宮位名稱', '對應星座', '宮位主星']
        st.table(df_h_disp)
        st.markdown("</div>", unsafe_allow_html=True)

    # Tab 2: Aspects
    with all_tabs[1]:
        st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
        st.subheader("行星相位與接納關係")
        if d['aspects']:
            df_a = pd.DataFrame(d['aspects'])
            df_a.columns = ['行星 1', '行星 2', '相位類型', '誤差', '接納關係']
            st.table(df_a)
        else:
            st.write("目前無顯著相位。")
        st.markdown("</div>", unsafe_allow_html=True)

    # Tab 3: Lots & Stars
    with all_tabs[2]:
        st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
        st.subheader("希臘點 (Lots)")
        df_l = pd.DataFrame(d['lots'])
        df_l.columns = ['點位名稱', '星座', '度數', '宮位']
        st.table(df_l)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
        st.subheader("重要恆星合相 (Fixed Stars)")
        if d['fixed_stars']:
            df_s = pd.DataFrame(d['fixed_stars'])
            df_s.columns = ['行星', '恆星', '誤差']
            st.table(df_s)
        else:
            st.write("目前無行星與重要恆星合相。")
        st.markdown("</div>", unsafe_allow_html=True)

    # Tab 4: Time Lords
    with all_tabs[3]:
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

else:
    st.markdown("<br><br><div style='text-align: center;'>", unsafe_allow_html=True)
    st.markdown("<h1 style='font-size: 2.5rem;'>古典占星命盤簡易排盤程式</h1>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top: 50px;'>請於側邊欄輸入出生日期與時間以開始分析</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
