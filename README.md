# Classical Astrology System (古典占星排盤系統)

本系統基於 Python 的 `flatlib` 與 `Streamlit` 開發，提供古典占星的基本排盤與分析功能。

## 功能特點
1. **行星計算**：計算七大古典行星的精確星座與度數。
2. **宮位系統**：實作「等宮制 (Equal House System)」。
3. **古典相位**：找出主要相位（0°, 60°, 90°, 120°, 180°），並使用古典占星標準的容許度（Moiety-based calculation）。
4. **小限法 (Annual Profections)**：根據當前年份計算年齡、小限宮位與年主星。

## 系統環境說明 (Linux Mint / Python 3.12)
由於 Python 3.12 移除了部分舊有的 Unicode API，導致官方版的 `pyswisseph` 無法直接安裝。本系統已手動編譯並安裝了相容於 Python 3.12 的版本到虛擬環境 `venv` 中。

## 如何執行
1. **進入專案目錄**：
   ```bash
   cd ~/桌面/my-astro-app
   ```

2. **啟動 Streamlit 應用程式**：
   使用預先配置好的虛擬環境執行：
   ```bash
   ./venv/bin/streamlit run app.py
   ```

3. **操作步驟**：
   - 在側邊欄輸入出生日期、時間、地點（如 "Taipei"）與 UTC 時區偏移。
   - 點擊「生成命盤報告」按鈕。

## 檔案說明
- `app.py`: Streamlit 網頁介面。
- `logic.py`: 核心占星運算邏輯。
- `requirements.txt`: 專案依賴。
- `venv/`: 包含 Python 3.12 相容版占星庫的虛擬環境。

---
*Note: 地名搜尋功能需連線至 Nominatim (OpenStreetMap) 服務。*