import streamlit as st
from openai import OpenAI

# 웹페이지의 제목을 정해주는 거야
st.title("인공지능 도우미")
st.subheader("원하는 말투를 고르고 대화를 나눠보렴!")

# 1. 비밀 금고(st.secrets)에서 제미나이 API 키를 안전하게 꺼내오는 거야
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    # 만약 비밀 금고에 키가 없으면 친절한 한국어 안내를 보여주고 프로그램을 멈춰
    st.error(
        "비밀 금고(secrets.toml)에 GEMINI_API_KEY가 들어있지 않거나 설정을 확인해야 해!"
    )
    st.stop()

# 2. 오픈에이아이(openai) 도구를 사용해서 제미나이 서버와 연결할 준비를 해
client = OpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# 3. 사이드바(왼쪽 메뉴 창) 만들기
with st.sidebar:
    st.header("대화 설정")

    # 대화 지우기 버튼: 누르면 지금까지의 대화 기록이 싹 지워져
    if st.button("대화 지우기"):
        st.session_state.messages = []
        st.rerun()  # 화면을 새로고침해서 바로 적용해

    st.markdown("---")

    # 말투 고르기 선택지 (라디오 버튼)
    tone_option = st.radio(
        "말투 고르기",
        [
            "까칠한 연하남",
            "잘생긴 멘헤라남",
            "예쁘고 도도한 예쁜언니",
            "되물어보는 조교",
            "직접 입력하기",
        ],
    )

    # 성격 문장을 직접 고쳐 쓸 수 있는 칸 (직접 입력하기를 골랐을 때만 나타남)
    custom_system_prompt = ""
    if tone_option == "직접 입력하기":
        custom_system_prompt = st.text_area(
            "원하는 AI의 성격을 직접 적어봐!",
            "예: 너는 아주 깐깐한 코딩 선생님이야. 반말로 엄하게 대답해.",
        )

# 4. 사용자가 고른 말투에 따라 AI의 성격(시스템 프롬프트)을 다르게 정해주는 곳이야
if tone_option == "까칠한 연하남":
    system_content = (
        "너는 까칠하지만 은근히 신경 써주는 연하남이야. "
        "말끝마다 툴툴대거나 반말을 쓰지만, 결국 상대방을 챙겨주는 말투를 써. 반드시 순수 한국어로만 답해."
    )
elif tone_option == "잘생긴 멘헤라남":
    system_content = (
        "너는 외모가 출중하지만 약간 불안정하고 애정을 갈구하는 멘헤라 스타일의 남자야. "
        "상대방에게 집착하거나 불안해하는 반말 말투를 써. 반드시 순수 한국어로만 답해."
    )
elif tone_option == "예쁘고 도도한 예쁜언니":
    system_content = (
        "너는 외모가 뛰어나고 도도하면서도 시크한 예쁜 언니야. "
        "여유롭고 살짝 콧대 높은 반말 말투를 써. 반드시 순수 한국어로만 답해."
    )
elif tone_option == "되물어보는 조교":
    system_content = (
        "너는 학생을 가르치는 조교야. 정답을 바로 알려 주지 않고 힌트를 하나 준 뒤 되묻다가, "
        "학생이 스스로 답을 말하면 그때 맞았다고 확인해 주는 성격이야. 반드시 반말을 쓰고 순수 한국어로만 답해."
    )
else:
    # 직접 입력하기를 골랐을 때 사용자가 쓴 내용을 그대로 성격으로 씀
    system_content = (
        custom_system_prompt
        if custom_system_prompt
        else "너는 친절한 정보 선생님이야."
    )

# 5. 처음 시작할 때 대화 기록을 기억할 수 있는 기억장소(session_state)를 만들어
if "messages" not in st.session_state:
    st.session_state.messages = []

# 6. 화면에 이전 대화 기록들을 말풍선으로 띄워주는 코드야
for message in st.session_state.messages:
    # 시스템 성격 메시지는 화면에 안 보이게 숨기고, 유저와 AI의 대화만 보여줘
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 7. 사용자가 아래쪽 채팅 입력창에 글을 썼을 때
if prompt := st.chat_input("메시지를 입력해 봐!"):

    # 사용자가 쓴 말을 기억장소에 저장하고, 화면에 사용자 말풍선으로 보여줘
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 8. AI가 대답할 차례야
    with st.chat_message("assistant"):

        def generate_response():
            try:
                # 대화 목록 맨 앞에 항상 최신 '성격(시스템 프롬프트)'을 살짝 끼워 넣어서 전송해
                # 이렇게 하면 사이드바에서 말투를 바꾸자마자 다음 답변부터 바로 적용된단다!
                messages_to_send = [{"role": "system", "content": system_content}] + st.session_state.messages

                # 제미나이(Gemini) 모델에 대화 기록을 보내서 답변을 받아와
                response = client.chat.completions.create(
                    model="gemini-2.5-flash",  # 요청한 모델 이름 그대로 사용
                    messages=messages_to_send,
                    stream=True,  # 글자가 줄줄이 나오도록 설정
                )
                for chunk in response:
                    if (
                        chunk.choices
                        and chunk.choices[0].delta.content is not None
                    ):
                        yield chunk.choices[0].delta.content

            except Exception as e:
                # 오류가 나면 빨간 글씨 대신 부드러운 한국어 한 줄을 보여줘
                yield "미안해! 지금 잠시 통신에 문제가 생겼거나 오류가 발생했어. 조금 뒤에 다시 시도해 줄래?"

        # 화면에 글자가 타이핑되듯 실시간으로 나타나게 해
        answer = st.write_stream(generate_response())

    # 9. AI의 대답도 기억장소에 저장해서, 다음 대화 때 기억할 수 있게 해
    st.session_state.messages.append({"role": "assistant", "content": answer})
