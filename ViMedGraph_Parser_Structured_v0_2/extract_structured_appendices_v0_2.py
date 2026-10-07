from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import fitz  # PyMuPDF
import pandas as pd

DISEASE_ID_RE = re.compile(r"\b650\d{4}\b")
SYMPTOM_ID_RE = re.compile(r"\b654\d{4}\b")
FORMULA_ID_RE = re.compile(r"\b658\d{4}\b")
U_CODE_RE = re.compile(r"\bU\d{2}\.\d+(?:\.\d+)*\b")
SYMPTOM_CODE_RE = re.compile(r"\bU\d{2}\.\d+(?:\.\d+)*\.[ĐK]\d{2}\b")
FORMULA_CODE_RE = re.compile(r"\bU\d{2}\.\d+(?:\.\d+)*\.(?:CP|NP|ĐP|DN|BT|TN)\d{3}\b")
ICD_RE = re.compile(r"\b[A-Z]\d{2}(?:\.\d+)?\b")

PILOT_DISEASE_CODES = {"U62.392.5", "U62.261", "U62.371", "U62.021"}
PILOT_PATTERN_CODES = {"U62.392.5.01", "U62.261.01", "U62.371.01", "U62.021.01"}

HEADER_HINTS = (
    "Mã dùng chung", "Tên bệnh theo", "Tên bệnh theo YHHĐ", "Mã ICD", "Bệnh danh YHCT",
    "Các thể lâm sàng", "Mã hóa", "Thành phần (nếu có)", "Bài thuốc theo thể lâm sàng",
)


def squish(s: object) -> str:
    if s is None:
        return ""
    return re.sub(r"\s+", " ", str(s)).strip()


def slug(text: str) -> str:
    s = unicodedata.normalize("NFD", text)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D")
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").upper()
    return s


def first_regex(pattern: re.Pattern, text: object) -> str:
    m = pattern.search(str(text or ""))
    return m.group(0) if m else ""


def _is_noise_token(tok: str) -> bool:
    t = tok.strip()
    if not t:
        return True
    if re.fullmatch(r"[\d_./:-]+", t):
        return True
    if re.fullmatch(r"[A-Za-z]", t):
        return True
    if t in {"t_", ".y", "m.", "_"}:
        return True
    return False


def clean_watermark_text(cell: object) -> str:
    """Remove known diagonal watermark fragments injected into table extraction.
    Applied only to disease/pattern/formula names, not ingredient names/codes.
    """
    if cell is None:
        return ""
    kept: List[str] = []
    for raw in str(cell).splitlines():
        line = raw.strip()
        line = re.sub(r"\bh\s+p\b", "hợp", line)
        if not line:
            continue
        toks = line.split()
        while toks and _is_noise_token(toks[0]):
            toks.pop(0)
        while toks and _is_noise_token(toks[-1]):
            toks.pop()
        if not toks:
            continue
        line = " ".join(toks).strip()
        if line:
            kept.append(line)
    text = squish(" ".join(kept))
    text = text.replace("thư ng", "thượng").replace("h p", "hợp")
    return text


def balance_single_parenthesis(text: str) -> str:
    if text.count("(") == text.count(")") + 1:
        return text + ")"
    return text


def name_in_parentheses(text: str) -> str:
    parts = re.findall(r"\(([^()]+)\)", text or "")
    return squish(parts[-1]) if parts else ""


def clean_formula_name(cell: object) -> str:
    return clean_watermark_text(cell)


def clean_ingredient(cell: object) -> str:
    x = squish(cell)
    if not x or x in {"(4)", "Thành phần (nếu có)"}:
        return ""
    if any(tok in x.lower() for tok in ["tuannm", "ydct_", "nguyen manh"]):
        return ""
    return x


def is_header_row(cells: List[object]) -> bool:
    cleaned = [clean_watermark_text(c) for c in cells]
    text = " | ".join(cleaned)
    hits = sum(h.lower() in text.lower() for h in HEADER_HINTS)
    header_tokens = {"YHCT", "YHHĐ", "YHHD", "Mã U", "Mã hóa", "Mã dùng", "chung", "Mã ICD-", "10", "với YHHD"}
    return hits >= 1 or any(c in header_tokens for c in cleaned if c)


def extract_pattern_catalog(pdf_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    diseases, patterns = [], []
    doc = fitz.open(pdf_path)
    pending = None

    def finalize_pending():
        nonlocal pending
        if not pending:
            return
        rows = pending["rows"]
        flat = [clean_watermark_text(c) for row in rows for c in row]
        row_text = " | ".join(flat)
        codes = U_CODE_RE.findall(row_text)
        if codes:
            disease_code = codes[-1]
            icd = ""
            for c in flat:
                m = ICD_RE.search(c)
                if m and not str(c).strip().startswith("U"):
                    icd = m.group(0)
                    break
            modern_parts = []
            yhct_parts = []
            title_parts = []
            for row in rows:
                if len(row) > 3 and clean_watermark_text(row[3]):
                    title_parts.append(clean_watermark_text(row[3]))
                if len(row) > 7 and clean_watermark_text(row[7]):
                    modern_parts.append(clean_watermark_text(row[7]))
                if len(row) > 13 and clean_watermark_text(row[13]):
                    yhct_parts.append(clean_watermark_text(row[13]))
            modern = balance_single_parenthesis(squish(" ".join(modern_parts)))
            yhct = balance_single_parenthesis(squish(" ".join(yhct_parts)))
            title = balance_single_parenthesis(squish(" ".join(title_parts))) or pending.get("title", "")
            if not yhct or len(yhct.split()) > 8:
                yhct = name_in_parentheses(title) or yhct
            diseases.append({
                "official_id": pending["official_id"],
                "official_code": disease_code,
                "canonical_name": yhct,
                "modern_name": modern,
                "icd10": icd,
                "source_pages": pending["page"],
                "quality_flag": "",
                "notes": "",
            })
        pending = None

    for pno, page in enumerate(doc):
        tables = page.find_tables().tables
        for table in tables:
            for row in table.extract():
                cells = [c or "" for c in row]
                if not cells or is_header_row(cells):
                    continue
                oid = first_regex(DISEASE_ID_RE, cells[0])
                cleaned = [clean_watermark_text(c) for c in cells]
                row_text = " | ".join(cleaned)
                codes = U_CODE_RE.findall(row_text)
                has_pattern_name = any("Thể " in squish(c) for c in cleaned)

                if oid:
                    finalize_pending()
                    if has_pattern_name and codes:
                        pattern_code = codes[-1]
                        name = next((squish(c) for c in cleaned if "Thể " in squish(c)), "")
                        name = balance_single_parenthesis(name.replace("thư ng", "thượng").replace("h p", "hợp"))
                        patterns.append({
                            "official_id": oid,
                            "official_code": pattern_code,
                            "canonical_name": name,
                            "parent_code": pattern_code.rsplit(".", 1)[0],
                            "source_pages": str(pno + 1),
                            "quality_flag": "",
                            "notes": "",
                        })
                    else:
                        title = cleaned[3] if len(cleaned) > 3 else ""
                        pending = {
                            "official_id": oid,
                            "title": title,
                            "page": str(pno + 1),
                            "rows": [cells],
                        }
                    continue

                if pending is not None:
                    pending["rows"].append(cells)

    finalize_pending()
    ddf = pd.DataFrame(diseases)
    pdf = pd.DataFrame(patterns)
    if not ddf.empty:
        ddf = ddf.drop_duplicates("official_code")
    if not pdf.empty:
        pdf = pdf.drop_duplicates("official_code")
    return ddf, pdf


def extract_symptom_source_parent_map(pdf_path: Path) -> Dict[str, str]:
    parent_map: Dict[str, str] = {}
    doc = fitz.open(pdf_path)
    for page in doc:
        for table in page.find_tables().tables:
            for row in table.extract():
                cells = [c or "" for c in row]
                row_text = " | ".join(str(c) for c in cells)
                sid = first_regex(SYMPTOM_ID_RE, row_text)
                if not sid:
                    continue
                for c in cells:
                    txt = squish(c)
                    if "Thể " in txt:
                        pc = first_regex(U_CODE_RE, txt)
                        if pc:
                            parent_map[sid] = pc
                            break
    return parent_map


def extract_symptoms(pdf_path: Path) -> pd.DataFrame:
    records = []
    source_parent_map = extract_symptom_source_parent_map(pdf_path)
    doc = fitz.open(pdf_path)
    for pno, page in enumerate(doc):
        text = page.get_text("text")
        matches = list(re.finditer(r"(?m)^\s*(654\d{4})\s*$", text))
        for i, m in enumerate(matches):
            sid = m.group(1)
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block = text[m.end():end]
            cm = SYMPTOM_CODE_RE.search(block)
            if not cm:
                continue
            code = cm.group(0)
            name = squish(block[:cm.start()])
            name = re.sub(r"tuannm\..*$", "", name, flags=re.I).strip()
            code_parent = code.rsplit(".", 1)[0]
            source_parent = source_parent_map.get(sid, "")
            parent_code = source_parent or code_parent
            mismatch = bool(source_parent and source_parent != code_parent)
            records.append({
                "official_id": sid,
                "official_code": code,
                "canonical_name": name,
                "parent_code": parent_code,
                "code_parent": code_parent,
                "source_pages": str(pno + 1),
                "quality_flag": "source_code_parent_mismatch" if mismatch else "",
                "notes": (f"Mã triệu chứng suy ra parent={code_parent}, nhưng cột Thể lâm sàng ghi {source_parent}. "
                          "Giữ nguyên official_code theo nguồn và dùng cột Thể lâm sàng làm parent_code.") if mismatch else "",
            })
    return pd.DataFrame(records).drop_duplicates("official_id")


def _row_formula_id(row: List[object]) -> str:
    return first_regex(FORMULA_ID_RE, row[0] if row else "")


def _row_ingredient(row: List[object]) -> str:
    return clean_ingredient(row[3] if len(row) > 3 else "")


def _is_full_width_orphan(table, row_idx: int, row_data: List[object]) -> bool:
    if _row_formula_id(row_data) or not _row_ingredient(row_data):
        return False
    cells = table.rows[row_idx].cells
    if not cells or len(cells) < 6:
        return False
    non_ing_rects = [cells[j] for j in [0, 1, 2, 4, 5]]
    return all(r is not None for r in non_ing_rects)


def _clean_orphan_ingredient(raw_cell: object, previous_ingredients: List[str]) -> str:
    raw_lines = [squish(x) for x in str(raw_cell or "").splitlines() if squish(x)]
    prev = set(previous_ingredients)
    while len(raw_lines) > 1 and raw_lines and raw_lines[0] in prev:
        raw_lines.pop(0)
    return clean_ingredient(" ".join(raw_lines))


def extract_formulas(pdf_path: Path) -> pd.DataFrame:
    records: List[Dict] = []
    doc = fitz.open(pdf_path)
    pending_for_next: List[Tuple[str, str]] = []
    current: Optional[Dict] = None
    last_flushed_ingredients: List[str] = []

    def flush_current():
        nonlocal current, last_flushed_ingredients
        if current is not None:
            current["ingredients"] = list(dict.fromkeys([x for x in current["ingredients"] if x]))
            last_flushed_ingredients = list(current["ingredients"])
            if not current["official_code"] and not current["canonical_name"] and not current["parent_code"] and not current["disease_code"]:
                current["quality_flag"] = "source_incomplete_record"
                current["notes"] = "Nguồn chỉ hiển thị official_id; các cột tên/mã/thể/bệnh để trống. Không gán thành phần của bản ghi kế tiếp vào bản ghi này."
            records.append(current)
            current = None

    for pno, page in enumerate(doc):
        tables = page.find_tables().tables
        if not tables:
            continue
        table = tables[0]
        rows = table.extract()
        seen_formula_this_page = False
        for i, row in enumerate(rows):
            fid = _row_formula_id(row)
            ing = _row_ingredient(row)

            if fid:
                seen_formula_this_page = True
                flush_current()
                row_text = " | ".join(str(c or "") for c in row)
                code = first_regex(FORMULA_CODE_RE, row_text)
                pattern_code = first_regex(U_CODE_RE, row[4] if len(row) > 4 else "")
                disease_code = first_regex(U_CODE_RE, row[5] if len(row) > 5 else "")
                current = {
                    "official_id": fid,
                    "official_code": code,
                    "canonical_name": clean_formula_name(row[1] if len(row) > 1 else ""),
                    "parent_code": pattern_code,
                    "disease_code": disease_code,
                    "source_pages": [str(pno + 1)],
                    "ingredients": [],
                    "quality_flag": "",
                    "notes": "",
                }
                if pending_for_next:
                    current["ingredients"].extend([x for x, _pg in pending_for_next])
                    for _x, pg in pending_for_next:
                        if pg not in current["source_pages"]:
                            current["source_pages"].append(pg)
                    pending_for_next = []
                if ing:
                    current["ingredients"].append(ing)
                continue

            if not ing:
                continue

            # If the source contains an ID-only/incomplete row (e.g. 6586594),
            # ingredient rows after it belong to the next visually merged record.
            if current is not None and not any([current["official_code"], current["canonical_name"], current["parent_code"], current["disease_code"]]):
                pending_for_next.append((ing, str(pno + 1)))
                continue

            if seen_formula_this_page and _is_full_width_orphan(table, i, row):
                raw_cell = row[3] if len(row) > 3 else ""
                orphan_ing = _clean_orphan_ingredient(raw_cell, last_flushed_ingredients)
                pending_for_next = [(orphan_ing, str(pno + 1))] if orphan_ing else []
                continue

            if pending_for_next:
                pending_for_next.append((ing, str(pno + 1)))
            elif current is not None:
                current["ingredients"].append(ing)
                if str(pno + 1) not in current["source_pages"]:
                    current["source_pages"].append(str(pno + 1))

    flush_current()
    for r in records:
        pages = sorted(set(r["source_pages"]), key=lambda x: int(x))
        r["source_pages"] = ";".join(pages)
        if r["official_code"] and r["parent_code"]:
            code_parent = r["official_code"].rsplit(".", 1)[0]
            if code_parent != r["parent_code"]:
                r["quality_flag"] = "source_code_parent_mismatch"
                r["notes"] = f"Mã bài thuốc suy ra parent={code_parent}, cột Thể lâm sàng ghi {r['parent_code']}."
    return pd.DataFrame(records).drop_duplicates("official_id")


def find_disease_ancestor(code: str, disease_codes: set[str]) -> str:
    matches = [d for d in disease_codes if code == d or code.startswith(d + ".")]
    return max(matches, key=len) if matches else ""


def build_pilot_graph(diseases: pd.DataFrame, patterns: pd.DataFrame, symptoms: pd.DataFrame, formulas: pd.DataFrame):
    disease_codes_all = set(diseases.official_code)
    diseases = diseases[diseases.official_code.isin(PILOT_DISEASE_CODES)].copy()
    patterns = patterns[patterns.official_code.isin(PILOT_PATTERN_CODES)].copy()
    symptoms = symptoms[symptoms.parent_code.isin(PILOT_PATTERN_CODES)].copy()
    formulas = formulas[formulas.parent_code.isin(PILOT_PATTERN_CODES)].copy()

    entities, relations, derived = [], [], []

    for _, d in diseases.iterrows():
        eid = f"BENH_{slug(d.official_code)}"
        entities.append({
            "entity_id": eid, "entity_type": "BỆNH_CHỨNG", "canonical_name": d.canonical_name,
            "official_id": d.official_id, "official_code": d.official_code, "parent_code": "",
            "modern_name": d.modern_name, "icd10": d.icd10,
            "source_file": "SRC_003_PL01_Danh_muc_the_lam_sang.pdf", "source_pages": d.source_pages,
            "normalization_status": "official_code", "annotation_status": "auto_extracted", "notes": ""
        })

    for _, p in patterns.iterrows():
        eid = f"THE_{slug(p.official_code)}"
        disease_code = find_disease_ancestor(p.official_code, disease_codes_all)
        entities.append({
            "entity_id": eid, "entity_type": "THỂ_BỆNH", "canonical_name": p.canonical_name,
            "official_id": p.official_id, "official_code": p.official_code, "parent_code": disease_code,
            "modern_name": "", "icd10": "",
            "source_file": "SRC_003_PL01_Danh_muc_the_lam_sang.pdf", "source_pages": p.source_pages,
            "normalization_status": "official_code", "annotation_status": "auto_extracted", "notes": ""
        })
        relations.append({
            "head_id": f"BENH_{slug(disease_code)}", "head_type": "BỆNH_CHỨNG", "relation": "CÓ_THỂ_BỆNH",
            "tail_id": eid, "tail_type": "THỂ_BỆNH", "source_file": "SRC_003_PL01_Danh_muc_the_lam_sang.pdf",
            "source_pages": p.source_pages, "relation_status": "explicit"
        })

    for _, s in symptoms.iterrows():
        eid = f"TC_{s.official_id}"
        entities.append({
            "entity_id": eid, "entity_type": "TRIỆU_CHỨNG", "canonical_name": s.canonical_name,
            "official_id": s.official_id, "official_code": s.official_code, "parent_code": s.parent_code,
            "modern_name": "", "icd10": "",
            "source_file": "SRC_004_PL01_Danh_muc_trieu_chung.pdf", "source_pages": s.source_pages,
            "normalization_status": "official_code", "annotation_status": "auto_extracted", "notes": s.get("notes", "")
        })
        relations.append({
            "head_id": f"THE_{slug(s.parent_code)}", "head_type": "THỂ_BỆNH", "relation": "CÓ_TRIỆU_CHỨNG",
            "tail_id": eid, "tail_type": "TRIỆU_CHỨNG", "source_file": "SRC_004_PL01_Danh_muc_trieu_chung.pdf",
            "source_pages": s.source_pages, "relation_status": "explicit"
        })
        disease_code = find_disease_ancestor(s.parent_code, disease_codes_all)
        derived.append({
            "head_id": f"BENH_{slug(disease_code)}", "head_type": "BỆNH_CHỨNG", "relation": "CÓ_TRIỆU_CHỨNG",
            "tail_id": eid, "tail_type": "TRIỆU_CHỨNG", "source_file": "DERIVED_FROM_EXPLICIT_RELATIONS",
            "source_pages": s.source_pages, "relation_status": "derived"
        })

    herb_sources: Dict[str, set] = {}
    for _, f in formulas.iterrows():
        feid = f"BT_{f.official_id}"
        entities.append({
            "entity_id": feid, "entity_type": "BÀI_THUỐC", "canonical_name": f.canonical_name,
            "official_id": f.official_id, "official_code": f.official_code, "parent_code": f.parent_code,
            "modern_name": "", "icd10": "",
            "source_file": "SRC_004_PL06_Bai_thuoc_thanh_phan_duoc_lieu_the_benh.pdf", "source_pages": f.source_pages,
            "normalization_status": "official_code", "annotation_status": "auto_extracted", "notes": f.get("notes", "")
        })
        relations.append({
            "head_id": f"THE_{slug(f.parent_code)}", "head_type": "THỂ_BỆNH", "relation": "ĐIỀU_TRỊ_BẰNG",
            "tail_id": feid, "tail_type": "BÀI_THUỐC", "source_file": "SRC_004_PL06_Bai_thuoc_thanh_phan_duoc_lieu_the_benh.pdf",
            "source_pages": f.source_pages, "relation_status": "explicit"
        })
        for herb in f.ingredients:
            heid = f"DL_{slug(herb)}"
            herb_sources.setdefault(herb, set()).update(str(f.source_pages).split(";"))
            relations.append({
                "head_id": feid, "head_type": "BÀI_THUỐC", "relation": "GỒM",
                "tail_id": heid, "tail_type": "DƯỢC_LIỆU", "source_file": "SRC_004_PL06_Bai_thuoc_thanh_phan_duoc_lieu_the_benh.pdf",
                "source_pages": f.source_pages, "relation_status": "explicit"
            })

    for herb, pages in herb_sources.items():
        entities.append({
            "entity_id": f"DL_{slug(herb)}", "entity_type": "DƯỢC_LIỆU", "canonical_name": herb,
            "official_id": "", "official_code": "", "parent_code": "", "modern_name": "", "icd10": "",
            "source_file": "SRC_004_PL06_Bai_thuoc_thanh_phan_duoc_lieu_the_benh.pdf",
            "source_pages": ";".join(sorted(pages, key=lambda x: int(x))),
            "normalization_status": "exact_name_only", "annotation_status": "auto_extracted",
            "notes": "Chưa đối chiếu mã dược liệu Phụ lục V."
        })

    edf = pd.DataFrame(entities).drop_duplicates("entity_id")
    rdf = pd.DataFrame(relations).drop_duplicates(["head_id", "relation", "tail_id"])
    ddf = pd.DataFrame(derived).drop_duplicates(["head_id", "relation", "tail_id"])
    return edf, rdf, ddf


def prf(pred: set, gold: set) -> Dict[str, float]:
    tp = len(pred & gold); fp = len(pred - gold); fn = len(gold - pred)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def _norm_pages(s: str) -> str:
    vals = []
    for x in str(s or "").split(";"):
        if x.strip().isdigit(): vals.append(int(x.strip()))
    return ";".join(str(x) for x in sorted(set(vals)))


def evaluate(pred_entities, pred_rel, pred_derived, gold_dir: Path):
    ge = pd.read_csv(gold_dir / "pilot_entities.csv", dtype=str).fillna("")
    gr = pd.read_csv(gold_dir / "pilot_relations_explicit.csv", dtype=str).fillna("")
    gd = pd.read_csv(gold_dir / "pilot_relations_derived.csv", dtype=str).fillna("")

    entity_metrics = prf(set(pred_entities.entity_id), set(ge.entity_id))
    rel_key = lambda df: set(zip(df.head_id, df.relation, df.tail_id))
    explicit_metrics = prf(rel_key(pred_rel), rel_key(gr))
    derived_metrics = prf(rel_key(pred_derived), rel_key(gd))

    per_type = {}
    for t in sorted(set(ge.entity_type) | set(pred_entities.entity_type)):
        per_type[t] = prf(
            set(pred_entities.loc[pred_entities.entity_type == t, "entity_id"]),
            set(ge.loc[ge.entity_type == t, "entity_id"]),
        )

    # Attribute accuracy on identity-matched entities; excludes annotation_status/notes by design.
    critical_fields = ["entity_type", "canonical_name", "official_id", "official_code", "parent_code", "modern_name", "icd10", "source_file", "source_pages", "normalization_status"]
    pmap = pred_entities.set_index("entity_id").fillna("")
    gmap = ge.set_index("entity_id").fillna("")
    attr_total = attr_ok = 0
    attr_diffs = []
    for eid in sorted(set(pmap.index) & set(gmap.index)):
        for field in critical_fields:
            pv = str(pmap.at[eid, field]) if field in pmap.columns else ""
            gv = str(gmap.at[eid, field]) if field in gmap.columns else ""
            if field == "source_pages":
                pv, gv = _norm_pages(pv), _norm_pages(gv)
            attr_total += 1
            if pv == gv:
                attr_ok += 1
            else:
                attr_diffs.append({"entity_id": eid, "field": field, "gold": gv, "pred": pv})

    return {
        "entities": entity_metrics,
        "relations_explicit": explicit_metrics,
        "relations_derived": derived_metrics,
        "entities_by_type": per_type,
        "entity_attribute_accuracy": attr_ok / attr_total if attr_total else 0.0,
        "entity_attribute_differences": attr_diffs,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=Path("/mnt/data"))
    ap.add_argument("--gold-dir", type=Path, default=Path("/mnt/data/ViMedGraph_Pilot_Gold_v0_3"))
    ap.add_argument("--out-dir", type=Path, default=Path("/mnt/data/ViMedGraph_Extraction_v0_2"))
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    diseases, patterns = extract_pattern_catalog(args.data_dir / "SRC_003_PL01_Danh_muc_the_lam_sang.pdf")
    symptoms = extract_symptoms(args.data_dir / "SRC_004_PL01_Danh_muc_trieu_chung.pdf")
    formulas = extract_formulas(args.data_dir / "SRC_004_PL06_Bai_thuoc_thanh_phan_duoc_lieu_the_benh.pdf")

    diseases.to_csv(args.out_dir / "parsed_diseases.csv", index=False, encoding="utf-8-sig")
    patterns.to_csv(args.out_dir / "parsed_patterns.csv", index=False, encoding="utf-8-sig")
    symptoms.to_csv(args.out_dir / "parsed_symptoms.csv", index=False, encoding="utf-8-sig")
    fsave = formulas.copy(); fsave["ingredients"] = fsave["ingredients"].apply(lambda xs: " | ".join(xs))
    fsave.to_csv(args.out_dir / "parsed_formulas.csv", index=False, encoding="utf-8-sig")

    entities, relations, derived = build_pilot_graph(diseases, patterns, symptoms, formulas)
    entities.to_csv(args.out_dir / "pilot_pred_entities.csv", index=False, encoding="utf-8-sig")
    relations.to_csv(args.out_dir / "pilot_pred_relations_explicit.csv", index=False, encoding="utf-8-sig")
    derived.to_csv(args.out_dir / "pilot_pred_relations_derived.csv", index=False, encoding="utf-8-sig")

    metrics = evaluate(entities, relations, derived, args.gold_dir)
    with open(args.out_dir / "evaluation_vs_gold_v0_3.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    quality = {
        "source_code_parent_conflicts_symptoms": symptoms.loc[symptoms.quality_flag == "source_code_parent_mismatch", ["official_id", "official_code", "parent_code", "code_parent", "source_pages", "notes"]].to_dict("records"),
        "source_incomplete_formula_records": formulas.loc[formulas.quality_flag == "source_incomplete_record", ["official_id", "source_pages", "notes"]].to_dict("records"),
        "formula_code_parent_conflicts": formulas.loc[formulas.quality_flag == "source_code_parent_mismatch", ["official_id", "official_code", "parent_code", "source_pages", "notes"]].to_dict("records"),
    }
    with open(args.out_dir / "data_quality_report.json", "w", encoding="utf-8") as f:
        json.dump(quality, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "parsed": {"diseases": len(diseases), "patterns": len(patterns), "symptoms": len(symptoms), "formulas": len(formulas)},
        "pilot_pred": {"entities": len(entities), "relations_explicit": len(relations), "relations_derived": len(derived)},
        "quality": {k: len(v) for k, v in quality.items()},
        "evaluation_vs_gold_v0_3": metrics,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
