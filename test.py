import streamlit as st 
from openai import OpenAI
import requests
import json
from typing import Dict, List, Optional
import time
import random
import io
import base64
from PIL import Image
from streamlit_extras.stylable_container import stylable_container

def set_custom_style():
    st.markdown("""
        <style>
        /* 기본 레이아웃 */
        .main .block-container {
            padding-top: 0;
            padding-bottom: 0;
            margin: 0;
            max-width: 1200px;
        }
        
        /* 스트림릿 헤더 숨기기 */
        .stAppHeader {
            display: none !important;
        }

        /* 네비게이션 아이콘 */
        .nav-icon {
            background-color: rgba(255, 107, 0, 0.1) !important;
            border: 2px solid #FF6B00 !important;
            padding: 8px 12px !important;
            border-radius: 50px !important;
            color: #FF6B00 !important;
            text-decoration: none !important;
            font-size: 1.2rem !important;
            margin: 0 4px !important;
            transition: all 0.3s ease !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 40px !important;
            height: 40px !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        }

        .nav-icon:hover {
            background-color: #FF6B00 !important;
            color: white !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px rgba(255, 107, 0, 0.2) !important;
        }

        /* 채팅 입력 */
        .stChatInput {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        
        .stChatInput textarea {
            border: none !important;
            background-color: transparent !important;
        }

        /* 채팅 메시지 */
        .stChatMessage {
            background-color: transparent !important;
            border: none !important;
        }

        /* 이미지 컨테이너 */
        .image-container {
            position: relative;
            overflow: hidden;
            background-color: #FFFFFF;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.75rem auto;
            border: 1px solid #E2E8F0;
            transition: all 0.2s ease;
            max-width: 600px;
        }

        .image-container:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        /* 오버레이 버튼 */
        .overlay-button {
            background-color: #1756A9;
            color: white;
            border-radius: 6px;
            border: none;
            width: 100%;
            padding: 0.75rem;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.2s;
            z-index: 10;
        }

        .overlay-button:hover {
            background-color: #1148A0;
            transform: translateY(-1px);
        }

        /* 헤더 스타일 */
        .header-container {
            background-color: #1756A9;
            padding: 1.5rem 2rem;
            margin: 0 auto;
            color: white;
            border-radius: 0 0 1rem 1rem;
            max-width: 1200px;
        }

        /* 프로그레스 바 */
        .stProgress > div > div > div {
            background-color: #1756A9;
        }

        /* 스크롤바 */
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

        /* 네비게이션 컨테이너 */
        .nav-container {
            position: fixed;
            top: 4.5rem;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            display: flex;
            gap: 0.5rem;
            max-width: 1200px;
            width: 100%;
            justify-content: flex-end;
            padding: 0 2rem;
        }

        /* 다운로드 버튼 */
        .download-button {
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

        .download-button:hover {
            background-color: #047857;
            transform: translateY(-1px);
        }

        /* 채팅 아바타 */
        .stChatMessage [data-testid="StyChatMessageAvatar"] {
            background-color: #F8FAFC !important;
            padding: 8px !important;
            border-radius: 50% !important;
            border: 2px solid #E2E8F0 !important;
        }
        
        .stChatMessage [data-testid="StyChatMessageAvatar"] img {
            width: 30px !important;
            height: 30px !important;
        }
        </style>
    """, unsafe_allow_html=True)

def typewriter_effect(text: str, speed: float = 0.03):
    """텍스트를 타이핑 효과로 표시"""
    message_placeholder = st.empty()
    full_text = ""
    for char in text:
        full_text += char
        message_placeholder.markdown(full_text + "▌")
        time.sleep(speed)
    message_placeholder.markdown(full_text)
    return message_placeholder

def confetti_effect():
    """스트림릿에서 confetti 효과를 표시"""
    st.markdown("""
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.4.0/dist/confetti.browser.min.js"></script>
    <script>
    const duration = 5 * 1000;
    const end = Date.now() + duration;

    (function frame() {
      confetti({
        particleCount: 3,
        angle: 60,
        spread: 55,
        origin: { x: 0 }
      });
      confetti({
        particleCount: 3,
        angle: 120,
        spread: 55,
        origin: { x: 1 }
      });

      if (Date.now() < end) {
        requestAnimationFrame(frame);
      }
    }());
    </script>
    """, unsafe_allow_html=True)

def fireworks_effect():
    """스트림릿에서 불꽃놀이 효과를 표시"""
    st.markdown("""
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.4.0/dist/confetti.browser.min.js"></script>
    <script>
    const duration = 5 * 1000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

    function randomInRange(min, max) {
      return Math.random() * (max - min) + min;
    }

    (function frame() {
      const timeLeft = animationEnd - Date.now();

      if (timeLeft <= 0) {
        return;
      }

      const particleCount = 50 * (timeLeft / duration);
      confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } }));
      confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } }));

      requestAnimationFrame(frame);
    }());
    </script>
    """, unsafe_allow_html=True)

class SF49StudioAssistant:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=st.secrets["openai_api_key"])
        self.assistant = None
        self.thread = None
        self.webhook_base_url = "https://hook.eu2.make.com"
        self.send_webhook = "/l1b22zor5v489mjyc6mgr8ybwliq763v"
        self.retrieve_webhook = "/7qia4xlc2hvxt1qs1yr5eh7g9nqs8brd"
        
    def create_assistant(self):
        """SF49 Studio Assistant 생성 및 상세 지침 설정"""
        self.assistant = self.client.beta.assistants.create(
            name="SF49 Studio Designer",
            instructions="""
            당신의 목적은 한국어로 대화하면서 이미지 생성을 처리하는 것입니다.
            당신은 SF49 Studio의 전문 디자이너처럼 행동합니다.
            창의적인 디자이너의 관점과 전문적이고 세련된 언어를 사용하며, 전문가의 톤을 유지합니다.
            모든 커뮤니케이션에서 명확성, 디자인적 미적 감각, 그리고 전문성을 우선시합니다.
            """,
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

    def create_thread(self):
        """새로운 대화 스레드 생성"""
        self.thread = self.client.beta.threads.create()
        return self.thread

    def send_image_data(self, visualization_text: str, unique_id: str) -> Dict:
        """이미지 생성 요청 전송 및 결과 확인"""
        url = f"{self.webhook_base_url}{self.send_webhook}"
        payload = {
            "imageData": visualization_text,
            "uniqueId": unique_id
        }
        
        try:
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
        """이미지 URL 목록 조회"""
        url = f"{self.webhook_base_url}{self.retrieve_webhook}"
        payload = {"uniqueId": unique_id}
        
        try:
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

    def process_message(self, user_message: str) -> Dict:
        """사용자 메시지 처리 및 응답 생성"""
        try:
            if self.thread is None:
                self.create_thread()

            if 'cancel_generation' in st.session_state:
                del st.session_state.cancel_generation

            message = self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=user_message
            )

            run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id
            )

            generated_id = None
            status_container = st.empty()
            
            while True:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=run.id
                )

                if run.status == "requires_action":
                    tool_outputs = []
                    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                        args = json.loads(tool_call.function.arguments)
                        
                        if tool_call.function.name == "send_image_request":
                            result = self.send_image_data(
                                args["visualization_text"],
                                args["unique_id"]
                            )
                            generated_id = result["unique_id"]
                            
                            if not result["success"]:
                                typewriter_effect(result["message"])
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

                    run = self.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=self.thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )

                    if generated_id:
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
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            progress_messages = [
                                "🎨 디자인 컨셉을 구상 중입니다...",
                                "✨ 시각적 요소를 배치하고 있습니다...",
                                "🖌️ 디테일을 다듬고 있습니다...",
                                "🔍 최종 점검 중입니다...",
                                "✅ 마무리 작업을 진행 중입니다..."
                            ]
                            
                            for i in range(100):
                                if i % 20 == 0:
                                    status_text.markdown(f"**{random.choice(progress_messages)}**")
                                progress_value = (i + 1) / 100
                                progress_bar.progress(progress_value)
                                time.sleep(0.1)

                            progress_bar.empty()
                            status_text.empty()

                        result = self.get_image_links(generated_id)
                        if result["success"] and result["images"]:
                            st.balloons()
                            confetti_effect()
                            fireworks_effect()
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
                    messages = self.client.beta.threads.messages.list(
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
            return {
                "status": "error",
                "response": f"예상치 못한 오류가 발생했습니다: {str(e)}"
            }

def initialize_session_state():
    """세션 상태 초기화"""
    if 'assistant' not in st.session_state:
        api_key = st.secrets["OPENAI_API_KEY"]
        st.session_state.assistant = SF49StudioAssistant(api_key)
        st.session_state.assistant.create_assistant()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []

def main():
    initialize_session_state()

    st.set_page_config(
        page_title="SF49 Studio Designer",
        page_icon="🎨",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    set_custom_style()

    with stylable_container(
        key="header_container",
        css_styles="""
        {
            background-color: #1756A9;
            padding: 1.5rem 2rem;
            margin: 0 auto;
            color: white;
            border-radius: 0 0 1rem 1rem;
            max-width: 1200px;
        }
        """
    ):
        st.title("SF49 Studio Designer")
        st.markdown('<p class="header-subtitle">AI 디자인 스튜디오</p>', unsafe_allow_html=True)

    # 플로팅 네비게이션
    st.markdown("""
        <div class="nav-container">
            <a href="https://sf49.studio/" 
               target="_blank" 
               class="nav-icon"
               data-tooltip="SF49 Studio">
                🏠
            </a>
            <a href="https://sf49.studio/guide" 
               target="_blank" 
               class="nav-icon"
               data-tooltip="이용 가이드">
                📖
            </a>
            <a href="https://sf49.studio/pricing" 
               target="_blank" 
               class="nav-icon"
               data-tooltip="요금제 안내">
                💳
            </a>
            <a href="https://sf49.studio/contact" 
               target="_blank" 
               class="nav-icon"
               data-tooltip="문의하기">
                ✉️
            </a>
        </div>
    """, unsafe_allow_html=True)
    
    # 설명 텍스트
    if 'shown_intro' not in st.session_state:
        with stylable_container(
            key="intro_container",
            css_styles="""
            {
                background-color: #FFFFFF;
                padding: 1.5rem;
                border-radius: 8px;
                margin: 1rem 0;
                border: 1px solid #E2E8F0;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            """
        ):
            with st.chat_message("assistant"):
                st.markdown("""
                💫 원하시는 이미지를 설명해 주세요<br>
                🎯 최적의 디자인으로 구현해드립니다
                """, unsafe_allow_html=True)
        st.session_state.shown_intro = True

    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
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
                                    margin: 0.75rem auto;
                                    border: 1px solid #E2E8F0;
                                    transition: all 0.2s ease;
                                    max-width: 600px;
                                }
                                :hover {
                                    transform: translateY(-2px);
                                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                                }
                                """
                            ):
                                buffer = io.BytesIO()
                                img = Image.open(requests.get(url, stream=True).raw)
                                img.save(buffer, format="PNG")
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
       # 사용자 텍스트는 즉시 표시
       st.session_state.messages.append({"role": "user", "content": prompt})
       with st.chat_message("user"):
           st.markdown(prompt)

       # AI 응답
       response = st.session_state.assistant.process_message(prompt)
       with st.chat_message("assistant"):
           if response["status"] == "success":
               typewriter_effect(response["response"], speed=0.02)
               message = {"role": "assistant", "content": response["response"]}
               
               # 이미지 URL이 있으면 해당 URL도 표시
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
                                   margin: 0.75rem auto;
                                   border: 1px solid #E2E8F0;
                                   transition: all 0.2s ease;
                                   max-width: 600px;
                                   position: relative;
                               }
                               :hover {
                                   transform: translateY(-2px);
                                   box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                               }
                               """
                           ):
                               buffer = io.BytesIO()
                               img = Image.open(requests.get(url, stream=True).raw)
                               img.save(buffer, format="PNG")
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
           else:
               typewriter_effect(response["response"], speed=0.02)

if __name__ == "__main__":
   main()