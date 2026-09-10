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
    {"name": "에버랜드 정기권", "url": "https://www.everland.com/everland/ticket"}
]

STATE_FILE = "latest_targets_state.json"

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"전송 실패: {e}")

def run():
    report = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for item in TARGETS:
            name = item["name"]
            url = item["url"]
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(3000)  # 자바스크립트 렌더링 3초 대기
                text = page.inner_text("body")
                report.append(f"• {name}: {len(text)}자 렌더링 완료")
            except Exception as e:
                report.append(f"• {name}: 에러({e})")

        browser.close()

    send_telegram("[크롬 렌더링 진단 보고]\n" + "\n".join(report))

if __name__ == "__main__":
    run()
