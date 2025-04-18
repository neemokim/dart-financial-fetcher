import pandas as pd
import re
import requests
import xml.etree.ElementTree as ET

# (주) 등 제거
def process_corp_info(df):
    cleaned_names = df.iloc[:, 0].str.replace(r"[\(주\)\s]|주식회사", "", regex=True)
    excluded_names = df.iloc[:, 0].str.extract(r"(\(주\)|주식회사)")[0].dropna().unique().flatten()
    return cleaned_names, excluded_names

# DART 전체 기업 목록에서 사업자명 매칭
def get_corp_code(corp_name, corp_list_df):
    match = corp_list_df[corp_list_df["corp_name"] == corp_name]
    if not match.empty:
        return match.iloc[0]["corp_code"]
    return None

# DART에서 사업보고서 숫자 가져오기
def get_dart_report_data(cleaned_names, year, report_type, api_key):
    # 기업 리스트 가져오기 (파일 저장 없이 바로 파싱)
    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={api_key}"
    response = requests.get(url)
    root = ET.fromstring(response.content)  # ✅ 바로 content로 파싱

    corp_list = []
    for corp in root.iter("list"):
        corp_list.append({
            "corp_code": corp.findtext("corp_code"),
            "corp_name": corp.findtext("corp_name")
        })
    corp_list_df = pd.DataFrame(corp_list)

    results = []
    for name in cleaned_names[:5]:  # 최대 5개만
        corp_code = get_corp_code(name, corp_list_df)
        if corp_code:
            url = (
                f"https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
                f"?crtfc_key={api_key}&corp_code={corp_code}&bsns_year={year}&reprt_code={report_type}"
            )
            r = requests.get(url).json()
            fs = {item["account_nm"]: item["thstrm_amount"] for item in r.get("list", [])}

            results.append({
                "사업자명": name,
                "자본총계": fs.get("자본총계", "없음"),
                "부채총계": fs.get("부채총계", "없음"),
                "매출액": fs.get("매출액", "없음"),
                "영업이익": fs.get("영업이익", "없음")
            })
        else:
            results.append({"사업자명": name, "조회결과 없음": "매칭 실패"})

    return pd.DataFrame(results)


    results = []
    for name in cleaned_names[:5]:  # 최대 5개만
        corp_code = get_corp_code(name, corp_list_df)
        if corp_code:
            url = (
                f"https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
                f"?crtfc_key={api_key}&corp_code={corp_code}&bsns_year={year}&reprt_code={report_type}"
            )
            r = requests.get(url).json()
            fs = {item["account_nm"]: item["thstrm_amount"] for item in r.get("list", [])}

            results.append({
                "사업자명": name,
                "자본총계": fs.get("자본총계", "없음"),
                "부채총계": fs.get("부채총계", "없음"),
                "매출액": fs.get("매출액", "없음"),
                "영업이익": fs.get("영업이익", "없음")
            })
        else:
            results.append({"사업자명": name, "조회결과 없음": "매칭 실패"})

    return pd.DataFrame(results)
