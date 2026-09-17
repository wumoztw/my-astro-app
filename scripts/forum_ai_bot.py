#!/usr/bin/env python3
"""
GitHub Discussions AI Astrologer Bot
-----------------------------------
Powered by Groq Cloud (llama-3.3-70b-versatile) + William Lilly 1647 Classical Astrology Framework.
Triggered automatically via GitHub Actions upon new Discussions or Comments.
"""

import os
import sys
import json
import argparse
import requests
from groq import Groq

# 系統提示詞：古典占星 William Lilly 1647 體系（大白話實戰解盤風格）
CLASSICAL_BOT_SYSTEM_PROMPT = """你是一位精通 1647 年 William Lilly 古典卜卦占星學的「白話解盤大師」（AI 駐站古典掌門）。
你的風格是：【直接、一針見血、講大白話】！
請徹底拋棄生硬刻板的學術調書袋與拉丁古文堆砌，用老百姓聽得懂的現代生活化語言，把古典天象精準翻譯成現實中的具體走勢與應對方案。

【三大核心原則】：
1. 開門見山，第一眼給出底牌：第一區塊必須明確給出「能不能成、機率多少、何時見分曉」，絕不繞圈子、絕不模稜兩可！
2. 生活化白話比喻：把枯燥的古典名詞用超生動的比喻翻譯給讀者聽：
   - 廟旺（手握好牌、有話語權、佔據主場優勢）
   - 落陷（掉進泥坑、處境被動、心有餘而力不足）
   - 光線傳遞 Translation of Light（貴人穿針引線、第三方牽線搭橋遞消息）
   - 光線收集 Collection of Light（主管高層仲裁拍板、權威第三方介入撮合）
   - 中途阻截 Prohibition / Refranation（半路殺出程咬金、被人截胡搶先、半路反悔變卦）
   - 古典互容 Mutual Reception（雙方互有默契、彼此各退一步妥協）
   - 月亮空亡 VOC（做了白工、暫時沒有下文、宜按兵不動靜觀其變）
3. 兼具犀利與溫度：像一位資深江湖老前輩，既指出盤面上的現實殘酷點，又給予具體接地氣的生活實戰破局建議。

【回覆版面結構 (繁體中文 zh-TW)】：

### 🎯 掌門一針見血結論
- **能否成事**：【直接回答：如「成事機率約 XX%」、「阻礙極大不宜強求」或「水到渠成但有小波折」】
- **核心劇本**：用一句生動白話講完這件事的發展走向。
- **預計應期**：約在【XX天 / XX週 / XX月】左右會有關鍵消息、轉折或定局。

### 🩺 這盤能算嗎？（William Lilly 盤體檢意白話說）
- **時機對不對**：上升度數是否太早急躁（<3°）、或大局已定為時已晚（>27°）、還是剛好成熟？
- **心態與局勢**：月亮狀態是淡定有著落，還是焦慮卡在泥坑（落陷/燃燒/空亡）？
- **體檢判定**：本盤有效性總結。

### ⚖️ 事情會怎麼演變？（星體角色與成事劇本）
- **代表你的是誰**：你的處境與戰力如何？（握有好牌，還是受制於人？）
- **代表這件事/對方的是誰**：對方的態度、條件或難度如何？
- **中間誰在推動或卡關**：有沒有貴人穿針引線？還是半路有小人或程咬金截胡？

### 💡 掌門給你的生活實戰建議
- 給出 2~3 點具體、接地氣的行動指引，告訴問卜者當前現實中「該做什麼、千萬別做什麼」以化解阻礙。
"""

def call_groq_analysis(title: str, body: str, api_keys: list) -> str:
    """調用 Groq 進行古典占星推理，支援多金鑰自動輪替 (Round-Robin & Failover)"""
    if not api_keys:
        raise ValueError("No Groq API keys provided.")

    user_content = f"""【討論串標題】：{title}

【案主發布之命盤與問題數據】：
{body}

請根據上述案例數據與 William Lilly 1647 原典體系，進行全面的古典盤體檢意、徵象星分析、成事路徑診斷與應期推算。"""

    models_to_try = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
    last_err = None

    # 對多把金鑰進行依序嘗試 (Failover)
    for idx, key in enumerate(api_keys, 1):
        masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
        print(f"[*] Trying Groq Key #{idx} ({masked_key}) ...", file=sys.stderr)
        client = Groq(api_key=key)

        for model in models_to_try:
            try:
                print(f"  └─ Calling model: {model} ...", file=sys.stderr)
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": CLASSICAL_BOT_SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    model=model,
                    temperature=0.3,
                    max_tokens=2500,
                )
                print(f"[+] Success with Key #{idx} and model {model}!", file=sys.stderr)
                return chat_completion.choices[0].message.content
            except Exception as e:
                print(f"  [!] Failed model {model} with Key #{idx}: {e}", file=sys.stderr)
                last_err = e
                # 若是 429 頻率限制或 401 密鑰問題，直接跳下一把 Key
                err_str = str(e).lower()
                if "rate limit" in err_str or "429" in err_str or "401" in err_str or "quota" in err_str:
                    print(f"  [!] Key #{idx} hit rate limit or auth error. Switching to next key...", file=sys.stderr)
                    break
                continue

    raise RuntimeError(f"All Groq keys and models failed: {last_err}")


def post_github_discussion_comment(discussion_id: str, comment_body: str, gh_token: str):
    """透過 GitHub GraphQL API 將分析結果發布為討論串回覆"""
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {gh_token}",
        "Content-Type": "application/json",
        "User-Agent": "my-astro-app-ai-bot"
    }
    
    mutation = """
    mutation AddDiscussionComment($discussionId: ID!, $body: String!) {
      addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
        comment {
          id
          url
        }
      }
    }
    """
    
    payload = {
        "query": mutation,
        "variables": {
            "discussionId": discussion_id,
            "body": comment_body
        }
    }
    
    res = requests.post(url, headers=headers, json=payload, timeout=30)
    if res.status_code != 200:
        raise RuntimeError(f"GraphQL request failed HTTP {res.status_code}: {res.text}")
    
    data = res.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL returned errors: {data['errors']}")
        
    comment_info = data.get("data", {}).get("addDiscussionComment", {}).get("comment", {})
    print(f"[+] Successfully posted comment: {comment_info.get('url')}", file=sys.stderr)
    return comment_info


def main():
    parser = argparse.ArgumentParser(description="GitHub Discussions AI Astrologer Bot")
    parser.add_argument("--dry-run", action="store_true", help="Print AI review to stdout without posting to GitHub")
    parser.add_argument("--title", type=str, default="", help="Discussion Title")
    parser.add_argument("--body", type=str, default="", help="Discussion Body")
    args = parser.parse_args()

    # 1. 取得環境變數或命令列參數（支援 3 把 Groq 金鑰輪替備援）
    raw_keys = [
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
        os.getenv("GROQ_API_KEY")
    ]
    # 去重且過濾空值
    groq_api_keys = []
    for k in raw_keys:
        if k and k.strip() and k.strip() not in groq_api_keys:
            groq_api_keys.append(k.strip())

    gh_token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    
    discussion_id = os.getenv("DISCUSSION_ID")
    discussion_title = args.title or os.getenv("DISCUSSION_TITLE", "占星案例求助")
    discussion_body = args.body or os.getenv("DISCUSSION_BODY", "")

    if not groq_api_keys:
        print("[!] Error: No valid Groq API key found in GROQ_API_KEY_1, GROQ_API_KEY_2, GROQ_API_KEY_3, or GROQ_API_KEY.", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Loaded {len(groq_api_keys)} Groq API Key(s) for automatic rotation & failover.", file=sys.stderr)

    if not discussion_body.strip():
        print("[!] No discussion body provided, nothing to analyze.", file=sys.stderr)
        sys.exit(0)

    print(f"[*] Analyzing discussion: '{discussion_title}' ...", file=sys.stderr)
    
    # 2. 呼叫 Groq 進行古典占星推理 (多金鑰輪替)
    ai_analysis = call_groq_analysis(discussion_title, discussion_body, groq_api_keys)
    
    full_comment = f"""### 🤖【AI 駐站古典掌門 · William Lilly 原典體檢報告】

{ai_analysis}

---
*✨ 報告由 **my-astro-app** 社群自動化引擎 + **Groq LPU (openai/gpt-oss-120b)** 於 2 秒內自動生成。歡迎各位易友於下方留言交流、發表不同流派見解或提供現實反饋！*
"""

    # 3. 輸出或發布
    if args.dry_run or not discussion_id or not gh_token:
        print("\n" + "="*50)
        print("=== [DRY RUN / LOCAL MODE OUTPUT] ===")
        print("="*50 + "\n")
        print(full_comment)
    else:
        print(f"[*] Posting comment to Discussion Node ID: {discussion_id} ...", file=sys.stderr)
        post_github_discussion_comment(discussion_id, full_comment, gh_token)

if __name__ == "__main__":
    main()
