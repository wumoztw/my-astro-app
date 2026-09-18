#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
forum_ai_service.py - AI Astrologer Bot Integration for Flet Forum
Powered by Groq LPU with multi-key rotation and failover.
"""

import os
import sys
from typing import Optional, Dict, Any
from groq import Groq
from forum_db import get_topic_detail, add_post

# 載入 .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(dotenv_path):
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip("'\"")

HORARY_BOT_PROMPT = """你是一位精通 17 世紀英國古典占星大師 William Lilly《基督教占星學》(Christian Astrology, 1647) 的「AI 駐站古典掌門」。
朋友在古典占星論壇的主題中向你請教卜卦成事吉凶。請以【最直接、大白話、幽默犀利】的老江湖前輩風格進行解答！

【回覆準則】：
1. 🎯 掌門一針見血結論：明確給出「能否成事（成事機率約 XX%）」、「核心劇本」與「預計應期（XX天/週/月）」。
2. 🩺 這盤能算嗎？（William Lilly 盤體檢意白話說）：檢視上升度數有效性、月亮狀態（落陷/燃燒/空亡/入相位）。
3. ⚖️ 事情會怎麼演變？（星體角色與成事劇本）：問卜者代表星、所問事項代表星、是否有光線傳遞（Translation of Light）或中途阻截。
4. 💡 掌門給你的生活實戰建議：2~3 點具體接地氣的行動指引。
"""

NATAL_BOT_PROMPT = """你是一位精通古典西洋占星學（希臘化、波斯阿拉伯與中世紀）的「白話命盤與流年推運掌門」（AI 駐站古典解盤掌門）。
朋友在論壇中發布了本命盤與推運數據。請以【最接地氣、一針見血、風趣犀利】的老江湖大白話講透，直擊人生命運核心！

【回覆結構】：
1. 🎯 掌門一針見血底牌總結：人格底色、老天賞飯天賦王牌（Almuten Figuris/強勢星）、人生最痛暗坑死穴。
2. 🌊 當前重大流年時運深度拆解：法達星限 (Firdaria) 十年大運、年度小限 (Profections) 今年戰場、黃道釋放 (ZR) 高峰或轉折期、太陽弧關鍵引動。
3. 🪐 弱勢星體吉凶化解與破局指南（Remediation）：給出 2 條具體生活能量轉化之道。
4. ⏳ 近 1~2 年關鍵轉折節點與行動避坑金律：未來 12~24 個月關鍵進攻 vs 防守月份，以及掌門三條決策金律。
"""

INTERACTIVE_FOLLOWUP_PROMPT = """你是一位精通古典西洋占星與流年推運的「白話解盤大師」（AI 駐站古典掌門）。
朋友在討論串中針對具體疑惑向你追問（例如轉職月份、感情合約、凶星化解等）。
請直球對決，不要重複整篇命盤，結合原盤與推運數據給予最犀利、清晰的生活化實戰破局指導！
"""


def get_groq_api_keys():
    raw_keys = [
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
        os.getenv("GROQ_API_KEY"),
    ]
    keys = []
    for k in raw_keys:
        if k and k.strip() and k.strip() not in keys:
            keys.append(k.strip())
    return keys


def call_groq_llm(prompt_sys: str, user_content: str) -> str:
    keys = get_groq_api_keys()
    if not keys:
        return "⚠️ 未檢測到 Groq API Key，請於系統環境變數或專案 `.env` 中設定 `GROQ_API_KEY`。"

    models_to_try = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
    last_err = None

    for idx, key in enumerate(keys, 1):
        client = Groq(api_key=key)
        for model in models_to_try:
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": prompt_sys},
                        {"role": "user", "content": user_content}
                    ],
                    model=model,
                    temperature=0.3,
                    max_tokens=2200,
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                last_err = e
                err_str = str(e).lower()
                if "rate limit" in err_str or "429" in err_str or "quota" in err_str:
                    break
                continue

    return f"⚠️ AI 駐站掌門暫時無法響應：{last_err}"


def generate_ai_reply_for_topic(topic_id: int, user_question: Optional[str] = None) -> Dict[str, Any]:
    """為指定主題生成 AI 駐站古典掌門解答並自動存入 SQLite 討論串"""
    topic = get_topic_detail(topic_id)
    if not topic:
        raise ValueError(f"Topic {topic_id} not found.")

    is_followup = bool(user_question and user_question.strip())

    if is_followup:
        sys_prompt = INTERACTIVE_FOLLOWUP_PROMPT
        user_content = f"""【討論串標題】：{topic['title']}
【盤體資料】：
{topic['chart_data_md']}

【朋友具體追問】：
{user_question}

請針對此問題進行一針見血的白話解析與破局建議。"""
    else:
        chart_type = topic.get("chart_type", "general")
        if chart_type == "horary":
            sys_prompt = HORARY_BOT_PROMPT
        else:
            sys_prompt = NATAL_BOT_PROMPT

        user_content = f"""【討論串標題】：{topic['title']}
【發布者說明與盤體數據】：
{topic['posts'][0]['content'] if topic.get('posts') else topic['chart_data_md']}

請依照掌門風格進行全面深入的大白話古典解析。"""

    # 呼叫 Groq
    ai_text = call_groq_llm(sys_prompt, user_content)

    # 存入資料庫
    post_id = add_post(
        topic_id=topic_id,
        author="🤖 AI 駐站古典掌門 · William Lilly 傳承",
        author_role="🧚 占星精靈",
        content=ai_text,
        is_ai=True,
        avatar="⚡"
    )

    return {
        "post_id": post_id,
        "author": "🤖 AI 駐站古典掌門 · William Lilly 傳承",
        "author_role": "🧚 占星精靈",
        "avatar": "⚡",
        "content": ai_text,
        "is_ai": True
    }


if __name__ == "__main__":
    print("[*] Testing Groq API Keys availability...")
    keys = get_groq_api_keys()
    print(f"[*] Found {len(keys)} Groq API Keys.")
