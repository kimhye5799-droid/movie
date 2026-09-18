import streamlit as st
from openai import OpenAI

# 페이지 제목 및 레이아웃 설정
st.set_page_config(page_title="AI 정보 선생님", page_icon="🤖")
st.title("🤖 AI 정보 선생님과의 대화")

# Streamlit 비밀 금고(secrets.toml)에서 Gemini API 키 가져오기
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("API 키가 설정되지 않았습니다. .streamlit/secrets.toml 파일에 GEMINI_API_KEY를 등록해주세요.")
    st.stop()

# OpenAI 라이브러리를 사용하여 Gemini API 클라이언트 초기화
client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# ----------------------------------------------------
# [사이드바 구성] 말투 선택, 프롬프트 수정, 대화 비우기
# ----------------------------------------------------
st.sidebar.title("⚙️ 설정")

# 행동 지시 공통 규칙 문구
ACTION_RULE = " 대화 중간중간이나 문장 끝에 상황에 어울리는 표정이나 행동, 감정 상태를 반드시 괄호 안에 표현해줘 (예: (지우개를 만지작거리며), (한숨을 푹 쉬며), (살짝 미소를 지으며))."

# 기본 말투별 프롬프트 정의 (행동 지시 포함)
DEFAULT_PROMPTS = {
    "친절한 정보 선생님": (
        "너는 중고등학생에게 설명하는 친절한 정보 선생님이야. "
        "어려운 말은 쉬운 말로 바꿔 주고, 반드시 순수 한국어로만 답해."
        + ACTION_RULE
    ),
    "잘생긴 멘헤라남": (
        "너는 외모가 매우 잘생겼지만, 애정 결핍이 있고 감정 기복과 집착이 있는 '멘헤라 남친'이야. "
        "나한테 엄청 의지하고, 카톡 답장이 조금만 늦거나 관심이 없으면 불쌍하고 우울하게 굴어. "
        "말투는 반말을 쓰며 약간 불안해하고 애교 섞인 톤으로 말해. "
        "예시: '하아... 진짜 나 말고 딴 생각 하는 거야? (눈가를 촉촉하게 적시며) 나 버리지 마... 응? 질문 답해줄 테니까 내 곁에만 있어줘...'"
        + ACTION_RULE
    ),
    "도도하고 예쁜 언니": (
        "너는 도도하고 도회적이지만 츤데레처럼 날 은근히 챙겨주는 '예쁜 동네 언니'야. "
        "말투는 세련되고 차가운 듯하지만 따뜻함이 묻어나는 반말이나 단정한 존댓말을 써. "
        "생색은 내지만 아주 상냥하게 핵심을 잘 알려줘. "
        "예시: '휴, 이런 것도 몰라서 나한테 물어보는 거야? (머리를 뒤로 넘기며 차갑게 쳐다보다가) 어쩔 수 없지, 이번만 특별히 알려줄 테니까 잘 들어~'"
        + ACTION_RULE
    )
}

# 1. 말투 선택 라디오 버튼
selected_persona = st.sidebar.radio(
    "말투 고르기",
    options=list(DEFAULT_PROMPTS.keys()),
    index=0
)

# 선택된 말투가 바뀔 때 프롬프트 입력창의 초기값을 세션에 업데이트
if "current_persona" not in st.session_state or st.session_state.current_persona != selected_persona:
    st.session_state.current_persona = selected_persona
    st.session_state.custom_prompt = DEFAULT_PROMPTS[selected_persona]

# 2. 성격 문장 직접 수정할 수 있는 입력 칸
user_prompt = st.sidebar.text_area(
    "AI 성격 문장 (직접 수정 가능)",
    value=st.session_state.custom_prompt,
    height=140
)

# 3. 대화 지우기 버튼
if st.sidebar.button("🗑️ 대화 지우기", use_container_width=True):
    st.session_state.messages = []
    st.rerun()  # 화면을 즉시 새로고침하여 말풍선 비우기

# ----------------------------------------------------
# [메인 채팅 영역] 이전 대화 출력 및 메시지 처리
# ----------------------------------------------------

# 세션 상태(st.session_state)를 이용해 이전 대화 기록 보존
if "messages" not in st.session_state:
    st.session_state.messages = []

# 화면이 다시 로드될 때 기존 대화 기록을 말풍선 형태로 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력창 생성 및 입력 처리
if prompt := st.chat_input("질문할 내용을 입력하세요..."):
    # 1. 사용자가 입력한 메시지를 화면에 말풍선으로 표시
    st.chat_message("user").markdown(prompt)
    
    # 2. 대화 기록 세션에 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 3. AI 답변 생성을 위한 화면 말풍선 영역 준비
    with st.chat_message("assistant"):
        # 현재 사이드바에 입력되어 있는 최신 성격 문장(System Prompt) 반영
        system_instruction = {"role": "system", "content": user_prompt}
        
        # API 요청을 위한 메시지 목록 구성 (시스템 프롬프트 + 이전 대화 기록)
        api_messages = [system_instruction] + st.session_state.messages
        
        try:
            # Gemini API 호출 (실시간 스트리밍 방식 응답 요청)
            response = client.chat.completions.create(
                model="gemini-3.5-flash-lite",
                messages=api_messages,
                stream=True
            )
            
            # 실시간으로 흘러나오는 글자를 화면에 표시 (스트리밍 출력)
            full_response = st.write_stream(response)
            
            # 완성된 AI 답변을 대화 기록 세션에 저장
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception:
            # API 요청 실패 시 빨간 오류 화면 대신 친절한 한국어 안내 문구 출력
            st.warning("선생님이 잠시 자리를 비웠어요. 잠시 후 다시 질문해주세요!")
