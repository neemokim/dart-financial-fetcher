import pandas as pd
import requests
from opendartreader_local import OpenDartReader

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
        pdf_data = extract_pdf_data(response.content)
        audit_data.append(pdf_data)
    
    return pd.DataFrame(audit_data)

def extract_pdf_data(pdf_content):
    """
    PDF 내용에서 재무 정보를 추출하는 함수입니다.
    """
    # 실제 PDF 파싱 코드 (PyPDF2, pdfminer 등을 사용 가능)
    return {"자본총계": 1000, "부채총계": 500, "매출액": 1200, "영업이익": 200}
