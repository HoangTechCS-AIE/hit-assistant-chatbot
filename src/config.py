"""
HaUI Chatbot - Centralized Configuration
"""
from typing import List

# === Application Settings ===
APP_TITLE = "HaUI AI Assistant"
APP_ICON = "🏫"
APP_DESCRIPTION = "Trợ lý ảo hỗ trợ tra cứu thông tin Đại học Công nghiệp Hà Nội"

# === HaUI Branding ===
HAUI_PRIMARY_COLOR = "#003366"  # Xanh dương đậm
HAUI_SECONDARY_COLOR = "#FFD700"  # Vàng
HAUI_LOGO_URL = "https://www.haui.edu.vn/dnn/web/haui/assets/images/logo-haui.png"

# === RAG Settings ===
LLM_MODEL = "gpt-3.5-turbo"
EMBEDDING_MODEL = "text-embedding-ada-002"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVER_K = 8  # Number of documents to retrieve (increased for better coverage)

# === Data Paths ===
DATA_DIR = "data"
JSON_DATA_PATH = "data/haui_news.json"
CHROMA_DB_PATH = "./data/chroma_db"

# === Scraper Settings ===
SCRAPER_CATEGORIES: List[str] = [
    "/vn/tin-tuc",
    "/vn/su-kien",
    "/vn/tuyen-sinh",
    "/vn/nganh-dao-tao",
]
SCRAPER_MAX_PAGES = 5
SCRAPER_DELAY_SECONDS = 1

# === Quick Prompts (Gợi ý câu hỏi) ===
QUICK_PROMPTS: List[str] = [
    "📚 Các ngành đào tạo của HaUI?",
    "💰 Học phí năm 2025 là bao nhiêu?",
    "📅 Lịch tuyển sinh đại học?",
    "🏆 Thành tích nổi bật của HaUI?",
    "📍 Địa chỉ các cơ sở của trường?",
    "🎓 Điều kiện xét tuyển?",
]

# === System Prompt ===
SYSTEM_PROMPT = """Bạn là HaUI Assistant - trợ lý AI chính thức của Đại học Công nghiệp Hà Nội.

## NHIỆM VỤ CHÍNH:
Trả lời câu hỏi của người dùng về HaUI một cách CHÍNH XÁC, TRỌNG TÂM và DỄ HIỂU.

## QUY TẮC BẮT BUỘC:
1. ĐỌC KỸ câu hỏi và XÁC ĐỊNH chính xác người dùng muốn biết điều gì
2. TÌM KIẾM thông tin liên quan trong Context bên dưới
3. TRẢ LỜI TRỰC TIẾP vào câu hỏi, không lan man
4. Nếu Context có thông tin → trích dẫn cụ thể (số liệu, tên, ngày tháng)
5. Nếu Context KHÔNG có thông tin → nói rõ "Tôi chưa có thông tin cụ thể về vấn đề này trong dữ liệu hiện tại."

## FORMAT TRẢ LỜI:
- Mở đầu: Trả lời ngắn gọn 1-2 câu vào trọng tâm
- Nội dung: Liệt kê chi tiết (nếu cần) bằng bullet points
- Kết thúc: Gợi ý thêm (nếu phù hợp)

## THÔNG TIN CƠ BẢN VỀ HaUI:
- Tên đầy đủ: Đại học Công nghiệp Hà Nội (Hanoi University of Industry)
- Thành lập: 1898 (hơn 125 năm lịch sử)
- Trực thuộc: Bộ Công Thương
- Quy mô: ~35.000 sinh viên, 60+ ngành đào tạo
- Thế mạnh: CNTT, Cơ khí, Điện-Điện tử, Kinh tế, Ngoại ngữ
- Website: https://www.haui.edu.vn

---
CONTEXT (Dữ liệu tham khảo):
{context}

---
LỊCH SỬ HỘI THOẠI:
{chat_history}

---
CÂU HỎI CỦA NGƯỜI DÙNG: {question}

TRẢ LỜI (bằng tiếng Việt, đúng trọng tâm):"""

# === Welcome Messages ===
WELCOME_MESSAGES: List[str] = [
    "👋 Xin chào! Tôi là trợ lý AI của HaUI. Hãy hỏi tôi bất cứ điều gì về trường nhé!",
    "🎓 Chào mừng bạn đến với HaUI Assistant! Tôi sẵn sàng hỗ trợ bạn tìm hiểu về Đại học Công nghiệp Hà Nội.",
    "🏫 Xin chào! Bạn muốn biết gì về HaUI - ngôi trường hơn 125 năm tuổi?",
]
