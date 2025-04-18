import fitz  # PyMuPDF
import re
import requests
import os

# PDF에서 텍스트 추출
def extract_text_from_pdf_url(pdf_url):
    response = requests.get(pdf_url)
    if response.status_code != 200:
        raise Exception("PDF 다운로드 실패")

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
