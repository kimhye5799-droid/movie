import random
import requests
import pandas as pd
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="🎬 오늘 뭐 볼까? 랜덤 영화 추천기", layout="wide")

st.title("🎲 KOBIS 데이터 기반 랜덤 영화 추천기")
st.caption("영화진흥위원회 DB에 등록된 영화 중 무작위로 하나를 추천해 드립니다!")

# --- 1. secrets에서 API 키 불러오기 ---
api_key = st.secrets.get("KOBIS_KEY")

if not api_key:
    st.error("🔑 Secrets에서 인증키(KOBIS_KEY)를 찾을 수 없습니다.")
    st.info(
        "Streamlit Cloud 설정(Settings -> Secrets)에 KOBIS_KEY = '발급받은키'를 등록해 주세요."
    )
    st.stop()


# --- 2. KOBIS 영화목록 API 호출 함수 ---
@st.cache_data(ttl=3600)  # 동일 조건 검색 시 1시간 동안 캐시 사용
def fetch_movie_list(keyword=""):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieList.json"
    params = {
        "key": api_key,
        "itemPerPage": "100",  # 최대 100개까지 가져오기
        "movieNm": keyword,
    }

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "faultInfo" in data:
            st.error("⚠️ API 오류가 발생했습니다.")
            st.write(
                f"메시지: {data['faultInfo'].get('message', '키를 확인해 주세요.')}"
            )
            return None

        movie_list = data.get("movieListResult", {}).get("movieList", [])
        return movie_list

    except requests.exceptions.RequestException:
        st.error("⚠️ 영화진흥위원회 서버와의 통신에 실패했습니다.")
        return None


# --- 3. 사용자 입력 및 추천 버튼 ---
st.markdown("---")
search_keyword = st.text_input(
    "검색하고 싶은 영화 제목 키워드를 입력하세요 (비워두면 전체 추천):", ""
)

col1, col2 = st.columns([1, 4])
with col1:
    pick_button = st.button("🎲 영화 뽑기!", use_container_width=True)

# --- 4. 영화 뽑기 로직 ---
if pick_button:
    movies = fetch_movie_list(keyword=search_keyword)

    if movies is None:
        st.stop()

    if not movies:
        st.warning("⚠️ 검색 결과에 해당하는 영화가 없습니다.")
        st.info("다른 검색어로 다시 시도해 보세요.")
        st.stop()

    # 랜덤으로 영화 1개 선택
    selected_movie = random.choice(movies)

    # 선택된 영화 정보 가져오기
    title = selected_movie.get("movieNm", "제목 정보 없음")
    title_en = selected_movie.get("movieNmEn", "")
    prdt_year = selected_movie.get("prdtYear", "연도 미상")
    genre = selected_movie.get("genreAlt", "장르 정보 없음")
    nation = selected_movie.get("repNationNm", "국가 정보 없음")
    directors = selected_movie.get("directors", [])
    director_name = (
        directors[0].get("peopleNm") if directors else "감독 정보 없음"
    )

    # --- 5. 결과 출력 ---
    st.balloons()  # 축하 효과
    st.success(f"🎉 오늘의 추천 영화: **{title}**")

    # 지표 카드 형태로 영화 주요 정보 표시
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric(label="제작 연도", value=f"{prdt_year}년")
    mc2.metric(label="대표 장르", value=genre)
    mc3.metric(label="제작 국가", value=nation)
    mc4.metric(label="감독", value=director_name)

    if title_en:
        st.caption(f"영문 제목: {title_en}")

    # 전체 후보 목록도 아래에 표로 제공
    st.markdown("---")
    st.write(f"📋 **검색된 후보 영화 목록 (총 {len(movies)}건 중 1건 추출)**")

    df = pd.DataFrame(movies)
    display_df = df[
        ["movieNm", "prdtYear", "repGenreNm", "repNationNm"]
    ].copy()
    display_df.columns = ["영화명", "제작연도", "장르", "국가"]

    st.dataframe(display_df, use_container_width=True, hide_index=True)
