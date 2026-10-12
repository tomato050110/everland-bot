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

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"전송 실패: {e}")

def run():
    saved_states = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                saved_states = json.load(f)
        except Exception:
            saved_states = {}

    new_states = {}
    changes = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for item in TARGETS:
            name = item["name"]
            url = item["url"]
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)
                
                # 핵심 변경: 헤더, 배너 롤링, 푸터를 무시하고 '실제 본문 콘텐츠 영역'만 추출
                main_elem = page.query_selector("main")
                if main_elem:
                    content_text = main_elem.inner_text()
                else:
                    content_text = page.inner_text("body")

                # 줄바꿈과 공백 정리 후 고유 해시 생성
                clean_text = " ".join(content_text.split())
                current_hash = hashlib.md5(clean_text.encode("utf-8")).hexdigest()
                new_states[name] = current_hash

                old_hash = saved_states.get(name)
                # 이전 기록이 있고 해시값이 달라졌을 때만 변동 판단
                if old_hash and old_hash != current_hash:
                    changes.append(f"• [{name}] 공지/이벤트 변동 감지!\n바로가기: {url}")
                elif not old_hash:
                    print(f"[{name}] 초기 기준 등록 완료")
            except Exception as e:
                print(f"[{name}] 에러: {e}")
                if name in saved_states:
                    new_states[name] = saved_states[name]

        browser.close()

    # 변동이 감지된 경우에만 알림 전송
    if changes:
        send_telegram("[에버랜드 실시간 변동 알림]\n\n" + "\n\n".join(changes))

    # 최신 상태 저장
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(new_states, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run()
