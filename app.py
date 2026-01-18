import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
from flatlib import const

# Modular Imports
from logic import AstrologyLogic

# Initialize Logic
logic = AstrologyLogic()

st.set_page_config(page_title="古典占星命盤簡易排盤程式", layout="wide")

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

# --- Sidebar Inputs ---
st.sidebar.header("輸入出生資料")

# Date/Time Input via Text
date_input_raw = st.sidebar.text_input("出生日期 (YYYY/MM/DD)", value="1900/01/01")
try:
    birth_date = datetime.strptime(date_input_raw.strip(), '%Y/%m/%d').date()
except ValueError:
    st.sidebar.error("請依照 YYYY/MM/DD 格式輸入日期")
    st.stop()

time_input_raw = st.sidebar.text_input("出生時間 (HH:MM)", value="12:00")
try:
    time_str = time_input_raw.replace('：', ':').strip()
    birth_time = datetime.strptime(time_str, '%H:%M').time()
except ValueError:
    st.sidebar.error("請依照 HH:MM 格式輸入時間")
    st.stop()

st.sidebar.markdown("---")

location_city = st.sidebar.text_input("輸入出生城市", "台北市")

with st.sidebar.expander("自行手動輸入經緯度與時區", expanded=False):
    manual_lon = st.number_input("經度 (Longitude)", value=121.50, format="%.2f")
    manual_lat = st.number_input("緯度 (Latitude)", value=25.03, format="%.2f")
    utc_offset = st.number_input("時區偏移 (UTC Offset)", value=8.0, step=0.5)

st.sidebar.markdown("---")
generate_btn = st.sidebar.button("排命盤", use_container_width=True)

# --- Logic Processing ---
if generate_btn:
    try:
        final_lat, final_lon = manual_lat, manual_lon
        if manual_lon == 121.50 and manual_lat == 25.03 and location_city != "台北市":
            coords = logic.get_location_coordinates(location_city)
            if coords:
                final_lat, final_lon = coords
            else:
                st.sidebar.warning("⚠️ 自動地點檢索暫時無法連線，請手動展開下方進階選項輸入經緯度。")

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
        prof_info = logic.calculate_profections(chart, houses, birth_date_str)
        aspects = logic.get_aspects(chart)
        is_day = logic.is_day_birth(chart, houses)
        f_data = logic.get_firdaria_data(birth_date_str, is_day)

        # Build Markdown Report
        md = "# 古典占星命盤完整資料\n\n"
        md += f"產出時間：{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n\n"
        md += "---\n\n"
        md += "## 出生資訊\n\n"
        md += f"- 生日：{birth_date_str} {birth_time_str}\n"
        md += f"- 地點：{location_city} ({final_lat:.2f}N, {final_lon:.2f}E)\n"
        md += f"- 上升星座：{asc_sign} {asc_deg}°{asc_min}'\n"
        md += f"- 太陽星座：{sun_sign} {sun_deg}°{sun_min}'\n"
        md += f"- 月亮星座：{moon_sign} {moon_deg}°{moon_min}'\n\n"
        
        md += "## 行星狀態\n\n"
        for p in planets_data:
            md += f"- {p['name']}：{p['sign']} {p['degree_str']} {p['retro']} | [{p['house']}]\n"
        md += "\n"
        
        md += "## 宮位資料\n\n"
        for h in houses:
            h_deg, h_min, _ = logic.degree_to_dms(h['degree'])
            md += f"- {h['id_str']}：{h['sign']} {h_deg}°{h_min}' (主：{h['ruler']})\n"
        md += "\n"
        
        md += "## 相位表\n\n"
        if aspects:
            for a in aspects:
                md += f"- {a['p1']} - {a['p2']}：{a['aspect']} (誤差 {a['orb']})\n"
        else:
            md += "無顯著相位。\n"
        md += "\n"
        
        md += "## 推運資訊\n\n"
        md += f"- 小限分限：{prof_info.get('prof_sign')} (第 {prof_info.get('prof_house_num')} 宮)\n"
        md += f"- 當前年主星：{prof_info.get('lord_of_year')}\n\n"
        
        act = f_data['active']
        m_n = logic.TRANS_PLANETS.get(act['major'], act['major'])
        mi_n = logic.TRANS_PLANETS.get(act['minor'], act['minor'])
        md += f"- 法達當前大運：{m_n}\n"
        md += f"- 法達當前小運：{mi_n}\n"
        md += f"- 下次換運日期：{act['end'].strftime('%Y/%m/%d')}\n"

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
            'is_day': is_day
        }
    except Exception as e:
        st.error(f"分析錯誤: {str(e)}")

# --- UI Layout ---
if st.session_state.report_data:
    d = st.session_state.report_data
    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>古典占星命盤完整資料</h1>", unsafe_allow_html=True)
    
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(f"<div class='summary-card'><div class='summary-title'>太陽星座</div><div class='summary-value'>{d['sun']}</div></div>", unsafe_allow_html=True)
    with sc2:
        st.markdown(f"<div class='summary-card'><div class='summary-title'>月亮星座</div><div class='summary-value'>{d['moon']}</div></div>", unsafe_allow_html=True)
    with sc3:
        st.markdown(f"<div class='summary-card'><div class='summary-title'>上升星座</div><div class='summary-value'>{d['asc']}</div></div>", unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(['宮位與行星分佈', '行星相位表', '法達星限與小限'])
    
    with t1:
        st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
        st.subheader("行星分佈表")
        df_p = pd.DataFrame(d['planets'])
        df_p_disp = df_p[['name', 'sign', 'degree_str', 'house']].copy()
        df_p_disp.columns = ['行星', '星座', '度數', '宮位位址']
        st.table(df_p_disp)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
        st.subheader("十二宮位表")
        df_h = pd.DataFrame(d['houses'])
        df_h_disp = df_h[['id_str', 'sign', 'ruler']].copy()
        df_h_disp.columns = ['宮位名稱', '對應星座', '宮位主星']
        st.table(df_h_disp)
        st.markdown("</div>", unsafe_allow_html=True)

    with t2:
        st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
        st.subheader("行星相位表")
        if d['aspects']:
            df_a = pd.DataFrame(d['aspects'])
            df_a.columns = ['行星 1', '行星 2', '相位類型', '誤差']
            st.dataframe(df_a, use_container_width=True)
        else:
            st.write("目前無顯著相位。")
        st.markdown("</div>", unsafe_allow_html=True)

    with t3:
        st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
        st.subheader("推運資訊摘要")
        pi = d['prof_info']
        st.write(f"當前年齡：{pi.get('age')} 歲")
        st.write(f"小限走到：{pi.get('prof_sign')} (第 {pi.get('prof_house_num')} 宮)")
        st.write(f"年度主星：{pi.get('lord_of_year')}")
        st.markdown("---")
        act = d['f_data']['active']
        st.write(f"法達當前大運：{logic.TRANS_PLANETS.get(act['major'], act['major'])}")
        st.write(f"法達當前小運：{logic.TRANS_PLANETS.get(act['minor'], act['minor'])}")
        st.write(f"下次換運：{act['end'].strftime('%Y/%m/%d')}")
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

else:
    st.markdown("<br><br><div style='text-align: center;'>", unsafe_allow_html=True)
    st.markdown("<h1 style='font-size: 2.5rem;'>古典占星命盤簡易排盤程式</h1>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top: 50px;'>請於側邊欄輸入出生日期與時間以開始分析</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
