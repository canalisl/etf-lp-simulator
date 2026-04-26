"""
배포용 데모 데이터 사전 생성 스크립트.
PLUS 5종목 + 인기 비교용 5종목을 CSV로 저장.
로컬에서 한 번만 실행하면 됨.
"""
import json
from pathlib import Path

from pykrx import stock
from lp_calc import PLUS_ETFS

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# PLUS 라인업 + 인기 비교 종목
DEMO_TICKERS = {
    **PLUS_ETFS,
    "069500": "KODEX 200",
    "360750": "TIGER 미국S&P500",
    "114800": "KODEX 인버스",
    "133690": "TIGER 미국나스닥100",
    "253150": "KODEX 레버리지",
}

START = "20250101"   # 약 1년 4개월치
END = "20260424"

names = {}
for ticker, name in DEMO_TICKERS.items():
    print(f"[{ticker}] {name} 다운로드 중...")
    try:
        df = stock.get_etf_ohlcv_by_date(START, END, ticker)
        if df.empty:
            print(f"  └ 데이터 없음 - 스킵")
            continue
        csv_path = DATA_DIR / f"{ticker}.csv"
        df.to_csv(csv_path, encoding="utf-8-sig")
        names[ticker] = name
        print(f"  └ {len(df)}행 → {csv_path.name}")
    except Exception as e:
        print(f"  └ 실패: {e}")

names_path = DATA_DIR / "etf_names.json"
with open(names_path, "w", encoding="utf-8") as f:
    json.dump(names, f, ensure_ascii=False, indent=2)

print(f"\n✅ {len(names)}개 종목 캐시 완료 → {DATA_DIR}")
print(f"✅ 종목명 매핑 → {names_path.name}")