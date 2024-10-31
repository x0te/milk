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

    def create_assistant(self):
        instructions = """
        당신의 목적은 한국어로 대화하면서 이미지 생성을 처리하는 것입니다.
        당신은 SF49 Studio의 전문 디자이너처럼 행동합니다.
        창의적인 디자이너의 관점과 전문적이고 세련된 언어를 사용하며, 전문가의 톤을 유지합니다.
        모든 커뮤니케이션에서 명확성, 디자인적 미적 감각, 그리고 전문성을 우선시합니다.
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
                                "description": "인터넷 기사 썸네일 이미지를 위한 시각화 텍스트"
                            },
                            "unique_id": {
                                "type": "string",
                                "description": "생성할 이미지의 고유 ID"
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

            self.client.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=user_message
            )

            run = self.client.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id
            )

            generated_id = None
            status_container = st.empty()
            
            cancel_button = st.button("생성 취소", key="cancel_generation", 
                                    help="이미지 생성을 취소합니다")

            while True:
                if cancel_button or ('cancel_generation' in st.session_state and 
                                   st.session_state.cancel_generation):
                    self.client.client.beta.threads.runs.cancel(
                        thread_id=self.thread.id,
                        run_id=run.id
                    )
                    return {
                        "status": "cancelled",
                        "response": "이미지 생성이 취소되었습니다."
                    }

                run = self.client.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=run.id
                )

                if run.status == "requires_action":
                    tool_outputs = []
                    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                        args = json.loads(tool_call.function.arguments)
                        
                        if tool_call.function.name == "send_image_request":
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

                            response_data = {
                                "status": "success",
                                "unique_id": generated_id,
                                "message": "이미지 생성을 시작합니다..."
                            }
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": json.dumps(response_data)
                            })

                    run = self.client.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=self.thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )

                    if generated_id:
                        progress_messages = [
                            "이미지 생성을 위한 초기 설정을 준비하고 있습니다...",
                            "아이디어를 시각적 요소로 분석하고 있습니다...",
                            "디자인 요소를 구성하고 있습니다...",
                            "이미지의 세부 요소를 조정하고 있습니다...",
                            "최종 디테일을 다듬고 있습니다...",
                            "생성된 이미지를 최적화하고 있습니다..."
                        ]
                        
                        my_bar = st.progress(0)
                        
                        for i in range(100):
                            if ('cancel_generation' in st.session_state and 
                                st.session_state.cancel_generation):
                                my_bar.empty()
                                status_container.empty()
                                return {
                                    "status": "cancelled",
                                    "response": "이미지 생성이 취소되었습니다."
                                }

                            if i % 20 == 0:
                                progress_text = random.choice(progress_messages)
                                status_container.markdown(f"**{progress_text}**")
                            progress_value = (i + 1) / 100
                            my_bar.progress(progress_value)
                            time.sleep(0.5)

                        my_bar.empty()
                        status_container.empty()

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
                                "response": "🎨 이미지 생성에 시간이 더 필요합니다. 잠시 후에 다시 시도해 주시겠어요?"
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
                        "response": "처리 중 문제가 발생했습니다. 다시 시도해주세요."
                    }
                
                time.sleep(0.5)

        except Exception as e:
            st.error(f"예상치 못한 오류가 발생했습니다: {str(e)}")
            return {
                "status": "error",
                "response": "서비스 처리 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
            }

def main():
    st.set_page_config(
        page_title="SF49 Studio Designer",
        page_icon="🌟",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    set_custom_style()

    openai_client = OpenAIClient(api_key=st.secrets["openai_api_key"])
    webhook_handler = WebhookHandler(
        base_url="https://hook.eu2.make.com",
        send_webhook="/l1b22zor5v489mjyc6mgr8ybwliq763v",
        retrieve_webhook="/7qia4xlc2hvxt1qs1yr5eh7g9nqs8brd"
    )
    assistant = SF49StudioAssistant(openai_client, webhook_handler)

    st.title("SF49 Studio Designer")
    st.markdown('<p class="header-subtitle">AI 디자인 스튜디오</p>', unsafe_allow_html=True)

    if 'shown_intro' not in st.session_state:
        with st.chat_message("assistant"):
            st.markdown("""
            💫 원하시는 이미지를 설명해 주세요<br>
            🎯 최적의 디자인으로 구현해드립니다
            """, unsafe_allow_html=True)
        st.session_state.shown_intro = True

    chat_container = st.container()
    
    with chat_container:
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
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
                                        <img src="{url}">
                                        <div class="overlay-buttons">
                                            <a href="data:image/png;base64,{img_base64}" 
                                               download="Design_Option_{idx + 1}.png" 
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
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
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
                                        <img src="{url}">
                                        <div class="overlay-buttons">
                                            <a href="data:image/png;base64,{img_base64}" 
                                               download="Design_Option_{idx + 1}.png" 
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