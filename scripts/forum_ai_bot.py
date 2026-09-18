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

# 1. 卜卦問事專用大白話 Prompt
HORARY_BOT_SYSTEM_PROMPT = """你是一位精通 1647 年 William Lilly 古典卜卦占星學的「白話解盤大師」（🧚 占星精靈）。
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

### 🎯 占星精靈一針見血結論
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

### 💡 占星精靈給你的生活實戰建議
- 給出 2~3 點具體、接地氣的行動指引，告訴問卜者當前現實中「該做什麼、千萬別做什麼」以化解阻礙。
"""

# 2. 本命格局與六大流年推運專用大白話 Prompt
NATAL_PREDICTIVE_BOT_SYSTEM_PROMPT = """你是一位精通古典西洋占星學（希臘化、希臘羅馬、波斯阿拉伯與中世紀體系）的「白話命盤與流年推運大師」（🧚 占星精靈）。
你的專長是把深奧複雜的古典本命盤底牌與多重推運體系，用【最接地氣、直指痛點、一針見血、風趣犀利】的老江湖大白話講透，讓案主一讀就懂自己的人生局勢與破局之道！

【核心原則】：
1. 拒絕算命套話與生硬調書袋：不堆砌晦澀名詞，把每顆星、每個推運象徵直接對應到生活場景（搞錢、升遷、感情合約、合夥撕逼、身心健康）。
2. 底牌與時運雙輪驅動：
   - 命格底牌：你是天生手握倚天劍，還是註定要先打怪升級？王牌天賦在哪裡？致命死穴何時會引爆？
   - 流年時運：大運（法達）在走什麼主題？今年焦點（小限）輪到哪座戰場？人生轉向（黃道釋放 ZR）在高峰還是低谷？
3. 既點出問題，更給出「化解破局之法」：古典占星講求趨吉避凶（Remediation），針對盤中弱點必須給出務實可行的生活調適方案！

【回覆版面結構 (繁體中文 zh-TW)】：

### 🎯 占星精靈一針見血底牌總結
- **人格底色與處世本能**：用一句犀利毒舌但精準的大白話，說出你骨子裡是個怎樣的人。
- **老天賞飯天賦王牌**：全盤總御星（Almuten Figuris）或本命最強勢星體宮位，告訴案主「這輩子走這條路最順、最容易成事賺錢」。
- **人生最痛暗坑與致命軟肋**：落陷、被凶星刑衝、或燃燒的星體宮位，直言其最容易栽跟頭、被反噬的盲區。

### 🌊 當前重大流年時運深度拆解
1. **法達星限 (Firdaria) —— 當前人生十年大週期**：
   - 目前主運星 / 副運星是誰？
   - 白話翻譯：這幾年的人生主線是「悶頭蓄力」、「財富擴張」、「關係考驗」還是「蛻變破繭」？
2. **年度小限 (Annual Profections) —— 今年主戰場**：
   - 今年（實歲）啟動哪一宮？誰是年度主當家（分宮主星）？
   - 白話翻譯：今年最容易被推上風口浪尖的生活焦點是什麼？資源會在哪裡聚集或承壓？
3. **希臘黃道釋放 (Zodiacal Releasing) —— 社會成就高光與轉向**：
   - 精神點（事業成就）與福德點（財富機遇）當前處於 Peak（高峰）期、蓄勢期、還是換宮重大轉向期（Losing of the Bond）？
4. **太陽弧 (Solar Arc) 與次限/行運關鍵引動**：
   - 近 1~2 年內有無容許度 1° 內的重磅星體相位碰觸？是否有重大外在事件（如升遷、搬遷、換賽道、合約）即將引動？

### 🪐 弱勢星體吉凶化解與破局指南（Remediation）
- 針對命盤中最棘手的受剋、落陷或凶星相位（例如土星壓迫、火星暴躁、水星燃燒），給出 2 條極為具體的生活轉化建議（例如如何借力使力、透過生活作息、特定行業屬性或心態修煉轉化凶性）。

### ⏳ 近 1~2 年關鍵轉折節點與行動避坑金律
- **關鍵時間點**：指出未來 12~24 個月內最關鍵的進攻月分 vs 需嚴格防守的月分。
- **占星精靈人生三條決策金律**：
  1. 【進攻金律】：何時該大膽下注搶佔先機？
  2. 【防守金律】：哪些事情千萬別衝動盲動（合約、轉職、投資或人際）？
  3. 【心態金律】：如何在當前星限週期中立於不敗之地？
"""

# 3. 討論串留言區追問互動專用 Prompt
INTERACTIVE_COMMENT_SYSTEM_PROMPT = """你是一位精通古典西洋占星與流年推運的「白話解盤大師」（🧚 占星精靈）。
朋友在討論串中向你追問問題（可能針對個人事業、感情、合約、健康、特定年份/月份轉職、或某顆星體的具體化解方式）。

【回覆準則】：
1. 一針見血，直球對決：絕不囉嗦廢話，不重複整篇排盤，直接針對他追問的具體疑惑給出最權威、清晰、接地氣的判斷！
2. 緊密結合原盤與推運數據：調用討論串主文中的命度、星體尊貴度、法達星限、小限宮位、黃道釋放、太陽弧等硬核數據給出實證推理。
3. 風格親切犀利：像一位身經百戰的占星精靈，給出「能做什麼 / 不能做什麼 / 關鍵時間點」的具體行動方案。
"""

def detect_chart_mode(title: str, body: str) -> str:
    """自動判定討論串是卜卦盤 (horary) 還是本命推運盤 (natal)"""
    text = (title + " " + body).lower()
    if "horary" in text or "卜卦" in text or "問事" in text or "成事" in text:
        return "horary"
    return "natal"

def call_groq_analysis(prompt_sys: str, user_content: str, api_keys: list) -> str:
    """調用 Groq 進行推理，支援多金鑰自動輪替 (Round-Robin & Failover)"""
    if not api_keys:
        raise ValueError("No Groq API keys provided.")

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
                        {"role": "system", "content": prompt_sys},
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
                err_str = str(e).lower()
                if "rate limit" in err_str or "429" in err_str or "401" in err_str or "quota" in err_str:
                    print(f"  [!] Key #{idx} hit rate limit or auth error. Switching to next key...", file=sys.stderr)
                    break
                continue

    raise RuntimeError(f"All Groq keys and models failed: {last_err}")


def post_github_discussion_comment(discussion_id: str, comment_body: str, gh_token: str, reply_to_id: str = None):
    """透過 GitHub GraphQL API 將分析結果發布為討論串回覆（若有 reply_to_id 則直接巢狀回覆留言）"""
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {gh_token}",
        "Content-Type": "application/json",
        "User-Agent": "my-astro-app-ai-bot"
    }
    
    # 1. 若有指定 reply_to_id，先嘗試巢狀回覆該則留言
    if reply_to_id:
        mutation_reply = """
        mutation AddDiscussionReply($discussionId: ID!, $replyToId: ID!, $body: String!) {
          addDiscussionComment(input: {discussionId: $discussionId, replyToId: $replyToId, body: $body}) {
            comment {
              id
              url
            }
          }
        }
        """
        payload_reply = {
            "query": mutation_reply,
            "variables": {
                "discussionId": discussion_id,
                "replyToId": reply_to_id,
                "body": comment_body
            }
        }
        try:
            res = requests.post(url, headers=headers, json=payload_reply, timeout=30)
            data = res.json()
            if res.status_code == 200 and "errors" not in data:
                comment_info = data.get("data", {}).get("addDiscussionComment", {}).get("comment", {})
                print(f"[+] Successfully posted threaded reply to {reply_to_id}: {comment_info.get('url')}", file=sys.stderr)
                return comment_info
            else:
                print(f"[*] Threaded reply fallback to top-level (GraphQL note: {data.get('errors')})", file=sys.stderr)
        except Exception as e:
            print(f"[*] Threaded reply failed ({e}), falling back to top-level comment.", file=sys.stderr)

    # 2. 標準討論串回覆
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
    parser.add_argument("--comment", type=str, default="", help="User follow-up comment")
    args = parser.parse_args()

    # 1. 取得環境變數或命令列參數（支援 3 把 Groq 金鑰輪替備援）
    raw_keys = [
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
        os.getenv("GROQ_API_KEY")
    ]
    groq_api_keys = []
    for k in raw_keys:
        if k and k.strip() and k.strip() not in groq_api_keys:
            groq_api_keys.append(k.strip())

    gh_token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    discussion_id = os.getenv("DISCUSSION_ID")
    discussion_title = args.title or os.getenv("DISCUSSION_TITLE", "占星案例求助")
    discussion_body = args.body or os.getenv("DISCUSSION_BODY", "")
    
    comment_body = args.comment or os.getenv("COMMENT_BODY", "")
    comment_author = os.getenv("COMMENT_AUTHOR", "朋友")
    comment_node_id = os.getenv("COMMENT_NODE_ID")
    event_name = os.getenv("EVENT_NAME", "discussion")

    if not groq_api_keys:
        print("[!] Error: No valid Groq API key found in secrets.", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Loaded {len(groq_api_keys)} Groq API Key(s) for automatic rotation & failover.", file=sys.stderr)

    # 2. 判斷是「新討論串首評」還是「留言區互動追問」
    is_interactive_followup = bool(comment_body.strip() and event_name == "discussion_comment")

    if is_interactive_followup:
        print(f"[*] Processing Interactive Follow-up by @{comment_author} ...", file=sys.stderr)
        sys_prompt = INTERACTIVE_COMMENT_SYSTEM_PROMPT
        user_content = f"""【討論串原命盤資料】：
{discussion_body}

【朋友 @{comment_author} 在留言中的具體追問】：
{comment_body}

請針對該朋友的追問，結合原命盤與推運數據，給予直接、一針見血、白話生活化的專業指點與實戰建議。"""
        header_title = f"### 🧚【占星精靈 · 深度解惑回覆】\n\n> 回覆 @{comment_author} 的提問：\n\n"
    else:
        # 新討論串首評：自動識別是 卜卦盤 還是 本命推運盤
        chart_mode = detect_chart_mode(discussion_title, discussion_body)
        print(f"[*] Analyzing new discussion: '{discussion_title}' (Detected Mode: {chart_mode}) ...", file=sys.stderr)
        
        if chart_mode == "horary":
            sys_prompt = HORARY_BOT_SYSTEM_PROMPT
            header_title = "### 🎯【占星精靈 · William Lilly 卜卦成事實戰斷言】\n\n"
        else:
            sys_prompt = NATAL_PREDICTIVE_BOT_SYSTEM_PROMPT
            header_title = "### 🏛️【占星精靈 · 本命底牌與流年推運深度剖析】\n\n"

        user_content = f"""【討論串標題】：{discussion_title}

【案主發布之命盤與問題數據】：
{discussion_body}

請進行全面、直白、大白話的深度剖析。"""

    # 3. 呼叫 Groq 進行推理
    ai_analysis = call_groq_analysis(sys_prompt, user_content, groq_api_keys)

    interactive_footer = """
---
*✨ 報告由 **my-astro-app** 社群自動化引擎 + **Groq LPU (openai/gpt-oss-120b)** 於 2 秒內自動生成。*  
*💬 **想針對本盤進一步追問嗎？** 直接在下方留言並標記 `@ai` 或 `@ai-astrologer`（例如：「`@ai 請教明年事業運如何？`」），占星精靈將在 20 秒內為你現身解答！*
"""

    full_comment = f"{header_title}{ai_analysis}\n{interactive_footer}"

    # 4. 輸出或發布
    if args.dry_run or not discussion_id or not gh_token:
        print("\n" + "="*50)
        print("=== [DRY RUN / LOCAL MODE OUTPUT] ===")
        print("="*50 + "\n")
        print(full_comment)
    else:
        print(f"[*] Posting comment to Discussion Node ID: {discussion_id} ...", file=sys.stderr)
        reply_target = comment_node_id if is_interactive_followup else None
        post_github_discussion_comment(discussion_id, full_comment, gh_token, reply_to_id=reply_target)

if __name__ == "__main__":
    main()
