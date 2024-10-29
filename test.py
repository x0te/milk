import streamlit as st
from openai import OpenAI
import requests
import json
import uuid
from typing import Dict, List, Optional
import time
import random
from datetime import datetime

def set_custom_style():
    st.markdown("""
        <style>
        /* 기본 테마 */
        .stApp {
            background: #1A1B1E;
        }
        
        /* 네비게이션 컨테이너 */
        .nav-container {
            position: fixed;
            top: 4.5rem;
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
        
        /* 채팅 컨테이너 */
        .chat-container {
            max-width: 800px;
            margin: 2rem auto;
            padding: 0 1rem;
        }

        /* 메시지 그룹 */
        .message-group {
            display: flex;
            flex-direction: column;
            gap: 2px;
            margin: 1rem 0;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* 채팅 메시지 스타일 */
        .stChatMessage {
            position: relative;
            padding: 0.8rem 1.2rem !important;
            margin: 0.2rem 0 !important;
            max-width: 80% !important;
            border-radius: 16px !important;
            font-size: 0.95rem !important;
            line-height: 1.5 !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        /* 사용자 메시지 */
        .stChatMessage[data-testid="chat-message-user"] {
            margin-left: auto !important;
            background: linear-gradient(135deg, #FF4B4B 0%, #FF7676 100%) !important;
            color: white !important;
            border: none !important;
            border-bottom-right-radius: 4px !important;
        }

        /* 어시스턴트 메시지 */
        .stChatMessage[data-testid="chat-message-assistant"] {
            margin-right: auto !important;
            background: rgba(255, 255, 255, 0.07) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-bottom-left-radius: 4px !important;
        }

        /* 프로필 영역 */
        .profile-container {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            margin-bottom: 4px;
        }

        .avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }

        /* 메시지 메타 정보 */
        .message-meta {
            font-size: 0.75rem;
            color: rgba(255, 255, 255, 0.5);
            margin-top: 0.2rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .message-time {
            opacity: 0.7;
        }

        .read-status {
            font-size: 0.7rem;
            opacity: 0.8;
        }

        /* 이미지 스타일 */
        .image-container {
            margin: 0.5rem 0;
            border-radius: 12px;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }

        .image-container:hover {
            transform: scale(1.02);
            border-color: rgba(255, 75, 75, 0.3);
        }

        .image-container img {
            width: 100%;
            height: auto;
            display: block;
        }

        .image-caption {
            text-align: center;
            color: rgba(255, 255, 255, 0.7);
            padding: 0.5rem;
            font-size: 0.9rem;
            background: rgba(0, 0, 0, 0.2);
        }

        /* 입력 필드 */
        .stTextInput {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 1rem;
            background: rgba(26, 27, 30, 0.95);
            backdrop-filter: blur(10px);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .stTextInput > div > div > input {
            background: rgba(255, 255, 255, 0.07);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 0.8rem 1rem;
            border-radius: 24px;
            color: white;
            font-size: 0.95rem;
        }

        .stTextInput > div > div > input:focus {
            border-color: #FF4B4B;
            box-shadow: 0 0 0 1px rgba(255, 75, 75, 0.3);
        }

        /* 스크롤바 스타일 */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: transparent;
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        </style>
    """, unsafe_allow_html=True)

def format_message(role: str, content: str, image_urls: List[str] = None) -> str:
    """메시지 HTML 포맷팅"""
    current_time = datetime.now().strftime("%H:%M")
    
    if role == "assistant":
        message_html = f"""
            <div class="message-group">
                <div class="profile-container">
                    <div class="avatar">🤖</div>
                    <div style="flex: 1;">
                        <div>{content}</div>
                        <div class="message-meta">
                            <span class="message-time">{current_time}</span>
                        </div>
                    </div>
                </div>
            </div>
        """
    else:
        message_html = f"""
            <div class="message-group" style="align-items: flex-end;">
                <div>{content}</div>
                <div class="message-meta">
                    <span class="message-time">{current_time}</span>
                    <span class="read-status">✓✓</span>
                </div>
            </div>
        """
    
    if image_urls:
        image_html = ""
        for i in range(0, len(image_urls), 2):
            image_html += '<div style="display: flex; gap: 1rem; margin-top: 0.5rem;">'
            for j, url in enumerate(image_urls[i:i+2]):
                image_html += f"""
                    <div class="image-container" style="flex: 1;">
                        <img src="{url}" alt="Generated Image {i+j+1}">
                        <div class="image-caption">Design Option {i+j+1}</div>
                    </div>
                """
            image_html += '</div>'
        message_html += image_html
    
    return message_html

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

# SF49StudioAssistant 클래스는 이전과 동일

def main():
    st.set_page_config(
        page_title="SF49 Studio Designer",
        page_icon="🎨",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    set_custom_style()

    # 상단 여백과 네비게이션
    st.markdown('<div style="margin-top: 4rem;"></div>', unsafe_allow_html=True)
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

    # 헤더
    st.title("SF49 Studio Designer")
    st.markdown('<p style="color: rgba(255, 255, 255, 0.7); margin-bottom: 2rem;">AI 디자인 스튜디오</p>', unsafe_allow_html=True)
    
    # 채팅 컨테이너 시작
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # 인트로 메시지
    if 'shown_intro' not in st.session_state:
        intro_message = """
        💫 원하시는 이미지를 설명해 주세요
        🎯 최적의 디자인으로 구현해드립니다
        """
        st.markdown(
            format_message("assistant", intro_message),
            unsafe_allow_html=True
        )
        st.session_state.shown_intro = True
    
    # 메시지 이력 표시
    for message in st.session_state.messages:
        image_urls = message.get("image_urls", None)
        st.markdown(
            format_message(
                message["role"],
                message["content"],
                image_urls
            ),
            unsafe_allow_html=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

    # 입력창
    if prompt := st.chat_input("어떤 이미지를 만들어드릴까요?"):
        # 사용자 메시지 추가
        st.markdown(
            format_message("user", prompt),
            unsafe_allow_html=True
        )
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Assistant 응답 처리
        with st.chat_message("assistant"):
            response = st.session_state.assistant.process_message(prompt)
            
            if response["status"] == "success":
                message_content = response["response"]
                image_urls = response.get("images", None)
                
                st.markdown(
                    format_message(
                        "assistant",
                        message_content,
                        image_urls
                    ),
                    unsafe_allow_html=True
                )
                
                message = {
                    "role": "assistant",
                    "content": message_content
                }
                if image_urls:
                    message["image_urls"] = image_urls
                
                st.session_state.messages.append(message)
            else:
                st.markdown(
                    format_message("assistant", response["response"]),
                    unsafe_allow_html=True
                )

if __name__ == "__main__":
    initialize_session_state()
    main()    
    