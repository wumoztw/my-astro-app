"""
GitHub Forum Exporter Module for my-astro-app
---------------------------------------------
Generates URL-safe compact representations of astrological charts
to prevent HTTP 414 'URL too long' errors, while providing full
Markdown payloads for easy clipboard copying.
"""

import urllib.parse
from datetime import datetime

REPO_URL = "https://github.com/wumoztw/my-astro-app"

def generate_discussion_payload(
    chart_type: str,
    question_or_theme: str,
    report_data: dict = None,
    report_md: str = "",
    extra_notes: str = ""
) -> dict:
    """
    產生 URL 安全長度 (< 2000 字元) 的 Deep-Link，同時提供完整報告 Markdown
    """
    clean_title = question_or_theme.strip() if question_or_theme else ("卜卦案例求助" if chart_type == "horary" else "古典本命推運研討")
    prefix = "[卜卦求助]" if chart_type == "horary" else "[本命推運]"
    title = f"{prefix} {clean_title}"
    category_slug = "q-a" if chart_type == "horary" else "general"

    # 1. 提煉緊湊型盤體數據 (Compact Payload) 供 URL 帶入
    compact_lines = [
        "---",
        f'chart_type: "{chart_type}"',
        f'title: "{clean_title}"',
        f'generated: "{datetime.utcnow().strftime("%Y-%m-%d %H:%M")} UTC"',
        "---",
        "",
        f"### ❓ 事項：{clean_title}"
    ]

    if extra_notes.strip():
        # 限制備註字數避免撐爆網址
        short_notes = extra_notes.strip()[:150]
        compact_lines.append(f"\n> **案主補充**：{short_notes}\n")

    if report_data:
        asc_str = report_data.get('asc', '-')
        planets = report_data.get('planets', [])
        
        compact_lines.append("### 🪐 核心盤體數據 (WSH 整宮制)")
        compact_lines.append(f"- **命度 (ASC)**：`{asc_str}`")
        compact_lines.append("")
        compact_lines.append("| 星體 | 位置 | 宮位 | 狀態 |")
        compact_lines.append("| :--- | :--- | :---: | :--- |")

        # 優先篩選古典七政 (7 Classical Planets)
        traditional_names = ['太陽', '月亮', '水星', '金星', '火星', '木星', '土星']
        for p in planets:
            p_name = p.get('name', '')
            if any(t in p_name for t in traditional_names):
                sym = p.get('symbol', '')
                sign = p.get('sign', '')
                deg = p.get('degree_str', '')
                house = p.get('house', '')
                retro = "Rx" if p.get('retro') or p.get('is_retrograde') else "-"
                compact_lines.append(f"| {p_name} {sym} | {sign} {deg} | {house} | {retro} |")
    else:
        # 無結構化資料時，取精簡文字摘要
        compact_lines.append("\n### 🪐 盤體摘要")
        compact_lines.append(report_md[:300] if report_md else "（無詳細星盤數據）")

    compact_lines.append("\n*💡 來自 easyastrology.streamlit.app。請 AI 駐站古典掌門 (William Lilly 體系) 進行體檢。*")
    compact_body = "\n".join(compact_lines)

    # 2. 完整報告 (Full Markdown) 供使用者複製或在 expander 展開
    full_markdown_body = f"""---
chart_type: "{chart_type}"
title: "{clean_title}"
generated_at: "{datetime.utcnow().isoformat()}Z"
---

### ❓ 事項說明
**{clean_title}**

{f'### 📖 補充備註：{extra_notes}' if extra_notes.strip() else ''}

### 🪐 命盤完整數據與報告
{report_md}

---
*💡 此案例由 easyastrology.streamlit.app 排盤系統生成。*
"""

    # 3. 進行 URL 編碼，確保 URL 長度安全
    encoded_title = urllib.parse.quote(title)
    encoded_body = urllib.parse.quote(compact_body)
    deep_link = f"{REPO_URL}/discussions/new?category={category_slug}&title={encoded_title}&body={encoded_body}"

    return {
        "title": title,
        "compact_body": compact_body,
        "full_markdown_body": full_markdown_body,
        "deep_link": deep_link,
        "repo_discussions_url": f"{REPO_URL}/discussions"
    }
