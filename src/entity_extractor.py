"""
Entity Extractor for HaUI Chatbot
Extracts structured information from crawled data and user queries.
Supports: phone numbers, emails, dates, addresses, departments.
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntities:
    """Container for extracted entities from text."""
    phone_numbers: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    dates: List[Dict[str, Any]] = field(default_factory=list)
    addresses: List[str] = field(default_factory=list)
    departments: List[str] = field(default_factory=list)
    deadlines: List[Dict[str, Any]] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "phone_numbers": self.phone_numbers,
            "emails": self.emails,
            "dates": self.dates,
            "addresses": self.addresses,
            "departments": self.departments,
            "deadlines": self.deadlines,
            "urls": self.urls,
        }
    
    def has_entities(self) -> bool:
        """Check if any entities were extracted."""
        return bool(
            self.phone_numbers or self.emails or self.dates or 
            self.addresses or self.departments or self.deadlines or self.urls
        )
    
    def format_for_response(self) -> str:
        """Format entities for chatbot response."""
        parts = []
        
        if self.phone_numbers:
            parts.append(f"📞 **Số điện thoại:** {', '.join(self.phone_numbers)}")
        
        if self.emails:
            parts.append(f"📧 **Email:** {', '.join(self.emails)}")
        
        if self.addresses:
            parts.append(f"📍 **Địa chỉ:** {'; '.join(self.addresses)}")
        
        if self.deadlines:
            deadline_strs = [d.get('text', '') for d in self.deadlines]
            parts.append(f"⏰ **Deadline:** {', '.join(deadline_strs)}")
        
        if self.urls:
            parts.append(f"🔗 **Link:** {', '.join(self.urls)}")
        
        return '\n'.join(parts)


class EntityExtractor:
    """
    Trích xuất thông tin có cấu trúc từ văn bản:
    - Số điện thoại (VN format)
    - Email
    - Ngày tháng, deadline
    - Địa chỉ
    - Phòng ban, đơn vị
    - URLs
    """
    
    # === REGEX PATTERNS ===
    
    # Số điện thoại Việt Nam
    PHONE_PATTERNS = [
        r'(?:0|\+84)(?:\d{9,10})',                    # 0123456789 or +84123456789
        r'(?:0|\+84)[\s.-]?\d{2,3}[\s.-]?\d{3}[\s.-]?\d{3,4}',  # 0xx xxx xxxx
        r'\d{4}[\s.-]?\d{3}[\s.-]?\d{3}',             # xxxx xxx xxx
    ]
    
    # Email
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    # URL
    URL_PATTERN = r'https?://[^\s<>"{}|\\^`\[\]]+'
    
    # Ngày tháng Việt Nam
    DATE_PATTERNS = [
        # dd/mm/yyyy or dd-mm-yyyy
        (r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', 'dmy'),
        # yyyy/mm/dd or yyyy-mm-dd
        (r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})', 'ymd'),
        # Ngày dd tháng mm năm yyyy
        (r'ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})', 'vn_full'),
        # dd tháng mm
        (r'(\d{1,2})\s+tháng\s+(\d{1,2})', 'vn_short'),
    ]
    
    # Deadline keywords
    DEADLINE_KEYWORDS = [
        'hạn', 'deadline', 'trước ngày', 'đến ngày', 'hết hạn',
        'nộp trước', 'đăng ký trước', 'hạn cuối', 'hạn nộp'
    ]
    
    # HaUI Departments
    DEPARTMENTS = [
        "Trường Công nghệ thông tin và Truyền thông",
        "Trường CNTT&TT", "SICT",
        "Khoa Công nghệ thông tin",
        "Khoa Điện tử", "Khoa Cơ khí",
        "Khoa Kinh tế", "Khoa Ngoại ngữ",
        "Phòng Đào tạo", "Phòng Công tác sinh viên",
        "Phòng Tài chính Kế toán",
        "Trung tâm Tuyển sinh",
        "Trung tâm Hỗ trợ sinh viên",
        "Thư viện", "Ký túc xá",
    ]
    
    # Address keywords
    ADDRESS_KEYWORDS = [
        'địa chỉ', 'tại', 'ở', 'đường', 'phố', 'quận', 'huyện',
        'phường', 'xã', 'thành phố', 'tỉnh', 'số nhà', 'tòa nhà',
        'cơ sở 1', 'cơ sở 2', 'cơ sở 3'
    ]
    
    def __init__(self):
        """Initialize entity extractor with compiled patterns."""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        # Compile phone patterns
        self._phone_patterns = [
            re.compile(p) for p in self.PHONE_PATTERNS
        ]
        
        # Compile email pattern
        self._email_pattern = re.compile(self.EMAIL_PATTERN, re.IGNORECASE)
        
        # Compile URL pattern
        self._url_pattern = re.compile(self.URL_PATTERN)
        
        # Compile date patterns
        self._date_patterns = [
            (re.compile(p, re.IGNORECASE), fmt) for p, fmt in self.DATE_PATTERNS
        ]
        
        # Compile deadline pattern
        deadline_keywords = '|'.join(re.escape(k) for k in self.DEADLINE_KEYWORDS)
        self._deadline_pattern = re.compile(
            rf'({deadline_keywords})\s*:?\s*(.{{10,50}})',
            re.IGNORECASE
        )
    
    def extract_phone_numbers(self, text: str) -> List[str]:
        """
        Trích xuất số điện thoại từ văn bản.
        
        Args:
            text: Văn bản đầu vào
            
        Returns:
            Danh sách số điện thoại
        """
        phones = set()
        for pattern in self._phone_patterns:
            matches = pattern.findall(text)
            for match in matches:
                # Normalize phone number
                phone = re.sub(r'[\s.\-]', '', match)
                if len(phone) >= 10:
                    phones.add(phone)
        return list(phones)
    
    def extract_emails(self, text: str) -> List[str]:
        """
        Trích xuất địa chỉ email từ văn bản.
        
        Args:
            text: Văn bản đầu vào
            
        Returns:
            Danh sách email
        """
        return list(set(self._email_pattern.findall(text)))
    
    def extract_urls(self, text: str) -> List[str]:
        """
        Trích xuất URLs từ văn bản.
        
        Args:
            text: Văn bản đầu vào
            
        Returns:
            Danh sách URLs
        """
        return list(set(self._url_pattern.findall(text)))
    
    def extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """
        Trích xuất ngày tháng từ văn bản.
        
        Args:
            text: Văn bản đầu vào
            
        Returns:
            Danh sách dates với format và raw text
        """
        dates = []
        seen = set()
        
        for pattern, fmt in self._date_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                raw_text = match.group(0)
                if raw_text in seen:
                    continue
                seen.add(raw_text)
                
                try:
                    groups = match.groups()
                    if fmt == 'dmy' and len(groups) >= 3:
                        day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                        date_obj = datetime(year, month, day)
                        dates.append({
                            "text": raw_text,
                            "day": day,
                            "month": month,
                            "year": year,
                            "iso": date_obj.strftime('%Y-%m-%d')
                        })
                    elif fmt == 'ymd' and len(groups) >= 3:
                        year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                        date_obj = datetime(year, month, day)
                        dates.append({
                            "text": raw_text,
                            "day": day,
                            "month": month,
                            "year": year,
                            "iso": date_obj.strftime('%Y-%m-%d')
                        })
                    elif fmt == 'vn_full' and len(groups) >= 3:
                        day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                        date_obj = datetime(year, month, day)
                        dates.append({
                            "text": raw_text,
                            "day": day,
                            "month": month,
                            "year": year,
                            "iso": date_obj.strftime('%Y-%m-%d')
                        })
                    elif fmt == 'vn_short' and len(groups) >= 2:
                        day, month = int(groups[0]), int(groups[1])
                        dates.append({
                            "text": raw_text,
                            "day": day,
                            "month": month,
                            "year": None,
                            "iso": None
                        })
                except (ValueError, IndexError):
                    # Invalid date, skip
                    continue
        
        return dates
    
    def extract_deadlines(self, text: str) -> List[Dict[str, Any]]:
        """
        Trích xuất thông tin deadline từ văn bản.
        
        Args:
            text: Văn bản đầu vào
            
        Returns:
            Danh sách deadlines
        """
        deadlines = []
        matches = self._deadline_pattern.finditer(text)
        
        for match in matches:
            keyword = match.group(1)
            context = match.group(2).strip()
            
            # Try to extract date from context
            dates = self.extract_dates(context)
            
            deadlines.append({
                "keyword": keyword,
                "text": context,
                "dates": dates
            })
        
        return deadlines
    
    def extract_departments(self, text: str) -> List[str]:
        """
        Trích xuất tên phòng ban, đơn vị từ văn bản.
        
        Args:
            text: Văn bản đầu vào
            
        Returns:
            Danh sách phòng ban
        """
        found = []
        text_lower = text.lower()
        
        for dept in self.DEPARTMENTS:
            if dept.lower() in text_lower:
                found.append(dept)
        
        return list(set(found))
    
    def extract_addresses(self, text: str) -> List[str]:
        """
        Trích xuất địa chỉ từ văn bản (heuristic).
        
        Args:
            text: Văn bản đầu vào
            
        Returns:
            Danh sách địa chỉ (ước tính)
        """
        addresses = []
        
        # Look for common address patterns
        patterns = [
            # Số nhà + đường
            r'(?:số\s*)?\d+[A-Za-z]?\s+(?:đường|phố)\s+[^,\n]{5,50}',
            # Cơ sở X
            r'cơ sở\s+\d\s*[-:]\s*[^,\n]{10,100}',
            # Địa chỉ: ...
            r'địa chỉ\s*:\s*[^,\n]{10,100}',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            addresses.extend(matches)
        
        return list(set(addr.strip() for addr in addresses))
    
    def extract_all(self, text: str) -> ExtractedEntities:
        """
        Trích xuất tất cả entities từ văn bản.
        
        Args:
            text: Văn bản đầu vào
            
        Returns:
            ExtractedEntities object với tất cả entities
        """
        return ExtractedEntities(
            phone_numbers=self.extract_phone_numbers(text),
            emails=self.extract_emails(text),
            dates=self.extract_dates(text),
            addresses=self.extract_addresses(text),
            departments=self.extract_departments(text),
            deadlines=self.extract_deadlines(text),
            urls=self.extract_urls(text),
        )


# === SINGLETON INSTANCE ===
_extractor_instance: Optional[EntityExtractor] = None

def get_entity_extractor() -> EntityExtractor:
    """Get or create the singleton entity extractor instance."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = EntityExtractor()
    return _extractor_instance


def extract_entities(text: str) -> ExtractedEntities:
    """
    Convenient function to extract entities from text.
    
    Args:
        text: Input text
        
    Returns:
        ExtractedEntities object
    """
    extractor = get_entity_extractor()
    return extractor.extract_all(text)


# === TEST ===
if __name__ == "__main__":
    extractor = EntityExtractor()
    
    test_texts = [
        """
        Liên hệ: Phòng Đào tạo - Số điện thoại: 024.3733.1699
        Email: daotao@haui.edu.vn
        Địa chỉ: Số 298 Cầu Diễn, Bắc Từ Liêm, Hà Nội
        """,
        """
        Hạn đăng ký học phần: trước ngày 15/01/2025
        Deadline nộp hồ sơ: 30 tháng 12 năm 2024
        """,
        """
        Trường Công nghệ thông tin và Truyền thông thông báo
        lịch thi học kỳ 1 năm học 2024-2025.
        Xem chi tiết tại: https://sict.haui.edu.vn/vn/thong-bao
        """,
    ]
    
    print("=" * 60)
    print("Entity Extractor - Test Cases")
    print("=" * 60)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📄 Test Case {i}:")
        print("-" * 40)
        entities = extractor.extract_all(text)
        print(entities.format_for_response() or "No entities found")
        print(f"\n📊 Full data: {entities.to_dict()}")
