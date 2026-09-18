#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
forum_db.py - Classical Astrology phpBB Mini Forum Database Layer
SQLite-backed persistence for categories, topics, posts, and member statistics.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "forum_astro.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化 SQLite 資料表結構與預設種子案例"""
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. 版塊分類表
    cur.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        icon TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0
    )
    """)

    # 2. 主題表
    cur.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL REFERENCES categories(id),
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        author_role TEXT DEFAULT '🌱 易壇道友',
        author_avatar TEXT DEFAULT '👤',
        chart_type TEXT DEFAULT 'general',
        chart_data_md TEXT DEFAULT '',
        views INTEGER DEFAULT 0,
        is_pinned INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # 3. 貼文樓層表
    cur.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
        floor_number INTEGER NOT NULL,
        author TEXT NOT NULL,
        author_role TEXT DEFAULT '🌱 易壇道友',
        author_avatar TEXT DEFAULT '👤',
        content TEXT NOT NULL,
        likes INTEGER DEFAULT 0,
        is_ai INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()

    # 檢查是否需要注入初始版塊
    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        seed_categories(cur)
        conn.commit()
        seed_topics_and_posts(cur)
        conn.commit()

    conn.close()


def seed_categories(cur):
    default_categories = [
        (
            "horary-cases",
            "🎯 卜卦問事實戰版",
            "依 William Lilly 1647 原典體系探討求職、感情、失物與事態吉凶成否。",
            "🎯",
            1
        ),
        (
            "natal-predictive",
            "🏛️ 本命與推運研討版",
            "法達星限 (Firdaria)、年度小限 (Profections)、希臘黃道釋放 (ZR) 與太陽弧生活實戰印證。",
            "🏛️",
            2
        ),
        (
            "classical-texts",
            "📜 古典典籍與技法考據",
            "托勒密《四書》、阿布馬謝、多羅修斯 (Dorotheus) 原典古籍義理考證。",
            "📜",
            3
        ),
        (
            "astrology-lounge",
            "☕ 易友茶水間與解盤閒聊",
            "生活心得分享、疑難雜症破局心得、新手入門請教與現實反饋。",
            "☕",
            4
        ),
    ]
    cur.executemany(
        "INSERT INTO categories (slug, title, description, icon, sort_order) VALUES (?, ?, ?, ?, ?)",
        default_categories
    )


def seed_topics_and_posts(cur):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 案例 1：卜卦問事
    cur.execute("""
    INSERT INTO topics (category_id, title, author, author_role, author_avatar, chart_type, chart_data_md, views, is_pinned, created_at, updated_at)
    VALUES (1, '【卜卦求助】下週的新創公司主管面試有機會順利錄取嗎？', '星空漫步者', '📜 資深占星師', '🔭', 'horary', '上升天蠍座 14°20''，10宮主太陽在處女座 25°，1宮主火星在巨蟹座 18°落陷。月亮在天蠍座 22°落陷，正準備與太陽成六分相。', 128, 1, ?, ?)
    """, (now, now))
    topic1_id = cur.lastrowid

    cur.execute("""
    INSERT INTO posts (topic_id, floor_number, author, author_role, author_avatar, content, likes, is_ai, created_at)
    VALUES (?, 1, '星空漫步者', '📜 資深占星師', '🔭', ?, 5, 0, ?)
    """, (
        topic1_id,
        "各位易友大家好！\n\n下週二要去面試一家心儀已久的 AI 新創公司主管職缺，想請教大家這盤的成事跡象與阻礙。\n\n**【占卜背景與盤體數據】**：\n- 上升度數：天蠍座 14°20'\n- 1宮主（我）：火星在巨蟹座 18°（落陷在第 9 宮）\n- 10宮主（職位/主管）：太陽在處女座 25°（第 11 宮）\n- 月亮（情勢進展）：天蠍座 22°（落陷在第 1 宮，入相位六分太陽處女座 25°）\n\n我自己看火星落陷感覺心態很虛，但月亮即將六分 10 宮主太陽，這是否構成光線傳遞（Translation of Light）？求高人指點！",
        now
    ))

    cur.execute("""
    INSERT INTO posts (topic_id, floor_number, author, author_role, author_avatar, content, likes, is_ai, created_at)
    VALUES (?, 2, '🤖 AI 駐站古典掌門 · William Lilly 傳承', '🤖 駐站大宗師', '⚡', ?, 12, 1, ?)
    """, (
        topic1_id,
        """### 🎯 掌門一針見血結論
- **能否成事**：【成事機率約 75%～80%，可以順利拿到 Offer，但過程會有薪資或權限上的討價還價】。
- **核心劇本**：你心裡沒底、自覺準備不足（火星落陷），但第三方獵頭或貴人朋友強力推薦，牽線搭橋促成主管點頭（月亮光線傳遞）。
- **預計應期**：約在 **3 天或 3 週** 左右（月亮距離太陽 3 度之差）會有確切錄取通知！

---

### 🩺 這盤能算嗎？（William Lilly 盤體檢意白話說）
1. **上升度數**：天蠍座 14°20'，介於 3°～27° 之間，盤體完全成熟且有效（Radical）。
2. **月亮狀態**：月亮在天蠍座落陷，說明你當前內心焦慮、得失心極重，生怕搞砸；但月亮並未空亡，且正緊密入相位吉相，事態仍在向前推進！

---

### ⚖️ 事情會怎麼演變？（星體角色與成事劇本）
- **代表你的是火星（巨蟹 18°）**：掉在水象落陷宮位，你在面試官面前可能表現得過於謙虛或缺乏攻擊性，需要注意別把自己的身價喊低了。
- **代表這份工作/主管的是太陽（處女 25°）**：處女座具備極高的挑剔度與專業細節要求，對方非常看重你的實務落地能力。
- **關鍵成事紅娘——月亮（天蠍 22°）**：月亮在第 1 宮主動接引火星的氣息，即將以 3° 之差與 10 宮主太陽形成吉利的六分相！這在 William Lilly 原典中是標準的「光線傳遞（Translation of Light）」，必有第三方推薦人或獵頭在背後為你美言撮合！

---

### 💡 掌門給你的生活實戰建議
1. **收起自卑，展現結構化邏輯**：面試時不要主動暴露缺點，多用處女座喜歡的數字與專案成果說話。
2. **緊密聯繫引薦人**：面試結束後立即向推薦你的朋友或獵頭回饋細節，讓他幫你在高層面前敲定薪資！""",
        now
    ))

    # 案例 2：本命推運研討
    cur.execute("""
    INSERT INTO topics (category_id, title, author, author_role, author_avatar, chart_type, chart_data_md, views, is_pinned, created_at, updated_at)
    VALUES (2, '【本命推運研討】32歲轉職外商：法達水星大限碰上小限 10 宮獅子座的威力', '星圖旅人', '🌱 易壇道友', '🧭', 'natal', '命度天蠍 18°，白天生人。法達星限正走水星大限/月亮小限。年度小限實歲 32 歲行至第 10 宮獅子座，太陽在雙魚座第 5 宮拱木星巨蟹座。', 95, 0, ?, ?)
    """, (now, now))
    topic2_id = cur.lastrowid

    cur.execute("""
    INSERT INTO posts (topic_id, floor_number, author, author_role, author_avatar, content, likes, is_ai, created_at)
    VALUES (?, 1, '星圖旅人', '🌱 易壇道友', '🧭', ?, 3, 0, ?)
    """, (
        topic2_id,
        "易友們好！\n\n今年剛滿 32 歲，原本在傳產當小主管，近期突然收到歐美外商的總監級職缺邀約。\n比對了一下推運：\n1. 法達星限：目前正值水星大限 / 月亮小限\n2. 年度小限：32 歲走到第 10 宮（獅子座），年度主星為太陽\n3. 本命太陽在雙魚座拱入廟巨蟹座木星\n\n這是否意味著今年是職業生涯的重要破局年？想聽聽各位與掌門的見解！",
        now
    ))


def get_forum_stats() -> Dict[str, Any]:
    """取得論壇全局統計數據"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM topics")
    total_topics = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM posts")
    total_posts = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT author) FROM posts")
    total_members = cur.fetchone()[0] + 5  # 基礎社群權重

    conn.close()
    return {
        "total_topics": total_topics,
        "total_posts": total_posts,
        "total_members": total_members,
        "online_users": 18,
        "ai_bot_status": "🟢 在線中 (Groq LPU)"
    }


def get_categories_with_stats() -> List[Dict[str, Any]]:
    """取得所有版塊及其統計與最新發表"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT c.id, c.slug, c.title, c.description, c.icon, c.sort_order,
           COUNT(DISTINCT t.id) as topic_count,
           COUNT(p.id) as post_count,
           MAX(t.updated_at) as last_updated
    FROM categories c
    LEFT JOIN topics t ON c.id = t.category_id
    LEFT JOIN posts p ON t.id = p.topic_id
    GROUP BY c.id
    ORDER BY c.sort_order ASC
    """)
    rows = cur.fetchall()

    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "slug": r["slug"],
            "title": r["title"],
            "description": r["description"],
            "icon": r["icon"],
            "topic_count": r["topic_count"],
            "post_count": r["post_count"],
            "last_updated": r["last_updated"] or "暫無發文"
        })

    conn.close()
    return results


def get_topics_by_category(category_id: Optional[int] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """取得特定版塊之主題清單（支援關鍵字搜尋）"""
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
    SELECT t.id, t.category_id, t.title, t.author, t.author_role, t.author_avatar,
           t.chart_type, t.views, t.is_pinned, t.created_at, t.updated_at,
           c.title as category_title, c.icon as category_icon,
           COUNT(p.id) as reply_count,
           MAX(p.created_at) as last_reply_time,
           (SELECT author FROM posts WHERE topic_id = t.id ORDER BY floor_number DESC LIMIT 1) as last_reply_author
    FROM topics t
    JOIN categories c ON t.category_id = c.id
    LEFT JOIN posts p ON t.id = p.topic_id
    """
    params = []
    where_clauses = []

    if category_id:
        where_clauses.append("t.category_id = ?")
        params.append(category_id)

    if search and search.strip():
        where_clauses.append("(t.title LIKE ? OR t.chart_data_md LIKE ?)")
        s = f"%{search.strip()}%"
        params.extend([s, s])

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " GROUP BY t.id ORDER BY t.is_pinned DESC, t.updated_at DESC"

    cur.execute(query, params)
    rows = cur.fetchall()

    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "category_id": r["category_id"],
            "category_title": r["category_title"],
            "category_icon": r["category_icon"],
            "title": r["title"],
            "author": r["author"],
            "author_role": r["author_role"],
            "author_avatar": r["author_avatar"],
            "chart_type": r["chart_type"],
            "views": r["views"],
            "is_pinned": bool(r["is_pinned"]),
            "reply_count": max(0, r["reply_count"] - 1),  # 排除 1 樓主貼
            "created_at": r["created_at"],
            "last_reply_time": r["last_reply_time"] or r["created_at"],
            "last_reply_author": r["last_reply_author"] or r["author"]
        })

    conn.close()
    return results


def get_topic_detail(topic_id: int) -> Optional[Dict[str, Any]]:
    """取得主題詳情與所有樓層留言"""
    conn = get_db_connection()
    cur = conn.cursor()

    # 閱讀數 +1
    cur.execute("UPDATE topics SET views = views + 1 WHERE id = ?", (topic_id,))
    conn.commit()

    cur.execute("""
    SELECT t.id, t.category_id, t.title, t.author, t.author_role, t.author_avatar,
           t.chart_type, t.chart_data_md, t.views, t.is_pinned, t.created_at,
           c.title as category_title, c.icon as category_icon
    FROM topics t
    JOIN categories c ON t.category_id = c.id
    WHERE t.id = ?
    """, (topic_id,))
    topic_row = cur.fetchone()

    if not topic_row:
        conn.close()
        return None

    cur.execute("""
    SELECT id, floor_number, author, author_role, author_avatar, content, likes, is_ai, created_at
    FROM posts
    WHERE topic_id = ?
    ORDER BY floor_number ASC
    """, (topic_id,))
    posts_rows = cur.fetchall()

    posts = []
    for p in posts_rows:
        posts.append({
            "id": p["id"],
            "floor_number": p["floor_number"],
            "author": p["author"],
            "author_role": p["author_role"],
            "author_avatar": p["author_avatar"],
            "content": p["content"],
            "likes": p["likes"],
            "is_ai": bool(p["is_ai"]),
            "created_at": p["created_at"]
        })

    result = {
        "id": topic_row["id"],
        "category_id": topic_row["category_id"],
        "category_title": topic_row["category_title"],
        "category_icon": topic_row["category_icon"],
        "title": topic_row["title"],
        "author": topic_row["author"],
        "author_role": topic_row["author_role"],
        "author_avatar": topic_row["author_avatar"],
        "chart_type": topic_row["chart_type"],
        "chart_data_md": topic_row["chart_data_md"],
        "views": topic_row["views"],
        "is_pinned": bool(topic_row["is_pinned"]),
        "created_at": topic_row["created_at"],
        "posts": posts
    }
    conn.close()
    return result


def add_topic(category_id: int, title: str, author: str, author_role: str, content: str,
              chart_type: str = "general", chart_data_md: str = "") -> int:
    """建立新主題並新增第 1 樓內容"""
    conn = get_db_connection()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("""
    INSERT INTO topics (category_id, title, author, author_role, author_avatar, chart_type, chart_data_md, views, is_pinned, created_at, updated_at)
    VALUES (?, ?, ?, ?, '👤', ?, ?, 1, 0, ?, ?)
    """, (category_id, title, author, author_role, chart_type, chart_data_md, now, now))
    topic_id = cur.lastrowid

    # 建立 1 樓
    full_content = content
    if chart_data_md and chart_data_md.strip() and chart_data_md.strip() not in content:
        full_content = f"{content}\n\n---\n### 📊 命盤數據\n\n{chart_data_md}"

    cur.execute("""
    INSERT INTO posts (topic_id, floor_number, author, author_role, author_avatar, content, likes, is_ai, created_at)
    VALUES (?, 1, ?, ?, '👤', ?, 0, 0, ?)
    """, (topic_id, author, author_role, full_content, now))

    conn.commit()
    conn.close()
    return topic_id


def add_post(topic_id: int, author: str, author_role: str, content: str, is_ai: bool = False, avatar: str = "👤") -> int:
    """為主題新增回覆樓層"""
    conn = get_db_connection()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 取得當前最大樓層
    cur.execute("SELECT MAX(floor_number) FROM posts WHERE topic_id = ?", (topic_id,))
    max_floor = cur.fetchone()[0] or 0
    new_floor = max_floor + 1

    cur.execute("""
    INSERT INTO posts (topic_id, floor_number, author, author_role, author_avatar, content, likes, is_ai, created_at)
    VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
    """, (topic_id, new_floor, author, author_role, avatar, content, 1 if is_ai else 0, now))
    post_id = cur.lastrowid

    # 更新主題更新時間
    cur.execute("UPDATE topics SET updated_at = ? WHERE id = ?", (now, topic_id))

    conn.commit()
    conn.close()
    return post_id


def like_post(post_id: int) -> int:
    """為貼文點讚"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post_id,))
    conn.commit()
    cur.execute("SELECT likes FROM posts WHERE id = ?", (post_id,))
    likes = cur.fetchone()[0]
    conn.close()
    return likes


if __name__ == "__main__":
    init_db()
    print("[+] forum_astro.db initialized with seed categories and topics successfully!")
