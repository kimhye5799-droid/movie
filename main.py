import datetime
import urllib.parse
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="🎬 시네마 박스오피스 & 예고편",
    page_icon="🍿",
    layout="wide"
)

# --- 1. 영화관 분위기의 고급스러운 CSS 배경 커스텀 ---
st.markdown("""
    <style>
    /* 전체 배경을 어두운 딥 그레이/블랙 영화관 스타일로 변경 */
    .stApp {
        background-color: #0f1117;
        color: #e0e0e0;
    }
    
    /* 제목 스타일 */
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #ff4b4b;
        text-align: center;
        margin-bottom: 5px;
        text-shadow: 2px 2px 4px #000000;
    }
    
    .sub-title {
        text-align: center;
        color: #aaaaaa;
        margin-bottom: 25px;
    }
    
    /* 카드 및 컨테이너 스타일 */
    div[data-testid="stMetric"] {
        background-color: #1a1c23;
        border: 1px solid #2d313e;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* 카드 안의 텍스트 색상 */
    div[data-testid="stMetricLabel"] > div {
        color: #999999 !important;
    }
    div[data-testid="stMetricValue"] > div {
        color: #ffffff !important;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


st.markdown('<div class="main-title">🍿 어제의 CINEMA 박스오피스</div>', unsafe_allow_html=True)


# --- 2. 한국 시간(KST) 기준 '어제' 날짜 계산 ---
def get_yesterday_kst():
    tz_kst = pytz.timezone("Asia/Seoul")
    now_kst = datetime.datetime.now(tz_kst)
    yesterday = now_kst - datetime.timedelta(days=1)
    return yesterday.strftime("%Y%m%d"), yesterday.strftime("%Y년 %m월 %d일")

target_date_str, display_date = get_yesterday_kst()
st.markdown(f'<div class="sub-title">📅 기준일자: {display_date}</div>', unsafe_allow_html=True)


# --- 3. Secrets 인증키 확인 ---
api_key = st.secrets.get("KOBIS_KEY")

if not api_key:
    st.error("🔑 Secrets에서 인증키(KOBIS_KEY)를 찾을 수 없습니다.")
    st.info("Streamlit Cloud 설정(Settings -> Secrets)에 KOBIS_KEY = '발급받은키'를 등록해 주세요.")
    st.stop()


# --- 4. KOBIS 박스오피스 API 호출 ---
boxoffice_url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
params = {"key": api_key, "targetDt": target_date_str}

try:
    response = requests.get(boxoffice_url, timeout=10)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException:
    st.error("⚠️ 영화진흥위원회 API 서버 통신에 실패했습니다.")
    st.info("네트워크 상태를 확인하시거나 잠시 후 다시 시도해 주세요.")
    st.stop()


# --- 5. 응답 검증 및 예외 처리 ---
if "faultInfo" in data:
    st.error("⚠️ API 인증 오류가 발생했습니다.")
    st.write(f"메시지: {data['faultInfo'].get('message', '인증키를 확인해 주세요.')}")
    st.stop()

daily_list = data.get("boxOfficeResult", {}).get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning("⚠️ 집계된 박스오피스 데이터가 없습니다.")
    st.info("해당 날짜의 데이터가 아직 업데이트 중일 수 있습니다.")
    st.stop()


# --- 6. 영화 상세 정보 호출 함수 (개봉일, 감독, 출연진 등) ---
@st.cache_data(ttl=3600)
def get_movie_detail(movie_code):
    detail_url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json"
    try:
        res = requests.get(detail_url, params={"key": api_key, "movieCd": movie_code}, timeout=5)
        res_data = res.json()
        return res_data.get("movieInfoResult", {}).get("movieInfo", {})
    except Exception:
        return {}


# --- 7. 데이터 전처리 ---
df = pd.DataFrame(daily_list)
int_cols = ["rank", "audiCnt", "audiAcc", "scrnCnt"]
for col in int_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)


# --- 8. 🏆 1위 영화 하이라이트 & 예고편 영상 ---
top_1 = df[df["rank"] == 1].iloc[0]
movie_code = top_1.get("movieCd", "")
movie_info = get_movie_detail(movie_code)

# 감독 및 출연배우 정보 추출
directors = [d.get("peopleNm") for d in movie_info.get("directors", [])]
actors = [a.get("peopleNm") for a in movie_info.get("actors", [])[:3]]  # 상위 3명만
genres = [g.get("genreNm") for g in movie_info.get("genres", [])]

director_str = ", ".join(directors) if directors else "정보 없음"
actor_str = ", ".join(actors) if actors else "정보 없음"
genre_str = ", ".join(genres) if genres else "정보 없음"

st.subheader(f"🥇 어제의 1위 영화: {top_1['movieNm']}")

col1, col2, col3 = st.columns(3)
col1.metric("당일 관객수", f"{top_1['audiCnt']:,} 명")
col2.metric("누적 관객수", f"{top_1['audiAcc']:,} 명")
col3.metric("스크린수", f"{top_1['scrnCnt']:,} 개")

# 1위 영화 영상 및 검색 연동
st.markdown("### 🎬 영화 예고편 및 상세 정보")

tab1, tab2 = st.columns([3, 2])

with tab1:
    # 유튜브에서 공식 예고편 검색어로 자동 연결되는 검색 링크 생성
    yt_query = urllib.parse.quote(f"{top_1['movieNm']} 예고편")
    yt_url = f"https://www.youtube.com/results?search_query={yt_query}"
    
    st.write(f"**장르:** {genre_str} | **감독:** {director_str}")
    st.write(f"**주요 출연진:** {actor_str}")
    
    st.info("💡 KOBIS API 정책상 텍스트 줄거리는 제공되지 않습니다. 아래 버튼을 통해 줄거리 및 공식 예고편을 바로 감상하실 수 있습니다.")
    st.link_button(f"▶️ '{top_1['movieNm']}' 유튜브 예고편 검색하기", yt_url, use_container_width=True)

with tab2:
    # 포털 검색 빠른 링크
    naver_query = urllib.parse.quote(f"영화 {top_1['movieNm']} 줄거리 정보")
    naver_url = f"https://search.naver.com/search.naver?query={naver_query}"
    st.link_button(f"🔍 네이버에서 줄거리·평점 검색", naver_url, use_container_width=True)


# --- 9. 📊 관객수 상위 5개 막대그래프 ---
st.markdown("---")
st.subheader("📊 TOP 5 영화 당일 관객수 비교")

top5_df = df.head(5)[["movieNm", "audiCnt"]].set_index("movieNm")
st.bar_chart(top5_df)


# --- 10. 📋 전체 순위 목록 표 ---
st.markdown("---")
st.subheader("📋 전체 박스오피스 순위")

display_df = df[["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
display_df.columns = ["순위", "영화명", "개봉일", "관객수", "누적관객", "스크린수"]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "관객수": st.column_config.NumberColumn(format="%d명"),
        "누적관객": st.column_config.NumberColumn(format="%d명"),
        "스크린수": st.column_config.NumberColumn(format="%d개"),
    },
)
