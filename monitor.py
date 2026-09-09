import os
import re
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
HISTORY_FILE = "latest_notice_id.txt"
TARGET_URL = "https://www.everland.com/everland/announcement"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9"
}

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("[오류] TELEGRAM_TOKEN 또는 CHAT_ID 누락")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    res = requests.post(url, json=payload, timeout=10)
    print(f"텔레그램 응답 코드: {res.status_code}")

def main():
    res = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
    html_text = res.text
    soup = BeautifulSoup(html_text, "html.parser")

    # 1. 정규표현식으로 CNT- 고유 공지 ID 패턴 직접 추출
    cnt_matches = re.findall(r"CNT-[A-Za-z0-9\-]+", html_text)
    
    # 2. 링크 또는 텍스트 기반 추출 시도
    notice_links = soup.find_all("a", href=re.compile(r"/announcement/CNT-"))
    
    if notice_links:
        top = notice_links[0]
        title = top.get_text(separator=" ", strip=True) or "에버랜드 공지사항"
        href = top.get("href", "")
        link = "https://www.everland.com" + href if not href.startswith("http") else href
        current_id = href
    elif cnt_matches:
        latest_cnt = cnt_matches[0]
        title = "에버랜드 최신 공지사항 등록"
        link = f"https://www.everland.com/everland/announcement/{latest_cnt}/01"
        current_id = latest_cnt
    else:
        # 비상 감지: 공지 페이지의 핵심 본문 해시값 비교
        current_id = str(len(html_text))
        title = "에버랜드 공지사항 웹페이지 변동 감지"
        link = TARGET_URL

    saved_id = ""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            saved_id = f.read().strip()

    # 최초 실행 시 기준값 저장 및 성공 알림 발송
    if not saved_id:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write(current_id)
        msg = f"<b>[에버랜드 알리미 정상 가동]</b>\n\n현재 모니터링이 시작되었습니다.\n📌 <b>기준 공지 ID:</b> {current_id[:30]}\n🔗 <a href='{link}'>에버랜드 공지 바로가기</a>"
        send_telegram(msg)
        print("초기화 알림 발송 완료")
        return

    # 새 공지 등록 시
    if current_id != saved_id:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write(current_id)
        msg = f"🚨 <b>[에버랜드 새 공지 등록!]</b>\n\n📌 {title}\n🔗 <a href='{link}'>공지 확인하기</a>"
        send_telegram(msg)
        print("새 공지 발송 완료")
    else:
        print("공지 변동 없음")

if __name__ == "__main__":
    main()
