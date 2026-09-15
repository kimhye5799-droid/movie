import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="어제의 영화 박스오피스", layout="wide")

st.title("🎬 어제의 영화 박스오피스 TOP 10")


# --- 1. 한국 시간(KST) 기준 '어제' 날짜 계산 ---
def get_yesterday_kst():
    # 서버 시계 설정과 상관없이 한국 표준시(Asia/Seoul) 기준 시각을 가져옵니다.
    tz_kst = pytz.timezone("Asia/Seoul")
    now_kst = datetime.datetime.now(tz_kst)

    # 어제 날짜 계산
    yesterday = now_kst - datetime.timedelta(days=1)

    # API 형식(YYYYMMDD)과 화면 표시용 형식(YYYY-MM-DD)으로 반환
    return yesterday.strftime("%Y%m%d"), yesterday.strftime("%Y년 %m월 %d일")


target_date_str, display_date = get_yesterday_kst()
st.subheader(f"📅 기준일: {display_date}")

# --- 2. secrets에서 인증키 불러오기 ---
# Streamlit Cloud의 Secrets 설정에서 'KOBIS_KEY'를 읽어옵니다.
api_key = st.secrets.get("KOBIS_KEY")

if not api_key:
    st.error("🔑 Secrets에서 인증키(KOBIS_KEY)를 찾을 수 없습니다.")
    st.info(
        "Streamlit Cloud 설정(Settings -> Secrets)에 KOBIS_KEY = '발급받은키' 형태로 등록되었는지 확인해 주세요."
    )
    st.stop()


# --- 3. KOBIS API 데이터 요청 ---
url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
params = {"key": api_key, "targetDt": target_date_str}

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()  # HTTP status error 체크
    data = response.json()
except requests.exceptions.RequestException as e:
    st.error("⚠️ 영화 진흥 위원회 API 서버와의 통신에 실패했습니다.")
    st.write("네트워크 연결 상태나 API 주소를 확인해 주세요.")
    st.stop()


# --- 4. 응답 예외 처리 및 데이터 검증 ---
# API 오류 응답(faultInfo)이 포함되어 있는지 확인
if "faultInfo" in data:
    st.error("⚠️ API 호출 중 오류가 발생했습니다.")
    st.write(
        f"**오류 메시지:** {data['faultInfo'].get('message', '알 수 없는 오류')}"
    )
    st.info(
        "Secrets에 입력한 KOBIS 인증키가 올바른지, 사용량이 초과되지 않았는지 확인해 주세요."
    )
    st.stop()

# 영화 목록 데이터 추출
boxoffice_result = data.get("boxOfficeResult", {})
daily_list = boxoffice_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning("⚠️ 조회된 박스오피스 데이터가 없습니다.")
    st.info(
        "해당 날짜의 데이터가 아직 업데이트되지 않았거나, KOBIS 서비스에 점검이 있을 수 있습니다."
    )
    st.stop()


# --- 5. 데이터 가공 (문자열 -> 숫자 변환) ---
df = pd.DataFrame(daily_list)

# 필요한 숫자 컬럼들을 정수형(int)으로 변환
int_columns = ["rank", "audiCnt", "audiAcc", "scrnCnt"]
for col in int_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)


# --- 6. 1위 영화 주요 지표 카드 표시 ---
top_1 = df[df["rank"] == 1].iloc[0]

st.markdown("---")
st.write(f"🏆 **1위 영화: {top_1['movieNm']}**")

col1, col2, col3 = st.columns(3)
col1.metric(label="당일 관객수", value=f"{top_1['audiCnt']:,} 명")
col2.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")
col3.metric(label="스크린수", value=f"{top_1['scrnCnt']:,} 개")


# --- 7. 상위 5개 영화 관객수 막대그래프 시각화 ---
st.markdown("---")
st.write("📊 **상위 5개 영화 당일 관객수 비교**")

top_5_df = df.head(5)[["movieNm", "audiCnt"]]
# 막대그래프 출력을 위해 영화명을 인덱스로 지정
top_5_df = top_5_df.set_index("movieNm")
st.bar_chart(top_5_df)


# --- 8. 전체 박스오피스 순위 표 출력 ---
st.markdown("---")
st.write("📋 **전체 순위 목록**")

# 화면에 보여줄 컬럼 선택 및 이름 변경
display_df = df[
    ["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]
].copy()
display_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수",
]

# 숫자에 천 단위 쉼표(,) 적용하여 표로 출력
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
