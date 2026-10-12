import os, hashlib, json, requests
from playwright.sync_api import sync_playwright

T=[{"name":"에버랜드 이벤트","url":"https://www.everland.com/everland/event"},{"name":"에버랜드 공지사항","url":"https://www.everland.com/everland/announcement"},{"name":"에버랜드 정기권","url":"https://www.everland.com/everland/ticket"},{"name":"캐리비안베이 이벤트","url":"https://www.everland.com/caribbeanbay/event"},{"name":"캐리비안베이 공지사항","url":"https://www.everland.com/caribbeanbay/announcement"},{"name":"홈브리지 공지사항","url":"https://www.everland.com/homebridge/announcement"}]
S="latest_targets_state.json"

def run():
    s={}
    if os.path.exists(S):
        try:
            with open(S,"r",encoding="utf-8") as f: s=json.load(f)
        except: s={}
    ns={}
    c=[]
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True)
        pg=b.new_page()
        for i in T:
            try:
                pg.goto(i["url"],wait_until="domcontentloaded",timeout=30000)
                pg.wait_for_timeout(3000)
                e=pg.query_selector("main")
                t=e.inner_text() if e else pg.inner_text("body")
                h=hashlib.md5(" ".join(t.split()).encode("utf-8")).hexdigest()
                ns[i["name"]]=h
                if i["name"] in s and s[i["name"]]!=h:
                    c.append(f"• [{i['name']}] 변동 발생!\n{i['url']}")
            except:
                if i["name"] in s: ns[i["name"]]=s[i["name"]]
        b.close()
    if c and os.environ.get("TELEGRAM_TOKEN") and os.environ.get("CHAT_ID"):
        try:
            requests.post(f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_TOKEN')}/sendMessage",json={"chat_id":os.environ.get("CHAT_ID"),"text":"[변동 알림]\n\n"+"\n".join(c)},timeout=10)
        except: pass
    with open(S,"w",encoding="utf-8") as f: json.dump(ns,f,ensure_ascii=False,indent=2)

if __name__=="__main__": run()
