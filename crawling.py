import os, csv, re, requests
from bs4 import BeautifulSoup

BASE_LIST = "https://pa.go.kr/online_contents/archive/president_speechIndex.jsp"
BASE_DETAIL = "https://pa.go.kr/online_contents/archive/president_speechIndex.jsp"
PARAMS = {"activePresident": "김대중", "pageIndex": 1}
HEADERS = {"User-Agent": "Mozilla/5.0"}

SAVE_DIR = "data/speeches/txt_test"
META_PATH = "data/metadata/documents_test.csv"
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(META_PATH), exist_ok=True)

session = requests.Session()
session.headers.update(HEADERS)

def get_soup(url, params=None, referer=None):
    headers = HEADERS.copy()
    if referer:
        headers["Referer"] = referer
    r = session.get(url, params=params, headers=headers)
    r.raise_for_status()
    r.encoding = "utf-8"
    return BeautifulSoup(r.text, "lxml")

# 목록 페이지 먼저
soup = get_soup(BASE_LIST, PARAMS)
rows = []

for tr in soup.select("table.board-list tr"):
    a = tr.select_one("a[href*='spMode=view']")
    if not a:
        continue
    title = a.get_text(strip=True)
    href = a["href"]
    detail_url = BASE_DETAIL + href
    txt = tr.get_text(" ", strip=True)
    m = re.search(r"\d{4}\.\d{2}\.\d{2}", txt)
    date = m.group(0) if m else ""
    rows.append((title, date, detail_url))

print(f"[DEBUG] {len(rows)}개 항목 발견")

# 상세 요청 (세션+Referer)
title, date, url = rows[0]
detail_soup = get_soup(url, referer=BASE_LIST)
print("✅ 상세 페이지 길이:", len(detail_soup.text))

content_box = detail_soup.select_one("td.content")
if content_box:
    print("본문 일부:", content_box.get_text(strip=True)[:200])
else:
    print("❌ 본문을 찾지 못했습니다.")
