# 📊 ETF LP 호가조정 시뮬레이터

🚀 **[Live Demo →](https://etf-lp-simulator.streamlit.app)** &nbsp;|&nbsp; [![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://etf-lp-simulator.streamlit.app)

> PLUS 라인업 분석을 핵심으로, 임의 ETF 종목 분석까지 지원하는 범용 LP 분석 도구

한화자산운용 PLUS 브랜드 ETF 분석을 핵심으로 하면서, **임의 ETF 종목코드 입력**과 **사용자 정의 비교**까지 지원하는 범용 LP 분석 도구입니다. PLUS 특화 분석은 그대로 유지하면서, 토글 하나로 모드 전환이 가능합니다.

> **한화투자증권 디지털금융 직무 포트폴리오 프로젝트**

---

## 🎯 핵심 기능

### 기본 분석
1. **PLUS 5종목 특화 분석** — 한화자산운용 PLUS 라인업에 집중한 깊이 있는 분석
2. **실시간 KRX 데이터 수집** — pykrx + KRX 회원 인증
3. **괴리율 분석** — 시장가-NAV 괴리율, 상태 분류, 통계
4. **PLUS 라인업 비교 대시보드** — 5종목 일괄 비교
5. **LP 호가 추천 알고리즘** — 비대칭 스프레드, KRX 호가단위 반영
6. **가상 호가창 시각화** — Plotly 인터랙티브 차트

### 범용 분석 (확장)
7. **임의 ETF 분석 지원** — KRX 상장 모든 ETF 종목코드 직접 입력 가능
8. **사용자 정의 비교** — 최대 10종목까지 자유롭게 선택해 비교
9. **종목명 자동 조회** — 종목코드만 입력하면 이름 표시 + 유효성 즉시 검증
10. **이중 모드 UI** — 토글 하나로 PLUS 라인업 / 직접 입력 전환

### 배포 (데모 모드)
11. **Streamlit Community Cloud 배포** — 정적 데이터 캐시 기반 데모 모드로 누구나 접근 가능
12. **이중 데이터 소스** — 환경변수(`DEMO_MODE`)로 실시간 KRX 호출 / CSV 캐시 자동 전환

---

## 📌 v1 → v2 변경사항

| 영역 | v1 | v2 (현재) |
|------|----|----|
| 단일 종목 선택 | PLUS 5종목 드롭다운 고정 | 토글: **PLUS 라인업** / **직접 입력** |
| 비교 분석 대상 | PLUS 5종목 자동 비교 | 토글: **PLUS** / **사용자 정의 (2~10종목)** |
| 종목 검증 | N/A | 종목명 자동 조회 + 유효성 표시 (✅/❌) |
| 헬퍼 함수 | - | `get_etf_name_safe`, `parse_ticker_list` 추가 |
| 캐싱 | `@st.cache_data` (데이터) | + `@functools.lru_cache` (종목명) |
| 배포 | 로컬 only | + Streamlit Cloud 데모 모드 배포 |

---

## 📈 주요 분석 결과 (PLUS 라인업, 2026-01-01 ~ 2026-04-24)

| 순위 | 종목코드 | 종목명 | 평균 괴리율 | 표준편차 | 정상범위 비율 |
|------|----------|--------|-------------|----------|---------------|
| 1 | 0000J0 | **PLUS 한화그룹주** | -0.127% | **0.211%** ★ | **75.9%** ★ |
| 2 | 457990 | PLUS 태양광&ESS | **-0.034%** ★ | 0.311% | 75.9% |
| 3 | 213630 | PLUS 미국다우존스고배당주(H) | -0.259% | 0.708% | 48.1% |
| 4 | 301400 | PLUS 코스닥150 | -0.302% | 0.333% | 43.0% |
| 5 | 461910 | PLUS 미국테크TOP10레버리지 | -0.214% | 1.595% | 30.4% |

★ = 카테고리 1위

### 핵심 인사이트

- **PLUS 한화그룹주가 LP 운용 안정성 1위** — 표준편차 0.211%, 정상범위 비율 75.9%로 PLUS 라인업 중 최고
- **레버리지·해외 환헷지 종목**은 본질적 변동성이 커서 LP 호가 조정의 빈도와 정확성이 더 중요해진다는 가설을 데이터로 확인
- **평균 괴리율은 PLUS 태양광&ESS가 0에 가장 근접** (-0.034%) — 양방향 호가 균형이 우수

### 활용 예: 운용사 비교 (직접 입력 모드)

| 종목코드 | 종목명 | 운용사 |
|---|---|---|
| 0000J0 | PLUS 한화그룹주 | 한화자산운용 |
| 069500 | KODEX 200 | 삼성자산운용 |
| 102110 | TIGER 200 | 미래에셋자산운용 |
| 152100 | ARIRANG 200 | 한화자산운용 (구) |

→ Tab 2에서 위 4종목 입력 시 **운용사·브랜드 간 LP 운용 품질 교차 비교** 가능

---

## 🛠 기술 스택

- **Python 3.13** (가상환경 venv)
- **pykrx** — 한국거래소(KRX) 데이터 수집
- **pandas / numpy** — 데이터 처리, 통계 산출
- **functools** — `lru_cache`로 종목명 조회 캐싱
- **Streamlit** — 웹 UI 프레임워크 (`st.session_state` 기반 상태 관리)
- **Plotly** — 인터랙티브 호가창 차트
- **Streamlit Community Cloud** — 무료 배포 호스팅

---

## 📁 프로젝트 구조

```
etf-lp-simulator/
├── lp_calc.py              # 데이터 수집 + 괴리율 계산 + LP 호가 추천 + 가상 호가창 + 종목명 헬퍼
├── main.py                 # CLI 비교 분석 스크립트 (PLUS 5종목 일괄 출력)
├── app.py                  # Streamlit 웹 앱 (메인 시뮬레이터, 2개 탭 + 이중 모드)
├── prepare_demo_data.py    # 데모 모드용 CSV 사전 생성 스크립트
├── data/                   # 데모 모드용 캐시 데이터 (CSV + 종목명 매핑)
│   ├── 0000J0.csv
│   ├── ... (총 10종목)
│   └── etf_names.json
├── requirements.txt        # 의존성 목록
└── README.md
```

---

## ⚙️ 핵심 로직

### 1. 괴리율 계산

```
괴리율(%) = (시장가 - NAV) / NAV × 100
```

- 양수 → **프리미엄**: 시장가가 NAV보다 비쌈
- 음수 → **디스카운트**: 시장가가 NAV보다 쌈

### 2. 상태 분류 (임계치 기본 ±0.3%)

| 상태 | 조건 | LP 액션 |
|------|------|---------|
| `NORMAL` | \|괴리율\| ≤ 임계치 | NAV 기준 대칭 호가 유지 |
| `PREMIUM` | 괴리율 > +임계치 | 매도호가를 NAV에 가까이 적극 제시 |
| `DISCOUNT` | 괴리율 < -임계치 | 매수호가를 NAV에 가까이 적극 제시 |

### 3. LP 호가 추천 (비대칭 스프레드 모델)

- **NORMAL**: 대칭 — `bid = NAV - half_spread`, `ask = NAV + half_spread`
- **PREMIUM**: 비대칭 — `ask = NAV + 0.5×half_spread` (적극), `bid = NAV - 1.5×half_spread`
- **DISCOUNT**: 비대칭 — `bid = NAV - 0.5×half_spread` (적극), `ask = NAV + 1.5×half_spread`

### 4. KRX 호가단위(Tick Size) 자동 반영

| 가격대 (원) | 호가단위 (원) |
|-------------|---------------|
| ~2,000 | 1 |
| 2,000 ~ 5,000 | 5 |
| 5,000 ~ 20,000 | 10 |
| 20,000 ~ 50,000 | 50 |
| 50,000 ~ 200,000 | 100 |
| 200,000 ~ 500,000 | 500 |
| 500,000 ~ | 1,000 |

### 5. 임의 ETF 종목명 안전 조회

```python
@functools.lru_cache(maxsize=512)
def get_etf_name_safe(ticker: str) -> str | None:
    """유효성 검사 + 이름 조회를 한 번에. 실패 시 None."""
```

→ 잘못된 종목코드 입력 시 비싼 OHLCV API 호출 전 **1차 검증**으로 차단.

### 6. 데모 / 실시간 모드 자동 분기

```python
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"

def fetch_etf_data(ticker, start_date, end_date):
    if DEMO_MODE:
        # CSV 캐시에서 읽음 (배포 환경)
        return pd.read_csv(DATA_DIR / f"{ticker}.csv", ...)
    # pykrx로 KRX 실시간 호출 (로컬 개발)
    return stock.get_etf_ohlcv_by_date(start_date, end_date, ticker)
```

→ KRX 데이터 라이선스 + 사용자 접근성의 균형 고려한 설계.

---

## 🚀 설치 및 실행

### 옵션 A: 라이브 데모 (즉시)

별도 셋업 없이 **[https://etf-lp-simulator.streamlit.app](https://etf-lp-simulator.streamlit.app)** 접속.

### 옵션 B: 로컬 개발 환경

#### 1. 가상환경 생성 + 의존성 설치

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### 2. KRX 회원 인증 환경변수 설정 (실시간 모드용)

[data.krx.co.kr](https://data.krx.co.kr) 무료 회원가입 후, PowerShell에서:

```powershell
[Environment]::SetEnvironmentVariable("KRX_ID", "your_id", "User")
[Environment]::SetEnvironmentVariable("KRX_PW", "your_password", "User")
```

→ 터미널 재시작 후 적용

#### 3. 실행

**CLI 비교 분석** (PLUS 5종목):

```powershell
python main.py
```

**Streamlit 웹 앱** (인터랙티브 시뮬레이터):

```powershell
streamlit run app.py
```

#### 4. 데모 모드로 실행 (KRX 인증 없이)

```powershell
$env:DEMO_MODE = "1"
streamlit run app.py
```

→ `data/` 폴더의 CSV 캐시에서 데이터를 읽음.

---

## 🖥 화면 구성 (Streamlit 앱)

### Tab 1: 단일 종목 상세

**모드 토글**: `📌 PLUS 라인업` / `🔍 직접 입력`

- **PLUS 모드**: 5종목 드롭다운에서 선택
- **직접 입력 모드**: 종목코드 텍스트 입력 → 종목명 자동 조회 → ✅/❌ 즉시 피드백

분석 실행 후 표시:
- KPI 카드 5개 (평균/표준편차/최저/최고/정상범위 비율)
- 괴리율 시계열 + NAV vs 시장가 차트
- 상태 분포 + LP 액션 가이드
- LP 추천 호가 (스프레드 슬라이더로 실시간 시뮬)
- 가상 호가창 (5단계 매수/매도, NAV/시장가 참조선)

### Tab 2: 라인업 비교

**모드 토글**: `📌 PLUS 라인업 (5종목)` / `🔍 직접 종목 선택`

- **PLUS 모드**: 5종목 자동 비교
- **직접 선택 모드**: 텍스트 박스에 종목코드 2~10개 입력 → 자동 검증 → 비교 분석

표시:
- 인사이트 카드 (정상비율 1위 / 표준편차 최저 / 평균괴리율 0근접)
- 종목별 정상범위 비율 비교 차트
- 종합 비교표 + CSV 다운로드

---

## 💼 면접 / 자소서 활용 포인트

### 기본 어필 포인트
1. **지원사 그룹 ETF 직접 분석** — PLUS 한화그룹주를 메인으로 두고, 한화자산운용 라인업의 LP 운용 품질을 정량화
2. **데이터 직접 수집·분석 경험** — KRX 인증 환경변수 처리 + pykrx로 실데이터 파이프라인 구축
3. **LP 핵심 KPI 이해** — 괴리율 최소화 + 정상범위 유지가 LP의 본질이라는 점을 직접 데이터로 확인
4. **알고리즘 구현** — 단순 대시보드를 넘어 NAV 기준 비대칭 스프레드 호가 추천 로직 직접 구현
5. **실무 디테일 반영** — KRX 호가단위 규정까지 반영해 주문 가능한 호가 산출
6. **Streamlit 상태 관리** — `st.session_state`로 데이터 fetching과 시각화 분리

### 확장성 어필 포인트 ★
7. **범용성 고려한 설계** — 특정 운용사·종목에 종속되지 않고, KRX 상장 모든 ETF에 적용 가능한 분석 도구로 확장
8. **방어적 프로그래밍** — `get_etf_name_safe`로 잘못된 입력에 대한 1차 검증 + `lru_cache`로 반복 호출 최적화
9. **확장 가능한 아키텍처** — PLUS 특화 모드와 범용 모드를 토글로 분리, 각 모드의 가치를 모두 보존
10. **실무 적용 가능성** — 신규 ETF 상장 시에도 코드 수정 없이 즉시 분석 가능

### 배포·운영 어필 포인트 ★★
11. **Streamlit Community Cloud 배포** — 면접관/평가자가 환경 셋업 없이 즉시 시연 가능
12. **이중 데이터 소스 설계** — 환경변수로 실시간 모드(KRX 인증) / 데모 모드(CSV 캐시) 자동 전환, 데이터 라이선스와 접근성의 균형 고려


## 🔮 향후 개선 방향

- **운용사 단위 비교** — KODEX vs TIGER vs PLUS vs ARIRANG 자동 그룹핑
- **자산군 자동 분류** — 국내/해외/원자재/채권 등 카테고리 분류 + 카테고리별 LP 품질 비교
- **실시간 iNAV 연동** — KIS Developers API 연동 (일별 NAV → 분 단위 iNAV 업그레이드)
- **백테스트 모듈** — 과거 시점에 호가 추천 적용 시 실제 괴리율 변화 효과 검증
- **임계치 자동 튜닝** — 종목별 변동성에 맞춘 동적 임계치 (Bayesian Optimization)
- **알림 자동화** — 괴리율 임계치 초과 시 슬랙/이메일 알림

---

## 📝 라이선스

본 프로젝트는 학습 및 포트폴리오 목적으로 작성되었습니다.
KRX 데이터의 상업적 사용은 별도 라이선스가 필요합니다.
