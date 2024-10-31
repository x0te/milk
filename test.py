import streamlit as st
from openai import OpenAI
import requests
import json
from typing import Dict
import time
import random
import io
import base64
from PIL import Image
from streamlit_extras.stylable_container import stylable_container

# CSS 스타일 정의
def apply_custom_css():
    st.markdown("""
        <style>
            .main .block-container {
                padding-top: 0;
                max-width: 1200px;
            }
            
            .stTextInput > div > div > input {
                background-color: #FFFFFF;
                border: 1px solid #E6E8EB;
                border-radius: 6px;
                padding: 0.75rem 1rem;
                font-size: 1rem;
                color: #1F2937;
                transition: border-color 0.2s, box-shadow 0.2s;
            }
            
            .stTextInput > div > div > input:focus {
                border-color: #1756A9;
                box-shadow: 0 0 0 2px rgba(23, 86, 169, 0.1);
            }
            
            .stChatMessage {
                background-color: transparent !important;
                border: none !important;
            }
            
            .stChatMessage [data-testid="StyledLinkIconContainer"] {
                display: none;
            }
            
            .stButton > button {
                width: 100%;
                border-radius: 6px;
                font-weight: 500;
                transition: all 0.2s;
            }
            
            .stProgress > div > div > div {
                background-color: #1756A9;
            }
            
            ::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: #F1F1F1;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #C5C5C5;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #A8A8A8;
            }
            
            section[data-testid="stSidebar"] {
                background-color: #FFFFFF;
                border-right: 1px solid #E6E8EB;
            }
            
            .stMarkdown {
                color: #1F2937;
            }
        </style>
    """, unsafe_allow_html=True)

# 이미지 로딩 최적화를 위한 캐싱
@st.cache_data
def load_image(url):
    try:
        return Image.open(requests.get(url, stream=True).raw)
    except Exception as e:
        st.error(f"이미지 로딩 중 오류 발생: {str(e)}")
        return None

class OpenAIClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def create_assistant(self, instructions: str, model: str, tools: list):
        try:
            return self.client.beta.assistants.create(
                name="SF49 Studio Designer",
                instructions=instructions,
                model=model,
                tools=tools
            )
        except Exception as e:
            st.error(f"Assistant 생성 중 오류 발생: {str(e)}")
            return None

class WebhookHandler:
    def __init__(self, base_url: str, send_webhook: str, retrieve_webhook: str):
        self.base_url = base_url
        self.send_webhook = send_webhook
        self.retrieve_webhook = retrieve_webhook

    def send_image_data(self, visualization_text: str, unique_id: str) -> Dict:
        try:
            url = f"{self.base_url}{self.send_webhook}"
            payload = {
                "imageData": visualization_text,
                "uniqueId": unique_id
            }
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return {
                "success": True,
                "message": "이미지 생성이 시작되었습니다",
                "unique_id": unique_id
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"이미지 생성 요청 중 오류가 발생했습니다: {str(e)}",
                "unique_id": unique_id
            }

    def get_image_links(self, unique_id: str) -> Dict:
        try:
            url = f"{self.base_url}{self.retrieve_webhook}"
            payload = {"uniqueId": unique_id}
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if "images" in result and isinstance(result["images"], list) and len(result["images"]) > 0:
                return {
                    "success": True,
                    "images": result["images"],
                    "message": "이미지가 성공적으로 생성되었습니다!"
                }
            else:
                return {
                    "success": False,
                    "images": [],
                    "message": "이미지가 아직 준비되지 않았습니다."
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "images": [],
                "message": f"이미지 조회 중 오류가 발생했습니다: {str(e)}"
            }

class SF49StudioAssistant:
    def __init__(self, openai_client: OpenAIClient, webhook_handler: WebhookHandler):
        self.client = openai_client
        self.webhook_handler = webhook_handler
        self.assistant = None
        self.thread = None

    def create_thread(self):
        self.thread = self.client.client.beta.threads.create()
        return self.thread

    def create_assistant(self):
        instructions = """
        당신은 SF49 Studio의 전문 디자이너입니다.
        사용자의 요청을 신중히 듣고 최적의 디자인을 제안합니다.
        항상 친절하고 전문적인 태도를 유지하며,
        디자인 과정에서 발생할 수 있는 문제에 대해 적절한 해결책을 제시합니다.
        """
        self.assistant = self.client.create_assistant(
            instructions=instructions,
            model="gpt-4o-mini",
            tools=[{
                "type": "function",
                "function": {
                    "name": "send_image_request",
                    "description": "이미지 생성을 위한 시각화 텍스트와 ID를 웹훅으로 전송",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "visualization_text": {
                                "type": "string",
                                "description": "시각화를 위한 상세 텍스트"
                            },
                            "unique_id": {
                                "type": "string",
                                "description": "이미지의 고유 ID"
                            }
                        },
                        "required": ["visualization_text", "unique_id"]
                    }
                }
            }]
        )
        return self.assistant

    def process_message(self, user_message: str) -> Dict:
        try:
            if self.thread is None:
                self.create_thread()

            if 'cancel_generation' in st.session_state:
                del st.session_state.cancel_generation

            message = self.client.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=user_message
            )

            run = self.client.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id
            )

            generated_id = None
            progress_placeholder = st.empty()
            
            while True:
                run = self.client.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=run.id
                )

                if run.status == "requires_action":
                    tool_outputs = []
                    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                        if tool_call.function.name == "send_image_request":
                            args = json.loads(tool_call.function.arguments)
                            result = self.webhook_handler.send_image_data(
                                args["visualization_text"],
                                args["unique_id"]
                            )
                            generated_id = result["unique_id"]
                            
                            if not result["success"]:
                                return {
                                    "status": "error",
                                    "response": result["message"]
                                }

                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": json.dumps(result)
                            })

                    self.client.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=self.thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )

                    if generated_id:
                        progress_messages = [
                            "🎨 디자인 컨셉을 구상 중입니다...",
                            "✨ 시각적 요소를 배치하고 있습니다...",
                            "🖌️ 디테일을 다듬고 있습니다...",
                            "🔍 최종 점검 중입니다...",
                            "✅ 마무리 작업을 진행 중입니다..."
                        ]
                        
                        with stylable_container(
                            key="progress_container",
                            css_styles="""
                            {
                                background-color: #F0F2F6;
                                padding: 1rem;
                                border-radius: 8px;
                                margin: 1rem 0;
                                border: 1px solid #E6E8EB;
                            }
                            """
                        ):
                            progress_bar = progress_placeholder.progress(0)
                            status_text = st.empty()
                            
                            for i in range(1000):
                                if 'cancel_generation' in st.session_state and st.session_state.cancel_generation:
                                    progress_bar.empty()
                                    status_text.empty()
                                    return {
                                        "status": "cancelled",
                                        "response": "🚫 이미지 생성이 취소되었습니다."
                                    }

                                if i % 20 == 0:
                                    status_text.markdown(f"**{random.choice(progress_messages)}**")
                                
                                progress_bar.progress((i + 1) // 10)
                                time.sleep(0.1)

                            progress_bar.empty()
                            status_text.empty()

                        with stylable_container(
                            key="cancel_button_container",
                            css_styles="""
                            button {
                                background-color: #DC2626;
                                color: white;
                                border-radius: 6px;
                                border: none;
                                padding: 0.75rem;
                                width: 100%;
                                margin-top: 0.5rem;
                                transition: all 0.2s;
                            }
                            button:hover {
                                background-color: #B91C1C;
                                transform: translateY(-1px);
                            }
                            """
                        ):
                            cancel_button = st.button(
                                "🚫 생성 취소",
                                key="cancel_generation",
                                help="현재 진행 중인 이미지 생성을 취소합니다"
                            )

                        result = self.webhook_handler.get_image_links(generated_id)
                        if result["success"] and result["images"]:
                            st.balloons()
                            return {
                                "status": "success",
                                "response": "✨ 디자인이 완성되었습니다! 마음에 드시는 결과물이 있으신가요?",
                                "images": result["images"]
                            }
                        else:
                            return {
                                "status": "error",
                                "response": "🎨 이미지 생성에 시간이 더 필요합니다. 잠시 후에 다시 시도해 주세요."
                            }

                elif run.status == "completed":
                    messages = self.client.client.beta.threads.messages.list(
                        thread_id=self.thread.id
                    )
                    return {
                        "status": "success",
                        "response": messages.data[0].content[0].text.value
                    }

                elif run.status == "failed":
                    return {
                        "status": "error",
                        "response": "⚠️ 처리 중 문제가 발생했습니다. 다시 시도해주세요."
                    }
                
                time.sleep(0.5)

        except Exception as e:
            st.error(f"예상치 못한 오류가 발생했습니다: {str(e)}")
            return {
                "status": "error",
                "response": "⚠️ 서비스 처리 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

def main():
    st.set_page_config(
        page_title="SF49 Studio Designer",
        page_icon="✨",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 커스텀 CSS 적용
    apply_custom_css()

    # 헤더 섹션
    with stylable_container(
        key="header_container",
        css_styles="""
        {
            background-color: #1756A9;
            padding: 1.5rem 2rem;
            margin-bottom: 2rem;
            color: white;
        }
        """
    ):
        st.markdown("""
            <h1 style='font-size: 2.5rem; font-weight: 600; margin-bottom: 0.5rem; letter-spacing: -0.5px; display: flex; align-items: center; gap: 0.5rem;'>
                ✨ SF49 Studio Designer
            </h1>
            <h3 style='font-size: 1.25rem; font-weight: 400; opacity: 0.9; margin-top: 0; letter-spacing: -0.3px;'>
                AI 기반 디자인 스튜디오
            </h3>
        """, unsafe_allow_html=True)

    openai_client = OpenAIClient(api_key=st.secrets["openai_api_key"])
    webhook_handler = WebhookHandler(
        base_url="https://hook.eu2.make.com",
        send_webhook="/l1b22zor5v489mjyc6mgr8ybwliq763v",
        retrieve_webhook="/7qia4xlc2hvxt1qs1yr5eh7g9nqs8brd"
    )
    assistant = SF49StudioAssistant(openai_client, webhook_handler)
    
    if not assistant.assistant:
        assistant.create_assistant()

    # 인트로 메시지
    if 'shown_intro' not in st.session_state:
        with stylable_container(
            key="intro_container",
            css_styles="""
            {
                background-color: #F8FAFC;
                padding: 1.5rem;
                border-radius: 8px;
                border: 1px solid #E2E8F0;
                margin-bottom: 1.5rem;
            }
            """
        ):
            st.markdown("""
                <div style='color: #1F2937;'>
                    <h3 style='margin: 0 0 0.5rem 0; font-weight: 600;'>환영합니다! 👋</h3>
                    <p style='margin: 0; color: #4B5563; line-height: 1.6;'>
                        원하시는 이미지를 자연스럽게 설명해 주세요.<br>
                        최적의 디자인으로 구현해드리겠습니다.
                    </p>
                </div>
            """, unsafe_allow_html=True)
        st.session_state.shown_intro = True

    chat_container = st.container()
    
    with chat_container:
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        # 메시지 표시
        for message in st.session_state.messages:
            with stylable_container(
                key=f"message_{hash(str(message))}",
                css_styles=f"""
                {{
                    background-color: {'#F8FAFC' if message["role"] == "user" else '#FFFFFF'};
                    padding: 1.25rem;
                    border-radius: 8px;
                    margin: 0.75rem 0;
                    border: 1px solid #E2E8F0;
                }}
                """
            ):
                st.markdown(message["content"])
                
                if "image_urls" in message:
                    cols = st.columns(2)
                    for idx, url in enumerate(message["image_urls"]):
                        with cols[idx % 2]:
                            with stylable_container(
                                key=f"image_container_{idx}_{hash(url)}",
                                css_styles="""
                                {
                                    background-color: #FFFFFF;
                                    padding: 1rem;
                                    border-radius: 8px;
                                    margin: 0.75rem 0;
                                    border: 1px solid #E2E8F0;
                                    transition: transform 0.2s ease;
                                }
                                :hover {
                                    transform: translateY(-2px);
                                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                                }
                                """
                            ):
                                image = load_image(url)
                                if image:
                                    st.image(image, use_column_width=True)
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        with stylable_container(
                                            key=f"download_button_{idx}_{hash(url)}",
                                            css_styles="""
                                            button {
                                                background-color: #059669;
                                                color: white;
                                                border-radius: 6px;
                                                border: none;
                                                width: 100%;
                                                padding: 0.75rem;
                                                font-size: 0.875rem;
                                                font-weight: 500;
                                                transition: all 0.2s;
                                            }
                                            button:hover {
                                                background-color: #047857;
                                                transform: translateY(-1px);
                                            }
                                            """
                                        ):
                                            buffer = io.BytesIO()
                                            image.save(buffer, format="PNG")
                                            btn = st.download_button(
                                                label="💾 다운로드",
                                                data=buffer.getvalue(),
                                                file_name=f"SF49_Design_{idx + 1}.png",
                                                mime="image/png"
                                            )
                                    
                                    with col2:
                                        with stylable_container(
                                            key=f"view_button_{idx}_{hash(url)}",
                                            css_styles="""
                                            button {
                                                background-color: #1756A9;
                                                color: white;
                                                border-radius: 6px;
                                                border: none;
                                                width: 100%;
                                                padding: 0.75rem;
                                                font-size: 0.875rem;
                                                font-weight: 500;
                                                transition: all 0.2s;
                                            }
                                            button:hover {
                                                background-color: #1148A0;
                                                transform: translateY(-1px);
                                            }
                                            """
                                        ):
                                            st.markdown(f'<a href="{url}" target="_blank"><button style="width:100%;padding:0.75rem;">🔍 크게 보기</button></a>', unsafe_allow_html=True)

        # 채팅 입력
        with stylable_container(
            key="chat_input_container",
            css_styles="""
            {
                background-color: #FFFFFF;
                padding: 1.5rem;
                border-radius: 8px;
                margin-top: 1rem;
                border: 1px solid #E2E8F0;
                position: sticky;
                bottom: 0;
            }
            """
        ):
            if prompt := st.chat_input("어떤 이미지를 만들어드릴까요?"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                with st.chat_message("user", avatar="👤"):
                    st.markdown(prompt)

                response = assistant.process_message(prompt)
                
                if response["status"] == "success":
                    with st.chat_message("assistant", avatar="✨"):
                        st.markdown(response["response"])
                        message = {"role": "assistant", "content": response["response"]}
                        
                        if "images" in response and response["images"]:
                            message["image_urls"] = response["images"]
                            cols = st.columns(2)
                            for idx, url in enumerate(response["images"]):
                                with cols[idx % 2]:
                                    with stylable_container(
                                        key=f"new_image_container_{idx}_{hash(url)}",
                                        css_styles="""
                                        {
                                            background-color: #FFFFFF;
                                            padding: 1rem;
                                            border-radius: 8px;
                                            margin: 0.75rem 0;
                                            border: 1px solid #E2E8F0;
                                            transition: transform 0.2s ease;
                                        }
                                        :hover {
                                            transform: translateY(-2px);
                                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                                        }
                                        """
                                    ):
                                        image = load_image(url)
                                        if image:
                                            st.image(image, use_column_width=True)
                                            
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                with stylable_container(
                                                    key=f"new_download_button_{idx}_{hash(url)}",
                                                    css_styles="""
                                                    button {
                                                        background-color: #059669;
                                                        color: white;
                                                        border-radius: 6px;
                                                        border: none;
                                                        width: 100%;
                                                        padding: 0.75rem;
                                                        font-size: 0.875rem;
                                                        font-weight: 500;
                                                        transition: all 0.2s;
                                                    }
                                                    button:hover {
                                                        background-color: #047857;
                                                        transform: translateY(-1px);
                                                    }
                                                    """
                                                ):
                                                    buffer = io.BytesIO()
                                                    image.save(buffer, format="PNG")
                                                    btn = st.download_button(
                                                        label="💾 다운로드",
                                                        data=buffer.getvalue(),
                                                        file_name=f"SF49_Design_{idx + 1}.png",
                                                        mime="image/png"
                                                    )
                                            
                                            with col2:
                                                with stylable_container(
                                                    key=f"new_view_button_{idx}_{hash(url)}",
                                                    css_styles="""
                                                    button {
                                                        background-color: #1756A9;
                                                        color: white;
                                                        border-radius: 6px;
                                                        border: none;
                                                        width: 100%;
                                                        padding: 0.75rem;
                                                        font-size: 0.875rem;
                                                        font-weight: 500;
                                                        transition: all 0.2s;
                                                    }
                                                    button:hover {
                                                        background-color: #1148A0;
                                                        transform: translateY(-1px);
                                                    }
                                                    """
                                                ):
                                                    st.markdown(f'<a href="{url}" target="_blank"><button style="width:100%;padding:0.75rem;">🔍 크게 보기</button></a>', unsafe_allow_html=True)
                        
                        st.session_state.messages.append(message)
                
                elif response["status"] == "cancelled":
                    with stylable_container(
                        key="cancelled_message",
                        css_styles="""
                        {
                            background-color: #FEF2F2;
                            color: #DC2626;
                            padding: 0.75rem;
                            border-radius: 8px;
                            border: 1px solid #FCA5A5;
                            margin: 0.5rem 0;
                        }
                        """
                    ):
                        st.warning(response["response"])
                else:
                    with stylable_container(
                        key="error_message",
                        css_styles="""
                        {
                            background-color: #FEF2F2;
                            color: #DC2626;
                            padding: 0.75rem;
                            border-radius: 8px;
                            border: 1px solid #FCA5A5;
                            margin: 0.5rem 0;
                        }
                        """
                    ):
                        st.error(response["response"])

if __name__ == "__main__":
    main()