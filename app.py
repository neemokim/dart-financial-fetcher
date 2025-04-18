import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="DART 재무정보 통합조회기", layout="wide")
st.title("📊 DART 재무정보 통합조회기")

st.markdown("""
이 앱은 두 가지 기능을 제공합니다:
1. 사업보고서 기반 일반 재무제표 조회  
2. 외부감사보고서 기반 PDF/XBRL 재무 수치 조회  

왼쪽 사이드바에서 원하는 기능을 선택하세요.
""")

api_key = st.secrets["OPEN_DART_API_KEY"]
menu = st.sidebar.radio("기능 선택", ["📘 사업보고서 조회", "📕 외부감사보고서 조회"])

# 공통 입력
current_year = datetime.datetime.now().year
year = st.sidebar.selectbox("조회 연도", [str(current_year - i) for i in range(3)])
report_types = {
    "사업보고서": "11011",
    "반기보고서": "11012",
    "1분기보고서": "11013",
    "3분기보고서": "11014"
}
report_type = st.sidebar.selectbox("보고서 유형", list(report_types.keys()))

if menu == "📘 사업보고서 조회":
    st.header("📘 사업보고서 기반 일반 재무제표 조회")
    
    if st.button("1️⃣ 기업정보 다운로드"):
        st.success("✅ 기업정보 다운로드 완료 (가정)")

    uploaded_file = st.file_uploader("2️⃣ 기업명 파일 업로드 (CSV 또는 Excel)", type=["csv", "xlsx"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith("csv") else pd.read_excel(uploaded_file)
        cleaned, excluded = process_corp_info(df)
        st.write("3️⃣ 제거된 문자열 (최대 5개):", list(excluded)[:5])
        st.write("4️⃣ 매칭된 기업명 (최대 5개):", cleaned.tolist()[:5])
        
        with st.spinner("📡 사업보고서 조회 중..."):
            result_df = get_dart_report_data(cleaned, year, report_types[report_type], api_key)
        st.success("✅ 조회 완료!")
        st.write("5️⃣ 재무정보 샘플:")
        st.dataframe(result_df)
        
        st.download_button("6️⃣ 결과 다운로드 (CSV)", result_df.to_csv(index=False), file_name="dart_재무정보.csv")

elif menu == "📕 외부감사보고서 조회":
    st.header("📕 외부감사보고서 기반 PDF/XBRL 수치 조회")
    st.info("🚧 현재 개발 중입니다. 추후 업데이트 예정입니다.")
