import fitz  # PyMuPDF
import re
import requests
import os
from bs4 import BeautifulSoup
import requests


# PDF에서 텍스트 추출
def extract_text_from_pdf_url(pdf_url):
    response = requests.get(pdf_url)
    if response.status_code != 200:
        raise Exception("PDF 다운로드 실패")

    # PDF 응답이 맞는지 체크 (응답 헤더 또는 내용 앞부분)
    if not response.headers["Content-Type"].startswith("application/pdf"):
        print("❌ PDF 아님! 응답 헤더:", response.headers)
        print("📦 응답 내용:", response.text[:200])
        raise Exception("PDF가 아닌 응답이 반환됨")

    temp_filename = "temp.pdf"
    with open(temp_filename, "wb") as f:
        f.write(response.content)

    text = ""
    with fitz.open(temp_filename) as doc:
        for page in doc:
            text += page.get_text()

    os.remove(temp_filename)
    return text

    temp_filename = "temp.pdf"
    with open(temp_filename, "wb") as f:
        f.write(response.content)

    text = ""
    with fitz.open(temp_filename) as doc:
        for page in doc:
            text += page.get_text()

    os.remove(temp_filename)
    return text

# 텍스트에서 숫자 추출 (정규표현식 사용)
def extract_financials_from_text(text):
    # 숫자 추출 정규표현식 (단위: 억 원, 조 원 등 포함 가능)
    def find_value(keyword):
        pattern = rf"{keyword}[\s:：\-]*([\d,]+)"
        match = re.search(pattern, text.replace(",", ""), re.IGNORECASE)
        return match.group(1) if match else "없음"

    return {
        "자본총계": find_value("자본총계"),
        "부채총계": find_value("부채총계"),
        "매출액": find_value("매출액"),
        "영업이익": find_value("영업이익")
    }

# 통합 함수 (PDF URL만 입력받아 결과 반환)
def parse_external_audit_pdf(pdf_url):
    try:
        text = extract_text_from_pdf_url(pdf_url)
        return extract_financials_from_text(text)
    except Exception as e:
        return {"오류": str(e)}

# rcp_no → 진짜 PDF 다운로드 URL 자동 추출 함수
def get_pdf_download_url(rcp_no):
    """
    rcp_no를 이용해 DART 보고서 페이지를 열고, PDF 다운로드 링크를 추출한다.
    """
    base_url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcp_no}"
    response = requests.get(base_url)
    
    if response.status_code != 200:
        raise Exception("DART 보고서 본문 페이지 접근 실패")

    soup = BeautifulSoup(response.text, "html.parser")
    
    # PDF 링크 찾기 (첨부파일 섹션에서)
    iframe = soup.find("iframe", {"id": "pdf"})
    if iframe and "src" in iframe.attrs:
        # 상대 경로일 경우 절대 경로로 바꿔주기
        pdf_url = "https://dart.fss.or.kr" + iframe["src"]
        return pdf_url
    else:
        raise Exception("PDF 링크를 찾을 수 없습니다.")

# 📄 "가장 최신 외부감사보고서의 rcp_no를 자동으로 가져오는 함수" 만들어줄게.
def get_latest_audit_rcp_no(corp_code, api_key):
    """
    기업코드 기준으로 최근 공시 목록 중 '감사' 포함된 보고서의 rcp_no 반환
    연도 조건 없이 전체 리스트 중에서 탐색함
    """
    url = (
        f"https://opendart.fss.or.kr/api/list.json?"
        f"crtfc_key={api_key}&corp_code={corp_code}&page_count=100"
    )
    response = requests.get(url).json()

    if response.get("status") != "000":
        raise Exception(f"공시 목록 조회 실패: {response.get('message')}")

    reports = response.get("list", [])

    for report in reports:
        if "감사" in report.get("report_nm", ""):
            return report["rcp_no"]

    raise Exception("감사보고서를 찾을 수 없습니다.")

# 이름 정규화도 포함 연도 조건 없이 감사보고서 자동 탐지
def normalize_name(name):
    return re.sub(r"[\s㈜(주)주식회사]", "", name.lower())

def get_corp_code(corp_name, corp_list_df):
    """
    (주), 공백 등을 제거한 정규화된 이름 기준으로 기업코드 조회
    """
    norm_name = normalize_name(corp_name)
    corp_list_df["norm_name"] = corp_list_df["corp_name"].apply(normalize_name)
    match = corp_list_df[corp_list_df["norm_name"] == norm_name]
    if not match.empty:
        return match.iloc[0]["corp_code"]
    return None

