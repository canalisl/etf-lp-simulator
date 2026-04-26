"""
ETF LP 시뮬레이터 - 데이터 수집 및 괴리율 계산 모듈
한화자산운용 PLUS 브랜드 ETF 분석에 특화
"""
import os
import json
import functools
from pathlib import Path

# import functools
import pandas as pd
import numpy as np
from pykrx import stock

# 환경변수로 모드 전환
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"
DATA_DIR = Path(__file__).parent / "data"


# ============================================================
# 분석 대상: 한화자산운용 PLUS 브랜드 ETF 5종
# ============================================================
PLUS_ETFS = {
    "0000J0": "PLUS 한화그룹주",                    # ★ 한화투자증권 그룹사 ETF
    "301400": "PLUS 코스닥150",                      # 국내 대표지수 (안정적 LP)
    "213630": "PLUS 미국다우존스고배당주(합성 H)",  # 해외+환헷지 (시차 영향)
    "461910": "PLUS 미국테크TOP10레버리지(합성)",   # 해외+레버리지 (변동성 큼)
    "457990": "PLUS 태양광&ESS",                     # 테마 (거래량 변동)
}


# def fetch_etf_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
#     """
#     pykrx로 특정 ETF의 OHLCV + NAV 데이터를 가져온다.

#     Args:
#         ticker: ETF 종목코드 (예: '0000J0')
#         start_date: 시작일 'YYYYMMDD' 형식
#         end_date: 종료일 'YYYYMMDD' 형식

#     Returns:
#         DataFrame. 컬럼: NAV, 시가, 고가, 저가, 종가, 거래량, 거래대금, 기초지수
#     """
#     df = stock.get_etf_ohlcv_by_date(start_date, end_date, ticker)
#     return df
def fetch_etf_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    ETF OHLCV+NAV 데이터 조회.
    - DEMO_MODE=1: 로컬 CSV 캐시에서 읽음 (배포 환경)
    - 그 외: pykrx로 KRX 실시간 호출 (로컬 개발)
    """
    if DEMO_MODE:
        csv_path = DATA_DIR / f"{ticker}.csv"
        if not csv_path.exists():
            return pd.DataFrame()
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        df.index.name = "날짜"
        # 기간 필터링
        try:
            start = pd.to_datetime(start_date, format="%Y%m%d")
            end = pd.to_datetime(end_date, format="%Y%m%d")
            return df.loc[start:end]
        except Exception:
            return df

    # 라이브 모드 (로컬)
    return stock.get_etf_ohlcv_by_date(start_date, end_date, ticker)



def add_premium_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrame에 '괴리율(%)' 컬럼 추가.
    공식: (시장가 - NAV) / NAV × 100
    양수=프리미엄(고평가), 음수=디스카운트(저평가)
    """
    df = df.copy()
    df['괴리율(%)'] = (df['종가'] - df['NAV']) / df['NAV'] * 100
    return df


def classify_state(premium_pct: float, threshold: float = 0.3) -> str:
    """
    괴리율 상태 분류.

    Returns:
        'PREMIUM'  - LP는 매도호가를 낮춰 격차를 좁혀야 함
        'DISCOUNT' - LP는 매수호가를 올려 격차를 좁혀야 함
        'NORMAL'   - 정상 범위, 호가 유지
    """
    if premium_pct > threshold:
        return 'PREMIUM'
    elif premium_pct < -threshold:
        return 'DISCOUNT'
    else:
        return 'NORMAL'


def summary_stats(df: pd.DataFrame) -> dict:
    """괴리율 통계 요약 (평균/표준편차/최저/최고/관측일수)."""
    if '괴리율(%)' not in df.columns:
        df = add_premium_column(df)
    s = df['괴리율(%)']
    return {
        '평균(%)': round(s.mean(), 4),
        '표준편차(%)': round(s.std(), 4),
        '최저(%)': round(s.min(), 4),
        '최고(%)': round(s.max(), 4),
        '관측일수': len(s),
    }

# ============================================================
# KRX ETF 호가단위 (Tick Size) 테이블
# ============================================================
TICK_SIZE_TABLE = [
    (2000, 1),
    (5000, 5),
    (20000, 10),
    (50000, 50),
    (200000, 100),
    (500000, 500),
    (float('inf'), 1000),
]


def get_tick_size(price: float) -> int:
    """KRX ETF 호가단위 계산 (가격대별)."""
    for upper_bound, tick in TICK_SIZE_TABLE:
        if price < upper_bound:
            return tick
    return 1000


def round_to_tick(price: float, tick: int = None) -> int:
    """가격을 가장 가까운 호가단위로 반올림."""
    if tick is None:
        tick = get_tick_size(price)
    return int(round(price / tick) * tick)


def recommend_lp_quotes(
    nav: float,
    last_close: float,
    threshold: float = 0.3,
    base_spread_bps: int = 20,
) -> dict:
    """
    LP 추천 호가 계산.

    원리:
    - PREMIUM (시장가>NAV): 매도호가를 NAV 가까이 제시 → 시장가 하향 유도
    - DISCOUNT (시장가<NAV): 매수호가를 NAV 가까이 제시 → 시장가 상향 유도
    - NORMAL : NAV 기준 대칭 스프레드 유지

    Args:
        nav: 현재 NAV
        last_close: 직전 종가 (시장가 기준)
        threshold: 정상 범위 임계치(%)
        base_spread_bps: 기본 스프레드(bps). 20bps = 0.2% (예: 4만원 → 80원)

    Returns:
        dict: 추천 호가 + LP 액션 가이드
    """
    premium_pct = (last_close - nav) / nav * 100
    state = classify_state(premium_pct, threshold)

    base_spread = nav * (base_spread_bps / 10000)
    half_spread = base_spread / 2

    if state == 'PREMIUM':
        # 매도호가 적극 (NAV에 더 가까이), 매수호가 보수적
        ask_raw = nav + half_spread * 0.5
        bid_raw = nav - half_spread * 1.5
        action = "🔴 PREMIUM: 매도호가를 NAV 근처로 적극 제시. 시장가 하향 유도."
    elif state == 'DISCOUNT':
        # 매수호가 적극 (NAV에 더 가까이), 매도호가 보수적
        bid_raw = nav - half_spread * 0.5
        ask_raw = nav + half_spread * 1.5
        action = "🔵 DISCOUNT: 매수호가를 NAV 근처로 적극 제시. 시장가 상향 유도."
    else:
        # 대칭 스프레드
        bid_raw = nav - half_spread
        ask_raw = nav + half_spread
        action = "🟢 NORMAL: NAV 기준 대칭 호가 유지."

    bid = round_to_tick(bid_raw)
    ask = round_to_tick(ask_raw)

    return {
        '현재_NAV': round(nav, 2),
        '직전_시장가': int(last_close),
        '괴리율(%)': round(premium_pct, 4),
        '상태': state,
        '추천_매수호가(bid)': bid,
        '추천_매도호가(ask)': ask,
        '스프레드': ask - bid,
        '스프레드(bps)': round((ask - bid) / nav * 10000, 1),
        '호가단위': get_tick_size(nav),
        'LP_액션': action,
    }

def build_synthetic_orderbook(
    lp_bid: int,
    lp_ask: int,
    n_levels: int = 5,
    tick: int = None,
    volume_seed: int = 42,
) -> dict:
    """
    가상 호가창 생성 (시각화용).

    LP가 깐 1단계 매수/매도 호가를 기준으로,
    추가 4단계의 가상 잔량을 생성한다.
    시드 고정으로 같은 입력 → 같은 호가창 (재현성).

    Args:
        lp_bid: LP 추천 매수호가 (1단계 매수)
        lp_ask: LP 추천 매도호가 (1단계 매도)
        n_levels: 위/아래 각 호가 단계 수 (LP 호가 포함)
        tick: 호가단위. 미지정 시 자동 계산.
        volume_seed: 잔량 무작위 생성 시드

    Returns:
        dict: 매수/매도 가격 리스트와 잔량 리스트
    """
    if tick is None:
        tick = get_tick_size((lp_bid + lp_ask) / 2)

    rng = np.random.default_rng(volume_seed)

    # 매도: lp_ask부터 위로 tick씩 (1단계 = lp_ask, 2단계 = lp_ask+tick, ...)
    ask_prices = [lp_ask + tick * i for i in range(n_levels)]
    # 매수: lp_bid부터 아래로 tick씩
    bid_prices = [lp_bid - tick * i for i in range(n_levels)]

    # 가상 잔량 (LP가 깐 1단계는 큰 값, 멀어질수록 다양)
    ask_volumes = [int(rng.integers(800, 4500)) for _ in range(n_levels)]
    bid_volumes = [int(rng.integers(800, 4500)) for _ in range(n_levels)]

    # LP 호가(1단계)는 시뮬상 LP가 두텁게 깐 것으로 표시
    ask_volumes[0] = int(rng.integers(2500, 5000))
    bid_volumes[0] = int(rng.integers(2500, 5000))

    return {
        "ask_prices": ask_prices,
        "ask_volumes": ask_volumes,
        "bid_prices": bid_prices,
        "bid_volumes": bid_volumes,
        "tick": tick,
    }

def round_to_tick_str(price: float) -> str:
    """NAV처럼 소수점 있는 값을 호가단위 정수로 반올림한 문자열."""
    return f"{round_to_tick(price):,}"

@functools.lru_cache(maxsize=512)
# def get_etf_name_safe(ticker: str) -> str | None:
#     """
#     ETF 종목명을 안전하게 조회. 유효하지 않으면 None.

#     유효성 검사 + 이름 조회를 한 번에 수행.
#     `lru_cache`로 같은 ticker 재조회 시 즉시 반환.

#     Args:
#         ticker: 6자리 종목코드 (또는 알파벳 포함 신형 코드)

#     Returns:
#         종목명 (str) 또는 None (찾을 수 없을 때)
#     """
#     if not ticker or not ticker.strip():
#         return None
#     try:
#         name = stock.get_etf_ticker_name(ticker.strip())
#         if name and isinstance(name, str) and name.strip():
#             return name.strip()
#         return None
#     except Exception:
#         return None
@functools.lru_cache(maxsize=512)
def get_etf_name_safe(ticker: str) -> str | None:
    """
    ETF 종목명 안전 조회.
    - DEMO_MODE=1: 캐시된 etf_names.json에서 조회
    - 그 외: pykrx 호출
    """
    if not ticker or not ticker.strip():
        return None
    ticker = ticker.strip()

    if DEMO_MODE:
        names_path = DATA_DIR / "etf_names.json"
        if not names_path.exists():
            return None
        try:
            with open(names_path, encoding="utf-8") as f:
                names = json.load(f)
            return names.get(ticker)
        except Exception:
            return None

    # 라이브 모드
    try:
        name = stock.get_etf_ticker_name(ticker)
        if name and isinstance(name, str) and name.strip():
            return name.strip()
        return None
    except Exception:
        return None

def parse_ticker_list(text: str) -> list[str]:
    """
    텍스트에서 종목코드 리스트 추출.
    콤마/공백/줄바꿈으로 구분된 코드들을 정리.

    Args:
        text: '069500, 102110\n114800' 같은 자유 형식

    Returns:
        ['069500', '102110', '114800']
    """
    import re
    # 쉼표/공백/줄바꿈 모두 분리자로 처리
    tokens = re.split(r'[,\s]+', text.strip())
    return [t.strip() for t in tokens if t.strip()]