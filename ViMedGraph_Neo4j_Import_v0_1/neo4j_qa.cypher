// ViMedGraph Neo4j QA v0.1

// Q1. Tổng số node - expected: 1117
MATCH (n:KG_NODE) RETURN count(n) AS total_nodes;

// Q2. Node theo loại - expected:
// BỆNH_CHỨNG=18, THỂ_BỆNH=67,
// TRIỆU_CHỨNG=572, BÀI_THUỐC=217,
// DƯỢC_LIỆU=243
MATCH (n:KG_NODE)
UNWIND [x IN labels(n) WHERE x <> 'KG_NODE'] AS node_type
RETURN node_type, count(*) AS n
ORDER BY n DESC;

// Q3. Tổng explicit relation - expected: 1890
MATCH ()-[r]->()
WHERE r.relation_status = 'explicit'
RETURN count(r) AS explicit_relations;

// Q4. Explicit relation theo loại - expected:
// CÓ_THỂ_BỆNH=67
// CÓ_TRIỆU_CHỨNG=572
// ĐIỀU_TRỊ_BẰNG=217
// GỒM=1034
MATCH ()-[r]->()
WHERE r.relation_status = 'explicit'
RETURN type(r) AS relation_type, count(*) AS n
ORDER BY n DESC;

// Q5. Derived relation - expected: 572
MATCH ()-[r]->()
WHERE r.relation_status = 'derived'
RETURN type(r) AS relation_type, count(*) AS n;

// Q6. Duplicate entity_id - expected: 0 rows
MATCH (n:KG_NODE)
WITH n.entity_id AS entity_id, count(*) AS c
WHERE c > 1
RETURN entity_id, c;

// Q7. Relationship endpoints missing - structurally impossible after MATCH import;
// expected: 0 invalid schema rows
MATCH (h:KG_NODE)-[r]->(t:KG_NODE)
WHERE
  (type(r)='CÓ_THỂ_BỆNH' AND NOT (h:`BỆNH_CHỨNG` AND t:`THỂ_BỆNH`))
  OR
  (type(r)='ĐIỀU_TRỊ_BẰNG' AND NOT (h:`THỂ_BỆNH` AND t:`BÀI_THUỐC`))
  OR
  (type(r)='GỒM' AND NOT (h:`BÀI_THUỐC` AND t:`DƯỢC_LIỆU`))
  OR
  (type(r)='CÓ_TRIỆU_CHỨNG' AND r.relation_status='explicit'
      AND NOT (h:`THỂ_BỆNH` AND t:`TRIỆU_CHỨNG`))
  OR
  (type(r)='CÓ_TRIỆU_CHỨNG' AND r.relation_status='derived'
      AND NOT (h:`BỆNH_CHỨNG` AND t:`TRIỆU_CHỨNG`))
RETURN h.entity_id, type(r), r.relation_id, t.entity_id;

// Q8. Explicit relations thiếu provenance - expected: 0
MATCH ()-[r]->()
WHERE r.relation_status='explicit'
  AND (r.source_id IS NULL OR r.pdf_page_start IS NULL OR r.pdf_page_end IS NULL OR r.evidence_text IS NULL)
RETURN count(r) AS missing_provenance;
