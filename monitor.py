import os
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
HISTORY_FILE = "latest_notice_id.txt"
TARGET_URL = "https://www.everland.com/everland/news/notice/list"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass

def main():
    try:
        res = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"웹페이지 요청 실패: {e}")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    notices = soup.select(".board_list tbody tr, .notice_list li, .list_wrap a")
    if not notices:
        print("목록을 찾지 못했습니다.")
        return

    top = notices[0]
    title = top.get_text(strip=True)
    link = top.get("href") or (top.find("a")["href"] if top.find("a") else "")
    if link and not link.startswith("http"):
        link = "https://www.everland.com" + link

    current_id = link if link else title

    saved_id = ""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            saved_id = f.read().strip()

    if not saved_id:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write(current_id)
        send_telegram(f"<b>[에버랜드 알리미 가동]</b>\n현재 최신 공지:\n{title}")
        print("초기화 완료")
        return

    if current_id != saved_id:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write(current_id)
        send_telegram(f"<b>[에버랜드 새 공지 등록]</b>\n\n📌 {title}\n🔗 {link}")
        print("새 공지 전송 완료")
    else:
        print("새 공지 없음")

if __name__ == "__main__":
    main()
