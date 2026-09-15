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

# --- 1. 영화관 분위기의 다크모드 CSS 커스텀 ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0f1117;
        color: #e0e0e0;
    }
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

st.markdown('<div class="main-title">🍿 어제의 CINEMA 박스오피스</div>', unsafe_allow_html=True)


# --- 2. 한국 시간(KST) 기준 '어제' 날짜 계산 ---
def get_yesterday_kst():
    tz_kst = pytz.timezone("Asia/Seoul")
    now_kst = datetime.datetime.now(tz_kst)
    yesterday = now_kst - datetime.timedelta(days=1)
    return yesterday.strftime("%Y%m%d"), yesterday.strftime("%Y년 %m월 %d일")

target_date_str, display_date = get_yesterday_kst()
st.markdown(f'<div class="sub-title">📅 기준일자: {display_date}</div>', unsafe_allow_html=True)


# --- 3. 데이터 로드 함수 (API 실패 시 샘플 데이터로 자동 대체) ---
def load_boxoffice_data(api_key):
    use_sample = False
    
    if api_key:
        url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
        try:
            res = requests.get(url, params={"key": api_key, "targetDt": target_date_str}, timeout=5)
            data = res.json()
            
            # API 키 오류나 다른 오류가 없을 때만 실제 데이터 사용
            if "faultInfo" not in data and "boxOfficeResult" in data:
                daily_list = data["boxOfficeResult"].get("dailyBoxOfficeList", [])
                if daily_list:
                    return daily_list, False
        except Exception:
            pass

    # API 호출 실패/키 오류 시 데모용 샘플 데이터 제공
    sample_data = [
        {
            "rank": "1", "movieNm": "파묘", "openDt": "2024-02-22",
            "audiCnt": "125430", "audiAcc": "11900000", "scrnCnt": "1850",
            "director": "장재현", "genre": "미스터리, 공포", "actor": "최민식, 김고은, 유해진",
            "synopsis": "미국 LA, 거액의 의뢰를 받은 무당 화림과 봉길은 기이한 병이 대대로 물려려오는 집안의 장손을 만난다. 조상의 묫자리가 화근임을 눈치챈 화림은 이장을 권하고, 돈 냄새를 맡은 풍수사 상덕과 장의사 영근이 합류하면서 악지가 드러나는데...",
            "yt_video_id": "tA3zs_8E9i8" # 실제 파묘 예고편 YouTube ID
        },
        {
            "rank": "2", "movieNm": "범죄도시4", "openDt": "2024-04-24",
            "audiCnt": "98420", "audiAcc": "11500000", "scrnCnt": "1620",
            "director": "허명행", "genre": "범죄, 액션", "actor": "마동석, 김무열, 이동휘",
            "synopsis": "신종 마약 사건 조사 중, 괴물형사 마석도는 배달앱을 이용한 마약 판매 사건이 온라인 불법 도박 조직과 연관되어 있음을 알게 된다. 앱 개발자가 필리핀에서 살해당하자 대형 온라인 불법 도박 조직을 소탕하기 위한 작전을 시작한다.",
            "yt_video_id": "i42a1Ea1x1s"
        },
        {
            "rank": "3", "movieNm": "인사이드 아웃 2", "openDt": "2024-06-12",
            "audiCnt": "85120", "audiAcc": "8700000", "scrnCnt": "1410",
            "director": "캘시 맨", "genre": "애니메이션", "actor": "다니엘 맥도널드",
            "synopsis": "13살이 된 라일리의 머릿속 감정 컨트롤 본부에 불안, 당황, 따분, 시기 등 새로운 감정들이 찾아오면서 기존 감정들과 충돌이 벌어지는 이야기.",
            "yt_video_id": "WzT_D_l1vC0"
        },
        {
            "rank": "4", "movieNm": "베테랑2", "openDt": "2024-09-13",
            "audiCnt": "64200", "audiAcc": "7500000", "scrnCnt": "1200",
            "director": "류승완", "genre": "액션, 범죄", "actor": "황정민, 정해인",
            "synopsis": "나쁜 놈은 끝까지 잡는 베테랑 서도철 형사의 강력범죄수사대에 막내 형사 박선우가 합류하면서 세상을 떠들썩하게 한 연쇄살인범을 쫓는 액션 범죄극.",
            "yt_video_id": "83M8J5b2W2g"
        },
        {
            "rank": "5", "movieNm": "훠궈의 맛", "openDt": "2024-08-01",
            "audiCnt": "32100", "audiAcc": "450000", "scrnCnt": "800",
            "director": "감독 정보", "genre": "드라마", "actor": "배우 정보",
            "synopsis": "흥미진진한 음식과 인간관계를 다룬 이야기입니다.",
            "yt_video_id": "tA3zs_8E9i8"
        }
    ]
    return sample_data, True


# 데이터 로드 실행
api_key = st.secrets.get("KOBIS_KEY")
raw_data, is_sample = load_boxoffice_data(api_key)

if is_sample:
    st.warning("💡 API 키가 없거나 유효하지 않아 [데모 샘플 데이터] 모드로 표시 중입니다.")


# --- 4. 데이터 전처리 ---
df = pd.DataFrame(raw_data)
int_cols = ["rank", "audiCnt", "audiAcc", "scrnCnt"]
for col in int_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)


# --- 5. 🏆 1위 영화 상세 정보 & 줄거리 / 예고편 영상 ---
top_1 = df[df["rank"] == 1].iloc[0]

st.subheader(f"🥇 어제의 1위 영화: {top_1['movieNm']}")

col1, col2, col3 = st.columns(3)
col1.metric("당일 관객수", f"{top_1['audiCnt']:,} 명")
col2.metric("누적 관객수", f"{top_1['audiAcc']:,} 명")
col3.metric("스크린수", f"{top_1['scrnCnt']:,} 개")

st.markdown("---")
st.subheader("🎬 1위 영화 상세 줄거리 & 예고편")

left_col, right_col = st.columns([1, 1])

with left_col:
    genre = top_1.get("genre", "정보 없음")
    director = top_1.get("director", "정보 없음")
    actor = top_1.get("actor", "정보 없음")
    synopsis = top_1.get("synopsis", "줄거리 정보는 포털 검색을 이용해 주세요.")
    
    st.markdown(f"**🎭 장르:** {genre}")
    st.markdown(f"**🎬 감독:** {director}")
    st.markdown(f"**👥 출연:** {actor}")
    st.markdown("**📖 줄거리:**")
    st.write(synopsis)
    
    # 네이버 검색 버튼
    q_str = urllib.parse.quote(f"영화 {top_1['movieNm']} 정보")
    st.link_button(f"🔍 네이버에서 '{top_1['movieNm']}' 상세 검색", f"https://search.naver.com/search.naver?query={q_str}")

with right_col:
    yt_id = top_1.get("yt_video_id")
    if yt_id:
        st.video(f"https://www.youtube.com/watch?v={yt_id}")
    else:
        yt_q = urllib.parse.quote(f"{top_1['movieNm']} 예고편")
        st.link_button(f"▶️ 유튜브에서 예고편 검색하기", f"https://www.youtube.com/results?search_query={yt_q}", use_container_width=True)


# --- 6. 📊 관객수 상위 5개 막대그래프 ---
st.markdown("---")
st.subheader("📊 TOP 5 영화 당일 관객수 비교")

top5_df = df.head(5)[["movieNm", "audiCnt"]].set_index("movieNm")
st.bar_chart(top5_df)


# --- 7. 📋 전체 순위 목록 표 ---
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
