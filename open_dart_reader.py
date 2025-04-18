import pandas as pd
import re
import requests
import zipfile
import io
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

# DART에서 재무제표 조회 (fnlttMultiAcnt.json 사용)
def extract_financial_values(data_list):
    fs = {}
    for item in data_list:
        name = item["account_nm"]
        value = item["thstrm_amount"]
        if "자본총계" in name or "자본" in name:
            fs["자본총계"] = value
        elif "부채총계" in name or "부채" in name:
            fs["부채총계"] = value
        elif "매출" in name or "영업수익" in name:
            fs["매출액"] = value
        elif "영업이익" in name:
            fs["영업이익"] = value
    return fs

def get_dart_report_data(cleaned_names, year, report_type, api_key):
    # 1. 기업 리스트 가져오기 (ZIP)
    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={api_key}"
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        with z.open("CORPCODE.xml") as xml_file:
            xml_data = xml_file.read().decode("utf-8")
    root = ET.fromstring(xml_data)
    corp_list = [
        {
            "corp_code": corp.findtext("corp_code"),
            "corp_name": corp.findtext("corp_name")
        }
        for corp in root.iter("list")
    ]
    corp_list_df = pd.DataFrame(corp_list)

    results = []
    for name in cleaned_names[:5]:
        corp_code = get_corp_code(name, corp_list_df)
        if not corp_code:
            results.append({"사업자명": name, "조회결과 없음": "코드 매칭 실패"})
            continue

        found = False
        for fs_div in ["CFS", "OFS"]:  # 연결 → 일반 순서로 시도
            url = (
                f"https://opendart.fss.or.kr/api/fnlttMultiAcnt.json"
                f"?crtfc_key={api_key}&corp_code={corp_code}&bsns_year={year}"
                f"&reprt_code={report_type}&fs_div={fs_div}"
            )
            r = requests.get(url).json()
            if r.get("status") == "000":
                fs = extract_financial_values(r.get("list", []))
                results.append({
                    "사업자명": name,
                    "보고서유형": "연결" if fs_div == "CFS" else "일반",
                    "자본총계": fs.get("자본총계", "없음"),
                    "부채총계": fs.get("부채총계", "없음"),
                    "매출액": fs.get("매출액", "없음"),
                    "영업이익": fs.get("영업이익", "없음")
                })
                found = True
                break  # 연결 성공하면 일반은 안 봐도 됨

        if not found:
            results.append({"사업자명": name, "조회결과 없음": "재무정보 없음"})

    return pd.DataFrame(results)


    # 2. 조회 반복
    results = []
    for name in cleaned_names[:5]:  # 최대 5개만
        corp_code = get_corp_code(name, corp_list_df)
        if not corp_code:
            results.append({"사업자명": name, "조회결과 없음": "코드 매칭 실패"})
            continue

        url = (
            f"https://opendart.fss.or.kr/api/fnlttMultiAcnt.json"
            f"?crtfc_key={api_key}&corp_code={corp_code}&bsns_year={year}"
            f"&reprt_code={report_type}&fs_div=CFS"
        )
        r = requests.get(url).json()

        if r.get("status") != "000":
            results.append({"사업자명": name, "조회결과 없음": r.get("message", "알 수 없는 오류")})
            continue

        fs = {item["account_nm"]: item["thstrm_amount"] for item in r.get("list", [])}

        results.append({
            "사업자명": name,
            "자본총계": fs.get("자본총계", "없음"),
            "부채총계": fs.get("부채총계", "없음"),
            "매출액": fs.get("매출액", "없음"),
            "영업이익": fs.get("영업이익", "없음")
        })

    return pd.DataFrame(results)
