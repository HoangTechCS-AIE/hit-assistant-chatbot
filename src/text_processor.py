"""
Vietnamese Text Processor for HaUI Chatbot
Handles spell checking, abbreviation expansion, and text normalization.
Optimized for educational domain (SICT/HaUI context).
"""

import re
import unicodedata
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class VietnameseTextProcessor:
    """
    Xử lý văn bản tiếng Việt:
    - Sửa lỗi chính tả thông dụng
    - Mở rộng từ viết tắt
    - Chuẩn hóa Unicode
    - Xử lý từ lóng giới trẻ
    """
    
    # === TỪ VIẾT TẮT PHỔ BIẾN ===
    ABBREVIATIONS: Dict[str, str] = {
        # Giáo dục
        "sv": "sinh viên",
        "gv": "giảng viên",
        "ths": "thạc sĩ",
        "ts": "tiến sĩ",
        "pgs": "phó giáo sư",
        "gs": "giáo sư",
        "cn": "cử nhân",
        "ks": "kỹ sư",
        "đh": "đại học",
        "cđ": "cao đẳng",
        "tc": "trung cấp",
        "hv": "học viên",
        "hvch": "học viên cao học",
        "ncs": "nghiên cứu sinh",
        "đatn": "đồ án tốt nghiệp",
        "kltn": "khóa luận tốt nghiệp",
        "đamh": "đồ án môn học",
        "btl": "bài tập lớn",
        "gpa": "điểm trung bình tích lũy",
        
        # Ngành học
        "cntt": "công nghệ thông tin",
        "khmt": "khoa học máy tính",
        "ktpm": "kỹ thuật phần mềm",
        "httt": "hệ thống thông tin",
        "attt": "an toàn thông tin",
        "ttnt": "trí tuệ nhân tạo",
        "ai": "trí tuệ nhân tạo",
        "ml": "học máy",
        "dl": "học sâu",
        "iot": "internet vạn vật",
        "cnđpt": "công nghệ đa phương tiện",
        "đtvt": "điện tử viễn thông",
        "cơđt": "cơ điện tử",
        "ktđk": "kỹ thuật điều khiển",
        
        # Trường/Khoa
        "haui": "đại học công nghiệp hà nội",
        "sict": "trường công nghệ thông tin và truyền thông",
        "dhcnhn": "đại học công nghiệp hà nội",
        "bct": "bộ công thương",
        
        # Hành chính
        "hp": "học phần",
        "tc": "tín chỉ",
        "hk": "học kỳ",
        "nh": "năm học",
        "ctđt": "chương trình đào tạo",
        "đcv": "điểm chuẩn vào",
        "xl": "xét lại",
        "hp2": "học phần 2",
        "tkb": "thời khóa biểu",
        "lhp": "lịch học phần",
        "đkhp": "đăng ký học phần",
        "clb": "câu lạc bộ",
        "đtn": "đoàn thanh niên",
        "hsv": "hội sinh viên",
        
        # Thông dụng
        "nt": "nhắn tin",
        "sđt": "số điện thoại",
        "đc": "địa chỉ",
        "hcm": "hồ chí minh",
        "hn": "hà nội",
        "tphcm": "thành phố hồ chí minh",
        "vn": "việt nam",
        "tn": "thứ năm",
        "t2": "thứ hai",
        "t3": "thứ ba",
        "t4": "thứ tư",
        "t5": "thứ năm",
        "t6": "thứ sáu",
        "t7": "thứ bảy",
        "cn": "chủ nhật",
        
        # Từ viết tắt internet
        "dc": "được",
        "ko": "không",
        "k": "không",
        "hok": "học",
        "thi": "thi",
        "bt": "bình thường",
        "ntn": "như thế nào",
        "cx": "cũng",
        "vs": "với",
        "j": "gì",
        "z": "vậy",
        "r": "rồi",
        "lm": "làm",
        "ns": "nói",
        "đc": "được",
        "đag": "đang",
        "mk": "mình",
        "bn": "bạn",
        "trc": "trước",
        "sau": "sau",
    }
    
    # === LỖI CHÍNH TẢ THÔNG DỤNG ===
    COMMON_TYPOS: Dict[str, str] = {
        # Lỗi dấu
        "công nghe": "công nghệ",
        "thông tinh": "thông tin",
        "đai học": "đại học",
        "nganh": "ngành",
        "truong": "trường",
        "sinh vien": "sinh viên",
        "giang vien": "giảng viên",
        "hoc phi": "học phí",
        "tuyen sinh": "tuyển sinh",
        "dao tao": "đào tạo",
        "chuong trinh": "chương trình",
        "ky thuat": "kỹ thuật",
        "phan mem": "phần mềm",
        "he thong": "hệ thống",
        "an toan": "an toàn",
        "may tinh": "máy tính",
        "khoa hoc": "khoa học",
        "cong nghiep": "công nghiệp",
        "ha noi": "hà nội",
        
        # Lỗi phụ âm
        "công ngệ": "công nghệ",
        "thôg tin": "thông tin",
        "sihn viên": "sinh viên",
        "giản viên": "giảng viên",
        
        # Lỗi nguyên âm
        "cuông nghệ": "công nghệ",
        "thung tin": "thông tin",
        "đoà tạo": "đào tạo",
        
        # Lỗi viết liền
        "côngnghệ": "công nghệ",
        "thôngtin": "thông tin",
        "sinhviên": "sinh viên",
        "đạihọc": "đại học",
        "họcphí": "học phí",
        
        # Domain-specific
        "cntt": "công nghệ thông tin",  # Đã có trong abbreviations nhưng giữ để backup
    }
    
    # === TỪ LÓNG GIỚI TRẺ ===
    SLANG_WORDS: Dict[str, str] = {
        "ôkê": "được",
        "ok": "được",
        "okie": "được",
        "okela": "được",
        "oke": "được",
        "noob": "người mới",
        "pro": "chuyên nghiệp",
        "fix": "sửa",
        "bug": "lỗi",
        "deadline": "hạn nộp",
        "submit": "nộp bài",
        "review": "đánh giá",
        "pass": "đỗ",
        "fail": "trượt",
        "gpa": "điểm trung bình",
        "gap year": "năm nghỉ",
        "intern": "thực tập",
        "offer": "đề nghị làm việc",
    }
    
    def __init__(self, enable_typo_fix: bool = True, enable_abbrev: bool = True):
        """
        Khởi tạo text processor.
        
        Args:
            enable_typo_fix: Bật/tắt sửa lỗi chính tả
            enable_abbrev: Bật/tắt mở rộng từ viết tắt
        """
        self.enable_typo_fix = enable_typo_fix
        self.enable_abbrev = enable_abbrev
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for faster matching."""
        # Pattern for abbreviations (word boundaries)
        abbrev_pattern = r'\b(' + '|'.join(
            re.escape(k) for k in sorted(self.ABBREVIATIONS.keys(), key=len, reverse=True)
        ) + r')\b'
        self._abbrev_regex = re.compile(abbrev_pattern, re.IGNORECASE)
        
        # Pattern for slang
        slang_pattern = r'\b(' + '|'.join(
            re.escape(k) for k in sorted(self.SLANG_WORDS.keys(), key=len, reverse=True)
        ) + r')\b'
        self._slang_regex = re.compile(slang_pattern, re.IGNORECASE)
    
    def normalize_unicode(self, text: str) -> str:
        """
        Chuẩn hóa Unicode (NFC normalization).
        Đảm bảo các ký tự tiếng Việt được biểu diễn nhất quán.
        
        Args:
            text: Văn bản đầu vào
            
        Returns:
            Văn bản đã chuẩn hóa
        """
        return unicodedata.normalize('NFC', text)
    
    def expand_abbreviations(self, text: str) -> str:
        """
        Mở rộng từ viết tắt thành từ đầy đủ.
        
        Args:
            text: Văn bản đầu vào
            
        Returns:
            Văn bản đã mở rộng từ viết tắt
        """
        if not self.enable_abbrev:
            return text
        
        def replace_abbrev(match):
            abbrev = match.group(1).lower()
            return self.ABBREVIATIONS.get(abbrev, match.group(0))
        
        return self._abbrev_regex.sub(replace_abbrev, text)
    
    def fix_typos(self, text: str) -> str:
        """
        Sửa lỗi chính tả thông dụng.
        
        Args:
            text: Văn bản đầu vào
            
        Returns:
            Văn bản đã sửa lỗi
        """
        if not self.enable_typo_fix:
            return text
        
        result = text.lower()
        for typo, correct in self.COMMON_TYPOS.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(typo), re.IGNORECASE)
            result = pattern.sub(correct, result)
        
        return result
    
    def replace_slang(self, text: str) -> str:
        """
        Thay thế từ lóng bằng từ chuẩn.
        
        Args:
            text: Văn bản đầu vào
            
        Returns:
            Văn bản đã thay thế từ lóng
        """
        def replace_slang_word(match):
            slang = match.group(1).lower()
            return self.SLANG_WORDS.get(slang, match.group(0))
        
        return self._slang_regex.sub(replace_slang_word, text)
    
    def clean_whitespace(self, text: str) -> str:
        """
        Chuẩn hóa khoảng trắng.
        
        Args:
            text: Văn bản đầu vào
            
        Returns:
            Văn bản đã chuẩn hóa khoảng trắng
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove whitespace around punctuation
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        return text.strip()
    
    def process(self, text: str) -> Tuple[str, Dict[str, any]]:
        """
        Xử lý toàn bộ văn bản qua tất cả các bước.
        
        Args:
            text: Văn bản đầu vào
            
        Returns:
            Tuple gồm (văn bản đã xử lý, metadata về các thay đổi)
        """
        original = text
        changes = {
            "original": original,
            "abbreviations_expanded": [],
            "typos_fixed": [],
            "slang_replaced": [],
        }
        
        # Step 1: Normalize Unicode
        text = self.normalize_unicode(text)
        
        # Step 2: Expand abbreviations
        before_abbrev = text
        text = self.expand_abbreviations(text)
        if before_abbrev != text:
            changes["abbreviations_expanded"].append({
                "before": before_abbrev,
                "after": text
            })
        
        # Step 3: Fix typos
        before_typo = text
        text = self.fix_typos(text)
        if before_typo.lower() != text.lower():
            changes["typos_fixed"].append({
                "before": before_typo,
                "after": text
            })
        
        # Step 4: Replace slang
        before_slang = text
        text = self.replace_slang(text)
        if before_slang.lower() != text.lower():
            changes["slang_replaced"].append({
                "before": before_slang,
                "after": text
            })
        
        # Step 5: Clean whitespace
        text = self.clean_whitespace(text)
        
        changes["processed"] = text
        changes["was_modified"] = original.lower() != text.lower()
        
        return text, changes
    
    def process_simple(self, text: str) -> str:
        """
        Xử lý văn bản đơn giản, chỉ trả về kết quả.
        
        Args:
            text: Văn bản đầu vào
            
        Returns:
            Văn bản đã xử lý
        """
        processed, _ = self.process(text)
        return processed


# === SINGLETON INSTANCE ===
_processor_instance: Optional[VietnameseTextProcessor] = None

def get_text_processor() -> VietnameseTextProcessor:
    """Get or create the singleton text processor instance."""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = VietnameseTextProcessor()
    return _processor_instance


def process_query(query: str) -> str:
    """
    Convenient function to process a query.
    
    Args:
        query: User's raw query
        
    Returns:
        Processed query ready for RAG
    """
    processor = get_text_processor()
    return processor.process_simple(query)


# === TEST ===
if __name__ == "__main__":
    processor = VietnameseTextProcessor()
    
    test_cases = [
        "CNTT là gì?",
        "Học phí SV năm 2025 là bao nhiêu?",
        "SICT có những ngành nào?",
        "công nghe thông tinh học j?",
        "deadline đăng ký học phần khi nào?",
        "GV hướng dẫn ĐATN là ai?",
        "cho mk hỏi HTTT vs KTPM khác j nhau?",
        "haui ở đâu z bn?",
    ]
    
    print("=" * 60)
    print("Vietnamese Text Processor - Test Cases")
    print("=" * 60)
    
    for query in test_cases:
        processed, changes = processor.process(query)
        print(f"\n📝 Input:  {query}")
        print(f"✅ Output: {processed}")
        if changes["was_modified"]:
            print(f"   [Modified]")
