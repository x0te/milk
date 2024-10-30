import streamlit as st
from openai import OpenAI
import requests
import json
import uuid
from typing import Dict, List, Optional
import time
import random

def set_custom_style():
    st.markdown("""
        <style>
        .stApp {
            background: #1A1B1E;
        }

        .nav-container {
            position: fixed;
            top: 4.5rem;
            right: 20px;
            z-index: 1000;
            display: flex;
            gap: 0.5rem;
            background: transparent;
        }

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

        .image-wrapper {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            overflow: hidden;
            margin: 0.5rem 0;
            position: relative;
        }

        .image-controls {
            display: none;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            gap: 0.5rem;
            background: rgba(0, 0, 0, 0.6);
            padding: 0.5rem;
            border-radius: 12px;
        }

        .image-wrapper:hover .image-controls {
            display: flex;
        }

        .image-control-button {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            background: rgba(255, 255, 255, 0.1);
            border: none;
            border-radius: 50%;
            font-size: 1.5rem;
            color: white;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .image-control-button:hover {
            background: rgba(255, 75, 75, 0.2);
        }

        .stDeployButton {
            display: none;
        }

        header[data-testid="stHeader"] {
            background: rgba(26, 27, 30, 0.9);
            backdrop-filter: blur(10px);
        }

        .main > div:first-child {
            padding-top: 5rem !important;
        }

        .header-subtitle {
            color: rgba(255, 255, 255, 0.7);
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }

        .intro-text {
            background: rgba(255, 255, 255, 0.05);
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin: 1rem 0 2rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

def display_image_with_controls(image_url: str, caption: str, col):
   with col:
       st.markdown(f"""
           <div class="image-wrapper">
               <img src="{image_url}" style="width: 100%; display: block;">
               <div class="image-controls">
                   <button onclick="window.open('{image_url}', '_blank')" class="image-control-button">🔍</button>
                   <button onclick="window.location.href='{image_url}'" download class="image-control-button">💾</button>
               </div>
           </div>
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
       self.thread = self.client.beta.threads.create()
       return self.thread

   def send_image_data(self, visualization_text: str, unique_id: str) -> Dict:
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
                   progress_messages = [
                       "이미지 생성을 위한 초기 설정을 준비하고 있습니다...",
                       "아이디어를 시각적 요소로 분석하고 있습니다...",
                       "디자인 요소를 구성하고 있습니다...",
                       "이미지의 세부 요소를 조정하고 있습니다...",
                       "최종 디테일을 다듬고 있습니다...",
                       "생성된 이미지를 최적화하고 있습니다..."
                   ]

                   my_bar = st.progress(0)

                   for i in range(90):
                       if i % 20 == 0:
                           progress_text = random.choice(progress_messages)
                       progress_value = (i + 1) / 90
                       my_bar.progress(progress_value, text=progress_text)
                       time.sleep(1)

                   my_bar.empty()

                   result = self.get_image_links(generated_id)
                   if result["success"] and result["images"]:
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
   if 'assistant' not in st.session_state:
       api_key = st.secrets["OPENAI_API_KEY"]
       st.session_state.assistant = SF49StudioAssistant(api_key)
       st.session_state.assistant.create_assistant()
       st.session_state.assistant.create_thread()

   if 'messages' not in st.session_state:
       st.session_state.messages = []

def main():
   st.set_page_config(
       page_title="SF49 Studio Designer",
       page_icon="🎨",
       layout="wide",
       initial_sidebar_state="collapsed"
   )

   set_custom_style()

   st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)

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

   initialize_session_state()

   if 'shown_intro' not in st.session_state:
       st.markdown("""
       💫 원하시는 이미지를 설명해 주세요
       🎯 최적의 디자인으로 구현해드립니다
       """)
       st.session_state.shown_intro = True
   else:
       st.markdown("""
       <div class="intro-text">
           💫 원하시는 이미지를 설명해 주세요<br>
           🎯 최적의 디자인으로 구현해드립니다
       </div>
       """, unsafe_allow_html=True)

   for message in st.session_state.messages:
       with st.chat_message(message["role"]):
           st.write(message["content"])

           if "image_urls" in message:
               cols = st.columns(2)
               for idx, url in enumerate(message["image_urls"]):
                   display_image_with_controls(url, f"Design Option {idx + 1}", cols[idx % 2])

   if prompt := st.chat_input("어떤 이미지를 만들어드릴까요?"):
       with st.chat_message("user"):
           st.write(prompt)
       st.session_state.messages.append({"role": "user", "content": prompt})

       with st.chat_message("assistant"):
           response = st.session_state.assistant.process_message(prompt)

           if response["status"] == "success":
               st.write(response["response"])
               message = {"role": "assistant", "content": response["response"]}

               if "images" in response and response["images"]:
                   message["image_urls"] = response["images"]
                   cols = st.columns(2)
                   for idx, url in enumerate(response["images"]):
                       display_image_with_controls(url, f"Design Option {idx + 1}", cols[idx % 2])

               st.session_state.messages.append(message)
           else:
               st.error(response["response"])

if __name__ == "__main__":
   main()
