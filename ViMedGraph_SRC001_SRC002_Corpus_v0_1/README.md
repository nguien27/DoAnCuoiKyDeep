# ViMedGraph SRC_001 + SRC_002 Corpus v0.1

Bộ dữ liệu trung gian cho RAG sau khi xử lý 2 tài liệu hướng dẫn chẩn đoán/điều trị chính.

## File chính
- `documents.csv`: metadata hai tài liệu.
- `diseases.csv`: 36 bệnh/chương và khoảng trang.
- `sections.csv`: các section cấp cao của từng bệnh.
- `chunks.csv` / `chunks.jsonl`: chunk dùng cho retrieval, kèm provenance.
- `page_stats.csv`: thống kê text sau làm sạch theo trang.
- `excluded_pages.csv`: trang chủ động không đưa vào corpus bệnh.
- `source_structure_anomalies.csv`: các bất thường đánh số section có sẵn trong nguồn, được giữ nguyên và gắn cờ.
- `qa_summary.json`: kết quả kiểm tra tự động.
- `QA_REPORT.md`: báo cáo kiểm tra ngược.
- `process_src001_src002.py`: script tái lập toàn bộ bước xử lý.

## Chunking
- Giữ ranh giới theo bệnh và section; không trộn hai bệnh hoặc hai section khác nhau.
- Mục tiêu tối đa khoảng 2.800 ký tự/chunk, overlap khoảng 250 ký tự theo line nguồn.
- `source_text`: text nguồn đã làm sạch kỹ thuật.
- `retrieval_text`: thêm tên bệnh + section để tăng ngữ cảnh khi embedding.

## Provenance
Mỗi chunk có: `source_id`, `source_file`, `source_year`, `disease_id`, `section_id`, `pdf_page_start/end`, `document_page_start/end`, `source_ref`, `sha256`.
