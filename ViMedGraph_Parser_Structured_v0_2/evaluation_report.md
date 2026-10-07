# ViMedGraph - Structured Appendix Parser v0.2

## Phạm vi
Parser rule-based cho 3 phụ lục bảng chính thức:
- SRC_003_PL01: BỆNH_CHỨNG và THỂ_BỆNH.
- SRC_004_PL01: TRIỆU_CHỨNG theo THỂ_BỆNH.
- SRC_004_PL06: BÀI_THUỐC/phương thức, thành phần DƯỢC_LIỆU và THỂ_BỆNH.

Chưa xử lý văn xuôi SRC_001/SRC_002.

## Coverage theo ID nguồn
- SRC_003_PL01: 228/228 ID 650xxxx = 38 bệnh/chứng + 190 thể bệnh.
- SRC_004_PL01: 1.451/1.451 ID 654xxxx.
- SRC_004_PL06: 523/523 ID 658xxxx.

Coverage chỉ chứng minh không bỏ sót ID, không đồng nghĩa mọi trường dữ liệu đều hoàn hảo.

## Audit dữ liệu và sửa lỗi từ parser v0.1
1. Bổ sung loại mã `TNxxx` cho 8 bản ghi `Thuốc nam` trong PL06.
2. Sửa xử lý qua trang quanh ID 6586594/6586595: nguồn có 6586594 chỉ hiện ID, không được gán nhầm thành phần của 6586595 sang 6586594.
3. Sửa biên trang quanh 6586864: loại phần `Sinh địa` bị table extractor kéo nhầm từ bản ghi trước; thành phần 6586864 bắt đầu bằng `Huyết dụ (lá)`.
4. Làm sạch watermark/layout noise trong tên bệnh, thể bệnh và bài thuốc.
5. Với triệu chứng, đối chiếu thêm cột `Thể lâm sàng` thay vì chỉ suy parent từ mã triệu chứng.
6. Sửa `run_parser.ps1` dùng `$PSScriptRoot`, tránh lỗi đường dẫn khi chạy từ thư mục dự án.
7. Sửa mặc định đánh giá sang gold v0.3 và bổ sung kiểm tra độ chính xác thuộc tính entity.

## Bất thường có ngay trong nguồn, không tự ý sửa official_code
- 6542131: official_code in là `U60.471.6.02.Đ13`, nhưng cột Thể lâm sàng ghi `U60.471.9.02`.
- 6542397: official_code in là `U66.371.02.Đ08`, nhưng cột Thể lâm sàng ghi `U66.372.02`.
Parser giữ nguyên `official_code` theo nguồn, đặt `parent_code` theo cột Thể lâm sàng và đánh cờ `source_code_parent_mismatch`.
- 6586594: nguồn chỉ hiện ID, các cột còn lại trống; parser giữ bản ghi nhưng đánh cờ `source_incomplete_record` và không gán dữ liệu của bản ghi kế tiếp.

Chi tiết nằm trong `data_quality_report.json`.

## Đánh giá pilot gold v0.3
- Entity identity: Precision=1.000, Recall=1.000, F1=1.000.
- Explicit relation identity: Precision=1.000, Recall=1.000, F1=1.000.
- Derived relation identity: Precision=1.000, Recall=1.000, F1=1.000.
- Entity attribute accuracy trên các trường quan trọng: 1.000.

Kết quả này chỉ áp dụng cho pilot 4 bệnh và các phụ lục bảng có mã chuẩn. Không được diễn giải là toàn pipeline ViMedGraph đạt 100%.
