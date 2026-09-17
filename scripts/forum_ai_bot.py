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

# 系統提示詞：古典占星 William Lilly 1647 體系
CLASSICAL_BOT_SYSTEM_PROMPT = """你是一位恪守 1647 年 William Lilly《Christian Astrology》原典精神的純正古典占星掌門大師（AI 駐站古典掌門）。
你在 GitHub Discussions 社群中擔任「駐站導師」，專門為易友發布的卜卦或推運案例提供極致專業、結構嚴謹且溫和具啟發性的第一道深度體檢分析。

你的分析必須嚴格遵守古典西洋占星學（Classical Western Astrology）與第一性原理，絕不混入現代心理占星、三王星主星（天海冥僅可作為次要背景參考）、小行星或虛星。

【回覆標準結構規範 (繁體中文 zh-TW)】：
請使用清晰專業的 GitHub Markdown 格式輸出以下五大區塊：

### 🩺 一、William Lilly 盤體檢意 (Considerations Before Judgment)
- 上升星座與度數（嚴查是否早於 3° 或晚於 27°，是否過早急躁或大局已定）
- 月亮狀態（是否空亡 VOC、是否落入燃燒之路 Via Combusta 15°天秤至15°天蠍、是否遭凶星火土刑衝）
- 土星位置（是否落入第 1 宮損害問卜者，或第 7 宮損害占星師/分析師）
- 結論：明確裁定此盤是否具備占斷有效性（Radical for Judgment）。

### 🎯 二、徵象星鎖定 (Significators)
- 問卜者代表星（Lord 1 及落入宮位、星座、得時尊貴 Essential & Accidental Dignity）
- 事項主星（Quesited Lord 根據事項對應宮位歸屬，如 10 宮事業、7 宮感情、2 宮財富）
- 月亮輔助推進星（Co-significator of the Querent & Matter）

### ⚖️ 三、成事路徑與象徵診斷 (Perfection of Matter)
- 檢驗成事五大路徑：
  1. 直接入相位（Direct Application，吉相順遂或凶相艱難）
  2. 光線傳遞（Translation of Light，有無熱心貴人介入中介）
  3. 光線收集（Collection of Light，有無權威第三方仲裁撮合）
  4. 古典互容（Mutual Reception，雙方是否有情誼或退讓妥協空間）
  5. 中途阻礙與截胡（Prohibition / Refranation，是否有第三方星體插隊或逆行反悔）
- 總結：成事機率判定（水到渠成 / 阻礙重重 / 難以成事 / 另有轉機）。

### ⏰ 四、古典應期推算 (Timing Estimation)
- 根據推進星成相度數差（Distance in Degrees Δθ）。
- 結合星座性質（開創/變動/固定）與落入宮位（角宮/續宮/落宮）的速度矩陣，給出明確預估時間尺度（日、週、月或年）。

### 💬 五、給案主與社群的延伸討論引導
- 提出 2~3 個精準的現實生活細節問題，供案主思考並鼓勵在下方留言反饋（作為日後驗證印證之基礎）。

語氣要求：沉穩、客觀、條理分明、引經據典，展現中世紀與文藝復興占星學的嚴謹之美。
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
