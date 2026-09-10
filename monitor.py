import os
import hashlib
import json
import re
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

TARGETS = [
    {
        "name": "에버랜드 공지사항",
        "url": "https://www.everland.com/everland/announcement"
    },
    {
        "name": "에버랜드 이벤트",
        "url": "https://www.everland.com/everland/event"
    },
    {
        "name": "에버랜드 티켓/정기권",
        "url": "https://www.everland.com/everland/ticket"
    },
    {
        "name": "캐리비안베이 공지사항",
        "url": "https://www.everland.com/caribbeanbay/announcement"
    },
    {
        "name": "캐리비안베이 이벤트",
        "url": "https://www.everland.com/caribbeanbay/event"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://www.everland.com/"
}

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")

def extract_content(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return f"에러: 상태코드 {res.status_code}", None

        # 1. Next.js 내부 데이터 태그(__NEXT_DATA__) 추적
        soup = BeautifulSoup(res.text, "html.parser")
        next_data_script = soup.find("script", id="__NEXT_DATA__")
        if next_data_script and next_data_script.string:
            data = json.loads(next_data_script.string)
            data_str = json.dumps(data, ensure_ascii=False)
            h = hashlib.md5(data_str.encode("utf-8")).hexdigest()
            return f"NextData 파싱 성공 (길이: {len(data_str)})", h

        # 2. 본문에 심긴 고유 콘텐츠 ID 패턴(CNT-XXXX-XXXX...) 직접 추출
        cnt_ids = re.findall(r"CNT-[A-Za-z0-9_\-]+", res.text)
        if cnt_ids:
            unique_ids = sorted(list(set(cnt_ids)))
            raw = ",".join(unique_ids)
            h = hashlib.md5(raw.encode("utf-8")).hexdigest()
            return f"콘텐츠 ID {len(unique_ids)}개 감지", h

        # 3. 만약 껍데기 HTML만 잡힌 경우 (3034 bytes 등)
        text_content = soup.get_text(separator=" ", strip=True)
        h = hashlib.md5(text_content.encode("utf-8")).hexdigest()
        return f"일반 텍스트 (길이: {len(text_content)})", h

    except Exception as e:
        return f"수집 에러: {e}", None

def monitor_loop():
    time.sleep(3)
    saved_states = {}
    report_lines = []

    # 최초 기동 시 데이터 실제 수집 진단
    for item in TARGETS:
        status_msg, sig = extract_content(item["url"])
        if sig:
            saved_states[item["name"]] = sig
            report_lines.append(f"• {item['name']}: {status_msg}")
        else:
            report_lines.append(f"• {item['name']}: {status_msg}")

    # 즉시 텔레그램으로 실제 파싱 결과 전송
    init_msg = "[실제 데이터 파싱 진단 보고]\n" + "\n".join(report_lines)
    send_telegram(init_msg)

    while True:
        time.sleep(90)
        for item in TARGETS:
            name = item["name"]
            status_msg, new_sig = extract_content(item["url"])
            if not new_sig:
                continue

            old_sig = saved_states.get(name)
            if old_sig and old_sig != new_sig:
                saved_states[name] = new_sig
                send_telegram(f"[공지/이벤트 변경 감지!]\n구분: {name}\n상태: {status_msg}\n바로가기: {item['url']}")
            elif not old_sig:
                saved_states[name] = new_sig

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK - BOT ACTIVE")

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
