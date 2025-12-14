"""
FAQ Handler for HaUI Chatbot
Provides fast responses for common questions without LLM calls.
Includes intent classification and related question suggestions.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Phân loại ý định câu hỏi."""
    FAQ = "faq"                     # Câu hỏi thường gặp
    INFORMATION = "information"      # Yêu cầu thông tin chi tiết
    NAVIGATION = "navigation"        # Yêu cầu link/hướng dẫn
    COMPARISON = "comparison"        # So sánh các lựa chọn
    CONTACT = "contact"             # Yêu cầu thông tin liên hệ
    SCHEDULE = "schedule"           # Hỏi về lịch/thời gian
    GREETING = "greeting"           # Chào hỏi
    UNKNOWN = "unknown"             # Không xác định


@dataclass
class FAQEntry:
    """Một mục trong FAQ database."""
    question: str
    answer: str
    keywords: List[str]
    category: str
    related_questions: List[str] = None


@dataclass
class FAQResult:
    """Kết quả tìm kiếm FAQ."""
    found: bool
    entry: Optional[FAQEntry] = None
    confidence: float = 0.0
    suggestions: List[str] = None


class FAQHandler:
    """
    Xử lý câu hỏi thường gặp:
    - Trả lời nhanh không cần LLM
    - Phân loại ý định (intent)
    - Gợi ý câu hỏi liên quan
    """
    
    # === FAQ DATABASE ===
    FAQ_DATA: List[FAQEntry] = [
        # === THÔNG TIN CHUNG ===
        FAQEntry(
            question="SICT là gì?",
            answer="""**SICT** (School of Information and Communications Technology) là **Trường Công nghệ thông tin và Truyền thông** thuộc Đại học Công nghiệp Hà Nội.

🏫 **Thông tin cơ bản:**
- Tên tiếng Việt: Trường Công nghệ thông tin và Truyền thông
- Trực thuộc: Đại học Công nghiệp Hà Nội (HaUI)
- Website: https://sict.haui.edu.vn""",
            keywords=["sict", "là gì", "viết tắt", "nghĩa là"],
            category="general",
            related_questions=[
                "SICT có những ngành đào tạo nào?",
                "Địa chỉ SICT ở đâu?",
                "Liên hệ SICT như thế nào?"
            ]
        ),
        
        FAQEntry(
            question="HaUI là trường gì?",
            answer="""**HaUI** (Hanoi University of Industry) là **Đại học Công nghiệp Hà Nội**.

🏛️ **Thông tin cơ bản:**
- Thành lập: 1898 (hơn 125 năm lịch sử)
- Trực thuộc: Bộ Công Thương
- Quy mô: ~35.000 sinh viên, 60+ ngành đào tạo
- Website: https://www.haui.edu.vn

📍 **3 Cơ sở:**
- Cơ sở 1: Số 298 Cầu Diễn, Bắc Từ Liêm, Hà Nội
- Cơ sở 2: Phường Yên Viên, Gia Lâm, Hà Nội
- Cơ sở 3: Phủ Lý, Hà Nam""",
            keywords=["haui", "đại học công nghiệp", "hà nội", "trường gì"],
            category="general",
            related_questions=[
                "HaUI có bao nhiêu cơ sở?",
                "Các ngành đào tạo của HaUI?",
                "HaUI trực thuộc bộ nào?"
            ]
        ),
        
        # === NGÀNH ĐÀO TẠO ===
        FAQEntry(
            question="SICT có những ngành đào tạo nào?",
            answer="""**SICT** đào tạo **6 ngành** ở bậc đại học:

1. 💻 **Công nghệ thông tin** (7480201)
2. 🔬 **Khoa học máy tính** (7480101)
3. 📊 **Hệ thống thông tin** (7480104)
4. 🔧 **Kỹ thuật phần mềm** (7480103)
5. 🔐 **An toàn thông tin** (7480202)
6. 🎨 **Công nghệ đa phương tiện** (7320113)

Tất cả các ngành đều cấp bằng **Cử nhân** sau 4 năm học.""",
            keywords=["ngành", "đào tạo", "chuyên ngành", "học gì", "có những"],
            category="programs",
            related_questions=[
                "Ngành CNTT học những gì?",
                "So sánh CNTT và KHMT?",
                "Điểm chuẩn các ngành?"
            ]
        ),
        
        FAQEntry(
            question="Ngành Công nghệ thông tin học gì?",
            answer="""**Ngành Công nghệ thông tin (CNTT)** đào tạo kiến thức và kỹ năng về:

📚 **Kiến thức chuyên môn:**
- Lập trình (Python, Java, C++, Web)
- Cơ sở dữ liệu và quản trị hệ thống
- Mạng máy tính và an ninh mạng
- Phát triển phần mềm và ứng dụng

🎯 **Chuẩn đầu ra:**
- Thiết kế, triển khai giải pháp phần mềm
- Quản trị hệ thống và mạng
- Làm việc nhóm và giao tiếp hiệu quả

💼 **Cơ hội việc làm:**
- Lập trình viên, Developer
- Quản trị mạng, System Admin
- Phân tích hệ thống, BA
- Tester, QA Engineer""",
            keywords=["cntt", "công nghệ thông tin", "học gì", "ra làm gì", "môn học"],
            category="programs",
            related_questions=[
                "Điểm chuẩn ngành CNTT?",
                "Học phí ngành CNTT?",
                "CNTT khác KTPM như thế nào?"
            ]
        ),
        
        FAQEntry(
            question="Ngành An toàn thông tin học gì?",
            answer="""**Ngành An toàn thông tin (ATTT)** đào tạo chuyên gia bảo mật:

🔐 **Kiến thức chuyên môn:**
- Mật mã học và bảo mật dữ liệu
- An ninh mạng và hệ thống
- Phát hiện và xử lý tấn công
- Kiểm thử xâm nhập (Penetration Testing)

🎯 **Chuẩn đầu ra:**
- Thiết kế giải pháp bảo mật
- Đánh giá và xử lý rủi ro
- Tuân thủ chính sách an toàn thông tin

💼 **Cơ hội việc làm:**
- Security Engineer
- Penetration Tester
- Security Analyst
- SOC Analyst""",
            keywords=["attt", "an toàn thông tin", "bảo mật", "security"],
            category="programs",
            related_questions=[
                "Điểm chuẩn ngành ATTT?",
                "ATTT có khó không?",
                "Việc làm ngành ATTT như thế nào?"
            ]
        ),
        
        # === TUYỂN SINH ===
        FAQEntry(
            question="Điểm chuẩn các ngành là bao nhiêu?",
            answer="""📊 **Điểm chuẩn** của SICT thay đổi hàng năm. Để biết điểm chuẩn mới nhất, bạn nên:

1. Truy cập website: https://sict.haui.edu.vn/vn/tuyen-sinh
2. Liên hệ Trung tâm Tuyển sinh: 024.3733.1699

💡 **Lưu ý:**
- Điểm chuẩn phụ thuộc vào tổ hợp xét tuyển
- Các ngành CNTT thường có điểm chuẩn cao hơn
- Có thể xét tuyển bằng học bạ hoặc điểm thi THPT""",
            keywords=["điểm chuẩn", "điểm xét tuyển", "bao nhiêu điểm"],
            category="admission",
            related_questions=[
                "Các phương thức xét tuyển?",
                "Tổ hợp xét tuyển ngành CNTT?",
                "Khi nào nộp hồ sơ?"
            ]
        ),
        
        # === HỌC PHÍ ===
        FAQEntry(
            question="Học phí là bao nhiêu?",
            answer="""💰 **Học phí** của HaUI được tính theo tín chỉ:

📋 **Thông tin chung:**
- Học phí tính theo tín chỉ đăng ký mỗi kỳ
- Mức học phí thay đổi theo năm học
- Có các chính sách miễn giảm cho sinh viên

📞 **Để biết mức học phí cụ thể:**
- Liên hệ Phòng Tài chính Kế toán
- Hotline: 024.3733.1699
- Website: https://www.haui.edu.vn

💡 **Chính sách hỗ trợ:**
- Học bổng khuyến khích học tập
- Miễn giảm học phí theo diện chính sách
- Vay vốn sinh viên qua Ngân hàng CSXH""",
            keywords=["học phí", "tiền học", "bao nhiêu tiền", "đóng tiền"],
            category="finance",
            related_questions=[
                "Có học bổng không?",
                "Chính sách miễn giảm học phí?",
                "Cách đóng học phí online?"
            ]
        ),
        
        # === LIÊN HỆ ===
        FAQEntry(
            question="Liên hệ SICT như thế nào?",
            answer="""📞 **Thông tin liên hệ Trường CNTT&TT (SICT):**

🏢 **Địa chỉ:**
Trường Công nghệ thông tin và Truyền thông
Đại học Công nghiệp Hà Nội
Số 298 Cầu Diễn, Bắc Từ Liêm, Hà Nội

📱 **Điện thoại:** 024.3733.1699
📧 **Email:** sict@haui.edu.vn
🌐 **Website:** https://sict.haui.edu.vn
📘 **Facebook:** /SICT.HaUI

⏰ **Giờ làm việc:**
- Thứ 2 - Thứ 6: 8:00 - 17:00
- Nghỉ trưa: 12:00 - 13:30""",
            keywords=["liên hệ", "số điện thoại", "email", "địa chỉ", "ở đâu"],
            category="contact",
            related_questions=[
                "Địa chỉ các cơ sở của HaUI?",
                "Phòng Đào tạo ở đâu?",
                "Hotline tuyển sinh?"
            ]
        ),
    ]
    
    # === GREETING PATTERNS ===
    GREETING_PATTERNS = [
        r'^(xin\s+)?chào',
        r'^hi\b',
        r'^hello',
        r'^hey\b',
        r'^ê\b',
        r'^alo',
    ]
    
    GREETING_RESPONSES = [
        "Xin chào! 👋 Tôi là trợ lý AI của SICT - HaUI. Bạn cần hỏi gì về trường không?",
        "Chào bạn! 🎓 Tôi có thể giúp gì cho bạn về SICT và HaUI?",
        "Hello! 👋 Mình là HaUI Assistant. Hãy hỏi mình bất cứ điều gì về trường nhé!",
    ]
    
    def __init__(self):
        """Initialize FAQ handler."""
        self._compile_patterns()
        self._build_keyword_index()
    
    def _compile_patterns(self):
        """Compile regex patterns."""
        self._greeting_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.GREETING_PATTERNS
        ]
    
    def _build_keyword_index(self):
        """Build keyword index for fast lookup."""
        self._keyword_index: Dict[str, List[FAQEntry]] = {}
        for entry in self.FAQ_DATA:
            for keyword in entry.keywords:
                kw_lower = keyword.lower()
                if kw_lower not in self._keyword_index:
                    self._keyword_index[kw_lower] = []
                self._keyword_index[kw_lower].append(entry)
    
    def classify_intent(self, query: str) -> IntentType:
        """
        Phân loại ý định của câu hỏi.
        
        Args:
            query: Câu hỏi của người dùng
            
        Returns:
            IntentType enum
        """
        query_lower = query.lower()
        
        # Check greeting
        for pattern in self._greeting_patterns:
            if pattern.search(query_lower):
                return IntentType.GREETING
        
        # Check contact
        contact_keywords = ['liên hệ', 'số điện thoại', 'email', 'địa chỉ', 'hotline']
        if any(kw in query_lower for kw in contact_keywords):
            return IntentType.CONTACT
        
        # Check schedule
        schedule_keywords = ['lịch', 'khi nào', 'thời gian', 'deadline', 'hạn']
        if any(kw in query_lower for kw in schedule_keywords):
            return IntentType.SCHEDULE
        
        # Check comparison
        comparison_keywords = ['so sánh', 'khác', 'hay là', 'nên chọn', 'vs', 'versus']
        if any(kw in query_lower for kw in comparison_keywords):
            return IntentType.COMPARISON
        
        # Check navigation
        nav_keywords = ['link', 'website', 'url', 'trang web', 'ở đâu']
        if any(kw in query_lower for kw in nav_keywords):
            return IntentType.NAVIGATION
        
        # Check FAQ keywords
        for keyword in self._keyword_index.keys():
            if keyword in query_lower:
                return IntentType.FAQ
        
        return IntentType.INFORMATION
    
    def find_faq(self, query: str) -> FAQResult:
        """
        Tìm kiếm câu trả lời trong FAQ database.
        
        Args:
            query: Câu hỏi của người dùng
            
        Returns:
            FAQResult với câu trả lời nếu tìm thấy
        """
        query_lower = query.lower()
        
        # Check greeting first
        for pattern in self._greeting_patterns:
            if pattern.search(query_lower):
                import random
                return FAQResult(
                    found=True,
                    entry=FAQEntry(
                        question="Chào hỏi",
                        answer=random.choice(self.GREETING_RESPONSES),
                        keywords=[],
                        category="greeting",
                        related_questions=["SICT là gì?", "Các ngành đào tạo?", "Liên hệ SICT?"]
                    ),
                    confidence=1.0,
                    suggestions=["SICT là gì?", "Các ngành đào tạo?", "Liên hệ SICT?"]
                )
        
        # Score each FAQ entry
        scores: List[Tuple[float, FAQEntry]] = []
        
        for entry in self.FAQ_DATA:
            score = 0.0
            matched_keywords = 0
            
            for keyword in entry.keywords:
                if keyword.lower() in query_lower:
                    matched_keywords += 1
                    score += 1.0 / len(entry.keywords)
            
            # Check category keywords
            category_boost = {
                "ngành": 0.2,
                "học": 0.1,
                "phí": 0.15,
                "điểm": 0.15,
                "liên hệ": 0.2,
            }
            for cat_kw, boost in category_boost.items():
                if cat_kw in query_lower and cat_kw in entry.question.lower():
                    score += boost
            
            if score > 0:
                scores.append((score, entry))
        
        if not scores:
            return FAQResult(found=False, suggestions=self._get_default_suggestions())
        
        # Sort by score
        scores.sort(key=lambda x: x[0], reverse=True)
        best_score, best_entry = scores[0]
        
        # Threshold for confidence
        if best_score >= 0.4:
            return FAQResult(
                found=True,
                entry=best_entry,
                confidence=min(best_score, 1.0),
                suggestions=best_entry.related_questions or self._get_default_suggestions()
            )
        
        return FAQResult(
            found=False,
            suggestions=[s[1].question for s in scores[:3]] or self._get_default_suggestions()
        )
    
    def _get_default_suggestions(self) -> List[str]:
        """Get default question suggestions."""
        return [
            "SICT có những ngành đào tạo nào?",
            "Điểm chuẩn các ngành?",
            "Liên hệ SICT như thế nào?",
        ]
    
    def get_related_questions(self, query: str, n: int = 3) -> List[str]:
        """
        Gợi ý câu hỏi liên quan.
        
        Args:
            query: Câu hỏi hiện tại
            n: Số lượng gợi ý
            
        Returns:
            Danh sách câu hỏi gợi ý
        """
        result = self.find_faq(query)
        if result.suggestions:
            return result.suggestions[:n]
        return self._get_default_suggestions()[:n]


# === SINGLETON INSTANCE ===
_faq_handler_instance: Optional[FAQHandler] = None

def get_faq_handler() -> FAQHandler:
    """Get or create the singleton FAQ handler instance."""
    global _faq_handler_instance
    if _faq_handler_instance is None:
        _faq_handler_instance = FAQHandler()
    return _faq_handler_instance


def check_faq(query: str) -> FAQResult:
    """
    Convenient function to check FAQ.
    
    Args:
        query: User's query
        
    Returns:
        FAQResult
    """
    handler = get_faq_handler()
    return handler.find_faq(query)


# === TEST ===
if __name__ == "__main__":
    handler = FAQHandler()
    
    test_queries = [
        "Xin chào",
        "SICT là gì?",
        "ngành cntt học gì?",
        "học phí bao nhiêu?",
        "liên hệ sict như thế nào?",
        "so sánh cntt và khmt",
        "deadline nộp hồ sơ khi nào?",
        "cho hỏi về machine learning",
    ]
    
    print("=" * 60)
    print("FAQ Handler - Test Cases")
    print("=" * 60)
    
    for query in test_queries:
        result = handler.find_faq(query)
        intent = handler.classify_intent(query)
        
        print(f"\n📝 Query: {query}")
        print(f"🎯 Intent: {intent.value}")
        print(f"✅ Found: {result.found} (confidence: {result.confidence:.2f})")
        if result.found and result.entry:
            print(f"📖 Answer preview: {result.entry.answer[:100]}...")
        print(f"💡 Suggestions: {result.suggestions}")
