# ViMedGraph Pilot/Gold v0.3

## Mục đích
Bộ dữ liệu nhỏ đã đối chiếu nguồn để kiểm tra parser, entity/relation extraction và import Knowledge Graph trước khi xử lý toàn corpus.

## Phạm vi
- 4 BỆNH_CHỨNG: Yêu thống, Hạc tất phong, Thống phong, Chứng tý (U62.021).
- Mỗi bệnh chọn 1 THỂ_BỆNH đại diện.
- 36 TRIỆU_CHỨNG.
- 15 BÀI_THUỐC/phương thức trong cột bài thuốc của Phụ lục VI.
- 65 tên DƯỢC_LIỆU duy nhất theo đúng cách viết trong Phụ lục VI.
- 124 entity.
- 151 relation được nguồn thể hiện trực tiếp.
- 36 relation BỆNH_CHỨNG --CÓ_TRIỆU_CHỨNG--> TRIỆU_CHỨNG được suy ra qua THỂ_BỆNH.
- Tổng 187 relation nếu gộp explicit + derived.

## Nguồn
1. SRC_003_PL01_Danh_muc_the_lam_sang.pdf
2. SRC_004_PL01_Danh_muc_trieu_chung.pdf
3. SRC_004_PL06_Bai_thuoc_thanh_phan_duoc_lieu_the_benh.pdf

## Quy tắc dữ liệu
- `explicit`: quan hệ được thể hiện trực tiếp trong bảng nguồn.
- `derived`: quan hệ suy ra qua đường BỆNH_CHỨNG -> THỂ_BỆNH -> TRIỆU_CHỨNG; không được coi là câu khẳng định trực tiếp của nguồn.
- `source_pages` dùng dấu `;` để phân tách nhiều trang, ví dụ `4;5`.
- DƯỢC_LIỆU hiện mới chuẩn hóa theo tên chính xác xuất hiện trong Phụ lục VI; chưa gán mã Phụ lục V và chưa gộp alias.
- Đây là gold kỹ thuật/source-verified, chưa phải gold được bác sĩ/chuyên gia YHCT thẩm định.

## Các file chính
- `pilot_entities.csv`
- `pilot_relations_explicit.csv`
- `pilot_relations_derived.csv`
- `pilot_gold_triples.csv`
- `pilot_summary.json`
- `gold_corrections_history.csv`

## Lịch sử sửa lỗi
- v0.1 -> v0.2: bỏ quan hệ sai `BT_6586402 --GỒM--> DL_THUONG_TRUAT`.
- v0.2 -> v0.3: sửa metadata bệnh/thể bệnh, chuẩn hóa trang nguồn và sửa số explicit relation trong README. Không thay đổi nội dung 151 explicit relation hay 36 derived relation.
