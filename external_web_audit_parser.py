import requests
from bs4 import BeautifulSoup
import re

def clean_corp_name(name):
    """
    기업명에서 (주), 주식회사, ㈜, 유한회사 등 정리
    """
    return re.sub(r"\(주\)|주식회사|㈜|주\s*|유한회사|유\s*|\(유\)", "", name).strip()

def get_latest_web_rcp_no(corp_name):
    """
    기업명을 기반으로 DART 웹에서 외부감사보고서의 rcpNo를 크롤링한다.
    """
    search_url = f"https://dart.fss.or.kr/dsap001/search.ax?textCrpNm={corp_name}"
    print(f"🌐 검색 URL: {search_url}")
    resp = requests.get(search_url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # 입력값 정제
    cleaned_input = clean_corp_name(corp_name)

    # '보고서명'에 '감사' 포함된 것 중 가장 최근 rcpNo 찾기
    links = soup.select("a[href*='rcpNo']")
    for link in links:
        title = link.get_text()
        if "감사" in title:
            # 기업명 일치 여부 검사 (링크 주변 텍스트에서 추출)
            parent = link.find_parent("td")
            if parent:
                corp_cell = parent.find_previous_sibling("td")
                if corp_cell:
                    listed_name = corp_cell.get_text(strip=True)
                    if cleaned_input in clean_corp_name(listed_name):
                        href = link["href"]
                        match = re.search(r"rcpNo=(\d+)", href)
                        if match:
                            rcp_no = match.group(1)
                            print(f"✅ rcpNo 추출 성공: {rcp_no}")
                            return rcp_no

    raise Exception("웹에서 외부감사보고서를 찾을 수 없습니다.")

def get_pdf_download_url(rcp_no):
    viewer_url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcp_no}"
    resp = requests.get(viewer_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    iframe = soup.find("iframe", {"id": "pdf"})
    if iframe and "src" in iframe.attrs:
        return "https://dart.fss.or.kr" + iframe["src"]
    raise Exception("PDF 링크를 찾을 수 없습니다.")

def parse_external_audit_pdf(pdf_url):
    import fitz  # PyMuPDF
    resp = requests.get(pdf_url)
    with open("temp.pdf", "wb") as f:
        f.write(resp.content)

    doc = fitz.open("temp.pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    # 숫자 추출 예시
    result = {}
    keywords = ["자본총계", "부채총계", "매출액", "영업이익"]
    for key in keywords:
        match = re.search(f"{key}.{{0,20}}?([\d,]+)", text)
        result[key] = match.group(1) if match else "없음"

    return result
