#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
flet_forum.py - Classical Astrology phpBB-Style Mini Forum
Built with Flet 1.0 (Python + Flutter), SQLite persistence, and Groq AI Bot.
Supports Web mode (http://localhost:8555) and native Desktop window mode.
"""

import sys
import os
import argparse
from datetime import datetime
import flet as ft

# 導入自訂資料庫與 AI 模組
from forum_db import (
    init_db,
    get_forum_stats,
    get_categories_with_stats,
    get_topics_by_category,
    get_topic_detail,
    add_topic,
    add_post,
    like_post
)
from forum_ai_service import generate_ai_reply_for_topic

# 初始化資料庫
init_db()

def main(page: ft.Page):
    page.title = "🏛️ 古典占星迷你論壇 (Classical Astrology Board)"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.AMBER)

    # 狀態管理
    current_view = {"view": "index", "category_id": None, "topic_id": None}

    # 頂部導航通知條
    def show_snackbar(text: str, color=ft.Colors.GREEN_400):
        page.overlay.append(
            ft.SnackBar(
                content=ft.Text(text, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
                bgcolor=color,
                open=True,
            )
        )
        page.update()

    # 主容器（居中最大寬度 1150px）
    content_area = ft.Container(expand=True, padding=ft.Padding.symmetric(horizontal=20, vertical=10))

    # --- 頂部 Header & 統計導航列 ---
    def build_header():
        stats = get_forum_stats()
        return ft.Container(
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                spacing=12,
                                controls=[
                                    ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.AMBER_400, size=32),
                                    ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text("🏛️ 古典占星迷你論壇", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_100),
                                            ft.Text("William Lilly 1647 原典體系 · 占星研討中心", size=12, color=ft.Colors.GREY_400),
                                        ]
                                    )
                                ]
                            ),
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.FilledButton(
                                        "🏠 回到首頁",
                                        icon=ft.Icons.HOME,
                                        on_click=lambda _: navigate_to("index"),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                                            color=ft.Colors.WHITE
                                        )
                                    ),
                                    ft.FilledButton(
                                        "✍️ 發布新主題",
                                        icon=ft.Icons.ADD_COMMENT,
                                        on_click=lambda _: open_new_topic_dialog(),
                                        style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.REFRESH,
                                        icon_color=ft.Colors.AMBER_300,
                                        tooltip="重新整理資料",
                                        on_click=lambda _: (refresh_current_view(), show_snackbar("🔄 已重新整理最新資料！", ft.Colors.BLUE_GREY_700))
                                    ),
                                ]
                            )
                        ]
                    ),
                    # phpBB 經典狀態統計橫條
                    ft.Container(
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Row(
                                    spacing=16,
                                    controls=[
                                        ft.Text("🟢 AI 駐站古典掌門: 正在線上", size=12, color=ft.Colors.GREEN_400, weight=ft.FontWeight.W_600),
                                        ft.Text(f"📊 總主題: {stats['total_topics']} 篇", size=12, color=ft.Colors.GREY_300),
                                        ft.Text(f"💬 總討論: {stats['total_posts']} 則", size=12, color=ft.Colors.GREY_300),
                                        ft.Text(f"👥 線上朋友: {stats['online_users']} 人", size=12, color=ft.Colors.GREY_300),
                                    ]
                                ),
                                ft.Text("⚡ Groq LPU 毫秒級推運運算核心", size=11, color=ft.Colors.AMBER_300)
                            ]
                        ),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                        padding=ft.Padding.symmetric(horizontal=14, vertical=6),
                        border_radius=6,
                        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
                    )
                ]
            ),
            padding=ft.Padding.symmetric(horizontal=24, vertical=12),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT))
        )

    # --- 1. 首頁視圖 (Board Index) ---
    def render_board_index():
        categories = get_categories_with_stats()
        cat_cards = []

        for cat in categories:
            c_id = cat["id"]
            cat_cards.append(
                ft.Container(
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            # 左側：圖示與版塊資訊
                            ft.Row(
                                spacing=16,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                                controls=[
                                    ft.Container(
                                        content=ft.Text(cat["icon"], size=30),
                                        width=52,
                                        height=52,
                                        alignment=ft.Alignment.CENTER,
                                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                                        border_radius=26,
                                        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
                                    ),
                                    ft.Column(
                                        spacing=4,
                                        expand=True,
                                        controls=[
                                            ft.Text(cat["title"], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_200),
                                            ft.Text(cat["description"], size=12, color=ft.Colors.GREY_400),
                                        ]
                                    )
                                ]
                            ),
                            # 右側：統計與最新發表
                            ft.Row(
                                spacing=24,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Column(
                                        spacing=2,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            ft.Text(f"{cat['topic_count']} 主題", size=13, weight=ft.FontWeight.BOLD),
                                            ft.Text(f"{cat['post_count']} 篇發言", size=11, color=ft.Colors.GREY_400),
                                        ]
                                    ),
                                    ft.Container(
                                        content=ft.Column(
                                            spacing=2,
                                            controls=[
                                                ft.Text(f"🕒 最新: {cat['last_updated'][:16]}", size=11, color=ft.Colors.GREY_300),
                                                ft.Text("點擊進入版塊討論 ➔", size=11, color=ft.Colors.AMBER_400),
                                            ]
                                        ),
                                        width=180
                                    )
                                ]
                            )
                        ]
                    ),
                    padding=16,
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    ink=True,
                    on_click=lambda _, cid=c_id: navigate_to("topics", category_id=cid)
                )
            )

        # phpBB 經典底部版塊與榮譽階級條
        legend_row = ft.Container(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.Text("👥 社群階級標示:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400),
                            ft.Text("🤖 駐站大宗師", size=12, color=ft.Colors.PURPLE_300, weight=ft.FontWeight.BOLD),
                            ft.Text("👑 易壇宗師", size=12, color=ft.Colors.AMBER_300),
                            ft.Text("📜 資深占星師", size=12, color=ft.Colors.CYAN_300),
                            ft.Text("🌱 易壇道友", size=12, color=ft.Colors.GREEN_300),
                        ]
                    ),
                    ft.Text("📜 依循 William Lilly 1647 原典體系驗證", size=11, color=ft.Colors.GREY_500)
                ]
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=10),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border_radius=6,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
        )

        return ft.Column(
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("📌 古典占星研討版面總覽 (Categories)", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_100),
                        ft.Text("請選擇版塊瀏覽案例或發起請教", size=13, color=ft.Colors.GREY_400)
                    ]
                ),
                *cat_cards,
                ft.Divider(color=ft.Colors.OUTLINE_VARIANT),
                legend_row
            ]
        )

    # --- 2. 主題列表視圖 (Topic List) ---
    def render_topic_list(category_id: int):
        topics = get_topics_by_category(category_id)
        categories = get_categories_with_stats()
        cat_info = next((c for c in categories if c["id"] == category_id), {"title": "討論版塊", "icon": "📁"})

        rows = []
        for t in topics:
            tid = t["id"]
            badge_color = ft.Colors.RED_ACCENT_400 if t["is_pinned"] else (
                ft.Colors.CYAN_700 if t["chart_type"] == "horary" else ft.Colors.PURPLE_700
            )
            badge_text = "📌 置頂" if t["is_pinned"] else (
                "🎯 卜卦" if t["chart_type"] == "horary" else ("🏛️ 本命" if t["chart_type"] == "natal" else "📜 研討")
            )

            rows.append(
                ft.Container(
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            # 標題與發布者
                            ft.Row(
                                spacing=12,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                                controls=[
                                    ft.Container(
                                        content=ft.Text(badge_text, size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                                        bgcolor=badge_color,
                                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                        border_radius=4
                                    ),
                                    ft.Column(
                                        spacing=2,
                                        expand=True,
                                        controls=[
                                            ft.Text(t["title"], size=15, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                                            ft.Text(f"發起人: {t['author']} ({t['author_role']}) · 發布於 {t['created_at'][:16]}", size=11, color=ft.Colors.GREY_400)
                                        ]
                                    )
                                ]
                            ),
                            # 回覆數與最後發言
                            ft.Row(
                                spacing=24,
                                controls=[
                                    ft.Column(
                                        spacing=2,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            ft.Text(f"💬 {t['reply_count']}", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300),
                                            ft.Text(f"👁️ {t['views']}", size=11, color=ft.Colors.GREY_400)
                                        ]
                                    ),
                                    ft.Container(
                                        content=ft.Column(
                                            spacing=2,
                                            controls=[
                                                ft.Text(f"由 {t['last_reply_author']}", size=11, color=ft.Colors.GREY_300),
                                                ft.Text(f"🕒 {t['last_reply_time'][:16]}", size=10, color=ft.Colors.GREY_500)
                                            ]
                                        ),
                                        width=150
                                    )
                                ]
                            )
                        ]
                    ),
                    padding=14,
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    border_radius=6,
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    ink=True,
                    on_click=lambda _, target_id=tid: navigate_to("thread", topic_id=target_id)
                )
            )

        return ft.Column(
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                # 麵包屑導航
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.TextButton(
                                    "🏠 回到首頁",
                                    icon=ft.Icons.HOME,
                                    style=ft.ButtonStyle(color=ft.Colors.AMBER_300),
                                    on_click=lambda _: navigate_to("index")
                                ),
                                ft.Text(">", color=ft.Colors.GREY_500),
                                ft.Text(f"{cat_info['icon']} {cat_info['title']}", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_200)
                            ]
                        ),
                        ft.FilledButton(
                            "✍️ 在此版發布新帖",
                            icon=ft.Icons.POST_ADD,
                            on_click=lambda _: open_new_topic_dialog(default_category_id=category_id),
                            style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE)
                        )
                    ]
                ),
                ft.Divider(color=ft.Colors.OUTLINE_VARIANT),
                *(rows if rows else [ft.Container(content=ft.Text("本版塊暫無主題，快來發布第一篇案例吧！", color=ft.Colors.GREY_400), padding=30)])
            ]
        )

    # --- 3. 討論串主題內頁視圖 (Thread View - phpBB 經典雙欄) ---
    def render_thread_view(topic_id: int):
        topic = get_topic_detail(topic_id)
        if not topic:
            return ft.Text("找不到該主題。")

        posts_cards = []
        for p in topic["posts"]:
            pid = p["id"]
            floor_text = f"#{p['floor_number']} 樓主" if p["floor_number"] == 1 else (
                f"#{p['floor_number']} 沙發" if p["floor_number"] == 2 else f"#{p['floor_number']} 樓"
            )
            is_ai = p["is_ai"]

            role_color = ft.Colors.PURPLE_300 if is_ai else ft.Colors.CYAN_300
            card_border = ft.BorderSide(1.5, ft.Colors.AMBER_500) if is_ai else ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
            card_bg = ft.Colors.SURFACE_CONTAINER_HIGH if is_ai else ft.Colors.SURFACE_CONTAINER

            posts_cards.append(
                ft.Container(
                    content=ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            # 左欄：phpBB 經典會員資訊卡片 (寬度 160px)
                            ft.Container(
                                width=160,
                                padding=12,
                                bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                                border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
                                content=ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=6,
                                    controls=[
                                        ft.CircleAvatar(
                                            content=ft.Text(p["author_avatar"] or "👤", size=24),
                                            radius=26,
                                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
                                        ),
                                        ft.Text(p["author"], size=13, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE),
                                        ft.Container(
                                            content=ft.Text(p["author_role"], size=10, color=role_color, weight=ft.FontWeight.W_600),
                                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                            border_radius=4
                                        ),
                                        ft.Divider(color=ft.Colors.OUTLINE_VARIANT, height=12),
                                        ft.Text(floor_text, size=11, color=ft.Colors.AMBER_400, weight=ft.FontWeight.BOLD),
                                        ft.Text(f"🕒 {p['created_at'][:16]}", size=10, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                                    ]
                                )
                            ),
                            # 右欄：帖子文章主體與 Markdown 渲染
                            ft.Container(
                                expand=True,
                                padding=16,
                                content=ft.Column(
                                    spacing=12,
                                    controls=[
                                        # 頂部條
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                            controls=[
                                                ft.Row(
                                                    spacing=6,
                                                    controls=[
                                                        ft.Icon(ft.Icons.SCHEDULE, size=14, color=ft.Colors.GREY_400),
                                                        ft.Text(f"發布時間: {p['created_at']}", size=11, color=ft.Colors.GREY_400),
                                                        ft.Container(
                                                            content=ft.Text("⚡ William Lilly 1647 原典驗證", size=10, color=ft.Colors.AMBER_300),
                                                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                                                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                                            border_radius=4,
                                                            visible=is_ai
                                                        )
                                                    ]
                                                ),
                                                ft.Text(floor_text, size=12, color=ft.Colors.GREY_500)
                                            ]
                                        ),
                                        ft.Divider(color=ft.Colors.OUTLINE_VARIANT, height=8),
                                        # Markdown 內容區
                                        ft.Markdown(
                                            value=p["content"],
                                            selectable=True,
                                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                                            code_theme="atom-one-dark"
                                        ),
                                        ft.Divider(color=ft.Colors.OUTLINE_VARIANT, height=8),
                                        # 底部操作條
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.END,
                                            spacing=8,
                                            controls=[
                                                ft.TextButton(
                                                    f"👍 感謝 ({p['likes']})",
                                                    icon=ft.Icons.THUMB_UP_OUTLINED,
                                                    on_click=lambda _, post_id=pid: handle_like(post_id)
                                                ),
                                                ft.TextButton(
                                                    "💬 引用回覆",
                                                    icon=ft.Icons.FORMAT_QUOTE,
                                                    on_click=lambda _, author=p['author'], content=p['content']: handle_quote(author, content)
                                                ),
                                            ]
                                        )
                                    ]
                                )
                            )
                        ]
                    ),
                    bgcolor=card_bg,
                    border_radius=8,
                    border=ft.Border.all(card_border.width, card_border.color)
                )
            )

        # 快速回覆輸入框
        reply_field = ft.TextField(
            hint_text="輸入您的回覆見解，或向 AI 駐站古典掌門提問...",
            multiline=True,
            min_lines=3,
            max_lines=6,
            expand=True
        )

        def submit_quick_reply(_):
            val = reply_field.value
            if not val or not val.strip():
                show_snackbar("請輸入回覆內容！", ft.Colors.RED_400)
                return
            add_post(topic_id, author="熱心朋友", author_role="🌱 易壇道友", content=val.strip())
            reply_field.value = ""
            show_snackbar("回覆發布成功！")
            refresh_current_view()

        def summon_ai_master(_):
            show_snackbar("⏳ 正在召喚 AI 駐站古典掌門推演命盤...", ft.Colors.AMBER_600)
            page.update()
            user_q = reply_field.value.strip() if reply_field.value else None
            try:
                generate_ai_reply_for_topic(topic_id, user_question=user_q)
                reply_field.value = ""
                show_snackbar("✨ AI 駐站古典掌門已完成推演並回覆於討論串！", ft.Colors.GREEN_500)
                refresh_current_view()
            except Exception as e:
                show_snackbar(f"AI 呼叫失敗: {e}", ft.Colors.RED_400)

        quick_reply_box = ft.Container(
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text("✍️ 快速回覆此主題", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_100),
                    reply_field,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.FilledButton(
                                "🤖 召喚 AI 駐站古典掌門立即解盤",
                                icon=ft.Icons.AUTO_AWESOME,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_800, color=ft.Colors.WHITE),
                                on_click=summon_ai_master
                            ),
                            ft.FilledButton(
                                "🚀 送出回覆",
                                icon=ft.Icons.SEND,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE),
                                on_click=submit_quick_reply
                            ),
                        ]
                    )
                ]
            ),
            padding=16,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
        )

        return ft.Column(
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                # 麵包屑
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.TextButton(
                                    "🏠 回到首頁",
                                    icon=ft.Icons.HOME,
                                    style=ft.ButtonStyle(color=ft.Colors.AMBER_300),
                                    on_click=lambda _: navigate_to("index")
                                ),
                                ft.Text(">", color=ft.Colors.GREY_500),
                                ft.TextButton(
                                    f"{topic['category_icon']} {topic['category_title']}",
                                    style=ft.ButtonStyle(color=ft.Colors.AMBER_200),
                                    on_click=lambda _: navigate_to("topics", category_id=topic["category_id"])
                                ),
                                ft.Text(">", color=ft.Colors.GREY_500),
                                ft.Text(topic["title"][:25] + "...", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                            ]
                        ),
                        ft.FilledButton(
                            "⬅️ 返回版塊",
                            icon=ft.Icons.ARROW_BACK,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, color=ft.Colors.WHITE),
                            on_click=lambda _: navigate_to("topics", category_id=topic["category_id"])
                        )
                    ]
                ),
                # 主題標題牌
                ft.Container(
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text(topic["title"], size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                    ft.Text(f"發布人: {topic['author']} ({topic['author_role']}) | 查看: {topic['views']} 次 | 總樓層: {len(topic['posts'])}", size=12, color=ft.Colors.GREY_400)
                                ]
                            ),
                            ft.FilledButton(
                                "🤖 召喚 AI 掌門",
                                icon=ft.Icons.BOLT,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_700, color=ft.Colors.WHITE),
                                on_click=summon_ai_master
                            )
                        ]
                    ),
                    padding=16,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.AMBER_700)
                ),
                # 所有樓層
                *posts_cards,
                # 快速回覆
                quick_reply_box
            ]
        )

    def handle_like(post_id: int):
        new_likes = like_post(post_id)
        show_snackbar(f"感謝點讚！當前點讚數: {new_likes}")
        refresh_current_view()

    def handle_quote(author: str, content: str):
        show_snackbar(f"已複製 @{author} 的發言摘要至回覆框！")

    # --- 發布新主題對話框 ---
    def open_new_topic_dialog(default_category_id: int = 1):
        categories = get_categories_with_stats()
        cat_dropdown = ft.Dropdown(
            label="選擇發布版塊",
            options=[ft.dropdown.Option(str(c["id"]), f"{c['icon']} {c['title']}") for c in categories],
            value=str(default_category_id),
            expand=True
        )
        title_input = ft.TextField(label="主題標題", hint_text="例如：【卜卦問事】下週合約能否順利簽約？", expand=True)
        author_input = ft.TextField(label="您的稱謂", value="易壇求知客", width=180)
        chart_type_dropdown = ft.Dropdown(
            label="盤體類型",
            options=[
                ft.dropdown.Option("horary", "🎯 卜卦問事盤"),
                ft.dropdown.Option("natal", "🏛️ 本命流年盤"),
                ft.dropdown.Option("general", "📜 一般占星研討"),
            ],
            value="horary",
            width=180
        )
        body_input = ft.TextField(
            label="說明與問題細節",
            hint_text="請描述所問問題、起盤背景，或貼入完整的命盤度數數據...",
            multiline=True,
            min_lines=6,
            max_lines=12
        )
        auto_ai_checkbox = ft.Checkbox(label="發布後立即召喚 AI 駐站古典掌門首評 (Groq LPU 秒級解盤)", value=True)

        def submit_new_topic(_):
            if not title_input.value or not title_input.value.strip():
                show_snackbar("請填寫主題標題！", ft.Colors.RED_400)
                return
            if not body_input.value or not body_input.value.strip():
                show_snackbar("請填寫內容細節或盤體數據！", ft.Colors.RED_400)
                return

            cid = int(cat_dropdown.value)
            tid = add_topic(
                category_id=cid,
                title=title_input.value.strip(),
                author=author_input.value.strip() or "朋友",
                author_role="🌱 易壇道友",
                content=body_input.value.strip(),
                chart_type=chart_type_dropdown.value
            )

            # 關閉對話框
            dialog.open = False
            page.update()

            show_snackbar("🎉 主題發布成功！")

            if auto_ai_checkbox.value:
                show_snackbar("⏳ 正在為您召喚 AI 駐站古典掌門進行首評...", ft.Colors.AMBER_600)
                try:
                    generate_ai_reply_for_topic(tid)
                    show_snackbar("✨ AI 掌門首評已發布！", ft.Colors.GREEN_500)
                except Exception as e:
                    show_snackbar(f"AI 首評失敗: {e}", ft.Colors.RED_400)

            navigate_to("thread", topic_id=tid)

        dialog = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.POST_ADD, color=ft.Colors.AMBER_400), ft.Text("發起新的古典占星研討主題")]),
            content=ft.Container(
                width=650,
                content=ft.Column(
                    spacing=12,
                    tight=True,
                    controls=[
                        ft.Row([cat_dropdown, chart_type_dropdown]),
                        ft.Row([title_input, author_input]),
                        body_input,
                        auto_ai_checkbox
                    ]
                )
            ),
            actions=[
                ft.TextButton("取消", on_click=lambda _: close_dialog(dialog)),
                ft.FilledButton("🚀 立即發布", style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE), on_click=submit_new_topic)
            ]
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def close_dialog(dialog):
        dialog.open = False
        page.update()

    # --- 路由與視圖切換控制器 ---
    def navigate_to(view: str, category_id: int = None, topic_id: int = None):
        current_view["view"] = view
        current_view["category_id"] = category_id
        current_view["topic_id"] = topic_id
        refresh_current_view()

    def refresh_current_view():
        v = current_view["view"]
        if v == "index":
            content_area.content = render_board_index()
        elif v == "topics":
            content_area.content = render_topic_list(current_view["category_id"])
        elif v == "thread":
            content_area.content = render_thread_view(current_view["topic_id"])
        page.update()

    # 初始渲染
    page.add(
        ft.Column(
            expand=True,
            spacing=0,
            controls=[
                build_header(),
                content_area
            ]
        )
    )
    navigate_to("index")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flet Classical Astrology phpBB Mini Forum")
    parser.add_argument("--port", type=int, default=8555, help="Web server port (default: 8555)")
    parser.add_argument("--desktop", action="store_true", help="Launch in native desktop window mode instead of web")
    args = parser.parse_args()

    port = int(os.environ.get("PORT", args.port))
    if args.desktop:
        print(f"[*] Starting Flet phpBB Forum in native desktop window mode...")
        ft.run(main)
    else:
        os.environ["FLET_FORCE_WEB_SERVER"] = "true"
        print(f"[*] Starting Flet phpBB Forum [Web Mode] on http://0.0.0.0:{port} ...")
        ft.run(main, host="0.0.0.0", port=port, view=ft.AppView.WEB_BROWSER)
