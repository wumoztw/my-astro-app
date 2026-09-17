"""
GitHub Forum Exporter Module for my-astro-app
---------------------------------------------
Generates structured Markdown representations of astrological charts
and one-click URL-encoded GitHub Discussions Deep-Links.
"""

import urllib.parse
from datetime import datetime

REPO_URL = "https://github.com/wumoztw/my-astro-app"

def generate_discussion_payload(
    chart_type: str,
    question_or_theme: str,
    report_md: str,
    extra_notes: str = ""
) -> dict:
    """
    將當前盤面數據 (report_md) 加上結構化 YAML Frontmatter 與格式化引導，
    輸出標準標題、Markdown 內文與 GitHub Discussions 免費 Deep-Link。
    """
    clean_title = question_or_theme.strip() if question_or_theme else ("卜卦案例求助" if chart_type == "horary" else "古典本命推運研討")
    prefix = "[卜卦求助]" if chart_type == "horary" else "[本命推運]"
    title = f"{prefix} {clean_title}"

    frontmatter = f"""---
chart_type: "{chart_type}"
title: "{clean_title}"
generated_at: "{datetime.utcnow().isoformat()}Z"
source: "easyastrology.streamlit.app"
---
"""

    notes_section = f"\n### 📖 案主補充說明與提問背景\n{extra_notes}\n" if extra_notes.strip() else ""

    body_md = f"""{frontmatter}
{notes_section}
### 🪐 命盤完整數據與分析
{report_md}

---
*💡 此案例由 [easyastrology.streamlit.app](https://easyastrology.streamlit.app/) 排盤系統一鍵生成。歡迎各位易友與 AI 駐站古典掌門共同研討！*
"""

    encoded_title = urllib.parse.quote(title)
    encoded_body = urllib.parse.quote(body_md)
    deep_link = f"{REPO_URL}/discussions/new?title={encoded_title}&body={encoded_body}"

    return {
        "title": title,
        "markdown_body": body_md,
        "deep_link": deep_link,
        "repo_discussions_url": f"{REPO_URL}/discussions"
    }
