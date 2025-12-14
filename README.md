# 🏫 HIT - RoiShaCoAy

**HIT - RoiShaCoAy** là hệ thống chatbot AI thông minh được xây dựng cho Trường Đại học Công nghiệp Hà Nội (HaUI), sử dụng công nghệ RAG (Retrieval-Augmented Generation) để cung cấp thông tin chính xác về trường học.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)

## ✨ Tính năng

- 🤖 **RAG Engine** - Truy xuất và sinh câu trả lời thông minh từ cơ sở dữ liệu
- 💬 **Conversation Memory** - Lưu trữ lịch sử hội thoại (ngắn hạn & dài hạn)
- 🔄 **Streaming Response** - Hiển thị câu trả lời theo thời gian thực
- 🌓 **Light/Dark Mode** - Giao diện hỗ trợ chế độ sáng/tối
- 📚 **Source Citation** - Trích dẫn nguồn tham khảo cho mỗi câu trả lời
- 🔍 **Domain Filtering** - Lọc câu hỏi theo phạm vi kiến thức
- 📱 **Responsive UI** - Giao diện thân thiện trên mọi thiết bị
- 🔗 **REST API** - API backend đầy đủ với FastAPI

## 🛠 Tech Stack

### Backend
- **FastAPI** - REST API framework
- **LangChain** - RAG orchestration
- **OpenAI GPT-4** - Language model
- **ChromaDB** - Vector database
- **SQLite** - Conversation memory storage

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Lucide React** - Icons
- **React Markdown** - Markdown rendering

### Additional
- **Streamlit** - Alternative UI (legacy)
- **BeautifulSoup4** - Web scraping
- **Sentence Transformers** - Vietnamese embeddings (optional)

## 📋 Yêu cầu hệ thống

- Python 3.8+
- Node.js 16+
- npm hoặc yarn
- OpenAI API key

## 🚀 Cài đặt

### 1. Clone repository
```bash
git clone https://github.com/yourusername/hit-assistant-chatbot.git
cd hit-assistant-chatbot
```

### 2. Thiết lập Backend

#### Tạo môi trường ảo (khuyến nghị)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows
```

#### Cài đặt dependencies
```bash
pip install -r requirements.txt
```

#### Cấu hình môi trường
Tạo file `.env` từ template:
```bash
cp .env.example .env
```

Chỉnh sửa `.env` và thêm OpenAI API key:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Thiết lập Frontend

```bash
cd frontend
npm install
```

### 4. Khởi tạo Database

```bash
# Thu thập dữ liệu từ website
python -c "from src.scraper import SICTAdvancedScraper; scraper = SICTAdvancedScraper(); scraper.crawl_all(); scraper.save_results()"

# Xây dựng vector database
python -c "from src.rag_engine import RAGSystem; rag = RAGSystem(); rag.ingest_data()"
```

## 🎮 Sử dụng

### Chạy Backend API
```bash
python api.py
```
API sẽ chạy tại: `http://localhost:8001`

### Chạy Frontend (React)
```bash
cd frontend
npm run dev
```
Frontend sẽ chạy tại: `http://localhost:3002`

### Chạy Streamlit App (Legacy)
```bash
streamlit run app.py
```
Streamlit sẽ chạy tại: `http://localhost:8501`

### Chạy tất cả cùng lúc
```bash
python start_app.py
```

## 📚 API Documentation

### Endpoints chính

#### Chat
```http
POST /api/chat
Content-Type: application/json

{
  "question": "SICT có những ngành nào?",
  "conversation_id": "uuid" (optional)
}
```

#### Streaming Chat
```http
POST /api/chat/stream
Content-Type: application/json

{
  "question": "Học phí năm 2025 là bao nhiêu?"
}
```

#### Conversations
```http
GET /api/conversations              # Lấy danh sách
GET /api/conversations/{id}        # Lấy chi tiết
DELETE /api/conversations/{id}     # Xóa conversation
POST /api/conversations/new        # Tạo mới
```

### API Docs (Swagger)
Truy cập: `http://localhost:8001/docs`

## 📁 Cấu trúc Project

```
hit-assistant-chatbot/
├── backend/              # FastAPI backend (legacy structure)
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── services/    # API services
│   │   └── App.jsx      # Main app
│   └── package.json
├── src/                 # Core modules
│   ├── rag_engine.py    # RAG system
│   ├── memory.py        # Conversation memory
│   ├── scraper.py       # Web scraper
│   └── config.py        # Configuration
├── data/                # Data storage
│   ├── sict_haui_data.json
│   ├── chroma_db/       # Vector database
│   └── memory.db        # SQLite database
├── api.py               # FastAPI main
├── app.py               # Streamlit app
├── requirements.txt     # Python dependencies
└── README.md
```

```

## 🔄 System Workflow

### Data Flow
1. **User Input** → Frontend React app
2. **API Request** → FastAPI backend (`/api/chat/stream`)
3. **Memory Check** → Load conversation history from SQLite
4. **RAG Retrieval** → Query ChromaDB for relevant documents
5. **LLM Generation** → OpenAI GPT-4 generates response with context
6. **Streaming Response** → Server-Sent Events back to frontend
7. **Memory Save** → Store conversation in SQLite
8. **UI Update** → Display streaming response with sources

## 🔧 Configuration


Chỉnh sửa `src/config.py` để tùy chỉnh:
- Model LLM
- Chunk size & overlap
- Retriever settings
- System prompt
- Embedding model

## 🧪 Testing

### Test scraper
```bash
python -c "from src.scraper import SICTAdvancedScraper; scraper = SICTAdvancedScraper(); scraper.crawl_all(max_pages=5)"
```

### Test RAG system
```bash
python -c "from src.rag_engine import RAGSystem; rag = RAGSystem(); print(rag.answer('SICT có những ngành nào?'))"
```

### Test API
```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Thông tin tuyển sinh"}'
```

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

## 👥 Authors

- **HoangTechCS-AIE** - [GitHub](https://github.com/HoangTechCS-AIE)

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) - RAG framework
- [OpenAI](https://openai.com/) - GPT models
- [Hanoi University of Industry](https://www.haui.edu.vn/)

## 📞 Contact

Project Link: [https://github.com/HoangTechCS-AIE/hit-assistant-chatbot](https://github.com/HoangTechCS-AIE/hit-assistant-chatbot)

---

Made with ❤️ for HaUI
