import os
import hashlib
import json
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
TARGETS = [
    {"name": "에버랜드 이벤트", "url": "https://www.everland.com/everland/event"},
    {"name": "에버랜드 공지사항", "url": "https://www.everland.com/everland/announcement"},
    {"name": "에버랜드 정기권", "url": "https://www.everland.com/everland/ticket"},
    {"name": "캐리비안베이 이벤트", "url": "https://www.everland.com/caribbeanbay/event"},
    {"name": "캐리비안베이 공지사항", "url": "https://www.everland.com/caribbeanbay/announcement"},
    {"name": "홈브리지 공지사항", "url": "https://www.everland.com/homebridge/announcement"}
]
STATE_FILE = "latest_targets_state.json"

def run():
    saved = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
        except:
            saved = {}

    new_s = {}
    changes = []
    
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page()
        for item in TARGETS:
            name, url = item["name"], item["url"]
            try:
                pg.goto(url, wait_until="domcontentloaded", timeout=30000)
                pg.wait_for_timeout(3000)
                elem = pg.query_selector("main")
                txt = elem.inner_text() if elem else pg.inner_text("body")
                clean = " ".join(txt.split())
                h = hashlib.md5(clean.encode("utf-8")).hexdigest()
                new_s[name] = h
                if name in saved and saved[name] != h:
                    changes.append(f"• [{name}] 변동 발생!\n{url}")
            except Exception as e:
                if name in saved:
                    new_s[name] = saved[name]
        b.close()

    if changes and TELEGRAM_TOKEN and CHAT_ID:
        try:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": "[변동 알림]\n\n" + "\n".join(changes)}, timeout=10)
        except:
            pass

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(new_s, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run()
