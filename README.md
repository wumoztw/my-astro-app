# Classical Astrology System (古典占星排盤系統)

這是一個專業的**古典占星 (Classical Astrology)** 排盤與分析系統。本系統基於 Python 的 `flatlib` 與 `Streamlit` 開發，專注於中世紀與希臘時期的占星理論，提供精確的星盤計算與深度分析功能。

---

## 核心技術框架
- **前端介面**：使用 [Streamlit](https://streamlit.io/) 構建的高品質 Web 介面，具有簡約的黑白美學與響應式佈局。
- **計算引擎**：整合了 `flatlib` 與瑞士星曆表 (`swisseph`)，確保星體位置與度數的科學精確度。
- **資料儲存**：包含 `ephem/` 目錄下的星曆表檔案，提供精確的行星位置計算。

---

## 主要功能模組解析

### 1. 行星狀態與本質力量分析
程式會根據行星所在的星座、度數以及晝夜區分，計算以下指標：
- **本質力量 (Essential Dignities)**：依照埃及界 (Egyptian Terms) 與迦勒底面 (Chaldean Faces) 的傳統規則，計算行星的廟 (Domicile)、旺 (Exaltation)、三分 (Triplicity)、界 (Term)、面 (Face) 的得分。
- **後天狀態 (Accidental Dignities)**：分析行星的宮位強度、日心 (Cazimi)/燃燒 (Combust) 狀態以及是否逆行。

### 2. 相位與接納關係
- **古典容許度**：基於行星自身的「光芒範圍 (Moiety)」計算合相、六分、四分、三分、對分相位。
- **接納 (Reception)**：自動判斷行星之間是否存在「接納」或「互容 (Mutual Reception)」關係。

### 3. 特殊點位與恆星
- **希臘點 (Lots/Parts)**：計算「幸運點 (Fortune)」與「精神點 (Spirit)」，並自動適應晝夜出生。
- **恆星合相 (Fixed Stars)**：偵測行星與重要恆星（如 Regulus、Spica）的合相。

### 4. 宮位與推運系統
- **等宮制 (Equal House System)**：以 ASC 為起點的宮位劃分。
- **推運利器**：實作了「小限法 (Annual Profections)」與「法達星限 (Firdaria)」，提供完整的年度與大運時間表。

---

## 獨特特色：AI 整合功能
程式內建了 **「深度思考型 AI 古典占星大師解析指引」**，會自動生成優化過的 Prompt，讓使用者能將排盤資料交給 AI 進行專業的邏輯化解讀。

---

## 系統環境說明 (Linux Mint / Python 3.12)
由於 Python 3.12 兼容性問題，本系統已手動編譯並安裝了相容版 `pyswisseph` 到虛擬環境 `venv` 中。

## 如何執行
1. **進入專案目錄**：
   ```bash
   cd ~/桌面/my-astro-app
   ```
2. **啟動應用程式**：
   ```bash
   ./venv/bin/streamlit run app.py
   ```

## 檔案說明
- `app.py`: Streamlit 網頁介面。
- `logic.py`: 核心占星運算邏輯。
- `dignities_logic.py`, `aspects_logic.py`, `lots_logic.py`, `time_lords_logic.py`: 模組化運算邏輯。
- `requirements.txt`: 專案依賴。

---
*Note: 地名搜尋功能需連線至 Nominatim (OpenStreetMap) 服務。*