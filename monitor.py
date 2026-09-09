import os
import re
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
HISTORY_FILE = "latest_notice_id.txt"
TARGET_URL = "https://www.everland.com/everland/announcement"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.everland.com/"
}

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("[오류] TELEGRAM_TOKEN 또는 CHAT_ID가 설정되지 않았습니다.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        print("[성공] 텔레그램 메시지 발송 완료")
    except Exception as e:
        print(f"[실패] 텔레그램 전송 실패: {e}")

def main():
    try:
        res = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"[오류] 웹페이지 요청 실패: {e}")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    
    # 에버랜드 공지사항 고유 링크 형식(/announcement/CNT-...) 우선 탐색
    notice_links = soup.find_all("a", href=re.compile(r"/announcement/CNT-", re.IGNORECASE))
    
    # 만약 패턴이 매칭되지 않으면 리스트 안의 모든 공지 링크 탐색
    if not notice_links:
        notice_links = [
            a for a in soup.select("ul li a, div.list a, a[href*='announcement']")
            if "/announcement" in a.get("href", "") and a.get("href") != "/everland/announcement"
        ]

    if not notice_links:
        print("[오류] 공지사항 목록 요소를 찾지 못했습니다.")
        # 디버깅용 페이지 타이틀 확인
        print("페이지 타이틀:", soup.title.get_text() if soup.title else "없음")
        return

    top_notice = notice_links[0]
    title = top_notice.get_text(separator=" ", strip=True)
    href = top_notice.get("href", "").strip()

    if href.startswith("http"):
        link = href
    else:
        link = "https://www.everland.com" + href

    current_id = link if link else title

    saved_id = ""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            saved_id = f.read().strip()

    # 첫 실행: 최신 공지를 기준점으로 저장하고 알림 전송
    if not saved_id:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write(current_id)
        msg = f"<b>[에버랜드 공지 알리미 정상 가동]</b>\n\n📌 <b>현재 최신 공지:</b>\n{title}\n\n🔗 <a href='{link}'>공지 확인하기</a>"
        send_telegram(msg)
        print(f"[초기화 완료] 기준 공지: {title}")
        return

    # 새로운 공지가 올라온 경우
    if current_id != saved_id:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write(current_id)
        msg = f"🚨 <b>[에버랜드 새 공지 등록!]</b>\n\n📌 <b>제목:</b> {title}\n🔗 <a href='{link}'>새 공지 바로가기</a>"
        send_telegram(msg)
        print(f"[알림 발송] 새 공지 등록: {title}")
    else:
        print("[확인] 새로운 공지사항이 없습니다. (정상 모니터링 중)")

if __name__ == "__main__":
    main()
