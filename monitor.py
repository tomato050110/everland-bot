import os
import hashlib
import json
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 감시할 대상 페이지 목록
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
        print(f"텔레그램 전송 에러: {e}")

def run():
    # 1. 이전 상태 파일 불러오기
    saved_states = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                saved_states = json.load(f)
        except Exception:
            saved_states = {}

    new_states = {}
    changes = []

    # 2. 크롬 브라우저 기동 및 텍스트 파싱
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for item in TARGETS:
            name = item["name"]
            url = item["url"]
            try:
                # 페이지 로딩 및 렌더링 대기
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)
                
                # 사람이 눈으로 보는 텍스트 전체 추출
                body_text = page.inner_text("body")
                
                # 텍스트 고유 해시값 생성
                current_hash = hashlib.md5(body_text.encode("utf-8")).hexdigest()
                new_states[name] = current_hash

                old_hash = saved_states.get(name)
                # 이전 기록이 있고, 해시값이 달라졌다면 실제 변동 발생
                if old_hash and old_hash != current_hash:
                    changes.append(f"• [{name}] 변동 감지!\n바로가기: {url}")
                elif not old_hash:
                    # 첫 실행 시 기준값 기록
                    print(f"[{name}] 초기 기준값 등록 완료 ({len(body_text)}자)")
            except Exception as e:
                print(f"[{name}] 처리 실패: {e}")
                # 에러 시 이전 상태를 유지하여 오작동 방지
                if name in saved_states:
                    new_states[name] = saved_states[name]

        browser.close()

    # 3. 변동이 감지된 경우에만 텔레그램 알림 발송
    if changes:
        alert_text = "[에버랜드 공지/이벤트 변동 감지]\n\n" + "\n\n".join(changes)
        send_telegram(alert_text)
        print("변동 사항 텔레그램 전송 완료")
    else:
        print("변동 사항 없음 (정상)")

    # 4. 최신 상태를 파일에 저장
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(new_states, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run()
