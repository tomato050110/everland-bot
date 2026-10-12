import os
import json
import asyncio
import urllib.request
import urllib.parse
from playwright.async_api import async_playwright

# 텔레그램 설정
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
STATE_FILE = "latest_targets_state.json"

# 유저가 직접 제공한 정확한 9개 감시 대상 URL
TARGETS = [
    {"name": "공지사항", "url": "https://www.everland.com/everland/announcement"},
    {"name": "이벤트", "url": "https://www.everland.com/everland/event"},
    {"name": "정기권", "url": "https://www.everland.com/everland/ticket"},
    {"name": "체험", "url": "https://www.everland.com/everland/promotion/exp-program"},
    {"name": "테마뮤직", "url": "https://www.everland.com/everland/everstory/everland-music"},
    {"name": "드림투어", "url": "https://www.everland.com/everland/promotion/dream-tour"},
    {"name": "캐리비안베이 공지", "url": "https://www.everland.com/caribbeanbay/announcement"},
    {"name": "캐비이벤트", "url": "https://www.everland.com/caribbeanbay/event"},
    {"name": "홈브리지", "url": "https://www.everland.com/homebridge/announcement"}
]

def send_telegram(message):
    """텔레그램 메시지 전송"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("텔레그램 토큰 또는 CHAT_ID가 설정되지 않았습니다.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=payload)
        with urllib.request.urlopen(req) as resp:
            print("텔레그램 알림 전송 성공")
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")

def load_previous_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_current_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

async def check_targets():
    prev_state = load_previous_state()
    current_state = {}
    updated_items = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for target in TARGETS:
            name = target["name"]
            url = target["url"]
            print(f"[{name}] 감시 중: {url}")

            try:
                # 네트워크 상태 안정화 대기
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)  # 자바스크립트 추가 렌더링 3초 대기

                # 메인 영역 또는 본문 전체 텍스트 추출
                content_element = await page.query_selector("main") or await page.query_selector("body")
                raw_text = await content_element.inner_text() if content_element else ""
                
                # 공백 정리
                clean_text = " ".join(raw_text.split())
                
                if not clean_text:
                    print(f"[{name}] 텍스트 추출 실패 (빈 페이지)")
                    current_state[name] = prev_state.get(name, "")
                    continue

                current_state[name] = clean_text

                # 이전 상태와 비교
                if name in prev_state:
                    if prev_state[name] != clean_text:
                        print(f"★ [{name}] 변동 감지!")
                        updated_items.append((name, url))
                else:
                    print(f"[{name}] 최초 상태 기록 완료")

            except Exception as e:
                print(f"[{name}] 로딩 실패/에러 발생: {e}")
                # 로딩 실패 시 기존 상태를 유지하여 잘못된 덮어쓰기 방지
                if name in prev_state:
                    current_state[name] = prev_state[name]

        await browser.close()

    # 변동 사항이 있을 때만 텔레그램 전송
    if updated_items:
        msg = "<b>🚨 에버랜드 새 소식 알림</b>\n\n"
        for item_name, item_url in updated_items:
            msg += f"• <b>{item_name}</b> 업데이트 발생!\n👉 <a href='{item_url}'>바로가기</a>\n\n"
        send_telegram(msg)
    
    # 상태 업데이트 저장
    save_current_state(current_state)

if __name__ == "__main__":
    asyncio.run(check_targets())
