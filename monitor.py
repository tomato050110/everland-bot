import os
import json
import asyncio
import urllib.request
import urllib.parse
from playwright.async_api import async_playwright

T = [
    {"n": "공지사항", "u": "https://www.everland.com/everland/announcement"},
    {"n": "이벤트", "u": "https://www.everland.com/everland/event"},
    {"n": "정기권", "u": "https://www.everland.com/everland/ticket"},
    {"n": "체험", "u": "https://www.everland.com/everland/promotion/exp-program"},
    {"n": "테마뮤직", "u": "https://www.everland.com/everland/everstory/everland-music"},
    {"n": "드림투어", "u": "https://www.everland.com/everland/promotion/dream-tour"},
    {"n": "캐리비안베이 공지", "u": "https://www.everland.com/caribbeanbay/announcement"},
    {"n": "캐비이벤트", "u": "https://www.everland.com/caribbeanbay/event"},
    {"n": "홈브리지", "u": "https://www.everland.com/homebridge/announcement"}
]

F = "latest_targets_state.json"

def send(msg):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("CHAT_ID")
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req) as resp:
            pass
    except Exception as e:
        print(e)

async def main():
    prev = {}
    if os.path.exists(F):
        try:
            with open(F, "r", encoding="utf-8") as f:
                prev = json.load(f)
        except:
            prev = {}

    curr = {}
    updated = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for t in T:
            name = t["n"]
            url = t["u"]
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)
                el = await page.query_selector("main") or await page.query_selector("body")
                txt = await el.inner_text() if el else ""
                clean = " ".join(txt.split())
                
                if not clean:
                    curr[name] = prev.get(name, "")
                    continue
                
                curr[name] = clean
                
                if name in prev:
                    if prev[name] != clean:
                        updated.append((name, url))
                else:
                    print(f"New: {name}")
            except Exception as e:
                print(f"Error {name}: {e}")
                if name in prev:
                    curr[name] = prev[name]

        await browser.close()

    if updated:
        msg = "<b>🚨 에버랜드 통합 소식 알림</b>\n\n"
        for name, url in updated:
            msg += f"• <b>{name}</b> 업데이트!\n👉 <a href='{url}'>바로가기</a>\n\n"
        send(msg)

    with open(F, "w", encoding="utf-8") as f:
        json.dump(curr, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
