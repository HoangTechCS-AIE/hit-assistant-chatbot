"""
HaUI AI Assistant - Main Streamlit Application
A RAG-based chatbot for Hanoi University of Industry with conversation memory.
"""
import streamlit as st
import time
import random
from dotenv import load_dotenv
from src.scraper import SICTAdvancedScraper
from src.rag_engine import RAGSystem
from src.memory import get_memory_manager, MemoryManager
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
        .main-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 10px 0;
            border-bottom: 3px solid {HAUI_PRIMARY_COLOR};
            margin-bottom: 20px;
        }}
        .main-header img {{ height: 60px; }}
        .main-header h1 {{ color: {HAUI_PRIMARY_COLOR}; margin: 0; font-size: 1.8rem; }}
        
        .source-box {{
            background-color: #f8f9fa;
            border-left: 4px solid {HAUI_PRIMARY_COLOR};
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 0 8px 8px 0;
        }}
        .source-box a {{ color: {HAUI_PRIMARY_COLOR}; text-decoration: none; }}
        
        .conversation-item {{
            padding: 8px 12px;
            margin: 4px 0;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .conversation-item:hover {{
            background-color: #f0f2f6;
        }}
        .conversation-item.active {{
            background-color: {HAUI_PRIMARY_COLOR};
            color: white;
        }}
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Render the main header."""
    st.markdown(f"""
    <div class="main-header">
        <img src="{HAUI_LOGO_URL}" alt="HaUI Logo" onerror="this.style.display='none'">
        <div>
            <h1>{APP_ICON} {APP_TITLE}</h1>
            <p style="margin: 0; color: gray;">{APP_DESCRIPTION}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


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


def render_sidebar(memory: MemoryManager):
    """Render sidebar with conversation history."""
    with st.sidebar:
        st.image(HAUI_LOGO_URL, width=150)
        
        # === New Conversation Button ===
        if st.button("➕ Cuộc trò chuyện mới", use_container_width=True, type="primary"):
            # Save current conversation first
            if memory.current_conversation and memory.current_conversation.messages:
                memory.save_conversation()
            
            # Start new conversation
            memory.start_conversation()
            st.session_state.messages = []
            st.session_state.sources_history = []
            st.session_state.current_conv_id = memory.current_conversation.id
            st.rerun()
        
        st.divider()
        
        # === Conversation History ===
        st.subheader("💬 Lịch sử trò chuyện")
        
        conversations = memory.get_conversation_list(limit=15)
        
        if conversations:
            for conv in conversations:
                is_active = (st.session_state.get("current_conv_id") == conv["id"])
                
                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(
                        f"{'📌 ' if is_active else ''}{conv['title'][:30]}...",
                        key=f"conv_{conv['id']}",
                        use_container_width=True,
                        disabled=is_active
                    ):
                        # Save current before switching
                        if memory.current_conversation:
                            memory.save_conversation()
                        
                        # Load selected conversation
                        memory.load_conversation(conv["id"])
                        st.session_state.current_conv_id = conv["id"]
                        st.session_state.messages = [
                            {"role": m.role, "content": m.content}
                            for m in memory.current_conversation.messages
                        ]
                        st.session_state.sources_history = []
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"del_{conv['id']}", help="Xóa"):
                        memory.delete_conversation(conv["id"])
                        if is_active:
                            memory.start_conversation()
                            st.session_state.messages = []
                            st.session_state.current_conv_id = memory.current_conversation.id
                        st.rerun()
        else:
            st.info("Chưa có lịch sử trò chuyện")
        
        st.divider()
        
        # === Settings ===
        with st.expander("⚙️ Cài đặt"):
            if st.button("🔄 Cập nhật Dữ liệu", use_container_width=True):
                try:
                    with st.spinner("Đang cập nhật..."):
                        scraper = SICTAdvancedScraper()
                        scraper.state.reset()
                        scraper.crawl_all(parallel=True)
                        scraper.save_results()
                        
                        rag = RAGSystem()
                        num_chunks = rag.ingest_data()
                        
                        st.cache_resource.clear()
                        st.success(f"✅ Đã cập nhật {len(scraper.articles)} bài viết!")
                except Exception as e:
                    st.error(f"❌ Lỗi: {e}")
            
            if st.button("🧹 Xóa toàn bộ lịch sử", use_container_width=True):
                if st.checkbox("Xác nhận xóa tất cả"):
                    memory.clear_all()
                    st.session_state.messages = []
                    st.rerun()


def get_rag_system():
    """Get cached RAG system."""
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
    
    # Initialize memory manager
    memory = get_memory_manager()
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    if "sources_history" not in st.session_state:
        st.session_state.sources_history = []
    
    if "current_conv_id" not in st.session_state:
        # Start or restore conversation
        if memory.current_conversation is None:
            memory.start_conversation()
        st.session_state.current_conv_id = memory.current_conversation.id
        
        # Add welcome message
        if not st.session_state.messages:
            welcome = random.choice(WELCOME_MESSAGES)
            st.session_state.messages.append({"role": "assistant", "content": welcome})
            memory.add_message("assistant", welcome)
    
    render_sidebar(memory)
    
    # === Main Chat Area ===
    
    # Quick prompts
    st.markdown("**💡 Gợi ý câu hỏi:**")
    cols = st.columns(3)
    selected_prompt = None
    for idx, prompt in enumerate(QUICK_PROMPTS):
        with cols[idx % 3]:
            if st.button(prompt, key=f"quick_{idx}", use_container_width=True):
                selected_prompt = prompt
    
    st.divider()
    
    # Display chat messages
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show sources for assistant messages
            if message["role"] == "assistant" and idx < len(st.session_state.sources_history):
                sources = st.session_state.sources_history[idx]
                if sources:
                    render_sources(sources)
    
    # Chat input
    prompt = st.chat_input("Bạn muốn hỏi gì về HaUI?")
    if selected_prompt:
        prompt = selected_prompt
    
    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        memory.add_message("user", prompt)
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            try:
                rag = get_rag_system()
                message_placeholder = st.empty()
                full_response = ""
                sources = []
                
                # Get context from memory
                chat_history = memory.get_context(max_turns=5)
                
                with st.spinner("🤔 Đang suy nghĩ..."):
                    for chunk in rag.stream_answer_with_sources(prompt, chat_history):
                        if chunk["type"] == "token":
                            full_response += chunk["content"]
                            message_placeholder.markdown(full_response + "▌")
                        elif chunk["type"] == "sources":
                            sources = chunk["content"]
                
                message_placeholder.markdown(full_response)
                
                # Store message
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state.sources_history.append(sources)
                memory.add_message("assistant", full_response)
                
                # Auto-save conversation
                memory.save_conversation()
                
                render_sources(sources)
                
            except Exception as e:
                error_msg = f"❌ Lỗi: {str(e)}"
                st.error(error_msg)
                
                if "not found" in str(e).lower():
                    st.info("💡 Nhấn '🔄 Cập nhật Dữ liệu' ở sidebar.")
                
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                st.session_state.sources_history.append([])


if __name__ == "__main__":
    main()
