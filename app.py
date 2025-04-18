import streamlit as st
import pandas as pd
import requests
from opendartreader import process_corp_info, process_external_audit_report, get_dart_report_data
import datetime

# Streamlit 페이지 설정
st.set_page_config(page_title="DART 재무정보 조회", layout="wide")

# 앱 제목
st.title("DART 재무정보 통합조회기")

# DART API 키 가져오기 (Streamlit Cloud의 Secrets 탭에서 읽어옴)
api_key = st.secrets["OPEN_DART_API_KEY"]

# 사이드바 메뉴
option = st.sidebar.selectbox(
    "원하는 기능을 선택하세요:",
    ("사업보고서 기반 일반 재무제표 조회", "외부감사보고서 기반 PDF/XBRL 재무 수치 조회")
)

# 연도 선택
current_year = datetime.datetime.now().year
year = st.sidebar.selectbox("조회 연도", options=[current_year-1, current_year-2, current_year-3], index=0)

# 보고서 유형 선택
report_types = {
    "사업보고서": "11011",
    "반기보고서": "11012",
    "1분기보고서": "11013",
    "3분기보고서": "11014"
}
report_type = st.sidebar.selectbox("보고서 유형", list(report_types.keys()))

if option == "사업보고서 기반 일반 재무제표 조회":
    st.header("사업보고서 기반 일반 재무제표 조회")
    
    # 기업정보 다운로드
    uploaded_file = st.file_uploader("기업 목록 파일 업로드 (CSV 또는 Excel)", type=['csv', 'xlsx'])
    if uploaded_file:
        # 기업정보 처리
        df = pd.read_csv(uploaded_file, encoding='utf-8') if uploaded_file.name.endswith('csv') else pd.read_excel(uploaded_file)
        st.write("업로드한 기업 목록:", df.head())

        # 사업자명 전처리
        cleaned_names, excluded_names = process_corp_info(df)
        st.write("전처리된 사업자명:", cleaned_names)
        st.write("제외된 사업자명 문자열:", excluded_names)

        # 기업 코드 매칭 및 재무제표 조회
        matched_companies = get_dart_report_data(cleaned_names, year, report_types[report_type], api_key)
        st.write("매칭된 기업 목록 및 재무제표:", matched_companies)

        # 다운로드 버튼
        st.download_button("재무제표 결과 다운로드", data=matched_companies.to_csv(), file_name="revenue_report.csv")

elif option == "외부감사보고서 기반 PDF/XBRL 재무 수치 조회":
    st.header("외부감사보고서 기반 PDF/XBRL 재무 수치 조회")

    uploaded_file = st.file_uploader("기업 목록 파일 업로드 (CSV 또는 Excel)", type=['csv', 'xlsx'])
    if uploaded_file:
        df = pd.read_csv(uploaded_file, encoding='utf-8') if uploaded_file.name.endswith('csv') else pd.read_excel(uploaded_file)
        st.write("업로드한 기업 목록:", df.head())

        # 사업자명 전처리
        cleaned_names, excluded_names = process_corp_info(df)
        st.write("전처리된 사업자명:", cleaned_names)
        st.write("제외된 사업자명 문자열:", excluded_names)

        # 외부감사보고서 찾기 및 수치 조회
        audit_report_data = process_external_audit_report(cleaned_names, year, report_types[report_type], api_key)
        st.write("조회된 외부감사보고서 수치:", audit_report_data)

        # 다운로드 버튼
        st.download_button("외부감사보고서 결과 다운로드", data=audit_report_data.to_csv(), file_name="audit_report.csv")
