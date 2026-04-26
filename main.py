"""
ETF LP 시뮬레이터 - PLUS 브랜드 ETF 비교 분석 스크립트
한화투자증권 LP 직무 지원용 포트폴리오 프로젝트
"""
import pandas as pd

from lp_calc import (
    PLUS_ETFS,
    fetch_etf_data,
    add_premium_column,
    classify_state,
    summary_stats,
)

# pandas 출력 옵션 (한글 컬럼 정렬)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)


def analyze_etf(ticker: str, name: str, start: str, end: str) -> dict | None:
    """단일 ETF 분석 + 결과 출력. 비교용 dict 반환."""
    print(f"\n{'=' * 72}")
    print(f"  {ticker}  -  {name}")
    print(f"{'=' * 72}")

    try:
        df = fetch_etf_data(ticker, start, end)
        if df.empty:
            print("  데이터 없음 (상장 전 또는 거래정지 가능)")
            return None

        df = add_premium_column(df)
        df['상태'] = df['괴리율(%)'].apply(classify_state)

        # 최근 5일치
        print("\n  [최근 5일치]")
        recent = df[['NAV', '종가', '괴리율(%)', '상태']].tail(5).round(3)
        print(recent.to_string())

        # KPI
        stats = summary_stats(df)
        normal_ratio = (df['상태'] == 'NORMAL').mean() * 100

        print("\n  [전체 기간 KPI]")
        for k, v in stats.items():
            print(f"    {k}: {v}")
        print(f"    정상범위(±0.3%) 비율: {normal_ratio:.1f}%")

        return {
            '종목코드': ticker,
            '종목명': name,
            '평균괴리율(%)': stats['평균(%)'],
            '표준편차(%)': stats['표준편차(%)'],
            '최저(%)': stats['최저(%)'],
            '최고(%)': stats['최고(%)'],
            '정상비율(%)': round(normal_ratio, 1),
            '관측일수': stats['관측일수'],
        }
    except Exception as e:
        print(f"  오류 발생: {e}")
        return None


def main():
    start = '20260101'
    end = '20260424'

    print(f"\n{'#' * 72}")
    print(f"#  한화자산운용 PLUS 브랜드 ETF - LP 운용 품질 비교 분석")
    print(f"#  분석 기간: {start} ~ {end}")
    print(f"#  분석 종목: {len(PLUS_ETFS)}개")
    print(f"{'#' * 72}")

    results = []
    for ticker, name in PLUS_ETFS.items():
        result = analyze_etf(ticker, name, start, end)
        if result:
            results.append(result)

    # 종합 비교표 - 자소서·면접 어필 핵심
    if results:
        print(f"\n\n{'=' * 72}")
        print(f"  📈 PLUS ETF 종합 비교 (LP 운용 품질 순위)")
        print(f"{'=' * 72}\n")
        comparison = pd.DataFrame(results)
        # 정상비율 높은 순으로 정렬 = LP가 일을 잘한 순
        comparison = comparison.sort_values('정상비율(%)', ascending=False).reset_index(drop=True)
        comparison.index += 1  # 1위부터 표시
        print(comparison.to_string())

        print(f"\n{'-' * 72}")
        print(f"  💡 인사이트:")
        print(f"  - 정상비율 1위: {comparison.iloc[0]['종목명']} ({comparison.iloc[0]['정상비율(%)']}%)")
        print(f"  - 표준편차 최저: {comparison.loc[comparison['표준편차(%)'].idxmin(), '종목명']}")
        print(f"  - 평균 괴리율 0에 가장 가까움: "
              f"{comparison.loc[comparison['평균괴리율(%)'].abs().idxmin(), '종목명']}")
        print(f"{'-' * 72}\n")


if __name__ == '__main__':
    main()