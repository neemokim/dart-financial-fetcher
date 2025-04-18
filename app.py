import streamlit as st
import pandas as pd
import datetime
import time
from open_dart_reader import process_corp_info, get_dart_report_data


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

    uploaded_file = st.file_uploader("📂 기업명 파일 업로드 (CSV 또는 Excel)", type=["csv", "xlsx"])
        if uploaded_file:
    try:
        if uploaded_file.name.endswith("csv"):
            try:
                df = pd.read_csv(uploaded_file, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(uploaded_file, encoding="cp949")
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"❌ 파일을 읽을 수 없습니다: {e}")
        st.stop()

    cleaned, excluded = process_corp_info(df)



        st.write("🧹 제거된 문자열 (최대 5개):", list(excluded)[:5])
        st.write("🔍 매칭된 사업자명 (최대 5개):", cleaned.tolist()[:5])

        total = len(cleaned[:5])
        st.info(f"총 {total}개 기업의 재무제표를 조회합니다.")
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        start_time = time.time()
        results = []

        for i, name in enumerate(cleaned[:5]):
            percent = int((i + 1) / total * 100)
            elapsed = int(time.time() - start_time)
            remaining = int((elapsed / (i + 1)) * (total - i - 1)) if i > 0 else 0

            status_text.markdown(
                f"🔄 진행률: **{percent}%** | 남은 기업: **{total - i - 1}개** | 예상 남은 시간: **{remaining}초**"
            )
            progress_bar.progress(percent)

            try:
                df_result = get_dart_report_data([name], year, report_types[report_type], api_key)
                results.extend(df_result.to_dict("records"))
            except Exception as e:
                results.append({"사업자명": name, "조회결과 없음": str(e)})

        result_df = pd.DataFrame(results)
        st.success("✅ 전체 기업 조회 완료")
        st.dataframe(result_df)
        st.download_button("⬇️ 결과 다운로드 (CSV)", result_df.to_csv(index=False), file_name="dart_재무정보.csv")

    else:
        st.info("CSV 또는 Excel 파일을 업로드해 주세요.")
elif menu == "📕 외부감사보고서 조회":
    st.header("📕 외부감사보고서 기반 PDF/XBRL 수치 조회")
    st.info("🚧 현재 개발 중입니다. 추후 업데이트 예정입니다.")
