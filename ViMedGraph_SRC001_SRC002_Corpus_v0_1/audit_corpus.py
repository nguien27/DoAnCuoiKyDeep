import fitz, csv, re, unicodedata, hashlib, json
from pathlib import Path
BASE=Path('/mnt/data/ViMedGraph_SRC001_SRC002_Corpus_v0_1')
SOURCES={
 'SRC_001':('/mnt/data/SRC_001_2020_QD5013_BYT_Huong_dan_chan_doan_dieu_tri_YHCT_Tap_I.pdf',0),
 'SRC_002':('/mnt/data/SRC_002_2025_QD3991_BYT_Huong_dan_chan_doan_dieu_tri_YHCT_Tap_II.pdf',-1),
}
TRANS=str.maketrans({'Ƣ':'Ư','ƣ':'ư','Õ':'Ò','Ö':'Ú','Ð':'Đ'})
def fix(s):
    return re.sub(r'[ \t]+',' ',unicodedata.normalize('NFC',s.translate(TRANS))).strip()
def clean_page(doc,p):
    out=[]
    for b in doc[p-1].get_text('dict',sort=True)['blocks']:
        if b.get('type')!=0: continue
        for l in b.get('lines',[]):
            dx,dy=l.get('dir',(1,0))
            if abs(dy)>0.05 or dx<0.95: continue
            txt=''.join(sp.get('text','') for sp in l.get('spans',[])).strip()
            if not txt: continue
            if l['bbox'][1]>790 and re.fullmatch(r'\d{1,3}',txt): continue
            if 'tuannm.ydct_' in txt or 'Nguyen Manh Tuan_' in txt: continue
            txt=fix(txt)
            if txt: out.append(txt)
    return out

def load(name):
    with open(BASE/name,encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))
chunks=load('chunks.csv'); sections=load('sections.csv'); diseases=load('diseases.csv')
docs={sid:fitz.open(path) for sid,(path,off) in SOURCES.items()}
page_cache={}
def page_text(sid,p):
    k=(sid,p)
    if k not in page_cache: page_cache[k]='\n'.join(clean_page(docs[sid],p))
    return page_cache[k]

checks={}
# Exact source verification, independently re-reading PDF
source_match_fail=[]
hash_fail=[]
page_bound_fail=[]
meta_fail=[]
for r in chunks:
    sid=r['source_id']; ps=int(r['pdf_page_start']); pe=int(r['pdf_page_end'])
    hay='\n'.join(page_text(sid,p) for p in range(ps,pe+1))
    if r['source_text'] not in hay: source_match_fail.append(r['chunk_id'])
    if hashlib.sha256(r['source_text'].encode()).hexdigest()!=r['sha256']: hash_fail.append(r['chunk_id'])
    if ps>pe or ps<1 or pe>len(docs[sid]): page_bound_fail.append(r['chunk_id'])
    if not all(r.get(k,'').strip() for k in ['chunk_id','source_id','disease_id','section_id','source_file','source_ref','source_text']): meta_fail.append(r['chunk_id'])
checks['chunks_total']=len(chunks)
checks['chunks_exactly_found_in_original_pdf_page_range']=len(chunks)-len(source_match_fail)
checks['chunks_source_match_fail']=len(source_match_fail)
checks['hash_fail']=len(hash_fail)
checks['page_bound_fail']=len(page_bound_fail)
checks['metadata_fail']=len(meta_fail)

# Relational integrity between CSVs
disease_ids={r['disease_id'] for r in diseases}; section_ids={r['section_id'] for r in sections}
checks['sections_missing_disease']=sum(1 for r in sections if r['disease_id'] not in disease_ids)
checks['chunks_missing_disease']=sum(1 for r in chunks if r['disease_id'] not in disease_ids)
checks['chunks_missing_section']=sum(1 for r in chunks if r['section_id'] not in section_ids)
checks['duplicate_disease_ids']=len(diseases)-len(disease_ids)
checks['duplicate_section_ids']=len(sections)-len(section_ids)
checks['duplicate_chunk_ids']=len(chunks)-len({r['chunk_id'] for r in chunks})

# Bounds: section inside disease, chunk inside section
D={r['disease_id']:r for r in diseases}; S={r['section_id']:r for r in sections}
section_range_fail=[]; chunk_range_fail=[]
for r in sections:
    d=D[r['disease_id']]
    if not (int(d['pdf_page_start'])<=int(r['pdf_page_start'])<=int(r['pdf_page_end'])<=int(d['pdf_page_end'])):
        section_range_fail.append(r['section_id'])
for r in chunks:
    s=S[r['section_id']]
    if not (int(s['pdf_page_start'])<=int(r['pdf_page_start'])<=int(r['pdf_page_end'])<=int(s['pdf_page_end'])):
        chunk_range_fail.append(r['chunk_id'])
checks['section_range_fail']=len(section_range_fail)
checks['chunk_range_fail']=len(chunk_range_fail)

# Reference flag consistency
checks['reference_flag_mismatch']=sum(1 for r in chunks if (r['section_type']=='tai_lieu_tham_khao') != (r['retrieval_enabled']=='0'))
# Encoding / watermark
bad=['Ƣ','ƣ','Õ','Ö','Ð']
checks['bad_encoding_chunks']=sum(1 for r in chunks if any(x in r['source_text'] for x in bad))
checks['watermark_chunks']=sum(1 for r in chunks if 'tuannm.ydct_' in r['source_text'] or 'Nguyen Manh Tuan_' in r['source_text'])

# Start page checks from diseases.csv
checks['disease_start_toc_mismatch']=sum(1 for r in diseases if int(r['document_page_start'])!=int(r['expected_document_page_start_from_toc']))

result={'checks':checks,'fail_samples':{
 'source_match_fail':source_match_fail[:20], 'hash_fail':hash_fail[:20], 'page_bound_fail':page_bound_fail[:20], 'metadata_fail':meta_fail[:20],
 'section_range_fail':section_range_fail[:20], 'chunk_range_fail':chunk_range_fail[:20]
}}
(BASE/'audit_independent.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
