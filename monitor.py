import os, json, asyncio, urllib.request, urllib.parse
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

async def run():
    tok = os.environ.get("TELEGRAM_TOKEN")
    cid = os.environ.get("CHAT_ID")
    prev = {}
    if os.path.exists(F):
        try:
            with open(F, "r", encoding="utf-8") as f: prev = json.load(f)
        except: prev = {}
    
    curr, up = {}, []
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        pg = await b.new_page()
        for t in T:
            try:
                await pg.goto(t["u"], wait_until="networkidle", timeout=30000)
                await pg.wait_for_timeout(3000)
                el = await pg.query_selector("main") or await pg.query_selector("body")
                txt = " ".join((await el.inner_text()).split()) if el else ""
                if not txt:
                    curr[t["n"]] = prev.get(t["n"], "")
                    continue
                curr[t["n"]] = txt
                if t["n"] in prev and prev[t["n"]] != txt:
                    up.append((t["n"], t["u"]))
                elif t["n"] not in prev:
                    pass
            except Exception as e:
                if t["n"] in prev: curr[t["n"]] = prev[t["n"]]
        await b.close()
    
    if up and tok and cid:
        msg = "<b>🚨 에버랜드 통합 소식 알림</b>\n\n"
        for n, u in up: msg += f"• <b>{n}</b> 업데이트!\n👉 <a href='{u}'>바로가기</a>\n\n"
        url = f"https://api.telegram.org/bot{tok}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": cid, "text": msg, "parse_mode": "HTML"}).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req) as r: pass
        except: pass
        
    with open(F, "w", encoding="utf-8") as f: json.dump(curr, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(run())
