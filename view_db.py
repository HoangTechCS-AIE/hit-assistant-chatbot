import streamlit as st
import json
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="HaUI Database Viewer", page_icon="🔍", layout="wide")

st.title("🔍 HaUI Database Viewer")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["📊 Thống kê", "📰 Dữ liệu JSON", "🗄️ Vector Database"])

# Tab 1: Statistics
with tab1:
    st.header("Thống kê dữ liệu")
    
    # Load JSON data
    json_path = "data/haui_news.json"
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Tổng số bài viết", len(data))
        
        # Count by category
        tin_tuc = sum(1 for item in data if '/tin-tuc/' in item['url'])
        su_kien = sum(1 for item in data if '/su-kien/' in item['url'])
        
        with col2:
            st.metric("Tin tức", tin_tuc)
        
        with col3:
            st.metric("Sự kiện", su_kien)
        
        # Check data quality
        no_title = sum(1 for item in data if item['title'] == "No Title")
        no_content = sum(1 for item in data if item['content'] == "Content not found")
        
        st.subheader("Chất lượng dữ liệu")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Bài viết thiếu tiêu đề", no_title)
        
        with col2:
            st.metric("Bài viết thiếu nội dung", no_content)
        
        if no_title > 0 or no_content > 0:
            st.warning("Có dữ liệu bị thiếu. Hãy chạy lại scraper hoặc nhấn 'Cập nhật Dữ liệu' trong app chính.")
        else:
            st.success("Dữ liệu hoàn chỉnh!")
    else:
        st.error(f"Không tìm thấy file dữ liệu: {json_path}")

# Tab 2: JSON Data Browser
with tab2:
    st.header("Danh sách bài viết")
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Filter options
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("Tìm kiếm theo tiêu đề hoặc URL")
        with col2:
            category_filter = st.selectbox("Lọc theo danh mục", ["Tất cả", "Tin tức", "Sự kiện"])
        
        # Apply filters
        filtered_data = data
        if search_term:
            filtered_data = [
                item for item in filtered_data 
                if search_term.lower() in item['title'].lower() or search_term.lower() in item['url'].lower()
            ]
        
        if category_filter == "Tin tức":
            filtered_data = [item for item in filtered_data if '/tin-tuc/' in item['url']]
        elif category_filter == "Sự kiện":
            filtered_data = [item for item in filtered_data if '/su-kien/' in item['url']]
        
        st.write(f"Hiển thị {len(filtered_data)} / {len(data)} bài viết")
        
        # Display articles
        for idx, item in enumerate(filtered_data[:50]):  # Limit to 50 for performance
            with st.expander(f"{idx+1}. {item['title'][:100]}..."):
                st.write(f"**URL:** {item['url']}")
                st.write(f"**Tiêu đề:** {item['title']}")
                st.write(f"**Nội dung:** ({len(item['content'])} ký tự)")
                st.text_area(
                    "Xem trước nội dung", 
                    item['content'][:500] + "..." if len(item['content']) > 500 else item['content'],
                    height=150,
                    key=f"content_{idx}"
                )
        
        if len(filtered_data) > 50:
            st.info(f"Chỉ hiển thị 50 bài viết đầu tiên. Tổng cộng có {len(filtered_data)} kết quả.")
    else:
        st.error("Không tìm thấy dữ liệu JSON")

# Tab 3: Vector Database
with tab3:
    st.header("Vector Database (Chroma)")
    
    db_path = "./data/chroma_db"
    
    if os.path.exists(db_path):
        try:
            from langchain_community.vectorstores import Chroma
            from langchain_openai import OpenAIEmbeddings
            
            embeddings = OpenAIEmbeddings()
            vectorstore = Chroma(persist_directory=db_path, embedding_function=embeddings)
            
            # Get collection info
            collection = vectorstore._collection
            count = collection.count()
            
            st.success(f"Đã kết nối với Chroma DB")
            st.metric("Số lượng chunks (đoạn văn bản)", count)
            
            # Search functionality
            st.subheader("Tìm kiếm tương tự")
            query = st.text_input("Nhập câu hỏi để tìm kiếm các đoạn văn bản liên quan")
            
            if query:
                results = vectorstore.similarity_search(query, k=5)
                
                st.write(f"Tìm thấy {len(results)} kết quả liên quan:")
                
                for idx, doc in enumerate(results):
                    with st.expander(f"Kết quả {idx+1}: {doc.metadata.get('title', 'N/A')[:80]}..."):
                        st.write(f"**Nguồn:** {doc.metadata.get('source', 'N/A')}")
                        st.write(f"**Tiêu đề:** {doc.metadata.get('title', 'N/A')}")
                        st.text_area(
                            "Nội dung", 
                            doc.page_content,
                            height=200,
                            key=f"vector_{idx}"
                        )
        
        except Exception as e:
            st.error(f"Lỗi khi đọc Chroma DB: {e}")
            st.info("Hãy đảm bảo bạn đã chạy `ingest_data()` trong RAGSystem để tạo database.")
    else:
        st.warning(f"Chưa có Chroma DB tại: {db_path}")
        st.info("Hãy nhấn 'Cập nhật Dữ liệu' trong app chính để tạo vector database.")

# Footer
st.divider()
st.caption("💡 **Tip:** Chạy app chính với `streamlit run app.py` và viewer này với `streamlit run view_db.py --server.port 8502`")
