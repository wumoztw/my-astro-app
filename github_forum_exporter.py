"""
GitHub Forum Exporter Module for my-astro-app
---------------------------------------------
Generates standardized Markdown representations of astrological charts
and supports both manual 2-step copy-publishing and direct GraphQL API publishing.
"""

import urllib.parse
import requests
from datetime import datetime

REPO_OWNER = "wumoztw"
REPO_NAME = "my-astro-app"
REPO_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}"

def generate_discussion_payload(
    chart_type: str,
    question_or_theme: str,
    report_data: dict = None,
    report_md: str = "",
    extra_notes: str = ""
) -> dict:
    """
    組裝標準格式的命盤 Markdown 發布內容
    """
    clean_title = question_or_theme.strip() if question_or_theme else ("卜卦案例求助" if chart_type == "horary" else "古典本命推運研討")
    prefix = "[卜卦求助]" if chart_type == "horary" else "[本命推運]"
    title = f"{prefix} {clean_title}"
    category_slug = "q-a" if chart_type == "horary" else "general"

    # 1. 提煉緊湊型盤體數據 (Compact Payload)
    compact_lines = [
        "---",
        f'chart_type: "{chart_type}"',
        f'title: "{clean_title}"',
        f'datetime: "{datetime.utcnow().strftime("%Y-%m-%d %H:%M")} UTC"',
        "---",
        "",
        f"### ❓ 事項：{clean_title}"
    ]

    if extra_notes.strip():
        compact_lines.append(f"\n> **案主補充說明**：{extra_notes.strip()}\n")

    if report_data:
        asc_str = report_data.get('asc', '-')
        planets = report_data.get('planets', [])
        
        compact_lines.append("### 🪐 核心盤體數據 (WSH 整宮制)")
        compact_lines.append(f"- **命度 (ASC)**：`{asc_str}`")
        compact_lines.append("")
        compact_lines.append("| 星體 | 位置 | 宮位 | 狀態 |")
        compact_lines.append("| :--- | :--- | :---: | :--- |")

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
        compact_lines.append("\n### 🪐 盤體摘要")
        compact_lines.append(report_md[:300] if report_md else "（無詳細星盤數據）")

    compact_lines.append("\n*💡 來自 easyastrology.streamlit.app。請 AI 駐站古典掌門 (William Lilly 體系) 進行體檢。*")
    compact_body = "\n".join(compact_lines)

    # 2. 完整報告 (Full Markdown)
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

    return {
        "title": title,
        "category_slug": category_slug,
        "compact_body": compact_body,
        "full_markdown_body": full_markdown_body,
        "new_discussion_url": f"{REPO_URL}/discussions/new",
        "repo_discussions_url": f"{REPO_URL}/discussions"
    }


def publish_discussion_via_api(token: str, title: str, body: str, chart_type: str = "horary") -> dict:
    """透過 GitHub GraphQL API 直接發布 Discussion"""
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Content-Type": "application/json",
        "User-Agent": "my-astro-app"
    }
    
    # 1. 取得 Repo ID 與 Category IDs
    query = """
    query GetRepoAndCategories($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        id
        discussionCategories(first: 20) {
          nodes {
            id
            name
            slug
          }
        }
      }
    }
    """
    try:
        res = requests.post(url, headers=headers, json={"query": query, "variables": {"owner": REPO_OWNER, "name": REPO_NAME}}, timeout=15)
        if res.status_code != 200:
            return {"success": False, "error": f"HTTP {res.status_code}: {res.text}"}
        
        data = res.json()
        if "errors" in data:
            return {"success": False, "error": str(data["errors"])}
            
        repo_data = data.get("data", {}).get("repository", {})
        repo_id = repo_data.get("id")
        categories = repo_data.get("discussionCategories", {}).get("nodes", [])
        
        target_slug = "q-a" if chart_type == "horary" else "general"
        category_id = None
        for c in categories:
            if c.get("slug") == target_slug:
                category_id = c.get("id")
                break
                
        if not category_id and categories:
            category_id = categories[0].get("id")
            
        if not repo_id or not category_id:
            return {"success": False, "error": "無法獲取 Repository 或 Category ID"}
            
        mutation = """
        mutation CreateDiscussion($repositoryId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
          createDiscussion(input: {repositoryId: $repositoryId, categoryId: $categoryId, title: $title, body: $body}) {
            discussion {
              id
              url
              number
            }
          }
        }
        """
        res = requests.post(url, headers=headers, json={
            "query": mutation,
            "variables": {
                "repositoryId": repo_id,
                "categoryId": category_id,
                "title": title,
                "body": body
            }
        }, timeout=15)
        
        m_data = res.json()
        if "errors" in m_data:
            return {"success": False, "error": str(m_data["errors"])}
            
        disc = m_data.get("data", {}).get("createDiscussion", {}).get("discussion", {})
        return {"success": True, "url": disc.get("url"), "number": disc.get("number")}
    except Exception as e:
        return {"success": False, "error": str(e)}
