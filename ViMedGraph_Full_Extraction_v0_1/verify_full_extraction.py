from pathlib import Path
import pandas as pd, json, zipfile, sys
BASE=Path('/mnt/data')
OUT=BASE/'ViMedGraph_Full_Extraction_v0_1'
REF=BASE/'ViMedGraph_Parser_Structured_v0_2'
e=pd.read_csv(OUT/'full_entities.csv')
r=pd.read_csv(OUT/'full_relations.csv')
dm=pd.read_csv(OUT/'disease_mapping.csv')
pm=pd.read_csv(OUT/'pattern_mapping.csv')
reg=pd.read_csv(OUT/'pilot_regression.csv')
dref=pd.read_csv(REF/'parsed_diseases.csv')
pref=pd.read_csv(REF/'parsed_patterns.csv')
sref=pd.read_csv(REF/'parsed_symptoms.csv')
fref=pd.read_csv(REF/'parsed_formulas.csv')
errors=[]

def check(cond,msg):
    if not cond: errors.append(msg)

check(len(dm)==36,f'disease mapping rows {len(dm)} !=36')
check(len(pm)==159,f'pattern rows {len(pm)} !=159')
check(e.entity_id.duplicated().sum()==0,'duplicate entity ids')
check(r.duplicated(['head_id','relation','tail_id','source_id','disease_id']).sum()==0,'duplicate relations')
nodes=set(e.entity_id)
check((((~r.head_id.isin(nodes))|(~r.tail_id.isin(nodes))).sum()==0),'dangling relation endpoint')
check((e.pdf_page_start.astype(int)<=e.pdf_page_end.astype(int)).all(),'invalid page range')
check(((r.relation=='CÓ_THỂ_BỆNH')&(r.relation_status=='explicit')).sum()==159,'disease-pattern relation count mismatch')
check(((dm.source_id=='SRC_001')&(dm.mapping_status=='unique')).sum()==18,'SRC001 unique disease mapping should be 18')
check(((dm.source_id=='SRC_001')&(dm.mapping_status=='ambiguous')).sum()==2,'SRC001 ambiguous disease mapping should be 2')
check(((dm.source_id=='SRC_002')&(dm.mapping_status=='unmapped')).sum()==16,'SRC002 unmapped diseases should be 16')
check(((pm.source_id=='SRC_001')&(pm.mapping_status=='official_code')).sum()==67,'SRC001 normalized patterns should be 67')
check(((pm.source_id=='SRC_001')&(pm.mapping_status=='ambiguous')).sum()==10,'SRC001 ambiguous patterns should be 10')
check(((pm.source_id=='SRC_002')&(pm.mapping_status=='unmapped_candidate')).sum()==82,'SRC002 unmapped patterns should be 82')
# Official code registry membership
sets={
'BỆNH_CHỨNG':set(dref.official_code.astype(str)),
'THỂ_BỆNH':set(pref.official_code.astype(str)),
'TRIỆU_CHỨNG':set(sref.official_code.astype(str)),
'BÀI_THUỐC':set(fref.official_code.astype(str)),
}
for typ,codes in sets.items():
    sub=e[(e.entity_type==typ)&e.official_code.notna()&(e.official_code.astype(str)!='')]
    bad=sub[~sub.official_code.astype(str).isin(codes)]
    check(bad.empty,f'{typ}: official codes missing from registry: {bad.official_code.tolist()[:10]}')
# Relation semantic parent consistency
entity_idx=e.set_index('entity_id')
for row in r[r.relation_status=='explicit'].itertuples(index=False):
    if row.relation=='CÓ_TRIỆU_CHỨNG':
        h=entity_idx.loc[row.head_id]; t=entity_idx.loc[row.tail_id]
        if str(h.official_code) and str(h.official_code)!='nan' and str(t.official_code) and str(t.official_code)!='nan':
            # Match by official_id first because the source registry itself contains duplicate/mistyped official_code values.
            sr=sref[sref.official_id.astype(str)==str(int(float(t.official_id)) if str(t.official_id)!='nan' else '')]
            if sr.empty:
                sr=sref[sref.official_code.astype(str)==str(t.official_code)]
            if sr.empty or str(sr.iloc[0].parent_code)!=str(h.official_code):
                errors.append(f'symptom parent mismatch {row.head_id}->{row.tail_id}')
    elif row.relation=='ĐIỀU_TRỊ_BẰNG':
        h=entity_idx.loc[row.head_id]; t=entity_idx.loc[row.tail_id]
        if str(h.official_code) and str(h.official_code)!='nan' and str(t.official_code) and str(t.official_code)!='nan':
            fr=fref[fref.official_code.astype(str)==str(t.official_code)]
            if fr.empty or str(fr.iloc[0].parent_code)!=str(h.official_code):
                errors.append(f'formula parent mismatch {row.head_id}->{row.tail_id}')
    elif row.relation=='GỒM':
        h=entity_idx.loc[row.head_id]; t=entity_idx.loc[row.tail_id]
        if str(h.official_code) and str(h.official_code)!='nan':
            fr=fref[fref.official_code.astype(str)==str(h.official_code)]
            if fr.empty:
                errors.append(f'GỒM formula code missing {h.official_code}')
            elif pd.notna(fr.iloc[0].ingredients):
                ings=[x.strip() for x in str(fr.iloc[0].ingredients).split(' | ')]
                if str(t.canonical_name) not in ings:
                    errors.append(f'ingredient mismatch {h.official_code}->{t.canonical_name}')
# Regression
if not reg.empty:
    check((reg.precision==1.0).all() and (reg.recall==1.0).all(),'pilot D01-D03 regression not perfect')
# QA file support failure
qa=json.loads((OUT/'qa_summary.json').read_text(encoding='utf-8'))
check(qa.get('source_support_failures')==0,'source support failures nonzero')
# ZIP CRC
zp=BASE/'ViMedGraph_Full_Extraction_v0_1.zip'
with zipfile.ZipFile(zp) as z:
    bad=z.testzip(); n=len(z.namelist())
check(bad is None,f'zip CRC failed {bad}')
print('STRICT QA:', 'PASS' if not errors else 'FAIL')
print('entities',len(e),'relations',len(r),'zip_files',n)
print('entity_types',e.entity_type.value_counts().to_dict())
print('relations',r.groupby(['relation','relation_status']).size().to_dict())
if errors:
    print('\n'.join(errors[:50]))
    sys.exit(1)
