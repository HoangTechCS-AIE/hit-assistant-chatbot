# Domain Filter - Quick Start Guide

## ✅ Đã hoàn thành

1. **Cập nhật System Prompt** (`src/config.py`)
   - Thêm phần "PHẠM VI TRẢ LỜI" 
   - Liệt kê rõ topic được phép/cấm
   - Thêm template từ chối lịch sự
   - Thêm 2 ví dụ từ chối cụ thể

2. **Tạo Test Script** (`test_domain_filter.py`)
   - 5 câu hỏi in-domain (sẽ trả lời)
   - 5 câu hỏi out-domain (sẽ từ chối)

---

## 🧪 Cách test

### Option 1: Chạy test script tự động

```bash
python test_domain_filter.py
```

Xem output để xác nhận filtering hoạt động.

### Option 2: Test thủ công trong Streamlit

1. **Restart app** (vì đã sửa config):
   ```bash
   Ctrl+C  # Dừng app đang chạy
   python -m streamlit run app.py
   ```

2. **Test các câu hỏi:**

   **In-domain (nên trả lời):**
   - "SICT có những ngành nào?"
   - "Học phí năm 2025"
   - "Địa chỉ trường ở đâu?"

   **Out-domain (nên từ chối lịch sự):**
   - "Giải phương trình x² + 5x + 6 = 0"
   - "Thủ đô Việt Vietnam là gì?"
   - "2 + 2 = ?"

---

## 📝 Expected Behavior

### ✅ In-domain response
```
SICT đào tạo 6 ngành bậc đại học:
1. 💻 Công nghệ thông tin (7480201)
...
```

### ❌ Out-domain response
```
Xin lỗi bạn, tôi là trợ lý chuyên về SICT/HaUI 
nên không thể giúp giải toán được.

Nhưng nếu bạn đang quan tâm đến ngành Toán tin 
hay Khoa học máy tính của HaUI thì tôi rất sẵn 
lòng tư vấn! 😊
```

---

## 🔧 Troubleshooting

**Nếu vẫn trả lời câu ngoài lề:**
- Kiểm tra app đã restart chưa (cache cũ)
- Xem lại `src/config.py` đã save chưa
- LLM có thể interpret linh hoạt, cần điều chỉnh prompt

**Nếu từ chối câu hỏi hợp lệ:**
- Mở rộng định nghĩa "in-domain" trong SYSTEM_PROMPT
- Thêm ví dụ edge case vào prompt
