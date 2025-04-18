import pandas as pd
import requests
from opendartreader import OpenDartReader
from pdfminer.high_level import extract_text

def process_corp_info(df):
    """
    사업자명에서 '(주)', '주식회사' 등을 제외하고, 이를 화면에 표시하는 함수입니다.
    """
    cleaned_names = df.iloc[:, 0].str.replace(r"[\(주\)주식회사]", "", regex=True)
    excluded_names = df.iloc[:, 0].str.extract(r"([\(주\)주식회사]+)").dropna().unique().flatten()
    return cleaned_names, excluded_names

def get_dart_report_data(cleaned_names, year, report_type, api_key):
    """
    DART API를 사용하여 재무제표를 동적으로 조회하는 함수입니다.
    """
    # DART API 설정 (API 키 필요)
    dart = OpenDartReader(api_key)
    
    matched_companies = []
    for name in cleaned_names:
        corp_info = dart.get_corp_code(corp_name=name)
        if corp_info:
            # 사업보고서를 조회하여 필요한 재무 수치 추출
            report_data = dart.get_finstate(corp_code=corp_info['corp_code'], bsns_year=year, reprt_code=report_type)
            matched_companies.append({
                '사업자명': name,
                '자본총계': report_data.get('capital', '없음'),
                '부채총계': report_data.get('liabilities', '없음'),
                '매출액': report_data.get('sales', '없음'),
                '영업이익': report_data.get('operating_income', '없음')
            })
        else:
            matched_companies.append({'사업자명': name, '조회결과 없음': '해당 기업 없음'})
    
    return pd.DataFrame(matched_companies)

def process_external_audit_report(cleaned_names, year, report_type, api_key):
    """
    외부감사보고서의 PDF/XBRL 파일을 다운로드하고 필요한 재무 수치를 추출하는 함수입니다.
    """
    audit_data = []
    for name in cleaned_names:
        # 외부 감사 대상 기업의 보고서를 찾고 PDF를 다운로드하여 파싱
        response = requests.get(f'https://external_audit_report_link/{name}')
        
        # PDF 파일이 정상적으로 다운로드 되었는지 확인
        if response.status_code == 200:
            pdf_data = extract_pdf_data(response.content)
            audit_data.append(pdf_data)
        else:
            audit_data.append({'사업자명': name, '조회결과 없음': 'PDF 다운로드 실패'})
    
    return pd.DataFrame(audit_data)

def extract_pdf_data(pdf_content):
    """
    PDF 내용에서 재무 정보를 추출하는 함수입니다.
    """
    # PDF에서 텍스트 추출
    text = extract_text(pdf_content)
    
    # 추출한 텍스트에서 자본총계, 부채총계 등을 정규식으로 찾아 반환
    capital = extract_financial_value(text, "자본총계")
    liabilities = extract_financial_value(text, "부채총계")
    sales = extract_financial_value(text, "매출액")
    operating_income = extract_financial_value(text, "영업이익")
    
    return {
        "자본총계": capital,
        "부채총계": liabilities,
        "매출액": sales,
        "영업이익": operating_income
    }

def extract_financial_value(text, keyword):
    """
    텍스트에서 특정 키워드(자본총계, 부채총계 등)를 찾아서 그에 해당하는 값을 추출하는 함수입니다.
    """
    import re
    pattern = re.compile(rf"{keyword}\s*[:：]?\s*([\d,]+)")
    match = pattern.search(text)
    
    if match:
        # 숫자 부분을 반환
        return int(match.group(1).replace(",", ""))
    return '없음'
