# ViMedGraph Text Extraction Pilot v0.3

## Mục tiêu
Chuyển văn xuôi của 4 bệnh pilot trong SRC_001 thành entity/relation CSV theo ontology v0.1.

## Phạm vi
- Đau cột sống thắt lưng / Yêu thống
- Thoái hóa khớp gối / Hạc tất phong
- Gout / Thống phong
- Viêm khớp dạng thấp / Chứng tý
- Chỉ dùng phần `III. Các thể lâm sàng và điều trị`.

Cả 4 pilot hiện đều thuộc SRC_001. SRC_002 đã được section/chunk ở giai đoạn trước nhưng chưa có bệnh nào của SRC_002 trong gold pilot hiện tại.

## Phương pháp
Baseline rule-based + dictionary-constrained:
1. Regex tìm THỂ_BỆNH.
2. Lấy đoạn Triệu chứng.
3. Chuẩn hóa triệu chứng bằng danh mục chính thức.
4. Tìm BÀI_THUỐC bằng tên/mã/alias.
5. Chỉ tạo `BÀI_THUỐC --GỒM--> DƯỢC_LIỆU` khi dược liệu xuất hiện trong span cục bộ của đúng bài thuốc.
6. Giữ provenance trang nguồn.

Không dùng LLM ở baseline này.

## Kết quả chính
- Entity: 323
- Explicit relation: 543
- Derived disease-symptom relation: 140
- Semantic/source support failures: 0
- Raw-PDF support failures: 0

## File
`text_entities.csv`, `text_relations.csv`, `text_relations_derived.csv`, `normalization_map.csv`,
`extraction_gold_entities.csv`, `extraction_gold_relations.csv`, `evaluation_metrics.csv`,
`error_analysis.csv`, `unmapped_mentions.csv`, `audit_summary.json`, `verify_outputs.py`.

## Cảnh báo
Precision/Recall/F1 = 1.000 là kết quả closed-set pilot có dictionary chuẩn hỗ trợ normalization.
Không được hiểu là open extraction trên toàn corpus đã đạt 100%.

## v0.3 QA fix
Đã sửa lỗi serialization `entity_id` của v0.2; v0.3 là bản nên dùng.
