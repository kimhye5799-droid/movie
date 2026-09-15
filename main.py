import datetime
import numpy as np
import pandas as pd
import pytz
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="어제의 물고기 폐사율 현황", layout="wide")

st.title("🐟 어제의 양식장 물고기 폐사율 현황")


# --- 1. 한국 시간(KST) 기준 '어제' 날짜 계산 ---
def get_yesterday_kst():
    # 서버 시계와 상관없이 한국 표준시(Asia/Seoul) 기준 시각을 가져옵니다.
    tz_kst = pytz.timezone("Asia/Seoul")
    now_kst = datetime.datetime.now(tz_kst)

    # 어제 날짜 계산
    yesterday = now_kst - datetime.timedelta(days=1)

    return yesterday.strftime("%Y%m%d"), yesterday.strftime("%Y년 %m월 %d일")


target_date_str, display_date = get_yesterday_kst()
st.subheader(f"📅 기준일: {display_date}")


# --- 2. 샘플 데이터 생성 함수 (실제 운영 시 DB/API 연동 구역) ---
def load_mortality_data():
    # 데이터 불러오기 시도 (예시용 데이터 생성)
    try:
        # 양식장 수조 목록
        tanks = [f"수조 {i}호" for i in range(1, 11)]

        # random seed를 어제 날짜 숫자로 고정하여 하루 동안은 동일한 데이터가 나오도록 설정
        np.random.seed(int(target_date_str))

        total_fish = np.random.randint(1000, 3000, size=10)  # 총 수량
        dead_fish = np.random.randint(5, 150, size=10)  # 폐사 수량

        df = pd.DataFrame(
            {
                "수조명": tanks,
                "전체수량": total_fish,
                "폐사수량": dead_fish,
            }
        )

        # 폐사율(%) 계산: (폐사수량 / 전체수량) * 100
        df["폐사율"] = (df["폐사수량"] / df["전체수량"]) * 100
        df["폐사율"] = df["폐사율"].round(2)

        # 폐사율이 높은 순서대로 정렬 및 순위 부여
        df = df.sort_values(by="폐사율", ascending=False).reset_index(drop=True)
        df["순위"] = df.index + 1

        return df

    except Exception as e:
        # 데이터 로드 실패 시 None 반환
        return None


# 데이터 불러오기
df = load_mortality_data()


# --- 3. 데이터 검증 및 예외 처리 ---
if df is None:
    st.error("⚠️ 폐사율 데이터를 불러오는 중 오류가 발생했습니다.")
    st.info(
        "데이터베이스 연결 상태나 API 서버 응답을 확인해 주세요."
    )
    st.stop()

if df.empty:
    st.warning("⚠️ 어제 집계된 폐사율 데이터가 없습니다.")
    st.info("기록된 데이터가 없거나 수집 장비 점검 중일 수 있습니다.")
    st.stop()


# --- 4. 주요 지표 카드 표시 (폐사율 1위 수조 및 전체 요약) ---
top_1 = df.iloc[0]
total_all_fish = df["전체수량"].sum()
total_dead_fish = df["폐사수량"].sum()
avg_mortality_rate = round((total_dead_fish / total_all_fish) * 100, 2)

st.markdown("---")
st.write(
    f"⚠️ **최고 폐사율 기록: {top_1['수조명']} ({top_1['폐사율']}%)**"
)

col1, col2, col3 = st.columns(3)
col1.metric(label="전체 양식 수량", value=f"{total_all_fish:,} 마리")
col2.metric(label="어제 총 폐사 수량", value=f"{total_dead_fish:,} 마리")
col3.metric(label="평균 폐사율", value=f"{avg_mortality_rate}%")


# --- 5. 폐사율 상위 5개 수조 막대그래프 시각화 ---
st.markdown("---")
st.write("📊 **폐사율 상위 5개 수조 비교 (%)**")

top_5_df = df.head(5)[["수조명", "폐사율"]].set_index("수조명")
st.bar_chart(top_5_df)


# --- 6. 전체 수조 폐사율 현황 표 출력 ---
st.markdown("---")
st.write("📋 **전체 수조별 집계 목록**")

# 컬럼 순서 정렬
display_df = df[["순위", "수조명", "전체수량", "폐사수량", "폐사율"]]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "전체수량": st.column_config.NumberColumn(format="%d마리"),
        "폐사수량": st.column_config.NumberColumn(format="%d마리"),
        "폐사율": st.column_config.NumberColumn(format="%.2f%%"),
    },
)
