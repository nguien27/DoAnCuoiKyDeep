# QA REPORT - SRC_001 + SRC_002 corpus preprocessing v0.1

## Phạm vi
- Chỉ xử lý phần 36 bệnh trong SRC_001 và SRC_002.
- Không chunk phần front matter; SRC_001 cũng loại danh mục dược liệu cuối tài liệu (đã có nguồn chuẩn hóa riêng).
- Xóa watermark xiên/stamp và số trang footer khỏi text; sửa các lỗi mã hóa ký tự rõ ràng của PDF 2025 (ví dụ Ƣ→Ư, ƣ→ư).

## Kết quả định lượng
- Bệnh: 36 (SRC_001=20, SRC_002=16).
- Section: 217.
- Chunk tổng: 351; dùng retrieval: 315; tài liệu tham khảo (flag không retrieval): 36.
- Độ dài chunk: median 2008 ký tự / 433 từ; mean 1797.1 ký tự; max 2800 ký tự.

## Kiểm tra ngược
- Đối chiếu độc lập lại từng chunk với PDF gốc: 351/351 chunk tìm thấy chính xác trong khoảng trang đã ghi.
- Disease ID trùng: 0
- Section ID trùng: 0
- Chunk ID trùng: 0
- Chunk rỗng: 0
- Page range sai: 0
- Ký tự mã hóa lỗi còn sót: 0
- Watermark/stamp còn sót: 0
- Metadata thiếu: 0
- Hash mismatch: 0
- Bệnh không bắt đầu bằng I. ĐẠI CƯƠNG: 0
- Mismatch số line body vs section: 0
- Bất thường số thứ tự section trong nguồn: 3

## Đối chiếu trang bắt đầu theo Mục lục
- SRC_001: 20/20 bệnh; sai trang bắt đầu so với Mục lục = 0.
- SRC_002: 16/16 bệnh; sai trang bắt đầu so với Mục lục = 0.

## Quy tắc provenance
- Mỗi chunk giữ source_id, tên file, năm, disease_id, section_id, page PDF và page hiển thị của tài liệu.
- source_text chỉ gồm text được lấy từ PDF sau bước làm sạch kỹ thuật; retrieval_text chỉ thêm tiêu đề bệnh + section phía trước source_text để dùng cho embedding/retrieval.
- TÀI LIỆU THAM KHẢO vẫn được lưu nhưng retrieval_enabled=0 để tránh retrieval lấy danh mục tài liệu thay vì nội dung chuyên môn.

## Cảnh báo từ chính tài liệu nguồn
- Có 3 bất thường đánh số section trong PDF gốc; parser giữ nguyên và gắn cờ, không tự sửa:
  - SRC_001 - Viêm dạ dày và tá tràng, PDF trang 117: `VI. KẾT HỢP ĐIỀU TRỊ Y HỌC HIỆN ĐẠI`, trong chuỗi section vị trí này đáng lẽ là IV.
  - SRC_001 - Bệnh phổi tắc nghẽn mạn tính, PDF trang 127: `V. CÁC THỂ LÂM SÀNG VÀ ĐIỀU TRỊ`, trong chuỗi section vị trí này đáng lẽ là III.
  - SRC_002 - Tăng sinh lành tính tuyến tiền liệt, PDF trang 91: `IV. PHÒNG BỆNH`, sau một mục IV khác nên vị trí này đáng lẽ là V.
- Các trường hợp này được ghi trong `source_structure_anomalies.csv` với `action=preserved_source_no_auto_fix`.