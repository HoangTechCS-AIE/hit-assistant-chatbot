# Hướng dẫn: Sửa lỗi Embedding Dimension Mismatch

## 🔴 Lỗi hiện tại
```
Collection expecting embedding with dimension of 1024, got 1536
```

**Nguyên nhân:** Database ChromaDB được tạo với Vietnamese embedding model (1024 dimensions), nhưng code hiện đang cố dùng OpenAI embedding model (1536 dimensions).

---

## ✅ Giải pháp (3 bước)

### Bước 1: Dừng tất cả Streamlit apps
**Vấn đề:** Database đang bị lock bởi app đang chạy

**Giải pháp:**
1. Nhấn `Ctrl+C` trong terminal để dừng:
   - `python -m streamlit run app.py`
   - `python -m streamlit run view_db.py --server.port 8510`

2. Hoặc dùng Task Manager để kill process `streamlit`

---

### Bước 2: Chạy script rebuild database
```bash
python rebuild_db.py
```

Script sẽ:
- ✅ Xóa database cũ (với dimension không đúng)
- ✅ Tạo database mới với embedding nhất quán
- ✅ Test kết nối

---

### Bước 3: Khởi động lại app
```bash
python -m streamlit run app.py
```

---

## 🔧 Tùy chọn: Chọn embedding model

Mở file `src/config.py` và chỉnh:

**Option 1: Dùng Vietnamese model (Khuyến nghị cho tiếng Việt)**
```python
USE_VIETNAMESE_EMBEDDING = True  # 1024 dims
```

**Option 2: Dùng OpenAI model (Nhanh hơn, ít yêu cầu RAM)**
```python
USE_VIETNAMESE_EMBEDDING = False  # 1536 dims
```

⚠️ **Lưu ý:** Sau khi đổi config, phải chạy lại `rebuild_db.py`

---

## 📊 Chi tiết kỹ thuật

| Model | Dimensions | Ưu điểm | Nhược điểm |
|-------|-----------|---------|------------|
| Vietnamese_Embedding | 1024 | Hiểu tiếng Việt tốt hơn | Cần cài `sentence-transformers` |
| OpenAI text-embedding-3-small | 1536 | Nhanh, ổn định | Tốn API cost, hiểu tiếng Việt kém hơn |

---

## ❓ Nếu vẫn lỗi

1. **Kiểm tra process đang chạy:**
   ```bash
   tasklist | findstr streamlit
   ```

2. **Xóa DB thủ công:**
   ```bash
   rmdir /s /q data\chroma_db
   ```

3. **Tạo lại từ đầu:**
   ```bash
   python rebuild_db.py
   ```
