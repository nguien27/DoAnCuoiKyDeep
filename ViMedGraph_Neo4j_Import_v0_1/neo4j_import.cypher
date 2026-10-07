// ViMedGraph Neo4j import v0.1
// Run each statement in Neo4j Browser / cypher-shell after copying CSV files into Neo4j import directory.

CREATE CONSTRAINT kg_node_entity_id IF NOT EXISTS FOR (n:KG_NODE) REQUIRE n.entity_id IS UNIQUE;

// BỆNH_CHỨNG
LOAD CSV WITH HEADERS FROM 'file:///nodes_BENH_CHUNG.csv' AS row
MERGE (n:KG_NODE:`BỆNH_CHỨNG` {entity_id: row.entity_id})
SET n.canonical_name = row.canonical_name,
    n.observed_name = row.observed_name,
    n.official_id = CASE WHEN row.official_id = '' THEN null ELSE row.official_id END,
    n.official_code = CASE WHEN row.official_code = '' THEN null ELSE row.official_code END,
    n.source_id = row.source_id,
    n.disease_id = row.disease_id,
    n.section_type = row.section_type,
    n.pdf_page_start = toInteger(row.pdf_page_start),
    n.pdf_page_end = toInteger(row.pdf_page_end),
    n.normalization_status = row.normalization_status,
    n.confidence = toFloat(row.confidence),
    n.notes = row.notes;

// THỂ_BỆNH
LOAD CSV WITH HEADERS FROM 'file:///nodes_THE_BENH.csv' AS row
MERGE (n:KG_NODE:`THỂ_BỆNH` {entity_id: row.entity_id})
SET n.canonical_name = row.canonical_name,
    n.observed_name = row.observed_name,
    n.official_id = CASE WHEN row.official_id = '' THEN null ELSE row.official_id END,
    n.official_code = CASE WHEN row.official_code = '' THEN null ELSE row.official_code END,
    n.source_id = row.source_id,
    n.disease_id = row.disease_id,
    n.section_type = row.section_type,
    n.pdf_page_start = toInteger(row.pdf_page_start),
    n.pdf_page_end = toInteger(row.pdf_page_end),
    n.normalization_status = row.normalization_status,
    n.confidence = toFloat(row.confidence),
    n.notes = row.notes;

// TRIỆU_CHỨNG
LOAD CSV WITH HEADERS FROM 'file:///nodes_TRIEU_CHUNG.csv' AS row
MERGE (n:KG_NODE:`TRIỆU_CHỨNG` {entity_id: row.entity_id})
SET n.canonical_name = row.canonical_name,
    n.observed_name = row.observed_name,
    n.official_id = CASE WHEN row.official_id = '' THEN null ELSE row.official_id END,
    n.official_code = CASE WHEN row.official_code = '' THEN null ELSE row.official_code END,
    n.source_id = row.source_id,
    n.disease_id = row.disease_id,
    n.section_type = row.section_type,
    n.pdf_page_start = toInteger(row.pdf_page_start),
    n.pdf_page_end = toInteger(row.pdf_page_end),
    n.normalization_status = row.normalization_status,
    n.confidence = toFloat(row.confidence),
    n.notes = row.notes;

// BÀI_THUỐC
LOAD CSV WITH HEADERS FROM 'file:///nodes_BAI_THUOC.csv' AS row
MERGE (n:KG_NODE:`BÀI_THUỐC` {entity_id: row.entity_id})
SET n.canonical_name = row.canonical_name,
    n.observed_name = row.observed_name,
    n.official_id = CASE WHEN row.official_id = '' THEN null ELSE row.official_id END,
    n.official_code = CASE WHEN row.official_code = '' THEN null ELSE row.official_code END,
    n.source_id = row.source_id,
    n.disease_id = row.disease_id,
    n.section_type = row.section_type,
    n.pdf_page_start = toInteger(row.pdf_page_start),
    n.pdf_page_end = toInteger(row.pdf_page_end),
    n.normalization_status = row.normalization_status,
    n.confidence = toFloat(row.confidence),
    n.notes = row.notes;

// DƯỢC_LIỆU
LOAD CSV WITH HEADERS FROM 'file:///nodes_DUOC_LIEU.csv' AS row
MERGE (n:KG_NODE:`DƯỢC_LIỆU` {entity_id: row.entity_id})
SET n.canonical_name = row.canonical_name,
    n.observed_name = row.observed_name,
    n.official_id = CASE WHEN row.official_id = '' THEN null ELSE row.official_id END,
    n.official_code = CASE WHEN row.official_code = '' THEN null ELSE row.official_code END,
    n.source_id = row.source_id,
    n.disease_id = row.disease_id,
    n.section_type = row.section_type,
    n.pdf_page_start = toInteger(row.pdf_page_start),
    n.pdf_page_end = toInteger(row.pdf_page_end),
    n.normalization_status = row.normalization_status,
    n.confidence = toFloat(row.confidence),
    n.notes = row.notes;

// Explicit relations
LOAD CSV WITH HEADERS FROM 'file:///relations_explicit_CO_THE_BENH.csv' AS row
MATCH (h:KG_NODE {entity_id: row.head_id})
MATCH (t:KG_NODE {entity_id: row.tail_id})
MERGE (h)-[r:`CÓ_THỂ_BỆNH` {relation_id: row.relation_id}]->(t)
SET r.source_id = row.source_id,
    r.disease_id = row.disease_id,
    r.section_type = row.section_type,
    r.pdf_page_start = toInteger(row.pdf_page_start),
    r.pdf_page_end = toInteger(row.pdf_page_end),
    r.evidence_text = row.evidence_text,
    r.confidence = toFloat(row.confidence),
    r.relation_status = row.relation_status;

LOAD CSV WITH HEADERS FROM 'file:///relations_explicit_CO_TRIEU_CHUNG.csv' AS row
MATCH (h:KG_NODE {entity_id: row.head_id})
MATCH (t:KG_NODE {entity_id: row.tail_id})
MERGE (h)-[r:`CÓ_TRIỆU_CHỨNG` {relation_id: row.relation_id}]->(t)
SET r.source_id = row.source_id,
    r.disease_id = row.disease_id,
    r.section_type = row.section_type,
    r.pdf_page_start = toInteger(row.pdf_page_start),
    r.pdf_page_end = toInteger(row.pdf_page_end),
    r.evidence_text = row.evidence_text,
    r.confidence = toFloat(row.confidence),
    r.relation_status = row.relation_status;

LOAD CSV WITH HEADERS FROM 'file:///relations_explicit_DIEU_TRI_BANG.csv' AS row
MATCH (h:KG_NODE {entity_id: row.head_id})
MATCH (t:KG_NODE {entity_id: row.tail_id})
MERGE (h)-[r:`ĐIỀU_TRỊ_BẰNG` {relation_id: row.relation_id}]->(t)
SET r.source_id = row.source_id,
    r.disease_id = row.disease_id,
    r.section_type = row.section_type,
    r.pdf_page_start = toInteger(row.pdf_page_start),
    r.pdf_page_end = toInteger(row.pdf_page_end),
    r.evidence_text = row.evidence_text,
    r.confidence = toFloat(row.confidence),
    r.relation_status = row.relation_status;

LOAD CSV WITH HEADERS FROM 'file:///relations_explicit_GOM.csv' AS row
MATCH (h:KG_NODE {entity_id: row.head_id})
MATCH (t:KG_NODE {entity_id: row.tail_id})
MERGE (h)-[r:`GỒM` {relation_id: row.relation_id}]->(t)
SET r.source_id = row.source_id,
    r.disease_id = row.disease_id,
    r.section_type = row.section_type,
    r.pdf_page_start = toInteger(row.pdf_page_start),
    r.pdf_page_end = toInteger(row.pdf_page_end),
    r.evidence_text = row.evidence_text,
    r.confidence = toFloat(row.confidence),
    r.relation_status = row.relation_status;

// Derived relations - import separately so provenance status stays explicit
LOAD CSV WITH HEADERS FROM 'file:///relations_derived_CO_TRIEU_CHUNG.csv' AS row
MATCH (h:KG_NODE {entity_id: row.head_id})
MATCH (t:KG_NODE {entity_id: row.tail_id})
MERGE (h)-[r:`CÓ_TRIỆU_CHỨNG` {relation_id: row.relation_id}]->(t)
SET r.source_id = row.source_id,
    r.disease_id = row.disease_id,
    r.section_type = row.section_type,
    r.pdf_page_start = toInteger(row.pdf_page_start),
    r.pdf_page_end = toInteger(row.pdf_page_end),
    r.evidence_text = row.evidence_text,
    r.confidence = toFloat(row.confidence),
    r.relation_status = row.relation_status;
