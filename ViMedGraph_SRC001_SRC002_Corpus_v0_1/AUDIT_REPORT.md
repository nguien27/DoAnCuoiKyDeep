# INDEPENDENT AUDIT - SRC_001 + SRC_002 corpus v0.1

Audit này đọc lại các CSV đã xuất và đọc lại trực tiếp hai PDF gốc, độc lập với dữ liệu đang nằm trong bộ nhớ khi parser chạy.

## Kết quả
- Chunk đối chiếu chính xác ngược về PDF gốc: 351/351.
- Chunk không tìm thấy trong trang nguồn: 0
- Hash sai: 0
- Page range sai: 0
- Metadata thiếu: 0
- Section không có disease cha: 0
- Chunk không có disease cha: 0
- Chunk không có section cha: 0
- Disease ID trùng: 0
- Section ID trùng: 0
- Chunk ID trùng: 0
- Section nằm ngoài khoảng trang disease: 0
- Chunk nằm ngoài khoảng trang section: 0
- Sai cờ retrieval cho tài liệu tham khảo: 0
- Chunk còn ký tự mã hóa lỗi: 0
- Chunk còn watermark/stamp: 0
- Trang bắt đầu disease lệch Mục lục: 0

## Bất thường giữ nguyên từ nguồn
- Phát hiện 3 bất thường đánh số section ngay trong PDF gốc. Không tự sửa nội dung nguồn.
- SRC_001 / SRC_001_D15 / PDF trang 117: `VI. KẾT HỢP ĐIỀU TRỊ Y HỌC HIỆN ĐẠI`; observed=VI, expected theo vị trí=4.
- SRC_001 / SRC_001_D17 / PDF trang 127: `V. CÁC THỂ LÂM SÀNG VÀ ĐIỀU TRỊ`; observed=V, expected theo vị trí=3.
- SRC_002 / SRC_002_D09 / PDF trang 91: `IV. PHÒNG BỆNH`; observed=IV, expected theo vị trí=5.