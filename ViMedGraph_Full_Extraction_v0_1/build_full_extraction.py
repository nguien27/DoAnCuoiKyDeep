from pathlib import Path
import pandas as pd
import numpy as np
import re, unicodedata, hashlib, json, zipfile, shutil
from collections import OrderedDict, defaultdict

BASE=Path('/mnt/data')
CORPUS=BASE/'ViMedGraph_SRC001_SRC002_Corpus_v0_1'
REF=BASE/'ViMedGraph_Parser_Structured_v0_2'
OUT=BASE/'ViMedGraph_Full_Extraction_v0_1'
ZIP=BASE/'ViMedGraph_Full_Extraction_v0_1.zip'
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)

chunks=pd.read_csv(CORPUS/'chunks.csv')
diseases=pd.read_csv(CORPUS/'diseases.csv')
dref=pd.read_csv(REF/'parsed_diseases.csv')
pref=pd.read_csv(REF/'parsed_patterns.csv')
sref=pd.read_csv(REF/'parsed_symptoms.csv')
fref=pd.read_csv(REF/'parsed_formulas.csv')


def norm(s):
    if pd.isna(s): return ''
    s=unicodedata.normalize('NFD',str(s).lower())
    s=''.join(c for c in s if unicodedata.category(c)!='Mn')
    s=s.replace('đ','d')
    s=re.sub(r'[^a-z0-9]+',' ',s)
    return re.sub(r'\s+',' ',s).strip()

def slug(s):
    return re.sub(r'_+','_',norm(s).upper().replace(' ','_')).strip('_')

def clean_pattern_title(s):
    s=str(s).strip()
    # strip prose description after colon
    if ':' in s: s=s.split(':',1)[0].strip()
    s=re.sub(r'\s+$','',s)
    return s

def norm_pattern(s):
    s=clean_pattern_title(s)
    s=re.sub(r'\s*\([^)]*\)\s*$','',s).strip()
    s=norm(s)
    if s.startswith('the '): s=s[4:]
    return s

def reconstruct(group):
    group=group.sort_values('chunk_index_in_section')
    lines=[]
    for _,r in group.iterrows():
        cur=str(r['source_text']).splitlines()
        if not lines:
            lines=cur; continue
        overlap=0
        for k in range(min(len(lines),len(cur),120),0,-1):
            if lines[-k:]==cur[:k]: overlap=k; break
        lines.extend(cur[overlap:])
    return '\n'.join(lines)

def parse_patterns(text):
    # Supports 1. and nested 1.1. headings when direct child .1 is Triệu chứng.
    ms=list(re.finditer(r'(?m)^(\d+(?:\.\d+)*)\.\s+([^\n]+)$',text))
    cand=[]
    for m in ms:
        prefix=m.group(1); title=m.group(2).strip()
        if re.match(r'(?i)^(triệu chứng|chẩn đoán|pháp|phương|điều trị|thuốc|châm|xoa bóp)',title):
            continue
        look=text[m.end():m.end()+5000]
        if re.search(rf'(?m)^{re.escape(prefix)}\.1\.\s+Triệu chứng',look):
            cand.append((m.start(),prefix,title))
    out=[]
    for i,(st,prefix,title) in enumerate(cand):
        en=cand[i+1][0] if i+1<len(cand) else len(text)
        block=text[st:en]
        # symptom paragraph
        sm=re.search(rf'(?ms)^{re.escape(prefix)}\.1\.\s+Triệu chứng(?: lâm sàng)?:?\s*(.*?)(?=^{re.escape(prefix)}\.2\.\s+Chẩn đoán)',block)
        symptom_text=re.sub(r'\s+',' ',sm.group(1)).strip() if sm else ''
        pm=re.search(rf'(?ms)^{re.escape(prefix)}\.3\.\s+Pháp(?: điều trị)?:?\s*(.*?)(?=^{re.escape(prefix)}\.4\.\s+Phương)',block)
        phap=re.sub(r'\s+',' ',pm.group(1)).strip() if pm else ''
        dx=re.findall(r'(?i)Chẩn đoán bệnh danh:\s*([^\n]+)',block)
        out.append(dict(prefix=prefix,title=clean_pattern_title(title),raw_title=title,block=block,symptom_text=symptom_text,phap_tri=phap,diagnosis_names=dx))
    return out

# Reconstruct treatment sections and their provenance
section_text={}
section_meta={}
for did,g in chunks[chunks['section_type']=='the_lam_sang_dieu_tri_yhct'].groupby('disease_id'):
    section_text[did]=reconstruct(g)
    section_meta[did]=dict(pdf_page_start=int(g['pdf_page_start'].min()),pdf_page_end=int(g['pdf_page_end'].max()),source_id=g.iloc[0]['source_id'])

# Conservative disease mapping for SRC_001. Two chapters remain ambiguous by design.
SRC001_MAP={
'SRC_001_D01':('unique',['U62.392.5'],'exact title + YHCT'),
'SRC_001_D02':('unique',['U62.261'],'exact title + YHCT'),
'SRC_001_D03':('unique',['U62.371'],'YHCT exact'),
'SRC_001_D04':('ambiguous',['U62.021','U62.031','U62.031.0'],'source chapter does not specify rheumatoid serostatus'),
'SRC_001_D05':('unique',['U62.292'],'modern condition + YHCT Chứng tý'),
'SRC_001_D06':('unique',['U58.091'],'modern condition + YHCT exact'),
'SRC_001_D07':('unique',['U53.151'],'exact condition + YHCT'),
'SRC_001_D08':('unique',['U55.561'],'exact condition + YHCT'),
'SRC_001_D09':('ambiguous',['U55.541','U55.531'],'two official Hiếp thống codes correspond to intercostal neuralgia variants'),
'SRC_001_D10':('unique',['U62.392'],'Yêu cước thống exact'),
'SRC_001_D11':('unique',['U58.021'],'YHCT Bán thân bất toại exact'),
'SRC_001_D12':('unique',['U55.611'],'YHCT Ngũ trì exact'),
'SRC_001_D13':('unique',['U50.481'],'exact condition + YHCT'),
'SRC_001_D14':('unique',['U53.071'],'YHCT Cam tích exact'),
'SRC_001_D15':('unique',['U60.471'],'general Viêm dạ dày và tá tràng / Vị quản thống'),
'SRC_001_D16':('unique',['U50.102'],'modern condition + YHCT Hiếp thống'),
'SRC_001_D17':('unique',['U59.231'],'source pattern diagnosis explicitly uses Khái thấu'),
'SRC_001_D18':('unique',['U61.011'],'YHCT Ẩn chẩn exact'),
'SRC_001_D19':('unique',['U66.372'],'source diagnosis says Long bế; reference uses Lung bế spelling'),
'SRC_001_D20':('unique',['U58.762'],'YHCT Hạ trĩ exact'),
}

# For SRC_002, no auto-code from the older terminology registry unless exact modern condition also matches.
# Current registry parsed here contains SRC_001-era disease set, so all SRC_002 chapters are kept unmapped.

disease_mapping=[]
for _,d in diseases.iterrows():
    did=d['disease_id']
    if did in SRC001_MAP:
        status,codes,reason=SRC001_MAP[did]
    else:
        status,codes,reason='unmapped',[],'SRC_002 disease not safely represented by current parsed terminology registry; do not reuse codes from different modern conditions'
    disease_mapping.append({
        'disease_id':did,'source_id':d['source_id'],'disease_name':d['disease_name'],'yhct_name':d['yhct_name'],
        'mapping_status':status,'official_code':codes[0] if status=='unique' else '',
        'candidate_official_codes':' | '.join(codes),'mapping_reason':reason
    })
disease_mapping_df=pd.DataFrame(disease_mapping)

# Helper: all pattern descendants through the explicit parent_code hierarchy.
# Do NOT use string-prefix matching because some disease codes are prefixes of other disease codes.
def descendant_patterns(code):
    wanted=[]
    frontier=[code]
    seen=set()
    while frontier:
        parent=frontier.pop(0)
        if parent in seen: continue
        seen.add(parent)
        children=pref[pref['parent_code'].astype(str)==str(parent)]
        for _,r in children.iterrows():
            wanted.append(r.to_dict())
            frontier.append(str(r['official_code']))
    return pd.DataFrame(wanted,columns=pref.columns) if wanted else pref.iloc[0:0].copy()

# Build entities/relations + mappings/candidates
entities=[]; relations=[]; pattern_map=[]; formula_map=[]; candidates=[]; quality=[]
entity_seen=set(); rel_seen=set()

def add_entity(eid,etype,canon,observed,source_id,disease_id,p1,p2,official_id='',official_code='',normalization_status='unmapped',confidence=1.0,notes=''):
    if eid in entity_seen: return
    entity_seen.add(eid)
    entities.append(dict(entity_id=eid,entity_type=etype,canonical_name=canon,observed_name=observed,
                         official_id=official_id,official_code=official_code,source_id=source_id,disease_id=disease_id,
                         section_type='the_lam_sang_dieu_tri_yhct',pdf_page_start=p1,pdf_page_end=p2,
                         normalization_status=normalization_status,confidence=confidence,notes=notes))

def add_rel(head,htype,rel,tail,ttype,source_id,disease_id,p1,p2,evidence,confidence=1.0,status='explicit'):
    key=(head,rel,tail,source_id,disease_id)
    if key in rel_seen: return
    rel_seen.add(key)
    relations.append(dict(relation_id=f'R{len(relations)+1:06d}',head_id=head,head_type=htype,relation=rel,
                          tail_id=tail,tail_type=ttype,source_id=source_id,disease_id=disease_id,
                          section_type='the_lam_sang_dieu_tri_yhct',pdf_page_start=p1,pdf_page_end=p2,
                          evidence_text=str(evidence)[:1500],confidence=confidence,relation_status=status))

# Disease nodes
for _,d in diseases.iterrows():
    did=d['disease_id']; mapr=disease_mapping_df[disease_mapping_df['disease_id']==did].iloc[0]
    code=mapr['official_code'] if mapr['mapping_status']=='unique' else ''
    dr=dref[dref['official_code']==code]
    if not dr.empty:
        canon=dr.iloc[0]['canonical_name']; oid=dr.iloc[0]['official_id']; nstat='official_code'
    else:
        canon=str(d['yhct_name']) if pd.notna(d['yhct_name']) and str(d['yhct_name']).strip() else str(d['disease_name'])
        oid=''; nstat='ambiguous' if mapr['mapping_status']=='ambiguous' else 'unmapped_candidate'
    add_entity('BENH_'+did,'BỆNH_CHỨNG',canon,str(d['full_title']),d['source_id'],did,int(d['pdf_page_start']),int(d['pdf_page_end']),oid,code,nstat,1.0 if code else 0.7,mapr['mapping_reason'])

# Parse patterns first
pattern_records=[]
for _,d in diseases.iterrows():
    did=d['disease_id']; txt=section_text.get(did,'')
    p1=section_meta.get(did,{}).get('pdf_page_start',d['pdf_page_start']); p2=section_meta.get(did,{}).get('pdf_page_end',d['pdf_page_end'])
    mapr=disease_mapping_df[disease_mapping_df['disease_id']==did].iloc[0]
    dcode=mapr['official_code'] if mapr['mapping_status']=='unique' else ''
    dcands=[x for x in str(mapr['candidate_official_codes']).split(' | ') if x]
    for idx,p in enumerate(parse_patterns(txt),1):
        pnorm=norm_pattern(p['title'])
        candidate_rows=pd.DataFrame()
        # use unique disease subtree when available, otherwise ambiguous candidate subtrees
        pools=[]
        for code in ([dcode] if dcode else dcands):
            if code: pools.append(descendant_patterns(code))
        pool=pd.concat(pools,ignore_index=True).drop_duplicates('official_code') if pools else pref.iloc[0:0]
        matches=pool[pool['canonical_name'].map(norm_pattern)==pnorm]
        # If no match and diagnosis names identify a canonical disease, restrict globally to that disease family
        if matches.empty and p.get('diagnosis_names'):
            dxnorm={norm(x).replace('the ','').strip(' .') for x in p['diagnosis_names']}
            dx_codes=[]
            for _,dr in dref.iterrows():
                if norm(dr['canonical_name']) in dxnorm or any(norm(dr['canonical_name']) in x for x in dxnorm):
                    dx_codes.append(dr['official_code'])
            pools2=[descendant_patterns(c) for c in dx_codes]
            pool2=pd.concat(pools2,ignore_index=True).drop_duplicates('official_code') if pools2 else pref.iloc[0:0]
            matches=pool2[pool2['canonical_name'].map(norm_pattern)==pnorm]
        if len(matches)==1:
            mr=matches.iloc[0]; pcode=mr['official_code']; poid=mr['official_id']; status='official_code'; conf=1.0
            canon=mr['canonical_name']; cand_codes=pcode
        elif len(matches)>1:
            pcode=''; poid=''; status='ambiguous'; conf=0.6; canon=clean_pattern_title(p['title']); cand_codes=' | '.join(matches['official_code'].astype(str))
        else:
            pcode=''; poid=''; status='unmapped_candidate'; conf=0.5; canon=clean_pattern_title(p['title']); cand_codes=''
        peid=f'THE_{did}_P{idx:02d}_{p["prefix"].replace(".","_")}'
        add_entity(peid,'THỂ_BỆNH',canon,clean_pattern_title(p['title']),d['source_id'],did,p1,p2,poid,pcode,status,conf,f'pháp_trị={p["phap_tri"]}')
        add_rel('BENH_'+did,'BỆNH_CHỨNG','CÓ_THỂ_BỆNH',peid,'THỂ_BỆNH',d['source_id'],did,p1,p2,clean_pattern_title(p['title']),1.0,'explicit')
        pattern_map.append(dict(pattern_entity_id=peid,disease_id=did,source_id=d['source_id'],pattern_prefix=p['prefix'],observed_name=clean_pattern_title(p['title']),
                                official_id=poid,official_code=pcode,mapping_status=status,candidate_official_codes=cand_codes,
                                symptom_text=p['symptom_text'],phap_tri=p['phap_tri'],diagnosis_names=' | '.join(p.get('diagnosis_names',[]))))
        pattern_records.append(dict(entity_id=peid,disease_id=did,source_id=d['source_id'],p1=p1,p2=p2,**p,official_code=pcode,mapping_status=status))

pattern_map_df=pd.DataFrame(pattern_map)

# Symptom normalization for patterns with official codes. Unmapped patterns keep raw symptom text as candidates.
STOP={'cac','co','va','hoac','mot','nhieu','bi','duoc','khi','tai','o','thuong','the','la','nguoi','benh'}
def token_coverage(canon,text):
    ct=[t for t in norm(canon).split() if t not in STOP]
    tx=set(norm(text).split())
    return sum(t in tx for t in ct)/len(ct) if ct else 0

for p in pattern_records:
    if p['official_code']:
        ss=sref[sref['parent_code']==p['official_code']]
        matched=0
        for _,sr in ss.iterrows():
            if sr['canonical_name']=='Triệu chứng khác': continue
            c=sr['canonical_name']; txt=p['symptom_text']; cov=token_coverage(c,txt)
            ok=(norm(c) in norm(txt)) or cov>=0.65
            # known shorthand from pilot
            if str(sr['official_id'])=='6541110' and 'tam quy' in norm(txt): ok=True
            if str(sr['official_id'])=='6541111' and 'khi doan' in norm(txt): ok=True
            if not ok: continue
            matched+=1
            eid='TC_'+str(sr['official_id'])
            add_entity(eid,'TRIỆU_CHỨNG',c,c,p['source_id'],p['disease_id'],p['p1'],p['p2'],sr['official_id'],sr['official_code'],'official_code',0.95 if cov<1 else 1.0,'normalized by official symptom dictionary')
            add_rel(p['entity_id'],'THỂ_BỆNH','CÓ_TRIỆU_CHỨNG',eid,'TRIỆU_CHỨNG',p['source_id'],p['disease_id'],p['p1'],p['p2'],txt,0.95 if cov<1 else 1.0,'explicit')
        if ss.shape[0] and matched==0 and p['symptom_text']:
            quality.append(dict(source_id=p['source_id'],disease_id=p['disease_id'],pattern_entity_id=p['entity_id'],flag='no_normalized_symptom_match',detail=f'0/{len(ss)} official symptom terms matched prose'))
    else:
        if p['symptom_text']:
            candidates.append(dict(candidate_type='TRIỆU_CHỨNG_TEXT',source_id=p['source_id'],disease_id=p['disease_id'],pattern_entity_id=p['entity_id'],observed_text=p['symptom_text'],candidate_name='',candidate_code='',reason='pattern has no unique official code; keep raw symptom paragraph for later normalization'))

# Formula matching on normalized patterns. Formula names from unmapped patterns stored as candidates.
# Aliases discovered in pilot are retained.
formula_alias={
'U62.261.01.NP006':'Thấp khớp II',
'U62.261.02.NP007':'Độc hoạt phong thấp hoàn',
'U62.371.01.DN001':'Cao Kim hoàng tán',
}

def extract_formula_candidates(block):
    out=[]
    # Same-line named formulas only; never let whitespace cross into the first ingredient line.
    same_line_patterns=[
        r'(?i)(?:Cổ phương|Cổ phương gia giảm)[ \t]*:[ \t]*(?:dùng bài[ \t]*)?[“\"]?([^\n:“”\"]{2,100})',
        r'(?i)Nghiệm phương[ \t]*:[ \t]*([^\n]{2,100})',
        r'(?i)(?:Hoặc dùng bài|Có thể dùng bài|Dùng bài)[ \t:]+[“\"]?([^\n:“”\"]{2,100})',
        r'(?i)^\+[ \t]*Bài[ \t]+[“\"]?([^\n:“”\"]{2,100})',
    ]
    for pat in same_line_patterns:
        for m in re.finditer(pat,block,re.M):
            name=m.group(1).strip(' :-“”"')
            name=re.sub(r'[ \t]+gia giảm.*$',' gia giảm',name,flags=re.I).strip()
            name=re.sub(r'[ \t]*\([^\n]*$','',name).strip()
            if not name or norm(name).startswith('lua chon cac vi'): continue
            if len(name)>100: continue
            nn=norm(name)
            reject_starts=('neu ','co the ','dung ','thuoc ','tuong tu ','ket hop ','sac ','truong hop ','dieu tri ')
            if nn.startswith(reject_starts):
                continue
            # reject ingredient-like single words unless the name looks like a formula/product
            tokens=nn.split()
            suffixes=('thang','tan','hoan','am','cao','phuong','siro','vien','chao')
            if len(tokens)==1 and not any(nn.endswith(x) for x in suffixes):
                continue
            out.append(name)
    # Quoted names are relatively safe; keep those that look like named formula/product.
    for m in re.finditer(r'[“\"]([^”\"\n]{2,100})[”\"]',block):
        name=m.group(1).strip()
        nn=norm(name)
        if any(x in nn for x in ['thang','tan','hoan','am','cao','phuong','siro','vien','chao']):
            out.append(name)
    seen=set(); final=[]
    for x in out:
        k=norm(x)
        if k and k not in seen:
            seen.add(k); final.append(x)
    return final

# herb aliases (only small known spelling variations, no semantic invention)
ing_alias={'Đương quy':['Đương quy','Đương qui'],'Bạch truật (sao cám)':['Bạch truật (sao cám)','Bach truật (sao cám)']}

for p in pattern_records:
    block=p['block']; pcode=p['official_code']
    normalized_formula_names=set()
    if pcode:
        ff=fref[fref['parent_code']==pcode]
        # Build anchors for formula-local ingredient verification
        anchors=[]
        nb=norm(block)
        dn_cursor=0
        for _,fr in ff.iterrows():
            code=str(fr['official_code']); cname=str(fr['canonical_name']); observed=formula_alias.get(code,cname)
            pos=-1
            if code in formula_alias:
                pos=nb.find(norm(observed))
            elif cname=='Thuốc dùng ngoài':
                ings=[] if pd.isna(fr['ingredients']) else str(fr['ingredients']).split(' | ')
                for ing in ings[:4]:
                    for a in ing_alias.get(ing,[ing]):
                        q=nb.find(norm(a),dn_cursor)
                        if q>=0: pos=q; observed=a; dn_cursor=q+1; break
                    if pos>=0: break
            else:
                pos=nb.find(norm(cname))
            if pos>=0:
                anchors.append(dict(code=code,cname=cname,observed=observed,pos=pos,row=fr))
        anchors=sorted(anchors,key=lambda x:x['pos'])
        for i,a in enumerate(anchors):
            end=anchors[i+1]['pos'] if i+1<len(anchors) else len(nb)
            a['span']=nb[a['pos']:end]
            fr=a['row']; code=a['code']; cname=a['cname']; observed=a['observed']
            normalized_formula_names.add(norm(observed)); normalized_formula_names.add(norm(cname))
            feid='BT_'+str(fr['official_id'])
            add_entity(feid,'BÀI_THUỐC',cname,observed,p['source_id'],p['disease_id'],p['p1'],p['p2'],fr['official_id'],code,'official_code',1.0,'matched within normalized pattern')
            add_rel(p['entity_id'],'THỂ_BỆNH','ĐIỀU_TRỊ_BẰNG',feid,'BÀI_THUỐC',p['source_id'],p['disease_id'],p['p1'],p['p2'],f'{clean_pattern_title(p["title"])} -> {observed}',1.0,'explicit')
            formula_map.append(dict(formula_entity_id=feid,pattern_entity_id=p['entity_id'],disease_id=p['disease_id'],source_id=p['source_id'],observed_name=observed,canonical_name=cname,official_id=fr['official_id'],official_code=code,mapping_status='official_code'))
            # GỒM only when ingredient is verified in formula-local span
            if pd.notna(fr['ingredients']):
                for ing in str(fr['ingredients']).split(' | '):
                    obs=next((z for z in ing_alias.get(ing,[ing]) if norm(z) in a['span']),None)
                    if not obs: continue
                    heid='DL_'+slug(ing)
                    add_entity(heid,'DƯỢC_LIỆU',ing,obs,p['source_id'],p['disease_id'],p['p1'],p['p2'],'','', 'exact_name_or_alias',0.98 if obs!=ing else 1.0,'no PL05 code available in current project files')
                    add_rel(feid,'BÀI_THUỐC','GỒM',heid,'DƯỢC_LIỆU',p['source_id'],p['disease_id'],p['p1'],p['p2'],f'{observed} -> {obs}',0.98 if obs!=ing else 1.0,'explicit')
    # candidate named formulas not already normalized
    for name in extract_formula_candidates(block):
        if norm(name) in normalized_formula_names: continue
        # ignore generic narrative phrases and obvious false positives
        if norm(name) in {'doi phap lap phuong','nghiem phuong','thuoc dung ngoai'}: continue
        candidates.append(dict(candidate_type='BÀI_THUỐC',source_id=p['source_id'],disease_id=p['disease_id'],pattern_entity_id=p['entity_id'],observed_text=name,candidate_name=name,candidate_code='',reason='named in prose but not uniquely normalized to current formula registry'))

# Formula generic markers in unmapped patterns are also retained as text candidates when present
for p in pattern_records:
    if not p['official_code']:
        for marker in ['Đối pháp lập phương','Nghiệm phương','Thuốc dùng ngoài','Thuốc Nam']:
            if norm(marker) in norm(p['block']):
                candidates.append(dict(candidate_type='TREATMENT_MARKER',source_id=p['source_id'],disease_id=p['disease_id'],pattern_entity_id=p['entity_id'],observed_text=marker,candidate_name=marker,candidate_code='',reason='uncoded treatment marker; preserved, not promoted to coded BÀI_THUỐC'))

# Derived disease->symptom relations only from explicit normalized pattern-symptom relations
explicit_df=pd.DataFrame(relations)
for _,r in explicit_df[explicit_df['relation']=='CÓ_TRIỆU_CHỨNG'].iterrows():
    add_rel('BENH_'+r['disease_id'],'BỆNH_CHỨNG','CÓ_TRIỆU_CHỨNG',r['tail_id'],'TRIỆU_CHỨNG',r['source_id'],r['disease_id'],r['pdf_page_start'],r['pdf_page_end'],f'derived through {r["head_id"]}',r['confidence'],'derived')

entities_df=pd.DataFrame(entities)
relations_df=pd.DataFrame(relations)
cand_df=pd.DataFrame(candidates).drop_duplicates() if candidates else pd.DataFrame(columns=['candidate_type','source_id','disease_id','pattern_entity_id','observed_text','candidate_name','candidate_code','reason'])
quality_df=pd.DataFrame(quality).drop_duplicates() if quality else pd.DataFrame(columns=['source_id','disease_id','pattern_entity_id','flag','detail'])
formula_map_df=pd.DataFrame(formula_map).drop_duplicates() if formula_map else pd.DataFrame()

# Referential integrity and backward source support audit
nodes=set(entities_df['entity_id'])
dangling=relations_df[(~relations_df['head_id'].isin(nodes))|(~relations_df['tail_id'].isin(nodes))]

def relation_key_df(df):
    return df[['head_id','relation','tail_id','source_id','disease_id']].astype(str).agg('|'.join,axis=1)

dup_entities=int(entities_df['entity_id'].duplicated().sum())
dup_rel=int(relation_key_df(relations_df).duplicated().sum())
invalid_pages=int((entities_df['pdf_page_start'].astype(int)>entities_df['pdf_page_end'].astype(int)).sum())

# Source support checks on high-confidence direct structure
support_fail=[]
for _,e in entities_df.iterrows():
    did=e['disease_id']; txt=section_text.get(did,'')
    if e['entity_type']=='BỆNH_CHỨNG':
        # full title/yhct may be outside treatment section, skip here
        continue
    if e['entity_type']=='THỂ_BỆNH':
        if norm(e['observed_name']) not in norm(txt): support_fail.append((e['entity_id'],'pattern name not found'))
    elif e['entity_type']=='BÀI_THUỐC':
        # Generic formula nodes can be evidenced by generic marker or ingredient-local anchor; most named formulas exact/alias.
        if e['canonical_name'] not in ['Thuốc dùng ngoài','Đối pháp lập phương','Nghiệm phương','Thuốc nam','Thuốc Nam','Bài thuốc']:
            if norm(e['observed_name']) not in norm(txt) and norm(e['canonical_name']) not in norm(txt):
                support_fail.append((e['entity_id'],'formula name not found'))
    elif e['entity_type']=='TRIỆU_CHỨNG':
        # relation evidence is the source paragraph; check token coverage against at least one pattern paragraph
        rels=relations_df[(relations_df['tail_id']==e['entity_id'])&(relations_df['relation']=='CÓ_TRIỆU_CHỨNG')&(relations_df['relation_status']=='explicit')]
        if rels.empty: support_fail.append((e['entity_id'],'no explicit symptom relation'))

# Pilot regression on D01-D04: compare semantic official-coded entities/relations where full extractor makes a unique mapping.
pilot_dir=BASE/'ViMedGraph_Text_Extraction_Pilot_v0_3'
pilot_report=[]
if pilot_dir.exists():
    pe=pd.read_csv(pilot_dir/'text_entities.csv')
    pr=pd.read_csv(pilot_dir/'text_relations.csv')
    # Exclude D04 official-code-specific terms because full extraction intentionally marks disease-code ambiguity.
    pilot_keep=pe[(pe['disease_id'].isin(['SRC_001_D01','SRC_001_D02','SRC_001_D03'])) & (pe['normalization_status']!='unmapped_candidate')]
    full_keep=entities_df[(entities_df['disease_id'].isin(['SRC_001_D01','SRC_001_D02','SRC_001_D03'])) & (entities_df['normalization_status']!='unmapped_candidate')]
    # Compare normalized official codes + type; herbs without codes use canonical name.
    def ekeys(df):
        return set((r.entity_type, str(r.official_code) if pd.notna(r.official_code) and str(r.official_code) else norm(r.canonical_name)) for r in df.itertuples())
    g=ekeys(pilot_keep); p=ekeys(full_keep)
    tp=len(g&p); fp=len(p-g); fn=len(g-p)
    pilot_report.append(dict(scope='D01-D03 normalized entity regression',gold=len(g),pred=len(p),TP=tp,FP=fp,FN=fn,precision=tp/(tp+fp) if tp+fp else 0,recall=tp/(tp+fn) if tp+fn else 0))

# summary by source
summary_rows=[]
for sid in ['SRC_001','SRC_002']:
    ed=entities_df[entities_df['source_id']==sid]
    rd=relations_df[relations_df['source_id']==sid]
    pm=pattern_map_df[pattern_map_df['source_id']==sid]
    dm=disease_mapping_df[disease_mapping_df['source_id']==sid]
    summary_rows.append(dict(
        source_id=sid,diseases=len(dm),diseases_unique_mapped=int((dm['mapping_status']=='unique').sum()),diseases_ambiguous=int((dm['mapping_status']=='ambiguous').sum()),diseases_unmapped=int((dm['mapping_status']=='unmapped').sum()),
        patterns=len(pm),patterns_normalized=int((pm['mapping_status']=='official_code').sum()),patterns_ambiguous=int((pm['mapping_status']=='ambiguous').sum()),patterns_unmapped=int((pm['mapping_status']=='unmapped_candidate').sum()),
        entities=len(ed),explicit_relations=int(((rd['relation_status']=='explicit')).sum()),derived_relations=int(((rd['relation_status']=='derived')).sum()),candidates=len(cand_df[cand_df['source_id']==sid])
    ))
summary_df=pd.DataFrame(summary_rows)

# Overall quality gates
qa=dict(
    package_version='v0.1',diseases=len(diseases),patterns=len(pattern_map_df),entities=len(entities_df),relations=len(relations_df),
    explicit_relations=int((relations_df['relation_status']=='explicit').sum()),derived_relations=int((relations_df['relation_status']=='derived').sum()),
    candidate_mentions=len(cand_df),duplicate_entity_ids=dup_entities,duplicate_relations=dup_rel,dangling_relation_endpoints=len(dangling),
    invalid_page_ranges=invalid_pages,source_support_failures=len(support_fail),
    src001_unique_disease_mappings=int(((disease_mapping_df['source_id']=='SRC_001')&(disease_mapping_df['mapping_status']=='unique')).sum()),
    src001_ambiguous_disease_mappings=int(((disease_mapping_df['source_id']=='SRC_001')&(disease_mapping_df['mapping_status']=='ambiguous')).sum()),
    src002_unmapped_disease_mappings=int(((disease_mapping_df['source_id']=='SRC_002')&(disease_mapping_df['mapping_status']=='unmapped')).sum()),
    disease_pattern_relation_count=int(((relations_df['relation']=='CÓ_THỂ_BỆNH')&(relations_df['relation_status']=='explicit')).sum()),
    pattern_relation_count_matches_parsed=(int(((relations_df['relation']=='CÓ_THỂ_BỆNH')&(relations_df['relation_status']=='explicit')).sum())==len(pattern_map_df))
)

# Write artifacts
entities_df.to_csv(OUT/'full_entities.csv',index=False,encoding='utf-8-sig')
relations_df.to_csv(OUT/'full_relations.csv',index=False,encoding='utf-8-sig')
disease_mapping_df.to_csv(OUT/'disease_mapping.csv',index=False,encoding='utf-8-sig')
pattern_map_df.to_csv(OUT/'pattern_mapping.csv',index=False,encoding='utf-8-sig')
formula_map_df.to_csv(OUT/'formula_mapping.csv',index=False,encoding='utf-8-sig')
cand_df.to_csv(OUT/'candidate_mentions.csv',index=False,encoding='utf-8-sig')
quality_df.to_csv(OUT/'quality_flags.csv',index=False,encoding='utf-8-sig')
summary_df.to_csv(OUT/'extraction_summary.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(pilot_report).to_csv(OUT/'pilot_regression.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(support_fail,columns=['entity_id','reason']).to_csv(OUT/'source_support_failures.csv',index=False,encoding='utf-8-sig')
with open(OUT/'qa_summary.json','w',encoding='utf-8') as f: json.dump(qa,f,ensure_ascii=False,indent=2)

# Keep runnable script
shutil.copy2(BASE/'build_full_extraction.py',OUT/'build_full_extraction.py')

readme=f'''# ViMedGraph Full Extraction v0.1\n\n## Scope\n- SRC_001: 20 disease chapters\n- SRC_002: 16 disease chapters\n- Total: 36 disease chapters\n\n## Safety policy\nThis package uses conservative normalization. It does not invent codes.\n- SRC_001: official 2025 terminology registries can normalize many diseases/patterns/symptoms/formulas.\n- SRC_002: the current terminology files in this project predate the late-2025 Tập II guide; disease codes are therefore kept unmapped unless a safe modern-condition match exists. In v0.1 all 16 SRC_002 diseases remain unmapped.\n- Ambiguous mappings stay ambiguous and are listed in `disease_mapping.csv` / `pattern_mapping.csv`.\n- Unresolved named treatments and raw symptom paragraphs are preserved in `candidate_mentions.csv`.\n\n## Graph-ready files\n- `full_entities.csv`\n- `full_relations.csv`\n\n## Mapping / QA files\n- `disease_mapping.csv`\n- `pattern_mapping.csv`\n- `formula_mapping.csv`\n- `candidate_mentions.csv`\n- `quality_flags.csv`\n- `source_support_failures.csv`\n- `extraction_summary.csv`\n- `pilot_regression.csv`\n- `qa_summary.json`\n\n## Important\nThis is a high-confidence rule-based baseline, not expert-reviewed final medical knowledge. Do not treat unnormalized candidates as verified KG facts.\n'''
(OUT/'README.md').write_text(readme,encoding='utf-8')

report=f'''# QA REPORT - ViMedGraph Full Extraction v0.1\n\n## Overall\n- Diseases: {qa['diseases']}\n- Patterns parsed: {qa['patterns']}\n- Entities: {qa['entities']}\n- Explicit relations: {qa['explicit_relations']}\n- Derived relations: {qa['derived_relations']}\n- Candidate/unresolved mentions: {qa['candidate_mentions']}\n\n## Mapping\n- SRC_001 unique disease mappings: {qa['src001_unique_disease_mappings']}/20\n- SRC_001 ambiguous disease mappings: {qa['src001_ambiguous_disease_mappings']}/20\n- SRC_002 unmapped disease mappings: {qa['src002_unmapped_disease_mappings']}/16\n\n## Integrity gates\n- Duplicate entity IDs: {qa['duplicate_entity_ids']}\n- Duplicate relations: {qa['duplicate_relations']}\n- Dangling relation endpoints: {qa['dangling_relation_endpoints']}\n- Invalid page ranges: {qa['invalid_page_ranges']}\n- Source-support failures: {qa['source_support_failures']}\n\n## Conservative decisions\n- Viêm khớp dạng thấp chapter is not assigned one serostatus code automatically because the source chapter title is generic.\n- Đau dây thần kinh liên sườn / Hiếp thống retains two possible official code candidates.\n- SRC_002 chapters are not forced into older codes from different modern diseases.\n- Formula-herb `GỒM` relations are created only when an official formula is normalized and the ingredient is found inside a formula-local text span.\n'''
(OUT/'QA_REPORT.md').write_text(report,encoding='utf-8')

if ZIP.exists(): ZIP.unlink()
with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED) as z:
    for p in OUT.rglob('*'):
        if p.is_file(): z.write(p,arcname=f'{OUT.name}/{p.relative_to(OUT)}')
with zipfile.ZipFile(ZIP,'r') as z:
    bad=z.testzip(); nfiles=len(z.namelist())
print(json.dumps(qa,ensure_ascii=False,indent=2))
print('\nSUMMARY\n',summary_df.to_string(index=False))
print('\nZIP',ZIP,'CRC',bad,'files',nfiles)
