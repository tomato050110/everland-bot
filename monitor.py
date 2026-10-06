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
    {"name": "에버랜드 체험 프로그램", "url": "https://www.everland.com/everland/promotion/exp-program"},
    {"name": "에버랜드 테마뮤직", "url": "https://www.everland.com/everland/everstory/everland-music"},
    {"name": "에버랜드 드림투어", "url": "https://www.everland.com/everland/promotion/dream-tour"},
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
        print(f"텔레그램 전송 에러: {e}")

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
                # 네트워크 통신 완료 및 SPA 데이터 렌더링 대기
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(5000)

                # main 영역 우선 추출, 없으면 body 추출
                content_element = page.query_selector("main") or page.query_selector("body")
                body_text = content_element.inner_text().strip() if content_element else ""

                # 유효 데이터(150자 이상)가 정상 렌더링되었을 때만 해시 비교
                if len(body_text) > 150:
                    current_hash = hashlib.md5(body_text.encode("utf-8")).hexdigest()
                    new_states[name] = current_hash

                    old_hash = saved_states.get(name)
                    if old_hash and old_hash != current_hash:
                        changes.append(f"• [{name}] 변동 감지!\n바로가기: {url}")
                    elif not old_hash:
                        print(f"[{name}] 초기 세팅 완료 ({len(body_text)}자)")
                else:
                    print(f"[{name}] 데이터 미완성/짧음 ({len(body_text)}자) -> 이전 상태 유지")
                    if name in saved_states:
                        new_states[name] = saved_states[name]

            except Exception as e:
                print(f"[{name}] 렌더링 실패: {e}")
                if name in saved_states:
                    new_states[name] = saved_states[name]

        browser.close()

    if changes:
        alert_text = "[에버랜드/캐리비안베이/홈브리지 변동 감지]\n\n" + "\n\n".join(changes)
        send_telegram(alert_text)
        print("텔레그램 전송 완료")
    else:
        print("변동 사항 없음")

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(new_states, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run()
