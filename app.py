"""
PLUS ETF LP 시뮬레이터 - Streamlit 메인 앱
한화자산운용 PLUS 브랜드 ETF 분석 · 한화투자증권 LP 직무 지원용 포트폴리오
"""
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from lp_calc import (
    PLUS_ETFS,
    fetch_etf_data,
    add_premium_column,
    classify_state,
    summary_stats,
    recommend_lp_quotes,
    build_synthetic_orderbook,
    # round_to_tick_str,
    get_etf_name_safe,
    parse_ticker_list,
)

# -------------------- 페이지 설정 --------------------
st.set_page_config(
    page_title="ETF LP 시뮬레이터",
    page_icon="📊",
    layout="wide",
)

st.title("📊 ETF LP 호가 조정 시뮬레이터")
import os
if os.getenv("DEMO_MODE", "0") == "1":
    st.info(
        "📅 **데모 모드**: 사전 캐싱된 데이터로 동작합니다 (2025-01 ~ 2026-04). "
        "실시간 데이터를 보려면 로컬에서 KRX 인증 환경변수 설정 후 실행하세요."
    )
st.caption("한화자산운용 PLUS 브랜드 ETF · KRX 실시간 NAV 데이터 기반 괴리율 분석")

# -------------------- 사이드바 공통 설정 --------------------
with st.sidebar:
    st.header("⚙️ 분석 설정")

    today = datetime.today()
    default_start = today - timedelta(days=120)
    col_a, col_b = st.columns(2)
    with col_a:
        start_date = st.date_input("시작일", value=default_start)
    with col_b:
        end_date = st.date_input("종료일", value=today)

    threshold = st.slider(
        "괴리율 정상 범위 임계치 (±%)",
        min_value=0.05,
        max_value=1.00,
        value=0.30,
        step=0.05,
        help="이 값을 넘으면 LP 호가 조정 필요. KRX 권고 기준은 ETF 종류별로 다름.",
    )

    st.divider()
    # st.markdown("### 📌 분석 대상 PLUS ETF")
    # for t, n in PLUS_ETFS.items():
    #     st.caption(f"`{t}`  {n}")
    with st.expander("📌 PLUS 라인업 (5종목)", expanded=True):
        for t, n in PLUS_ETFS.items():
            st.caption(f"`{t}`  {n}")
    st.caption("💡 단일/비교 탭에서 '직접 입력' 모드로 전환하면 임의 종목 분석 가능")    


# -------------------- 데이터 로딩 (캐시) --------------------
@st.cache_data(ttl=3600, show_spinner=False)
def load_etf(ticker: str, start: str, end: str) -> pd.DataFrame:
    """KRX 데이터 호출 + 괴리율 컬럼 추가까지. 1시간 캐싱."""
    df = fetch_etf_data(ticker, start, end)
    if df.empty:
        return df
    return add_premium_column(df)


# -------------------- 탭 구성 --------------------
tab1, tab2 = st.tabs(["🎯 단일 종목 상세", "📊 PLUS 라인업 비교"])

# ============================================================
# Tab 1 : 단일 종목 상세 분석
# ============================================================
with tab1:
    # selected_ticker = st.selectbox(
    #     "분석할 종목 선택",
    #     options=list(PLUS_ETFS.keys()),
    #     index=0,
    #     format_func=lambda t: f"{t}  -  {PLUS_ETFS[t]}",
    # )

    # ----- 입력 모드 토글 -----
    input_mode = st.radio(
        "종목 선택 방식",
        options=["📌 PLUS 라인업", "🔍 직접 입력"],
        horizontal=True,
        key="input_mode",
    )

    if input_mode == "📌 PLUS 라인업":
        selected_ticker = st.selectbox(
            "PLUS ETF 선택",
            options=list(PLUS_ETFS.keys()),
            index=0,
            format_func=lambda t: f"{t}  -  {PLUS_ETFS[t]}",
        )
        selected_name = PLUS_ETFS[selected_ticker]
        ticker_valid = True
    else:
        # 직접 입력 모드
        custom_ticker = st.text_input(
            "ETF 종목코드 입력",
            value="069500",
            help="예: 069500=KODEX 200, 360750=TIGER 미국S&P500, "
                 "0000J0=PLUS 한화그룹주. 6자리 또는 알파벳 포함 코드.",
            placeholder="6자리 종목코드 입력",
        )
        selected_ticker = custom_ticker.strip()

        # 종목명 자동 조회 + 유효성 표시
        if selected_ticker:
            with st.spinner("종목명 조회 중..."):
                selected_name = get_etf_name_safe(selected_ticker)
            if selected_name:
                st.success(f"✅ `{selected_ticker}` — **{selected_name}**")
                ticker_valid = True
            else:
                st.error(f"❌ `{selected_ticker}` 종목을 찾을 수 없습니다. 종목코드 확인 필요.")
                ticker_valid = False
        else:
            st.info("종목코드를 입력하세요.")
            selected_name = None
            ticker_valid = False


    # 분석 버튼 클릭 시: 데이터 받아서 session_state에 저장(유효한 종목일 때만)
    if st.button("📥 분석 실행", type="primary", key="single_run"):
        # with st.spinner(f"{PLUS_ETFS[selected_ticker]} 데이터 받는 중..."):
        with st.spinner(f"{selected_name} 데이터 받는 중..."):
            df = load_etf(
                selected_ticker,
                start_date.strftime("%Y%m%d"),
                end_date.strftime("%Y%m%d"),
            )

        if df.empty:
            st.error("데이터가 비어있습니다. 기간을 확인하세요.")
            st.session_state.analyzed_df = None
        else:
            # 분석 결과를 세션에 저장 (슬라이더 움직여도 살아있음)
            st.session_state.analyzed_df = df
            st.session_state.analyzed_ticker = selected_ticker
            st.session_state.analyzed_name = selected_name
            st.session_state.analyzed_period = (start_date, end_date)

    # 분석 결과 표시 (버튼 클릭과 무관하게, session_state에 데이터 있으면 항상 표시)
    if st.session_state.get("analyzed_df") is not None:
        df = st.session_state.analyzed_df.copy()
        ticker = st.session_state.analyzed_ticker
        period_start, period_end = st.session_state.analyzed_period

        # 상태 라벨은 현재 임계치로 매번 재계산 (슬라이더 즉시 반영)
        df["상태"] = df["괴리율(%)"].apply(lambda x: classify_state(x, threshold))

        # st.subheader(f"📌 {ticker} — {PLUS_ETFS[ticker]}")
        # PLUS 모드 / 직접 입력 모드 모두 처리
        display_name = st.session_state.get("analyzed_name") or PLUS_ETFS.get(ticker, "(이름 없음)")
        st.subheader(f"📌 {ticker} — {display_name}")

        st.caption(
            f"기간: {period_start} ~ {period_end}  ·  "
            f"관측일수: {len(df)}일  ·  임계치: ±{threshold}%"
        )

        # KPI 카드
        stats = summary_stats(df)
        normal_ratio = (df["상태"] == "NORMAL").mean() * 100

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("평균 괴리율", f"{stats['평균(%)']:+.4f}%")
        c2.metric("표준편차", f"{stats['표준편차(%)']:.4f}%")
        c3.metric("최저 (디스카운트)", f"{stats['최저(%)']:+.4f}%")
        c4.metric("최고 (프리미엄)", f"{stats['최고(%)']:+.4f}%")
        c5.metric("정상범위 비율", f"{normal_ratio:.1f}%")

        st.divider()

        # 차트
        cc1, cc2 = st.columns(2)
        with cc1:
            st.subheader("📈 괴리율 시계열")
            st.line_chart(df["괴리율(%)"], height=300)
            st.caption(f"|괴리율| > {threshold}% 인 날 = LP 호가 조정 필요 구간")
        with cc2:
            st.subheader("💰 NAV vs 시장가")
            st.line_chart(df[["NAV", "종가"]], height=300)
            st.caption("두 선의 격차 = 괴리율의 절댓값")

        st.divider()

        # 상태 분포
        st.subheader("📊 상태 분포 & LP 액션 가이드")
        sd1, sd2 = st.columns([1, 2])
        with sd1:
            st.bar_chart(df["상태"].value_counts())
        with sd2:
            st.markdown("- 🟢 **NORMAL** : 정상 범위. 호가 유지.")
            st.markdown("- 🔴 **PREMIUM** : 시장가 > NAV. **매도 호가를 낮춰** 격차 좁힘.")
            st.markdown("- 🔵 **DISCOUNT** : 시장가 < NAV. **매수 호가를 올려** 격차 좁힘.")

        st.divider()

        # -------------------- 🎯 LP 추천 호가 --------------------
        st.subheader("🎯 LP 추천 호가 (가장 최근 일자 기준)")

        base_spread_bps = st.slider(
            "기본 스프레드 (bps)",
            min_value=5, max_value=100, value=20, step=5,
            help="LP가 NAV 기준으로 띄울 스프레드 폭. "
                 "20bps = 0.2% (예: 4만원짜리 ETF면 80원).",
            key="spread_bps",
        )

        last_row = df.iloc[-1]
        quotes = recommend_lp_quotes(
            nav=last_row["NAV"],
            last_close=last_row["종가"],
            threshold=threshold,
            base_spread_bps=base_spread_bps,
        )

        q1, q2, q3 = st.columns(3)
        q1.metric("📥 추천 매수호가 (Bid)", f"{quotes['추천_매수호가(bid)']:,}원")
        q2.metric("📤 추천 매도호가 (Ask)", f"{quotes['추천_매도호가(ask)']:,}원")
        q3.metric(
            "↔️ 스프레드",
            f"{quotes['스프레드']:,}원",
            f"{quotes['스프레드(bps)']} bps",
        )

        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("기준 NAV", f"{quotes['현재_NAV']:,}원")
        mc2.metric("직전 시장가", f"{quotes['직전_시장가']:,}원")
        mc3.metric("호가단위 (KRX 룰)", f"{quotes['호가단위']}원")

        if quotes["상태"] == "PREMIUM":
            st.error(quotes["LP_액션"])
        elif quotes["상태"] == "DISCOUNT":
            st.warning(quotes["LP_액션"])
        else:
            st.success(quotes["LP_액션"])

        with st.expander("📋 호가 계산 상세 (JSON)"):
            st.json(quotes)

        st.divider()

# -------------------- 📊 가상 호가창 시각화 --------------------
        st.subheader("📊 가상 호가창 시뮬레이션")
        st.caption(
            "LP가 추천 호가를 시장에 깔았을 때의 호가창 모습. "
            "1단계 매수/매도는 실제 추천 호가, 2~5단계 잔량은 가상값(시드 고정)."
        )

        ob = build_synthetic_orderbook(
            lp_bid=quotes["추천_매수호가(bid)"],
            lp_ask=quotes["추천_매도호가(ask)"],
            n_levels=5,
        )

        fig_ob = go.Figure()

        # 매도 호가 (빨강 계열) — y는 숫자!
        fig_ob.add_trace(go.Bar(
            y=ob["ask_prices"],
            x=ob["ask_volumes"],
            orientation="h",
            marker=dict(color="rgba(255, 99, 99, 0.75)"),
            name="매도 (Ask)",
            text=[f"{v:,}" for v in ob["ask_volumes"]],
            textposition="outside",
            hovertemplate="가격: %{y:,}원<br>잔량: %{x:,}<extra></extra>",
        ))

        # 매수 호가 (파랑 계열) — y는 숫자!
        fig_ob.add_trace(go.Bar(
            y=ob["bid_prices"],
            x=ob["bid_volumes"],
            orientation="h",
            marker=dict(color="rgba(99, 149, 255, 0.75)"),
            name="매수 (Bid)",
            text=[f"{v:,}" for v in ob["bid_volumes"]],
            textposition="outside",
            hovertemplate="가격: %{y:,}원<br>잔량: %{x:,}<extra></extra>",
        ))

        # 참조선: NAV (숫자 그대로)
        fig_ob.add_hline(
            y=float(last_row["NAV"]),
            line=dict(color="limegreen", width=2, dash="dash"),
            annotation_text=f"NAV {last_row['NAV']:,.2f}원",
            annotation_position="right",
        )
        # 참조선: 직전 시장가 (숫자 그대로)
        fig_ob.add_hline(
            y=float(last_row["종가"]),
            line=dict(color="orange", width=2, dash="dot"),
            annotation_text=f"시장가 {int(last_row['종가']):,}원",
            annotation_position="right",
        )

        fig_ob.update_layout(
            title=f"가상 호가창 — 스프레드 {quotes['스프레드']:,}원 ({quotes['스프레드(bps)']} bps)",
            xaxis_title="잔량 (가상)",
            yaxis=dict(
                title="가격 (원)",
                tickformat=",",      # 천단위 콤마 표시
            ),
            height=550,
            barmode="overlay",
            showlegend=True,
            margin=dict(r=180),
        )

        st.plotly_chart(fig_ob, use_container_width=True)

        st.divider()

        # 데이터 테이블
        st.subheader("📋 일별 상세")
        display_df = df[["NAV", "종가", "괴리율(%)", "상태"]].round(3)
        st.dataframe(display_df, use_container_width=True, height=400)

        csv = display_df.to_csv().encode("utf-8-sig")
        # st.download_button(
        #     "💾 CSV 다운로드",
        #     data=csv,
        #     file_name=f"plus_etf_{ticker}_{period_start}_{period_end}.csv",
        #     mime="text/csv",
        #     key="download_single",
        # )
        safe_name = display_name.replace(" ", "_").replace("/", "-")[:30]
        st.download_button(
            "💾 CSV 다운로드",
            data=csv,
            file_name=f"etf_{ticker}_{safe_name}_{period_start}_{period_end}.csv",
            mime="text/csv",
            key="download_single",
        )


# ============================================================
# Tab 2 : PLUS 라인업 비교
# ============================================================
# with tab2:
#     st.markdown(f"### 🔍 PLUS 브랜드 {len(PLUS_ETFS)}개 종목 LP 운용 품질 일괄 비교")
#     st.caption("종목별 평균 괴리율, 표준편차, 정상범위 비율을 한 화면에서 비교 분석합니다.")

#     if st.button("📥 전체 분석 실행", type="primary", key="compare_run"):
#         results = []
#         progress = st.progress(0, text="분석 시작...")

#         for i, (ticker, name) in enumerate(PLUS_ETFS.items()):
#             progress.progress(
#                 (i + 1) / len(PLUS_ETFS),
#                 text=f"{name} 분석 중... ({i + 1}/{len(PLUS_ETFS)})",
#             )
#             try:
#                 df = load_etf(
#                     ticker,
#                     start_date.strftime("%Y%m%d"),
#                     end_date.strftime("%Y%m%d"),
#                 )
#                 if df.empty:
#                     continue

#                 df["상태"] = df["괴리율(%)"].apply(lambda x: classify_state(x, threshold))
#                 stats = summary_stats(df)
#                 normal_ratio = (df["상태"] == "NORMAL").mean() * 100

#                 results.append({
#                     "종목코드": ticker,
#                     "종목명": name,
#                     "평균괴리율(%)": stats["평균(%)"],
#                     "표준편차(%)": stats["표준편차(%)"],
#                     "최저(%)": stats["최저(%)"],
#                     "최고(%)": stats["최고(%)"],
#                     "정상비율(%)": round(normal_ratio, 1),
#                     "관측일수": stats["관측일수"],
#                 })
#             except Exception as e:
#                 st.warning(f"{name} 분석 실패: {e}")

#         progress.empty()

#         if not results:
#             st.error("분석 가능한 종목이 없습니다. 기간 또는 종목코드를 확인하세요.")
#         else:
#             comparison = pd.DataFrame(results)
#             comparison_sorted = (
#                 comparison
#                 .sort_values("정상비율(%)", ascending=False)
#                 .reset_index(drop=True)
#             )
#             comparison_sorted.index += 1  # 1위부터

#             # 핵심 인사이트 카드
#             top = comparison_sorted.iloc[0]
#             min_std = comparison.loc[comparison["표준편차(%)"].idxmin()]
#             min_abs_premium = comparison.loc[comparison["평균괴리율(%)"].abs().idxmin()]

#             i1, i2, i3 = st.columns(3)
#             i1.metric("🏆 정상범위 비율 1위", top["종목명"], f"{top['정상비율(%)']}%")
#             i2.metric("🎯 표준편차 최저", min_std["종목명"], f"{min_std['표준편차(%)']:.4f}%")
#             i3.metric("⚖️ 평균 괴리율 0 근접", min_abs_premium["종목명"],
#                       f"{min_abs_premium['평균괴리율(%)']:+.4f}%")

#             st.divider()

#             st.subheader("📊 종목별 정상범위 비율 비교")
#             chart_data = comparison.set_index("종목명")["정상비율(%)"]
#             st.bar_chart(chart_data)

#             st.subheader("📋 종합 비교표 (정상비율 내림차순)")
#             st.dataframe(comparison_sorted, use_container_width=True)

#             csv = comparison_sorted.to_csv().encode("utf-8-sig")
#             st.download_button(
#                 "💾 비교표 CSV 다운로드",
#                 data=csv,
#                 file_name=f"plus_etf_comparison_{start_date}_{end_date}.csv",
#                 mime="text/csv",
#                 key="download_compare",
#             )
#     else:
#         st.info("👆 **전체 분석 실행** 버튼을 누르면 PLUS 종목 전체를 한 번에 분석합니다 (약 30초~1분 소요)")

with tab2:
    st.markdown("### 🔍 ETF LP 운용 품질 일괄 비교")
    st.caption("종목별 평균 괴리율, 표준편차, 정상범위 비율을 한 화면에서 비교 분석합니다.")

    # ----- 비교 대상 모드 토글 -----
    compare_mode = st.radio(
        "비교 대상 선택",
        options=[
            f"📌 PLUS 라인업 ({len(PLUS_ETFS)}종목)",
            "🔍 직접 종목 선택",
        ],
        horizontal=True,
        key="compare_mode",
    )

    if compare_mode.startswith("📌"):
        target_etfs = dict(PLUS_ETFS)
        st.info(f"비교 대상: {len(target_etfs)}개 PLUS 종목")
    else:
        custom_input = st.text_area(
            "비교할 종목코드 (콤마/공백/줄바꿈으로 구분, 2~10개 권장)",
            value="0000J0\n069500\n360750\n114800\n253150",
            height=120,
            help="예: 069500 (KODEX 200), 360750 (TIGER 미국S&P500), "
                 "114800 (KODEX 인버스), 253150 (KODEX 레버리지)",
        )
        tickers = parse_ticker_list(custom_input)

        if len(tickers) < 2:
            st.warning("비교를 위해 최소 2개 이상의 종목코드를 입력하세요.")
            target_etfs = {}
        elif len(tickers) > 10:
            st.warning(f"입력된 {len(tickers)}개 중 처음 10개만 분석합니다 (속도 고려).")
            tickers = tickers[:10]

        # 종목명 조회
        target_etfs = {}
        if 2 <= len(tickers) <= 10:
            with st.spinner("종목명 조회 중..."):
                for t in tickers:
                    name = get_etf_name_safe(t)
                    if name:
                        target_etfs[t] = name
                    else:
                        st.warning(f"`{t}` 종목을 찾을 수 없어 제외합니다.")

            if target_etfs:
                st.success(f"✅ 비교 대상 {len(target_etfs)}개 확정: " +
                           ", ".join([f"`{t}`={n}" for t, n in target_etfs.items()]))

    # ----- 분석 실행 -----
    if target_etfs and st.button("📥 전체 분석 실행", type="primary", key="compare_run"):
        results = []
        progress = st.progress(0, text="분석 시작...")

        for i, (ticker, name) in enumerate(target_etfs.items()):
            progress.progress(
                (i + 1) / len(target_etfs),
                text=f"{name} 분석 중... ({i + 1}/{len(target_etfs)})",
            )
            try:
                df = load_etf(
                    ticker,
                    start_date.strftime("%Y%m%d"),
                    end_date.strftime("%Y%m%d"),
                )
                if df.empty:
                    continue

                df["상태"] = df["괴리율(%)"].apply(lambda x: classify_state(x, threshold))
                stats = summary_stats(df)
                normal_ratio = (df["상태"] == "NORMAL").mean() * 100

                results.append({
                    "종목코드": ticker,
                    "종목명": name,
                    "평균괴리율(%)": stats["평균(%)"],
                    "표준편차(%)": stats["표준편차(%)"],
                    "최저(%)": stats["최저(%)"],
                    "최고(%)": stats["최고(%)"],
                    "정상비율(%)": round(normal_ratio, 1),
                    "관측일수": stats["관측일수"],
                })
            except Exception as e:
                st.warning(f"{name} 분석 실패: {e}")

        progress.empty()

        if not results:
            st.error("분석 가능한 종목이 없습니다. 기간 또는 종목코드를 확인하세요.")
        else:
            comparison = pd.DataFrame(results)
            comparison_sorted = (
                comparison
                .sort_values("정상비율(%)", ascending=False)
                .reset_index(drop=True)
            )
            comparison_sorted.index += 1

            top = comparison_sorted.iloc[0]
            min_std = comparison.loc[comparison["표준편차(%)"].idxmin()]
            min_abs_premium = comparison.loc[comparison["평균괴리율(%)"].abs().idxmin()]

            i1, i2, i3 = st.columns(3)
            i1.metric("🏆 정상범위 비율 1위", top["종목명"], f"{top['정상비율(%)']}%")
            i2.metric("🎯 표준편차 최저", min_std["종목명"], f"{min_std['표준편차(%)']:.4f}%")
            i3.metric("⚖️ 평균 괴리율 0 근접", min_abs_premium["종목명"],
                      f"{min_abs_premium['평균괴리율(%)']:+.4f}%")

            st.divider()

            st.subheader("📊 종목별 정상범위 비율 비교")
            chart_data = comparison.set_index("종목명")["정상비율(%)"]
            st.bar_chart(chart_data)

            st.subheader("📋 종합 비교표 (정상비율 내림차순)")
            st.dataframe(comparison_sorted, use_container_width=True)

            csv = comparison_sorted.to_csv().encode("utf-8-sig")
            st.download_button(
                "💾 비교표 CSV 다운로드",
                data=csv,
                file_name=f"etf_comparison_{start_date}_{end_date}.csv",
                mime="text/csv",
                key="download_compare",
            )
    elif not target_etfs:
        st.info("👆 비교 대상 종목을 선택한 후 **전체 분석 실행** 버튼을 누르세요.")