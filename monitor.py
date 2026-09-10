import os
import hashlib
import time
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

TARGETS = [
    {"name": "에버랜드 공지사항", "url": "https://www.everland.com/everland/announcement"},
    {"name": "에버랜드 이벤트", "url": "https://www.everland.com/everland/event"},
    {"name": "에버랜드 티켓/정기권", "url": "https://www.everland.com/everland/ticket"},
    {"name": "에버랜드 체험 프로그램", "url": "https://www.everland.com/everland/promotion/exp-program"},
    {"name": "에버랜드 메인 홈 배너", "url": "https://www.everland.com/everland/home/main"},
    {"name": "에버랜드 공식 보도자료", "url": "https://www.witheverland.com/category/PRESS%20CENTER/%EB%B3%B4%EB%8F%84%EC%9E%90%EB%A3%8C"},
    {"name": "캐리비안베이 공지사항", "url": "https://www.everland.com/caribbeanbay/announcement"},
    {"name": "캐리비안베이 이벤트", "url": "https://www.everland.com/caribbeanbay/event"},
    {"name": "캐리비안베이 메인 홈 배너", "url": "https://www.everland.com/caribbeanbay/home/main"},
    {"name": "홈브리지 공지사항", "url": "https://www.everland.com/homebridge/announcement"}
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"전송 실패: {e}")

def get_hash(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return None
        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup(["script", "style", "meta", "noscript"]):
            tag.extract()
        text = soup.get_text(separator=" ", strip=True)
        return hashlib.md5(text.encode("utf-8")).hexdigest()
    except Exception as e:
        print(f"조회 실패 ({url}): {e}")
        return None

send_telegram("[에버랜드 24시간 실시간 모니터링 가동]\n상시 감시 시스템이 정상 시작되었습니다!")

saved_states = {}

for item in TARGETS:
    sig = get_hash(item["url"])
    if sig:
        saved_states[item["name"]] = sig

print(f"초기 세팅 완료: {len(saved_states)}개 채널 감시 시작")

while True:
    time.sleep(90)
    for item in TARGETS:
        name = item["name"]
        url = item["url"]
        new_sig = get_hash(url)
        if not new_sig:
            continue
        old_sig = saved_states.get(name)
        if old_sig and old_sig != new_sig:
            saved_states[name] = new_sig
            msg = f"[업데이트 감지!]\n\n구분: {name}\n새로운 공지 또는 변경 사항이 등록되었습니다.\n바로가기: {url}"
            send_telegram(msg)
            print(f"[{name}] 감지 완료")
        elif not old_sig:
            saved_states[name] = new_sig
