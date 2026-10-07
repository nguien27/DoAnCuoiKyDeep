# ViMedGraph Neo4j Import v0.1

## Trạng thái
Gói này được tạo từ KG Core v0.2. Dữ liệu đã qua kiểm tra offline trước import.

### Expected graph size
- Nodes: 1117
  - BỆNH_CHỨNG: 18
  - THỂ_BỆNH: 67
  - TRIỆU_CHỨNG: 572
  - BÀI_THUỐC: 217
  - DƯỢC_LIỆU: 243
- Explicit relations: 1890
  - CÓ_THỂ_BỆNH: 67
  - CÓ_TRIỆU_CHỨNG: 572
  - ĐIỀU_TRỊ_BẰNG: 217
  - GỒM: 1034
- Derived relations: 572 CÓ_TRIỆU_CHỨNG (BỆNH_CHỨNG -> TRIỆU_CHỨNG)

## Quan trọng
Hiện KG Core này chỉ chứa SRC_001. SRC_002 vẫn ở backlog/candidate vì chưa có mapping mã chuẩn đủ chắc; không được tự suy đoán để đưa vào graph.

## Cách import bằng Neo4j Desktop
1. Tạo/start một database Neo4j.
2. Mở thư mục `import` của database.
3. Copy toàn bộ CSV trong gói này vào thư mục `import`.
   - Có thể dùng `copy_csv_to_neo4j_import.ps1`.
4. Mở Neo4j Browser.
5. Chạy `neo4j_import.cypher` từng statement.
6. Chạy `neo4j_qa.cypher`.
7. Chỉ chấp nhận graph nếu các kết quả đúng với expected counts và các truy vấn lỗi trả 0 rows/0 count.

## File
- `neo4j_import.cypher`: tạo constraint, node và relationship.
- `neo4j_qa.cypher`: kiểm tra sau import.
- `sample_queries.cypher`: truy vấn thử.
- `verify_import_files.py`: QA offline trước Neo4j.
- `nodes_*.csv`: node chia theo 5 entity type.
- `relations_explicit_*.csv`: 4 loại relation trực tiếp.
- `relations_derived_CO_TRIEU_CHUNG.csv`: relation suy diễn, tách riêng.
- `kg_core_*.csv`: dữ liệu KG Core nguyên bản.

## Technical label
Mỗi node có thêm label `KG_NODE` chỉ để tạo unique constraint và MATCH nhanh khi import.
Đây KHÔNG phải entity thứ 6 của ontology. Entity chuyên môn vẫn chỉ có 5 loại đã chốt.

## Chính sách dữ liệu
- Không import candidate/backlog.
- Không tự gán mã.
- Explicit và derived giữ `relation_status` riêng.
- Mỗi relation giữ `source_id`, page range và `evidence_text`.
