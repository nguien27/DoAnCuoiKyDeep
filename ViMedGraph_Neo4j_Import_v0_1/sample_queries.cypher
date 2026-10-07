// ViMedGraph sample queries

// 1. Yêu thống có những thể nào?
MATCH (b:`BỆNH_CHỨNG` {canonical_name:'Yêu thống'})-[r:`CÓ_THỂ_BỆNH`]->(t:`THỂ_BỆNH`)
WHERE r.relation_status='explicit'
RETURN b.canonical_name AS benh, t.canonical_name AS the_benh, t.official_code
ORDER BY t.official_code;

// 2. Thể hàn thấp của Yêu thống có triệu chứng gì?
MATCH (b:`BỆNH_CHỨNG` {canonical_name:'Yêu thống'})-[:`CÓ_THỂ_BỆNH`]->(t:`THỂ_BỆNH`)
MATCH (t)-[r:`CÓ_TRIỆU_CHỨNG`]->(s:`TRIỆU_CHỨNG`)
WHERE t.official_code='U62.392.5.01' AND r.relation_status='explicit'
RETURN s.canonical_name AS trieu_chung, s.official_code, r.source_id, r.pdf_page_start, r.pdf_page_end
ORDER BY s.official_code;

// 3. Thể hàn thấp điều trị bằng bài thuốc nào?
MATCH (t:`THỂ_BỆNH` {official_code:'U62.392.5.01'})-[r:`ĐIỀU_TRỊ_BẰNG`]->(f:`BÀI_THUỐC`)
RETURN f.canonical_name AS bai_thuoc, f.official_code, r.evidence_text
ORDER BY f.official_code;

// 4. Can khương thương truật thang gồm những dược liệu nào?
MATCH (f:`BÀI_THUỐC` {canonical_name:'Can khương thương truật thang'})-[r:`GỒM`]->(d:`DƯỢC_LIỆU`)
RETURN d.canonical_name AS duoc_lieu, r.source_id, r.pdf_page_start
ORDER BY duoc_lieu;

// 5. Truy nguồn một relation
MATCH (h:KG_NODE)-[r]->(t:KG_NODE)
WHERE r.relation_id='R000001'
RETURN h.canonical_name, type(r), t.canonical_name,
       r.source_id, r.pdf_page_start, r.pdf_page_end, r.evidence_text;
