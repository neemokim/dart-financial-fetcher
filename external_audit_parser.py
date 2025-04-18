# external_audit_parser.py

import requests
import fitz  # PyMuPDF
import re

# 샘플 키워드 기반 숫자 추출 함수
def extract_financial_values_from_text(text):
    result = {
        "자본총계": "없음",
        "부채총계": "없음",
        "매출액": "없음",
        "영업이익": "없음"
    }

    patterns = {
        "자본총계": r"자본\s*총계\s*[:：]?\s*([0-9,]+)",
        "부채총계": r"부채\s*총계\s*[:：]?\s*([0-9,]+)",
        "매출액": r"매출\s*액\s*[:：]?\s*([0-9,]+)",
        "영업이익": r"영업\s*이익\s*[:：]?\s*([0-9,]+)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text.replace("\n", ""), re.IGNORECASE)
        if match:
            result[key] = match.group(1)

    return result

# PDF URL에서 텍스트 추출 후 수치 추출
def parse_pdf_from_url(pdf_url):
    try:
        response = requests.get(pdf_url)
        doc = fitz.open(stream=response.content, filetype="pdf")

        full_text = ""
        for page in doc:
            full_text += page.get_text()

        return extract_financial_values_from_text(full_text)
    except Exception as e:
        return {"error": str(e)}
