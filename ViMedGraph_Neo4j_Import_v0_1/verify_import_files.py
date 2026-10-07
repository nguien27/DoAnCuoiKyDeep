from pathlib import Path
import csv, collections, sys

BASE=Path(__file__).resolve().parent

def rows(name):
    with open(BASE/name,encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

E=rows("kg_core_entities.csv")
R=rows("kg_core_relations_explicit.csv")
D=rows("kg_core_relations_derived.csv")
emap={x["entity_id"]:x for x in E}

errors=[]
if len(emap)!=len(E):
    errors.append("duplicate entity_id")

allowed={
    "CÓ_THỂ_BỆNH":("BỆNH_CHỨNG","THỂ_BỆNH"),
    "CÓ_TRIỆU_CHỨNG":("THỂ_BỆNH","TRIỆU_CHỨNG"),
    "ĐIỀU_TRỊ_BẰNG":("THỂ_BỆNH","BÀI_THUỐC"),
    "GỒM":("BÀI_THUỐC","DƯỢC_LIỆU")
}

for r in R:
    if r["head_id"] not in emap or r["tail_id"] not in emap:
        errors.append("dangling explicit "+r["relation_id"])
        continue
    actual=(emap[r["head_id"]]["entity_type"],emap[r["tail_id"]]["entity_type"])
    if allowed.get(r["relation"])!=actual:
        errors.append("schema explicit "+r["relation_id"])

for r in D:
    if r["head_id"] not in emap or r["tail_id"] not in emap:
        errors.append("dangling derived "+r["relation_id"])
        continue
    actual=(emap[r["head_id"]]["entity_type"],emap[r["tail_id"]]["entity_type"])
    if not (r["relation"]=="CÓ_TRIỆU_CHỨNG" and actual==("BỆNH_CHỨNG","TRIỆU_CHỨNG")):
        errors.append("schema derived "+r["relation_id"])

print("Nodes:",len(E),collections.Counter(x["entity_type"] for x in E))
print("Explicit:",len(R),collections.Counter(x["relation"] for x in R))
print("Derived:",len(D),collections.Counter(x["relation"] for x in D))
print("Errors:",len(errors))
if errors:
    print(errors[:20])
    sys.exit(1)
