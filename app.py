import streamlit as st
import pandas as pd
import datetime
from open_dart_reader import process_corp_info, get_dart_report_data

# 🎯 API 키 (Streamlit Cloud의 secrets에서 가져옴)
api_key = st.secrets["OPEN_DART_API_KEY"]

# 🗓️ 기본 조회 조건
current_year = datetime.datetime.now().year
year = st.sidebar.selectbox("조회 연도", [str(current_year - i) for i in range(3)])
report_types = {
    "사업보고서": "11011",
    "반기보고서": "11012",
    "1분기보고서": "11013",
    "3분기보고서": "11014"
}
report_type = st.sidebar.selectbox("보고서 유형", list(report_types.keys()))

# 📤 파일 업로드
st.title("📊 사업보고서 기반 재무제표 조회")
uploaded_file = st.file_uploader("기업명 리스트 업로드 (CSV 또는 Excel)", type=["csv", "xlsx"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith("csv") else pd.read_excel(uploaded_file)
        st.success("✅ 파일 업로드 성공")
    except Exception as e:
        st.error(f"❌ 파일 읽기 실패: {e}")
        st.stop()

    cleaned_names, excluded = process_corp_info(df)
    st.write("🔍 전처리된 사업자명:", cleaned_names.tolist()[:5])
    st.write("🧹 제외된 문자열:", list(excluded))

    if st.button("📈 재무정보 조회 시작"):
        with st.spinner("조회 중입니다..."):
            result_df = get_dart_report_data(
                cleaned_names, year, report_types[report_type], api_key
            )
        st.success("🎉 조회 완료")
        st.dataframe(result_df)
        st.download_button("⬇️ 결과 다운로드", result_df.to_csv(index=False), file_name="dart_재무정보.csv")

else:
    st.info("📎 CSV 또는 Excel 파일을 업로드하세요.")
