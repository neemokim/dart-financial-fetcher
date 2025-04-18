import pandas as pd
import re
from opendartreader import OpenDartReader

def process_corp_info(df):
    # (주), 주식회사 등 제거
    cleaned_names = df.iloc[:, 0].str.replace(r"[\(주\)\s]|주식회사", "", regex=True)
    excluded_names = df.iloc[:, 0].str.extract(r"(\(주\)|주식회사)").dropna().unique().flatten()
    return cleaned_names, excluded_names

def get_dart_report_data(cleaned_names, year, report_type, api_key):
    dart = OpenDartReader(api_key)
    results = []

    for name in cleaned_names[:5]:  # 최대 5개 샘플
        try:
            corp_code = dart.find_corp_code(name)
            fs = dart.finstate(corp_code, year, reprt_code=report_type)
            results.append({
                '사업자명': name,
                '자본총계': fs.get('자본총계', '없음'),
                '부채총계': fs.get('부채총계', '없음'),
                '매출액': fs.get('매출액', '없음'),
                '영업이익': fs.get('영업이익', '없음')
            })
        except Exception as e:
            results.append({'사업자명': name, '조회결과 없음': str(e)})
    
    return pd.DataFrame(results)
