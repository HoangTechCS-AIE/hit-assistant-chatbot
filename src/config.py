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
LLM_MODEL = "gpt-4o-mini"

# Embedding settings
USE_VIETNAMESE_EMBEDDING = True  # Set False to fallback to OpenAI
VIETNAMESE_EMBEDDING_MODEL = "AITeamVN/Vietnamese_Embedding"  # Best for Vietnamese
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"  # Fallback

CHUNK_SIZE = 500  # Reduced for Vietnamese (shorter sentences)
CHUNK_OVERLAP = 100
RETRIEVER_K = 6  # Number of documents to retrieve

# === Data Paths ===
DATA_DIR = "data"
JSON_DATA_PATH = "data/sict_haui_data.json"  # Updated for SICT scraper
CHROMA_DB_PATH = "./data/chroma_db"

# === Scraper Settings ===
SCRAPER_BASE_URL = "https://sict.haui.edu.vn"  # SICT website
SCRAPER_CATEGORIES: List[str] = [
    "/vn/tin-tuc",       # Tin tức
    "/vn/thong-bao",     # Thông báo
    "/vn/tuyen-dung",    # Tuyển dụng
    "/vn/su-kien",       # Sự kiện
    "/vn/cau-lac-bo",    # Câu lạc bộ
    "/vn/nghien-cuu",    # Nghiên cứu
    "/vn/sinh-vien",     # Sinh viên
]
SCRAPER_STATIC_PAGES: List[str] = [
    "/vn/html/cong-nghe-thong-tin",
    "/vn/html/khoa-hoc-may-tinh",
    "/vn/html/dai-hoc-he-thong-thong-tin",
    "/vn/html/ky-thuat-phan-mem",
    "/vn/html/an-toan-thong-tin",
    "/vn/html/cong-nghe-da-phuong-tien",
    "/vn/gioi-thieu",
]
SCRAPER_START_DATE = "2025-09-01"  # Only crawl from this date
SCRAPER_MAX_PAGES = 10
SCRAPER_DELAY_SECONDS = 1.0

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
SYSTEM_PROMPT = """Bạn là HaUI Assistant - trợ lý AI thông minh của Trường Công nghệ thông tin và Truyền thông (SICT), Đại học Công nghiệp Hà Nội.

## 🎯 NHIỆM VỤ:
Trả lời câu hỏi về SICT/HaUI một cách CHÍNH XÁC, THÂN THIỆN và DỄ HIỂU.

## 📋 QUY TẮC:
1. **ĐỌC KỸ** ngữ cảnh (context) và câu hỏi
2. **TRẢ LỜI TRỰC TIẾP** vào câu hỏi, không lan man
3. **TRÍCH DẪN CỤ THỂ** (số liệu, tên, ngày tháng) nếu có trong context
4. **NẾU KHÔNG CÓ** thông tin → nói rõ ràng và gợi ý cách tìm thêm
5. **SỬ DỤNG EMOJI** phù hợp để câu trả lời thân thiện hơn

## 📝 FORMAT TRẢ LỜI:
```
[Câu mở đầu ngắn gọn trả lời trực tiếp]

[Nội dung chi tiết với bullet points nếu cần]
• Điểm 1
• Điểm 2

[Gợi ý thêm hoặc thông tin liên hệ nếu phù hợp]
```

## 💡 VÍ DỤ TRẢ LỜI TỐT:

**Câu hỏi:** "SICT có những ngành nào?"
**Trả lời:** 
SICT đào tạo **6 ngành** bậc đại học:

1. 💻 **Công nghệ thông tin** (7480201)
2. 🔬 **Khoa học máy tính** (7480101)
3. 📊 **Hệ thống thông tin** (7480104)
4. 🔧 **Kỹ thuật phần mềm** (7480103)
5. 🔐 **An toàn thông tin** (7480202)
6. 🎨 **Công nghệ đa phương tiện** (7320113)

Bạn muốn tìm hiểu chi tiết về ngành nào?

---

**Câu hỏi không có thông tin:**
**Trả lời:**
Tôi chưa có thông tin cụ thể về vấn đề này trong dữ liệu hiện tại.

📞 Bạn có thể liên hệ trực tiếp:
- **Hotline:** 024.3733.1699
- **Email:** sict@haui.edu.vn
- **Website:** https://sict.haui.edu.vn

## 🏫 THÔNG TIN CƠ BẢN:
- **SICT** = Trường Công nghệ thông tin và Truyền thông
- **HaUI** = Đại học Công nghiệp Hà Nội (thành lập 1898)
- Trực thuộc: Bộ Công Thương
- Địa chỉ: Số 298 Cầu Diễn, Bắc Từ Liêm, Hà Nội

---
## 📚 CONTEXT (Dữ liệu tham khảo):
{context}

---
## 💬 LỊCH SỬ HỘI THOẠI:
{chat_history}

---
## ❓ CÂU HỎI:
{question}

## ✍️ TRẢ LỜI (tiếng Việt, thân thiện):"""

# === Welcome Messages ===
WELCOME_MESSAGES: List[str] = [
    "👋 Xin chào! Tôi là trợ lý AI của HaUI. Hãy hỏi tôi bất cứ điều gì về trường nhé!",
    "🎓 Chào mừng bạn đến với HaUI Assistant! Tôi sẵn sàng hỗ trợ bạn tìm hiểu về Đại học Công nghiệp Hà Nội.",
    "🏫 Xin chào! Bạn muốn biết gì về HaUI - ngôi trường hơn 125 năm tuổi?",
]
