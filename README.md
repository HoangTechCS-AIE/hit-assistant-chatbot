# HaUI AI Assistant 🏫

Trợ lý AI hỗ trợ tra cứu thông tin Đại học Công nghiệp Hà Nội (HaUI).

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.1+-green.svg)

## 🌟 Tính năng

- **💬 Chat thông minh**: Hỏi đáp về HaUI với AI
- **📚 Nguồn tham khảo**: Hiển thị nguồn cho mỗi câu trả lời
- **🔄 Cập nhật dữ liệu**: Crawl tự động từ website HaUI
- **💡 Gợi ý câu hỏi**: Quick prompts phổ biến
- **🎨 Giao diện HaUI**: Branding chính thức của trường

## 🚀 Cài đặt

```bash
# 1. Clone repository
cd haui-chatbot

# 2. Tạo virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Cài đặt dependencies
pip install -r requirements.txt

# 4. Cấu hình API key
cp .env.example .env
# Sửa file .env và thêm OPENAI_API_KEY
```

## 📖 Sử dụng

```bash
# Chạy ứng dụng
streamlit run app.py

# Mở trình duyệt: http://localhost:8501
```

## 🏗️ Kiến trúc

```
haui-chatbot/
├── app.py                 # Streamlit UI
├── src/
│   ├── config.py         # Cấu hình tập trung
│   ├── scraper.py        # Web scraper cho HaUI
│   └── rag_engine.py     # RAG với LangChain
├── data/
│   ├── haui_news.json    # Dữ liệu crawl
│   └── chroma_db/        # Vector database
└── .streamlit/
    └── config.toml       # Theme Streamlit
```

## 🛠️ Công nghệ

| Thành phần | Công nghệ |
|------------|-----------|
| Frontend | Streamlit |
| LLM | OpenAI GPT-3.5 |
| Embeddings | OpenAI Ada-002 |
| Vector DB | ChromaDB |
| Framework | LangChain |

## 👥 Tác giả

Đại học Công nghiệp Hà Nội - HaUI

## 📄 License

MIT License
