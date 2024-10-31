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

# 이미지 로딩 최적화를 위한 캐싱
@st.cache_data
def load_image(url):
    try:
        return Image.open(requests.get(url, stream=True).raw)
    except Exception as e:
        st.error(f"이미지 로딩 중 오류 발생: {str(e)}")
        return None

def set_custom_style():
    st.markdown("""
        <style>
        /* 전체 앱 스타일 */
        .stApp {
            background-color: #FFFFFF;
        }
        
        /* 헤더 스타일 */
        .stHeader {
            background-color: #FFFFFF;
            border-bottom: 1px solid #F0F2F6;
        }
        
        /* 사이드바 스타일 */
        .css-1d391kg {
            background-color: #FFFFFF;
        }
        
        /* 메인 콘텐츠 영역 */
        .main .block-container {
            max-width: 1000px;
            padding: 2rem;
            background-color: #FFFFFF;
        }
        
        /* 채팅 메시지 스타일 */
        .stChatMessage {
            background-color: #F8F9FA;
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
            border: 1px solid #E9ECEF;
        }
        
        /* 사용자 메시지 */
        .stChatMessage[data-testid="user-message"] {
            background-color: #E3F2FD;
        }
        
        /* 어시스턴트 메시지 */
        .stChatMessage[data-testid="assistant-message"] {
            background-color: #FFFFFF;
        }
        
        /* 입력 필드 스타일 */
        .stTextInput > div > div > input {
            border: 1px solid #DEE2E6;
            border-radius: 8px;
            padding: 0.75rem;
            background-color: #FFFFFF;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #4299E1;
            box-shadow: 0 0 0 1px #4299E1;
        }
        
        /* 버튼 스타일 */
        .stButton > button {
            background-color: #4299E1;
            color: white;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            border: none;
            transition: all 0.2s;
        }
        
        .stButton > button:hover {
            background-color: #3182CE;
            transform: translateY(-1px);
        }
        
        /* 이미지 컨테이너 스타일 */
        .image-container {
            background: #FFFFFF;
            border-radius: 10px;
            padding: 0.5rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            margin: 1rem 0;
            transition: transform 0.2s;
        }
        
        .image-container:hover {
            transform: translateY(-2px);
        }
        
        .image-container img {
            width: 100%;
            border-radius: 8px;
        }
        
        /* 이미지 오버레이 버튼 */
        .overlay-buttons {
            position: absolute;
            top: 10px;
            right: 10px;
            display: flex;
            gap: 0.5rem;
            opacity: 0;
            transition: opacity 0.2s;
        }
        
        .image-container:hover .overlay-buttons {
            opacity: 1;
        }
        
        .overlay-button {
            background: rgba(255, 255, 255, 0.9);
            color: #4299E1;
            border-radius: 50%;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            transition: all 0.2s;
        }
        
        .overlay-button:hover {
            background: #4299E1;
            color: white;
        }
        
        /* 프로그레스 바 스타일 */
        .stProgress > div > div {
            background-color: #4299E1;
        }
        
        /* 메시지 스타일 */
        .success-message {
            color: #2F855A;
            background-color: #F0FFF4;
            padding: 1rem;
            border-radius: 6px;
            border: 1px solid #C6F6D5;
        }
        
        .error-message {
            color: #C53030;
            background-color: #FFF5F5;
            padding: 1rem;
            border-radius: 6px;
            border: 1px solid #FED7D7;
        }
        
        /* 캡션 스타일 */
        .image-caption {
            text-align: center;
            color: #718096;
            margin-top: 0.5rem;
            font-size: 0.875rem;
        }
        </style>
    """, unsafe_allow_html=True)

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
            model="gpt-4-1106-preview",
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
            
            # 새로운 취소 버튼 디자인
            cancel_col1, cancel_col2, cancel_col3 = st.columns([1, 1, 1])
            with cancel_col2:
                cancel_button = st.button(
                    "🚫 생성 취소",
                    key="cancel_generation",
                    help="현재 진행 중인 이미지 생성을 취소합니다",
                    use_container_width=True
                )

            while True:
                if cancel_button or ('cancel_generation' in st.session_state and 
                                   st.session_state.cancel_generation):
                    self.client.client.beta.threads.runs.cancel(
                        thread_id=self.thread.id,
                        run_id=run.id
                    )
                    progress_placeholder.empty()
                    return {
                        "status": "cancelled",
                        "response": "🚫 이미지 생성이 취소되었습니다."
                    }

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
                        
                        progress_bar = progress_placeholder.progress(0)
                        status_text = progress_placeholder.empty()
                        
                        for i in range(100):
                            if cancel_button or ('cancel_generation' in st.session_state and 
                                               st.session_state.cancel_generation):
                                progress_bar.empty()
                                status_text.empty()
                                return {
                                    "status": "cancelled",
                                    "response": "🚫 이미지 생성이 취소되었습니다."
                                }

                            if i % 20 == 0:
                                status_text.markdown(f"**{random.choice(progress_messages)}**")
                            
                            progress_bar.progress(i + 1)
                            time.sleep(0.1)

                        progress_bar.empty()
                        status_text.empty()

                        result = self.webhook_handler.get_image_links(generated_id)
                        if result["success"] and result["images"]:
                            st.balloons()
                            return {
                                "status": "success",
                                "response": "✨ 디자인이 완성되었습니다!",
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

    set_custom_style()

    # 헤더 영역
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='color: #2D3748; margin-bottom: 0.5rem;'>✨ SF49 Studio Designer</h1>
            <p style='color: #718096; font-size: 1.1rem;'>AI 기반 디자인 스튜디오</p>
        </div>
    """, unsafe_allow_html=True)

    openai_client = OpenAIClient(api_key=st.secrets["openai_api_key"])
    webhook_handler = WebhookHandler(
        base_url="https://hook.eu2.make.com",
        send_webhook="/l1b22zor5v489mjyc6mgr8ybwliq763v",
        retrieve_webhook="/7qia4xlc2hvxt1qs1yr5eh7g9nqs8brd"
    )
    assistant = SF49StudioAssistant(openai_client, webhook_handler)

    if 'shown_intro' not in st.session_state:
        with st.chat_message("assistant", avatar="✨"):
            st.markdown("""
                <div style='background-color: #F7FAFC; padding: 1.5rem; border-radius: 10px; border: 1px solid #E2E8F0;'>
                    <h3 style='color: #2D3748; margin-bottom: 1rem;'>환영합니다! 👋</h3>
                    <p style='color: #4A5568; margin-bottom: 0.5rem;'>원하시는 이미지를 자연스럽게 설명해 주세요.</p>
                    <p style='color: #4A5568;'>최적의 디자인으로 구현해드리겠습니다.</p>
                </div>
            """, unsafe_allow_html=True)
        st.session_state.shown_intro = True

    chat_container = st.container()
    
    with chat_container:
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "✨"):
                st.markdown(message["content"])
                
                if "image_urls" in message:
                    cols = st.columns(2)
                    for idx, url in enumerate(message["image_urls"]):
                        with cols[idx % 2]:
                            image = load_image(url)
                            if image:
                                buffer = io.BytesIO()
                                image.save(buffer, format="PNG")
                                img_base64 = base64.b64encode(buffer.getvalue()).decode()
                                st.markdown(f"""
                                    <div class="image-container">
                                        <img src="{url}" alt="Generated Design {idx + 1}">
                                        <div class="overlay-buttons">
                                            <a href="data:image/png;base64,{img_base64}" 
                                               download="SF49_Design_{idx + 1}.png" 
                                               class="overlay-button" 
                                               title="이미지 다운로드">💾</a>
                                            <a href="{url}" 
                                               target="_blank" 
                                               class="overlay-button" 
                                               title="크게 보기">🔍</a>
                                        </div>
                                        <p class="image-caption">Design Option {idx + 1}</p>
                                    </div>
                                """, unsafe_allow_html=True)

    if prompt := st.chat_input("어떤 이미지를 만들어드릴까요?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="✨"):
            response = assistant.process_message(prompt)
            
            if response["status"] == "success":
                st.markdown(response["response"])
                message = {"role": "assistant", "content": response["response"]}
                
                if "images" in response and response["images"]:
                    message["image_urls"] = response["images"]
                    cols = st.columns(2)
                    for idx, url in enumerate(response["images"]):
                        with cols[idx % 2]:
                            image = load_image(url)
                            if image:
                                buffer = io.BytesIO()
                                image.save(buffer, format="PNG")
                                img_base64 = base64.b64encode(buffer.getvalue()).decode()
                                st.markdown(f"""
                                    <div class="image-container">
                                        <img src="{url}" alt="Generated Design {idx + 1}">
                                        <div class="overlay-buttons">
                                            <a href="data:image/png;base64,{img_base64}" 
                                               download="SF49_Design_{idx + 1}.png" 
                                               class="overlay-button" 
                                               title="이미지 다운로드">💾</a>
                                            <a href="{url}" 
                                               target="_blank" 
                                               class="overlay-button" 
                                               title="크게 보기">🔍</a>
                                        </div>
                                        <p class="image-caption">Design Option {idx + 1}</p>
                                    </div>
                                """, unsafe_allow_html=True)
                
                st.session_state.messages.append(message)
            elif response["status"] == "cancelled":
                st.warning(response["response"])
            else:
                st.error(response["response"])

if __name__ == "__main__":
    main()