# Offline QA Report - ViMedGraph Neo4j Import v0.1

PASS.

- Node total: 1117
- Explicit relation total: 1890
- Derived relation total: 572
- Duplicate entity IDs: 0
- Duplicate explicit relations: 0
- Duplicate derived relations: 0
- Dangling endpoints: 0
- Relation schema violations: 0
- Explicit relations missing source/page/evidence: 0

Relationship schema verified:
- BỆNH_CHỨNG -> CÓ_THỂ_BỆNH -> THỂ_BỆNH
- THỂ_BỆNH -> CÓ_TRIỆU_CHỨNG -> TRIỆU_CHỨNG
- THỂ_BỆNH -> ĐIỀU_TRỊ_BẰNG -> BÀI_THUỐC
- BÀI_THUỐC -> GỒM -> DƯỢC_LIỆU
- Derived only: BỆNH_CHỨNG -> CÓ_TRIỆU_CHỨNG -> TRIỆU_CHỨNG

Neo4j itself was not run in this environment because the Neo4j executable is not installed.
Use `neo4j_qa.cypher` after local import to confirm runtime counts.
