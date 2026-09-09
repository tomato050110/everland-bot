import os
import json
import hashlib
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
HISTORY_FILE = "latest_targets_state.json"

TARGETS = [
    # 🎡 에버랜드 채널
    {"name": "에버랜드 공지사항", "url": "https://www.everland.com/everland/announcement"},
    {"name": "에버랜드 이벤트", "url": "https://www.everland.com/everland/event"},
    {"name": "에버랜드 티켓/정기권", "url": "https://www.everland.com/everland/ticket"},
    {"name": "에버랜드 체험 프로그램", "url": "https://www.everland.com/everland/promotion/exp-program"},
    {"name": "에버랜드 메인 홈 배너", "url": "https://www.everland.com/everland/home/main"},
    {"name": "에버랜드 공식 보도자료", "url": "https://www.witheverland.com/category/PRESS%20CENTER/%EB%B3%B4%EB%8F%84%EC%9E%90%EB%A3%8C"},

    # 🌊 캐리비안베이 채널
    {"name": "캐리비안베이 공지사항", "url": "https://www.everland.com/caribbeanbay/announcement"},
    {"name": "캐리비안베이 이벤트", "url": "https://www.everland.com/caribbeanbay/event"},
    {"name": "캐리비안베이 메인 홈 배너", "url": "https://www.everland.com/caribbeanbay/home/main"},

    # 🏡 홈브리지(숙소) 채널
    {"name": "홈브리지 공지사항", "url": "https://www.everland.com/homebridge/announcement"}
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9"
}

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"전송 실패: {e}")

def get_page_signature(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup(["script", "style", "meta", "noscript"]):
        tag.extract()
    text = soup.get_text(separator=" ", strip=True)
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def main():
    saved_states = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                saved_states = json.load(f)
        except Exception:
            saved_states = {}

    is_first_run = (len(saved_states) == 0)
    updated_states = dict(saved_states)

    for item in TARGETS:
        name = item["name"]
        url = item["url"]

        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            res.raise_for_status()
            current_sig = get_page_signature(res.text)
        except Exception as e:
            print(f"[{name}] 접근 실패: {e}")
            continue

        prev_sig = saved_states.get(name)

        if is_first_run:
            updated_states[name] = current_sig
        else:
            if prev_sig and prev_sig != current_sig:
                updated_states[name] = current_sig
                msg = f"[업데이트 감지!]\n\n구분: {name}\n새로운 공지 또는 변경 사항이 등록되었습니다.\n바로가기: {url}"
                send_telegram(msg)
                print(f"[{name}] 업데이트 발견 및 발송")
            elif not prev_sig:
                updated_states[name] = current_sig

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_states, f, ensure_ascii=False, indent=2)

    if is_first_run:
        send_telegram("[에버랜드 리조트 10대 채널 통합 감시 가동]\n에버랜드·캐리비안베이·홈브리지·보도자료 전체 등록 완료!")
        print("10대 채널 통합 초기화 완료")

if __name__ == "__main__":
    main()
