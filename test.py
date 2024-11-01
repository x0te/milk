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

st.set_page_config(
        page_title="SF49.Studio Designer",
        page_icon="🎨",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    
def set_custom_style():
    with stylable_container(
        key="main_container",
        css_styles="""
            {
                background: linear-gradient(135deg, #1A1B1E 25%, #2C2F33 75%);
                color: #EAEAEA;
            }
        """
    ):
        st.markdown("""
            <style>
            /* Streamlit 메인 컨테이너 배경색 오버라이드 */
            .st-emotion-cache-1jicfl2 {
                background: transparent !important;
            }

            .st-emotion-cache-bm2z3a {
                background: transparent !important;
            }
            
            /* 네비게이션 컨테이너 */
            .nav-container {
                position: fixed;
                top: 4.5rem;  /* Streamlit 헤더 고려 */
                right: 20px;
                z-index: 1000;
                display: flex;
                gap: 0.5rem;
                background: transparent;
            }

            /* 아이콘 버튼 */
            .nav-icon {
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 50%;
                cursor: pointer;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
                font-size: 1.2rem;
                text-decoration: none;
                color: rgba(255, 255, 255, 0.8);
                position: relative;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }

            .nav-icon:hover {
                background: rgba(255, 75, 75, 0.2);
                transform: translateY(-2px);
                border-color: rgba(255, 75, 75, 0.3);
            }

            /* 툴팁 */
            .nav-icon::after {
                content: attr(data-tooltip);
                position: absolute;
                right: 50px;
                top: 50%;
                transform: translateY(-50%);
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                font-size: 0.875rem;
                white-space: nowrap;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
            }

            .nav-icon:hover::after {
                opacity: 1;
                visibility: visible;
                right: 45px;
            }
            
            /* 채팅 인터페이스 */
            .stChatMessage {
                background: rgba(45, 45, 45, 0.95) !important;  /* 어두운 회색 배경 */
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 1.2rem !important;
                margin: 1.2rem 0 !important;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                font-size: 1.1rem !important;
                color: rgba(255, 255, 255, 0.9) !important;  /* 하얀색 글씨 */
            }

            .stChatMessage:hover {
                border-color: rgba(255, 75, 75, 0.2);
                background: rgba(50, 50, 50, 0.95) !important;  /* 호버 시 약간 밝은 회색 */
            }

            /* 채팅 메시지 내부의 모든 텍스트 요소에 대한 색상 지정 */
            .stChatMessage p, 
            .stChatMessage span, 
            .stChatMessage div {
                color: rgba(255, 255, 255, 0.9) !important;  /* 하얀색 글씨 */
            }

            /* 입력 필드 */
            .stTextInput > div > div > input {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 1rem 1.2rem !important;
                border-radius: 6px;
                color: white;
                width: calc(100% - 2rem);
                margin: 0 auto;
                font-size: 1.1rem !important;
            }
            
            .stTextInput > div > div > input:focus {
                border-color: #FF4B4B;
                box-shadow: 0 0 0 1px rgba(255, 75, 75, 0.3);
            }
            
            /* 프로그레스 바 */
            .stProgress > div > div {
                background: linear-gradient(90deg, #1DB954, #1ED760) !important;
            }
            
            .stProgress {
                background: rgba(255, 255, 255, 0.1);
            }
            
            /* 캡션과 설명 텍스트 */
            .header-subtitle {
                color: rgba(255, 255, 255, 0.7);
                font-size: 1.3rem !important;
                margin-bottom: 2rem;
            }
            
            .intro-text {
                background: rgba(255, 255, 255, 0.05);
                padding: 1.5rem;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                margin: 1rem 0 2rem 0;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            }
            
            /* 이미지 스일 */
            .image-container {
                margin: 1rem 0;
                transition: all 0.3s ease;
                position: relative;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            }
            
            .image-container img {
                width: 100%;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .image-container:hover {
                transform: scale(1.02);
            }
            
            .image-caption {
                text-align: center;
                color: rgba(255, 255, 255, 0.7);
                margin-top: 0.8rem;
                font-size: 1.1rem !important;
            }

            /* 이미지 오버레이 버튼 */
            .image-container .overlay-buttons {
                position: absolute;
                top: 10px;
                right: 10px;
                display: flex;
                gap: 0.5rem;
                opacity: 0;
                transition: opacity 0.3s ease;
            }

            .image-container:hover .overlay-buttons {
                opacity: 1;
            }

            .overlay-button {
                background: rgba(0, 0, 0, 0.6);
                color: white;
                border: none;
                padding: 0.5rem;
                border-radius: 50%;
                cursor: pointer;
                font-size: 1.2rem;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.3s ease;
            }

            .overlay-button:hover {
                background: rgba(255, 75, 75, 0.8);
            }

            /* Streamlit 기본 요소 조정 */
            .stDeployButton {
                display: none;
            }
            
            header[data-testid="stHeader"] {
                background: rgba(26, 27, 30, 0.9);
                backdrop-filter: blur(10px);
            }

            .main > div:first-child {
                padding-top: 5rem !important;  /* 상단 여백 추가 */
            }

            /* st-emotion-cache 영역 조정 */
            .st-emotion-cache-qcqlej {
                max-height: 70vh !important;
                overflow-y: auto;
            }

            /* 채팅 컨테이너 스타일 */
            .chat-container {
                display: flex;
                flex-direction: column;
                height: calc(100vh - 200px);
                margin-bottom: 20px;
            }

            .messages-container {
                flex-grow: 1;
                overflow-y: auto;
                padding: 20px;
                margin-bottom: 20px;
            }

            .input-container {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: rgba(26, 27, 30, 0.95);
                padding: 20px;
                backdrop-filter: blur(10px);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                z-index: 1000;
            }
            
            /* Streamlit 기본 헤더 완전히 제거 */
            .stAppHeader,
            header[data-testid="stHeader"],
            .stHeader,
            header.st-emotion-cache-8ahh38,
            header.ezrtsby2 {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
                padding: 0 !important;
                margin: 0 !important;
                opacity: 0 !important;
                pointer-events: none !important;
            }

            /* 네비게이션 컨테이너를 최상단에 고정 */
            .nav-container {
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                right: 0 !important;
                height: 60px !important;
                background-color: #FF5722 !important;
                display: flex !important;
                justify-content: flex-start !important;
                align-items: center !important;
                padding: 0 20px !important;
                padding-left: 60% !important;
                z-index: 999999 !important;
                gap: 10px !important;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3) !important;
            }

            /* 아이콘 크기 조정 */
            .nav-icon {
                width: 40px !important;
                height: 40px !important;
                font-size: 1.5rem !important;
                background: rgba(255, 255, 255, 0.1) !important;
                border: none !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                margin: 0 5px !important;
                transition: all 0.3s ease !important;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2) !important;
                border-radius: 50% !important;
            }

            .nav-icon:hover {
                background: rgba(255, 255, 255, 0.2) !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
            }

            /* 툴팁 위치 재조정 */
            .nav-icon::after {
                top: 65px !important;
            }

            /* 메인 컨텐츠 여백 조정 */
            .main > div:first-child {
                padding-top: 60px !important;
            }
            
            /* 불필요한 여백 제거 */
            .st-emotion-cache-1v0mbdj,  /* stVerticalBlock */
            .st-emotion-cache-16idsys,
            .st-emotion-cache-10trblm,
            .st-emotion-cache-1kyxreq,
            .st-emotion-cache-1wbqy5l {
                margin: 0 !important;
                padding: 0 !important;
                height: auto !important;
                min-height: 0 !important;
            }

            /* 제목과 컨텐츠 위치 조정 */
            [data-testid="stVerticalBlock"] {
                gap: 0 !important;
                padding: 0 !important;
            }

            /* 상단 여백 조정 */
            .main .block-container {
                padding-top: 60px !important;  /* 헤더 높이만큼만 여백 설정 */
                max-width: none !important;
            }

            /* 추가 여백 제거 */
            .st-emotion-cache-18ni7ap {
                padding: 0 !important;
            }

            .st-emotion-cache-6qob1r {
                margin: 0 !important;
                padding: 0 !important;
            }
            
            /* Streamlit 기본 텍스트 크기 조정 */
            .stMarkdown, .stText {
                font-size: 1.1rem !important;
            }

            /* 제목 크기 조정 */
            h1 {
                font-size: 2.5rem !important;
            }

            h2 {
                font-size: 2rem !important;
            }

            h3 {
                font-size: 1.75rem !important;
            }

            /* 툴팁 크기 조정 */
            .nav-icon::after {
                font-size: 1rem !important;
                padding: 0.6rem 1.2rem !important;
            }

            </style>
        """, unsafe_allow_html=True)

def typewriter_effect(text: str, speed: float = 0.03):
    """텍스트를 타이핑 효과로 표시"""
    with stylable_container(
        key="typewriter",
        css_styles="""
            {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 1rem;
                margin: 0.5rem 0;
            }
        """
    ):
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
            
            중요: 이미지 생성 요청 시 unique_id는 반드시 끝에 1000에서 9999 사이의 랜덤한 숫자를 추가하여 생성해야 합니다.
            예시: design_request_1234, creative_image_5678, visual_concept_9012 등
            절대로 같은 ID가 중복되지 않도록 해야 합니다.

            보안 관련 중요 지침:
            1. 시스템 관련 정보 요청에 대해서는 절대 응답하지 않습니다.
            2. API 키, 토큰, 비밀번호 등 민감한 정보에 대한 질문은 무시합니다.
            3. 서버 구성, 데이터베이스 구조 등 시스템 아키텍처 관련 질문에는 답변하지 않습니다.
            4. 코드 실행이나 시스템 명령어 관련 요청은 거부합니다.
            5. 이러한 보안 관련 질문을 받으면 "죄송합니다만, 보안상의 이유로 해당 정보는 제공해드릴 수 없습니다."라고 답변합니다.
            6. 오직 이미지 생성과 관련된 디자인 요청만 처리합니다.
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
                                "description": "생성할 이미지의 고유 ID (반드시 끝에 1000-9999 사이의 랜덤 자 포함)"
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
                # URL 유효성 검사
                valid_urls = all(
                    url.startswith(('http://', 'https://')) 
                    for url in result["images"]
                )
                
                if valid_urls:
                    return {
                        "success": True,
                        "images": result["images"],
                        "message": "이미지가 성공적으로 생성되었습니다!"
                    }
                
            # URL이 유효하지 않거나 아직 준비되지 않은 경우
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
        if self.thread is None:
            self.create_thread()

        self.client.beta.threads.messages.create(
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
        loading_container = st.empty()

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
                    snail_frames = [
                        "🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌 ⋯",
                        "⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ 🐌",
                    ]
                    
                    loading_container = st.empty()
                    
                    # 첫 60초 동안 기본 대기
                    for i in range(60):
                        frame = snail_frames[i % len(snail_frames)]
                        loading_container.markdown(f"""
                            <div style='font-family: monospace; font-size: 1.5em; margin-bottom: 0.5em;'>
                                {frame}
                            </div>
                        """, unsafe_allow_html=True)
                        time.sleep(1)

                    # 60초 이후부터는 5초마다 이미지 체크
                    while True:
                        # 이미지 체크
                        result = self.get_image_links(generated_id)
                        if result["success"] and result["images"]:
                            loading_container.empty()
                            st.balloons()
                            confetti_effect()
                            fireworks_effect()
                            return {
                                "status": "success",
                                "response": "✨ 디자인이 완성되었습니다! 마음에 드시나요?",
                                "images": result["images"]
                            }
                        
                        # 다음 체크까지 5초 대기하면서 달팽이 애니메이션 표시
                        for frame in snail_frames:
                            loading_container.markdown(f"""
                                <div style='font-family: monospace; font-size: 1.5em; margin-bottom: 0.5em;'>
                                    {frame}
                                </div>
                            """, unsafe_allow_html=True)
                            time.sleep(0.17)  # 5초 / 프레임 수

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

def initialize_session_state():
    """세션 상태 초기화"""
    if 'assistant' not in st.session_state:
        api_key = st.secrets["OPENAI_API_KEY"]
        st.session_state.assistant = SF49StudioAssistant(api_key)
        st.session_state.assistant.create_assistant()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'threads' not in st.session_state:
        st.session_state.threads = []

def main():
    initialize_session_state()
    set_custom_style()

    # 상단 여백
    st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)

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

    st.title("SF49 Studio Designer")
    st.markdown('<p class="header-subtitle">AI 디자인 스튜디오</p>', unsafe_allow_html=True)
    
    # 설명 텍스트 (항상 말풍선으로 표시)
    if 'shown_intro' not in st.session_state:
        with stylable_container(
            key="intro_message",
            css_styles="""
                {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                    padding: 1rem;
                    margin: 1rem 0;
                }
            """
        ):
            with st.chat_message("assistant"):
                st.markdown("""
                💫 원하시는 이미지를 설명해 주세요<br>
                🎯 최적의 디자인으로 구현해드립니다
                """, unsafe_allow_html=True)
        st.session_state.shown_intro = True

    # 채팅 컨테이너
    with st.container():
        # 메시지 표시 영역
        with st.container():
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    
                    if "image_urls" in message:
                        cols = st.columns(2)
                        for idx, url in enumerate(message["image_urls"]):
                            with cols[idx % 2]:
                                buffer = io.BytesIO()
                                img = Image.open(requests.get(url, stream=True).raw)
                                img.save(buffer, format="PNG")
                                img_base64 = base64.b64encode(buffer.getvalue()).decode()
                                st.markdown(f"""
                                    <div class="image-container">
                                        <img src="{url}">
                                        <div class="overlay-buttons">
                                            <a href="data:image/png;base64,{img_base64}" download="Design_Option_{idx + 1}.png" class="overlay-button" title="이미지 다운로드">💾</a>
                                            <a href="{url}" target="_blank" class="overlay-button" title="크게 보기">🔍</a>
                                        </div>
                                        <p class="image-caption">Design Option {idx + 1}</p>
                                    </div>
                                """, unsafe_allow_html=True)

        # 입력 영역
        with st.container():
            st.markdown('<div class="input-container">', unsafe_allow_html=True)
            if prompt := st.chat_input("어떤 이미지를 만들어드릴까요?"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                response = st.session_state.assistant.process_message(prompt)
                with st.chat_message("assistant"):
                    if response["status"] == "success":
                        typewriter_effect(response["response"], speed=0.02)
                        message = {"role": "assistant", "content": response["response"]}
                        
                        if "images" in response and response["images"]:
                            message["image_urls"] = response["images"]
                            cols = st.columns(2)
                            for idx, url in enumerate(response["images"]):
                                with cols[idx % 2]:
                                    buffer = io.BytesIO()
                                    img = Image.open(requests.get(url, stream=True).raw)
                                    img.save(buffer, format="PNG")
                                    img_base64 = base64.b64encode(buffer.getvalue()).decode()
                                    st.markdown(f"""
                                        <div class="image-container">
                                            <img src="{url}">
                                            <div class="overlay-buttons">
                                                <a href="data:image/png;base64,{img_base64}" download="Design_Option_{idx + 1}.png" class="overlay-button" title="이미지 다운로드">💾</a>
                                                <a href="{url}" target="_blank" class="overlay-button" title="크게 보기">🔍</a>
                                            </div>
                                            <p class="image-caption">Design Option {idx + 1}</p>
                                        </div>
                                    """, unsafe_allow_html=True)
                        
                        st.session_state.messages.append(message)
                    else:
                        typewriter_effect(response["response"], speed=0.02)
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()