import os
import hashlib
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 에버랜드 및 캐리비안베이 실제 데이터 API 엔드포인트 목록
TARGETS = [
    {
        "name": "에버랜드 이벤트 목록",
        "url": "https://www.everland.com/api/everland/events",
        "fallback_url": "https://www.everland.com/everland/event",
        "link": "https://www.everland.com/everland/event"
    },
    {
        "name": "에버랜드 공지사항",
        "url": "https://www.everland.com/api/everland/announcements",
        "fallback_url": "https://www.everland.com/everland/announcement",
        "link": "https://www.everland.com/everland/announcement"
    },
    {
        "name": "에버랜드 티켓/프로모션",
        "url": "https://www.everland.com/api/everland/tickets",
        "fallback_url": "https://www.everland.com/everland/ticket",
        "link": "https://www.everland.com/everland/ticket"
    },
    {
        "name": "캐리비안베이 이벤트",
        "url": "https://www.everland.com/api/caribbeanbay/events",
        "fallback_url": "https://www.everland.com/caribbeanbay/event",
        "link": "https://www.everland.com/caribbeanbay/event"
    },
    {
        "name": "캐리비안베이 공지사항",
        "url": "https://www.everland.com/api/caribbeanbay/announcements",
        "fallback_url": "https://www.everland.com/caribbeanbay/announcement",
        "link": "https://www.everland.com/caribbeanbay/announcement"
    },
    {
        "name": "홈브리지 공지사항",
        "url": "https://www.everland.com/api/homebridge/announcements",
        "fallback_url": "https://www.everland.com/homebridge/announcement",
        "link": "https://www.everland.com/homebridge/announcement"
    },
    {
        "name": "공식 보도자료",
        "url": "https://www.witheverland.com/category/PRESS%20CENTER/%EB%B3%B4%EB%8F%84%EC%9E%90%EB%A3%8C",
        "fallback_url": None,
        "link": "https://www.witheverland.com/category/PRESS%20CENTER/%EB%B3%B4%EB%8F%84%EC%9E%90%EB%A3%8C"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.everland.com/"
}

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"텔레그램 전송 에러: {e}")

def get_data_hash(item):
    # 1순위: 내부 JSON API 호출
    url = item["url"]
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            return hashlib.md5(res.content).hexdigest()
    except Exception:
        pass

    # 2순위: API 경로 변경 시 웹페이지 본문으로 대체
    if item.get("fallback_url"):
        try:
            res = requests.get(item["fallback_url"], headers=HEADERS, timeout=12)
            if res.status_code == 200:
                return hashlib.md5(res.content).hexdigest()
        except Exception as e:
            print(f"[{item['name']}] 수집 에러: {e}")
            return None
    return None

def monitor_loop():
    send_telegram("[에버랜드 API 실시간 모니터링 가동]\n내부 데이터 직접 감시가 정상 작동 중입니다!")
    saved_states = {}
    for item in TARGETS:
        sig = get_data_hash(item)
        if sig:
            saved_states[item["name"]] = sig
    print(f"기준값 세팅 완료: {len(saved_states)}개 채널 감시 시작")

    while True:
        time.sleep(90)
        for item in TARGETS:
            name = item["name"]
            new_sig = get_data_hash(item)
            if not new_sig:
                continue
            old_sig = saved_states.get(name)
            if old_sig and old_sig != new_sig:
                saved_states[name] = new_sig
                msg = f"[새 공지/이벤트 등록 감지!]\n\n구분: {name}\n실제 데이터 변경이 감지되었습니다.\n바로가기: {item['link']}"
                send_telegram(msg)
                print(f"[{name}] 변경 감지 완료")
            elif not old_sig:
                saved_states[name] = new_sig

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    t = threading.Thread(target=monitor_loop, daemon=True)
    t.start()
    run_server()
