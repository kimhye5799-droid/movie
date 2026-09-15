import datetime
import random
import urllib.parse
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="🎬 시네마 룰렛 - KOBIS 랜덤 영화 추천",
    page_icon="🍿",
    layout="wide"
)

# --- 1. 시네마 다크모드 CSS 커스텀 ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0f1117;
        color: #e0e0e0;
    }
    .main-title {
        font-size: 2.6rem;
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
    div[data-testid="stMetric"] {
        background-color: #1a1c23;
        border: 1px solid #2d313e;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetricLabel"] > div {
        color: #999999 !important;
    }
    div[data-testid="stMetricValue"] > div {
        color: #ffffff !important;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🎲 KOBIS 랜덤 영화 추천기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">영화진흥위원회 데이터베이스 기반 오늘 볼 영화 룰렛</div>', unsafe_allow_html=True)


# --- 2. 영화 데이터 로드 함수 (API 장애/키 오류 시 예외 처리) ---
@st.cache_data(ttl=1800)
def fetch_kobis_movies(api_key, keyword=""):
    if api_key:
        url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieList.json"
        params = {
            "key": api_key,
            "itemPerPage": "100",  # 최대 100개 검색
            "movieNm": keyword
        }
        try:
            res = requests.get(url, params=params, timeout=5)
            data = res.json()
            if "faultInfo" not in data and "movieListResult" in data:
                movies = data["movieListResult"].get("movieList", [])
                if movies:
                    return movies, False
        except Exception:
            pass

    # API 호출 실패 시 활용할 데모 샘플 영화 데이터셋
    sample_movies = [
        {
            "movieNm": "파묘", "movieNmEn": "Exhuma", "prdtYear": "2024",
            "repGenreNm": "미스터리", "repNationNm": "한국", "directors": [{"peopleNm": "장재현"}],
            "synopsis": "미국 LA, 거액의 의뢰를 받은 무당 화림과 봉길은 기이한 병이 대대로 물려오는 집안의 장손을 만난다...",
            "yt_id": "tA3zs_8E9i8"
        },
        {
            "movieNm": "범죄도시4", "movieNmEn": "The Roundupt : Punishment", "prdtYear": "2024",
            "repGenreNm": "액션", "repNationNm": "한국", "directors": [{"peopleNm": "허명행"}],
            "synopsis": "신종 마약 사건 조사 중, 괴물형사 마석도는 배달앱을 이용한 마약 판매 사건이 불법 도박 조직과 연관되었음을 알게 된다...",
            "yt_id": "i42a1Ea1x1s"
        },
        {
            "movieNm": "인사이드 아웃 2", "movieNmEn": "Inside Out 2", "prdtYear": "2024",
            "repGenreNm": "애니메이션", "repNationNm": "미국", "directors": [{"peopleNm": "캘시 맨"}],
            "synopsis": "13살이 된 라일리의 머릿속 감정 컨트롤 본부에 불안, 당황, 따분, 시기 등 새로운 감정들이 찾아온다!",
            "yt_id": "WzT_D_l1vC0"
        },
        {
            "movieNm": "베테랑2", "movieNmEn": "I, THE EXECUTIONER", "prdtYear": "2024",
            "repGenreNm": "액션", "repNationNm": "한국", "directors": [{"peopleNm": "류승완"}],
            "synopsis": "나쁜 놈은 끝까지 잡는 베테랑 서도철 형사의 강력범죄수사대에 막내 형사 박선우가 합류하면서 벌어지는 액션극.",
            "yt_id": "83M8J5b2W2g"
        },
        {
            "movieNm": "인터스텔라", "movieNmEn": "Interstellar", "prdtYear": "2014",
            "repGenreNm": "SF", "repNationNm": "미국", "directors": [{"peopleNm": "크리스토퍼 놀란"}],
            "synopsis": "세계 각국의 정부와 경제가 완전히 붕괴된 미래, 인류의 희망을 찾아 우주로 떠나는 탐사대원들의 이야기.",
            "yt_id": "zSWdZVtXT7E"
        }
    ]
    
    # 키워드 필터링 (샘플 데이터 적용 시)
    if keyword:
        filtered = [m for m in sample_movies if keyword.lower() in m["movieNm"].lower()]
        return filtered, True
    return sample_movies, True


# --- 3. 사용자 검색 조작부 ---
st.markdown("---")
c1, c2 = st.columns([3, 1])

with c1:
    search_input = st.text_input("🔍 특정 단어가 들어간 영화 내에서 뽑고 싶다면 입력하세요 (비워두면 전체 범위):", "")

with c2:
    st.write(" ")
    st.write(" ")
    pick_btn = st.button("🎲 영화 뽑기!", use_container_width=True, type="primary")

api_key = st.secrets.get("KOBIS_KEY")


# --- 4. 랜덤 영화 뽑기 실행 ---
if pick_btn:
    movies, is_sample = fetch_kobis_movies(api_key, search_input)

    if is_sample and not api_key:
        st.info("💡 Secrets에 API 키가 설정되지 않아 데모 영화 데이터셋 모드로 동작합니다.")

    if not movies:
        st.warning("⚠️ 검색 결과에 해당하는 영화가 없습니다. 다른 검색어로 시도해 보세요.")
        st.stop()

    # 랜덤 1개 영화 추출
    picked = random.choice(movies)

    # 데이터 추출
    movie_name = picked.get("movieNm", "제목 미상")
    movie_en = picked.get("movieNmEn", "")
    prdt_year = picked.get("prdtYear", "연도 미상")
    genre = picked.get("repGenreNm", "장르 미상")
    nation = picked.get("repNationNm", "국가 미상")
    
    directors = picked.get("directors", [])
    director_name = directors[0].get("peopleNm") if directors else "정보 없음"
    synopsis = picked.get("synopsis", "KOBIS API 기본 목록 데이터에는 상세 줄거리가 포함되지 않습니다. 아래 포털/유튜브 링크를 활용해 확인해 보세요!")
    yt_id = picked.get("yt_id")

    # 효과 및 결과 표시
    st.balloons()
    st.success(f"🎉 오늘의 추천 영화: **{movie_name}**")

    # 핵심 정보 카드리스트
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("제작 연도", f"{prdt_year}년")
    m2.metric("장르", genre)
    m3.metric("제작 국가", nation)
    m4.metric("감독", director_name)

    # 줄거리 / 영상 / 링크 구역
    st.markdown("---")
    l_col, r_col = st.columns([1, 1])

    with l_col:
        st.subheader("📖 영화 줄거리 & 정보 검색")
        if movie_en:
            st.caption(f"영문 제목: {movie_en}")
        st.write(synopsis)
        
        # 검색 바로가기 버튼
        naver_q = urllib.parse.quote(f"영화 {movie_name} 줄거리 정보")
        st.link_button(f"🔍 네이버에서 '{movie_name}' 검색하기", f"https://search.naver.com/search.naver?query={naver_q}")

    with r_col:
        st.subheader("🎬 예고편 영상")
        if yt_id:
            st.video(f"https://www.youtube.com/watch?v={yt_id}")
        else:
            yt_q = urllib.parse.quote(f"{movie_name} 예고편")
            st.link_button(f"▶️ 유튜브에서 '{movie_name}' 예고편 보기", f"https://www.youtube.com/results?search_query={yt_q}", use_container_width=True)

    # 전체 후보 목록
    st.markdown("---")
    st.subheader(f"📋 추출 범위 전체 목록 (총 {len(movies)}건)")
    df = pd.DataFrame(movies)
    
    # 존재하는 컬럼만 안전하게 표시
    cols_to_show = [c for c in ["movieNm", "prdtYear", "repGenreNm", "repNationNm"] if c in df.columns]
    display_df = df[cols_to_show].copy()
    display_df.columns = ["영화명", "제작연도", "장르", "국가"][:len(cols_to_show)]

    st.dataframe(display_df, use_container_width=True, hide_index=True)
