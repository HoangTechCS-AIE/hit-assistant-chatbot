"""
HaUI AI Assistant - Main Streamlit Application
A RAG-based chatbot for Hanoi University of Industry.
"""
import streamlit as st
import time
import random
from dotenv import load_dotenv
from src.scraper import HaUIScraper
from src.rag_engine import RAGSystem
from src.config import (
    APP_TITLE, APP_ICON, APP_DESCRIPTION,
    HAUI_PRIMARY_COLOR, HAUI_LOGO_URL,
    QUICK_PROMPTS, WELCOME_MESSAGES
)

load_dotenv()

# === Custom CSS ===
def inject_custom_css():
    """Inject custom CSS for HaUI branding."""
    st.markdown(f"""
    <style>
        /* Header styling */
        .main-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 10px 0;
            border-bottom: 3px solid {HAUI_PRIMARY_COLOR};
            margin-bottom: 20px;
        }}
        .main-header img {{
            height: 60px;
        }}
        .main-header h1 {{
            color: {HAUI_PRIMARY_COLOR};
            margin: 0;
            font-size: 1.8rem;
        }}
        
        /* Quick prompt buttons */
        .quick-prompt {{
            background-color: #f0f2f6;
            border: 1px solid #ddd;
            border-radius: 20px;
            padding: 8px 16px;
            margin: 4px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .quick-prompt:hover {{
            background-color: {HAUI_PRIMARY_COLOR};
            color: white;
        }}
        
        /* Source citation styling */
        .source-box {{
            background-color: #f8f9fa;
            border-left: 4px solid {HAUI_PRIMARY_COLOR};
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 0 8px 8px 0;
        }}
        .source-box a {{
            color: {HAUI_PRIMARY_COLOR};
            text-decoration: none;
        }}
        .source-box a:hover {{
            text-decoration: underline;
        }}
        
        /* Chat message avatars */
        .stChatMessage [data-testid="chatAvatarIcon-user"] {{
            background-color: {HAUI_PRIMARY_COLOR} !important;
        }}
        .stChatMessage [data-testid="chatAvatarIcon-assistant"] {{
            background-color: #FFD700 !important;
        }}
        
        /* Footer */
        .footer {{
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: {HAUI_PRIMARY_COLOR};
            color: white;
            text-align: center;
            padding: 8px;
            font-size: 0.8rem;
        }}
        
        /* Feedback buttons */
        .feedback-btn {{
            background: none;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 5px 10px;
            cursor: pointer;
            margin: 2px;
        }}
        .feedback-btn:hover {{
            background-color: #f0f2f6;
        }}
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Render the main header with HaUI branding."""
    st.markdown(f"""
    <div class="main-header">
        <img src="{HAUI_LOGO_URL}" alt="HaUI Logo" onerror="this.style.display='none'">
        <div>
            <h1>{APP_ICON} {APP_TITLE}</h1>
            <p style="margin: 0; color: gray;">{APP_DESCRIPTION}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_quick_prompts():
    """Render quick prompt suggestion buttons."""
    st.markdown("**💡 Gợi ý câu hỏi:**")
    cols = st.columns(3)
    for idx, prompt in enumerate(QUICK_PROMPTS):
        col_idx = idx % 3
        with cols[col_idx]:
            if st.button(prompt, key=f"quick_{idx}", use_container_width=True):
                return prompt
    return None


def render_sources(sources):
    """Render source citations."""
    if not sources:
        return
    
    with st.expander("📚 Nguồn tham khảo", expanded=False):
        for idx, src in enumerate(sources, 1):
            st.markdown(f"""
            <div class="source-box">
                <strong>{idx}. {src['title'][:80]}...</strong><br>
                <small>📁 {src['category']}</small><br>
                <a href="{src['url']}" target="_blank">🔗 Xem bài viết gốc</a>
            </div>
            """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with settings and controls."""
    with st.sidebar:
        st.image(HAUI_LOGO_URL, width=150)
        st.header("⚙️ Cài đặt")
        
        # Data update button
        if st.button("🔄 Cập nhật Dữ liệu", use_container_width=True):
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("📥 Đang thu thập dữ liệu...")
                scraper = HaUIScraper()
                scraper.crawl()
                progress_bar.progress(50)
                
                status_text.text("🔄 Đang xử lý và lưu vào database...")
                rag = RAGSystem()
                num_chunks = rag.ingest_data()
                progress_bar.progress(100)
                
                status_text.text(f"✅ Hoàn tất! Đã tạo {num_chunks} chunks.")
                time.sleep(2)
                status_text.empty()
                progress_bar.empty()
                
                st.cache_resource.clear()
                st.success("Dữ liệu đã được cập nhật!")
                
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
        
        st.divider()
        
        # Clear chat button
        if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.sources_history = []
            st.rerun()
        
        st.divider()
        
        # Statistics
        st.subheader("📊 Thống kê")
        if "messages" in st.session_state:
            user_msgs = len([m for m in st.session_state.messages if m["role"] == "user"])
            st.metric("Số câu hỏi", user_msgs)
        
        st.divider()
        
        # About section
        with st.expander("ℹ️ Về ứng dụng"):
            st.markdown("""
            **HaUI AI Assistant** là chatbot hỗ trợ tra cứu thông tin về Đại học Công nghiệp Hà Nội.
            
            - 🔍 Tìm kiếm thông tin tuyển sinh
            - 📚 Tra cứu ngành đào tạo
            - 📰 Cập nhật tin tức mới nhất
            
            **Phiên bản:** 2.0
            """)


def get_rag_system():
    """Get or create cached RAG system."""
    @st.cache_resource
    def _get_rag():
        return RAGSystem()
    return _get_rag()


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    inject_custom_css()
    render_header()
    render_sidebar()
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        welcome_msg = random.choice(WELCOME_MESSAGES)
        st.session_state.messages.append({
            "role": "assistant",
            "content": welcome_msg
        })
    
    if "sources_history" not in st.session_state:
        st.session_state.sources_history = []
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Quick prompts
        selected_prompt = render_quick_prompts()
        
        st.divider()
        
        # Chat history
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Show sources if available
                if message["role"] == "assistant" and idx < len(st.session_state.sources_history):
                    sources = st.session_state.sources_history[idx]
                    if sources:
                        render_sources(sources)
                
                # Feedback buttons for assistant messages
                if message["role"] == "assistant" and idx > 0:
                    col_a, col_b, col_c = st.columns([1, 1, 10])
                    with col_a:
                        if st.button("👍", key=f"up_{idx}"):
                            st.toast("Cảm ơn phản hồi của bạn!")
                    with col_b:
                        if st.button("👎", key=f"down_{idx}"):
                            st.toast("Cảm ơn! Chúng tôi sẽ cải thiện.")
        
        # Chat input
        prompt = st.chat_input("Bạn muốn hỏi gì về HaUI?")
        
        # Handle quick prompt selection
        if selected_prompt:
            prompt = selected_prompt
        
        if prompt:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate response
            with st.chat_message("assistant"):
                try:
                    rag = get_rag_system()
                    message_placeholder = st.empty()
                    full_response = ""
                    sources = []
                    
                    # Stream response
                    with st.spinner("🤔 Đang suy nghĩ..."):
                        for chunk in rag.stream_answer_with_sources(
                            prompt, 
                            st.session_state.messages[:-1]  # Exclude current question
                        ):
                            if chunk["type"] == "token":
                                full_response += chunk["content"]
                                message_placeholder.markdown(full_response + "▌")
                            elif chunk["type"] == "sources":
                                sources = chunk["content"]
                    
                    message_placeholder.markdown(full_response)
                    
                    # Store message and sources
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response
                    })
                    st.session_state.sources_history.append(sources)
                    
                    # Render sources
                    render_sources(sources)
                    
                except Exception as e:
                    error_msg = f"❌ Xin lỗi, đã xảy ra lỗi: {str(e)}"
                    st.error(error_msg)
                    
                    if "not found" in str(e).lower():
                        st.info("💡 Hãy nhấn '🔄 Cập nhật Dữ liệu' ở sidebar để khởi tạo database.")
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
                    st.session_state.sources_history.append([])
    
    with col2:
        # News highlights sidebar
        st.markdown("### 📰 Tin mới nhất")
        st.info("Tính năng đang phát triển...")


if __name__ == "__main__":
    main()
