import os
import hashlib
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 실제 공지가 노출되는 페이지 목록
TARGETS = [
    {"name": "에버랜드 이벤트", "url": "https://www.everland.com/everland/event"},
    {"name": "에버랜드 공지사항", "url": "https://www.everland.com/everland/announcement"},
    {"name": "에버랜드 정기권", "url": "https://www.everland.com/everland/ticket"},
    {"name": "캐리비안베이 이벤트", "url": "https://www.everland.com/caribbeanbay/event"},
    {"name": "캐리비안베이 공지사항", "url": "https://www.everland.com/caribbeanbay/announcement"},
    {"name": "홈브리지 공지사항", "url": "https://www.everland.com/homebridge/announcement"}
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"텔레그램 실패: {e}")

def check_target(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        # 응답 코드와 데이터 크기 반환
        return res.status_code, len(res.content), hashlib.md5(res.content).hexdigest()
    except Exception as e:
        return 0, str(e), None

def monitor_loop():
    time.sleep(3)
    saved_states = {}
    report_lines = []

    # 1회차 전체 점검 및 결과 생성
    for item in TARGETS:
        status, size, sig = check_target(item["url"])
        if status == 200 and sig:
            saved_states[item["name"]] = sig
            report_lines.append(f"O {item['name']}: {size} bytes")
        else:
            report_lines.append(f"X {item['name']}: 에러({status})")

    # 가동 즉시 현재 읽은 상태를 그대로 보고
    report_msg = "[진단 결과 보고]\n" + "\n".join(report_lines)
    send_telegram(report_msg)

    while True:
        time.sleep(90)
        for item in TARGETS:
            name = item["name"]
            status, size, new_sig = check_target(item["url"])
            if status != 200 or not new_sig:
                continue

            old_sig = saved_states.get(name)
            if old_sig and old_sig != new_sig:
                saved_states[name] = new_sig
                send_telegram(f"[변동 감지!]\n{name} 내용 변경됨 (크기: {size} bytes)\n{item['url']}")
            elif not old_sig:
                saved_states[name] = new_sig

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK - EVERLAND BOT RUNNING")

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
