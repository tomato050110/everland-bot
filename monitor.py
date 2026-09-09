import os
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
HISTORY_FILE = "latest_notice_id.txt"
TARGET_URL = "https://www.everland.com/everland/announcement"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def send_telegram(message_text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("토큰 또는 Chat ID 누락")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message_text
    }
    res = requests.post(url, json=payload, timeout=10)
    print("텔레그램 전송 상태코드:", res.status_code)

def main():
    try:
        res = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"웹페이지 요청 실패: {e}")
        return

    soup = BeautifulSoup(res.text, "html.parser")

    # 공지사항 상세 링크(/announcement/CNT-...) 탐색
    links = [a for a in soup.find_all("a", href=True) if "/announcement/CNT-" in a["href"]]

    if links:
        top_link = links[0]
        title = top_link.get_text(separator=" ", strip=True) or "에버랜드 최신 공지"
        href = top_link["href"]
        link = "https://www.everland.com" + href if href.startswith("/") else href
        current_id = href
    else:
        # 링크 태그가 없을 경우 페이지 본문 크기(바이트)를 기준으로 감지
        title = "에버랜드 공지사항 목록 업데이트"
        link = TARGET_URL
        current_id = f"PAGE_SIZE_{len(res.text)}"

    saved_id = ""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            saved_id = f.read().strip()

    # 최초 1회 실행 시 안내 메시지 전송
    if not saved_id:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write(current_id)
        msg = f"[에버랜드 공지 알리미 가동]\n모니터링이 시작되었습니다!\n\n최신 공지: {title}\n바로가기: {link}"
        send_telegram(msg)
        print("초기화 완료")
        return

    # 새 글이 올라왔을 때
    if current_id != saved_id:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write(current_id)
        msg = f"[에버랜드 새 공지 등록!]\n\n제목: {title}\n바로가기: {link}"
        send_telegram(msg)
        print("새 공지 발송 완료")
    else:
        print("변동 없음 (정상 대기)")

if __name__ == "__main__":
    main()
