from __future__ import annotations
import fitz
import re, csv, json, hashlib, unicodedata, statistics
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple

OUTDIR = Path('/mnt/data/ViMedGraph_SRC001_SRC002_Corpus_v0_1')
OUTDIR.mkdir(parents=True, exist_ok=True)

SOURCE_CONFIGS = [
    {
        'source_id': 'SRC_001',
        'path': Path('/mnt/data/SRC_001_2020_QD5013_BYT_Huong_dan_chan_doan_dieu_tri_YHCT_Tap_I.pdf'),
        'title': 'Hướng dẫn chẩn đoán và điều trị bệnh theo YHCT, kết hợp YHCT và YHHĐ - Tập I',
        'year': 2020,
        'pdf_to_document_page_offset': 0,
        'appendix_start_pdf_page': 152,
        'diseases': [
            (1,'Đau cột sống thắt lưng','Yêu thống',7),
            (2,'Thoái hóa khớp gối','Hạc tất phong',15),
            (3,'Gout','Thống phong',21),
            (4,'Viêm khớp dạng thấp','Chứng tý',29),
            (5,'Hội chứng cổ vai cánh tay','Chứng tý',37),
            (6,'Tăng huyết áp vô căn','Huyễn vựng',44),
            (7,'Rối loạn chuyển hóa lipoprotein và tình trạng tăng lipid máu khác','Chứng đàm',51),
            (8,'Bệnh dây thần kinh mặt','Khẩu nhãn oa tà',59),
            (9,'Đau dây thần kinh liên sườn','Hiếp thống',64),
            (10,'Đau thần kinh tọa','Yêu cước thống',72),
            (11,'Di chứng nhồi máu não','Bán thân bất toại',79),
            (12,'Bại não trẻ em','Ngũ trì',87),
            (13,'Di chứng viêm não do virus','Ôn bệnh',96),
            (14,'Suy dinh dưỡng thể marasmus','Cam tích',104),
            (15,'Viêm dạ dày và tá tràng','Vị quản thống',111),
            (16,'Viêm gan virus mạn','Hiếp thống',119),
            (17,'Bệnh phổi tắc nghẽn mạn tính (COPD)','Khái suyễn',125),
            (18,'Mày đay','Ẩn chẩn',135),
            (19,'Bí đái cơ năng','Long bế',140),
            (20,'Bệnh trĩ','Hạ trĩ',146),
        ]
    },
    {
        'source_id': 'SRC_002',
        'path': Path('/mnt/data/SRC_002_2025_QD3991_BYT_Huong_dan_chan_doan_dieu_tri_YHCT_Tap_II.pdf'),
        'title': 'Hướng dẫn chẩn đoán và điều trị bệnh theo YHCT, kết hợp YHCT và YHHĐ - Tập II',
        'year': 2025,
        'pdf_to_document_page_offset': -1,  # PDF có 1 trang quyết định trước trang số 1 của tài liệu
        'appendix_start_pdf_page': None,
        'diseases': [
            (1,'Cảm mạo','Cảm mạo',5),
            (2,'Viêm mũi do vận mạch và dị ứng','Tỵ cừu, tỵ uyên',21),
            (3,'Sốt xuất huyết Dengue','Ôn bệnh',28),
            (4,'Bệnh trào ngược dạ dày - thực quản','Vị khí nghịch',37),
            (5,'Hội chứng ruột kích thích','Tiết tả, táo bón hoặc xen kẽ',46),
            (6,'Táo bón','Tiện bí',57),
            (7,'Đái dầm','Di niệu',68),
            (8,'Sỏi tiết niệu','Thạch lâm',78),
            (9,'Tăng sinh lành tính tuyến tiền liệt','Long bế',85),
            (10,'Loãng xương không kèm gẫy xương bệnh lý','Cốt tý',91),
            (11,'Đái tháo đường không phụ thuộc insulin','Tiêu khát',101),
            (12,'Suy nhược cơ thể (khó ở và mệt mỏi)','Hư lao',111),
            (13,'Mất ngủ không thực tổn','Thất miên',131),
            (14,'Rối loạn chức năng tiền đình','Huyễn vựng',142),
            (15,'Nhồi máu não','Trúng phong thiên khô',153),
            (16,'Xuất huyết não','Trúng phong',173),
        ]
    },
]

BAD_CHAR_MAP = str.maketrans({
    'Ƣ':'Ư','ƣ':'ư','Õ':'Ò','Ö':'Ú','Ð':'Đ',
})
BAD_MARKERS = ['Ƣ','ƣ','Õ','Ö','Ð']

@dataclass
class Line:
    page_pdf: int
    page_doc: int
    text: str
    y0: float
    y1: float
    x0: float
    x1: float
    max_size: float
    bold: bool
    line_order: int


def fix_encoding(s: str) -> str:
    s = s.translate(BAD_CHAR_MAP)
    s = unicodedata.normalize('NFC', s)
    # Sửa khoảng trắng nhưng giữ nội dung nguyên gốc về mặt từ ngữ.
    s = re.sub(r'[ \t]+', ' ', s).strip()
    return s


def norm_match(s: str) -> str:
    s = fix_encoding(s).upper()
    s = s.replace('–','-').replace('—','-')
    s = re.sub(r'[^0-9A-ZÀ-ỸĐ ]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def is_rotated(line_dict: dict) -> bool:
    dx, dy = line_dict.get('dir',(1.0,0.0))
    return abs(dy) > 0.05 or dx < 0.95


def extract_clean_lines(doc: fitz.Document, page_num_1: int, offset: int) -> List[Line]:
    p = doc[page_num_1-1]
    d = p.get_text('dict', sort=True)
    rows: List[Line] = []
    order=0
    for b in d['blocks']:
        if b.get('type') != 0:
            continue
        for l in b.get('lines',[]):
            if is_rotated(l):
                continue  # watermark xiên của SRC_002
            spans=l.get('spans',[])
            txt=''.join(sp.get('text','') for sp in spans).strip()
            if not txt:
                continue
            x0,y0,x1,y1=l['bbox']
            # Bỏ số trang footer đơn độc.
            if y0 > 790 and re.fullmatch(r'\d{1,3}', txt.strip()):
                continue
            # Bỏ dấu stamp username nếu có lọt vào text ngang.
            if 'tuannm.ydct_' in txt or 'Nguyen Manh Tuan_' in txt:
                continue
            txt=fix_encoding(txt)
            if not txt:
                continue
            max_size=max((float(sp.get('size',0)) for sp in spans), default=0.0)
            bold=any((int(sp.get('flags',0)) & 16) != 0 for sp in spans)
            order+=1
            rows.append(Line(page_num_1, page_num_1+offset, txt, y0,y1,x0,x1,max_size,bold,order))
    return rows


def find_disease_start(doc, cfg, disease_name: str, expected_doc_page: int) -> Tuple[int, int, List[Line]]:
    offset=cfg['pdf_to_document_page_offset']
    expected_pdf=expected_doc_page-offset
    target=norm_match(disease_name)
    candidates=[]
    for pdf_page in range(max(1, expected_pdf-2), min(len(doc), expected_pdf+2)+1):
        lines=extract_clean_lines(doc,pdf_page,offset)
        top=[ln for ln in lines if ln.y0<210]
        joined=norm_match(' '.join(ln.text for ln in top[:18]))
        has_i=any(norm_match(ln.text).startswith('I ĐẠI CƯƠNG') for ln in top[:18])
        if target in joined and has_i:
            candidates.append((pdf_page,lines))
    if not candidates:
        # fallback toàn file, nhưng vẫn yêu cầu mục I. Đại cương trên cùng trang.
        for pdf_page in range(1,len(doc)+1):
            lines=extract_clean_lines(doc,pdf_page,offset)
            top=[ln for ln in lines if ln.y0<210]
            joined=norm_match(' '.join(ln.text for ln in top[:18]))
            has_i=any(norm_match(ln.text).startswith('I ĐẠI CƯƠNG') for ln in top[:18])
            if target in joined and has_i:
                candidates.append((pdf_page,lines)); break
    if not candidates:
        raise RuntimeError(f"Không tìm thấy trang bắt đầu bệnh: {disease_name} in {cfg['source_id']}")
    pdf_page,lines=candidates[0]
    return pdf_page, pdf_page+offset, lines


def is_roman_heading(text: str, bold: bool, size: float) -> bool:
    t=fix_encoding(text)
    if not re.match(r'^(?:I|II|III|IV|V|VI|VII|VIII|IX|X)\.\s+', t):
        return False
    letters=[c for c in t if c.isalpha()]
    upper_ratio=(sum(1 for c in letters if c.isupper())/len(letters)) if letters else 0
    return bold and size>=11.5 and upper_ratio>=0.72


def is_reference_heading(text: str, bold: bool, size: float) -> bool:
    t=norm_match(text)
    return ('TÀI LIỆU THAM KHẢO' in fix_encoding(text).upper() or t=='TAI LIEU THAM KHAO') and (bold or size>=11.5)


def section_type(title: str) -> str:
    t=norm_match(title)
    if 'ĐẠI CƯƠNG' in fix_encoding(title).upper(): return 'dai_cuong'
    if 'NGUYÊN NHÂN' in fix_encoding(title).upper() or 'CƠ CHẾ BỆNH SINH' in fix_encoding(title).upper(): return 'nguyen_nhan_co_che'
    if 'THỂ LÂM SÀNG' in fix_encoding(title).upper() or 'ĐIỀU TRỊ THEO Y HỌC CỔ TRUYỀN' in fix_encoding(title).upper(): return 'the_lam_sang_dieu_tri_yhct'
    if 'ĐIỀU TRỊ Y HỌC HIỆN ĐẠI' in fix_encoding(title).upper() or 'KẾT HỢP ĐIỀU TRỊ' in fix_encoding(title).upper() or 'ĐIỀU TRỊ KẾT HỢP' in fix_encoding(title).upper(): return 'dieu_tri_yhhd_ket_hop'
    if 'TIẾN TRIỂN' in fix_encoding(title).upper() or 'BIẾN CHỨNG' in fix_encoding(title).upper(): return 'tien_trien_bien_chung'
    if 'PHÒNG' in fix_encoding(title).upper() or 'DỰ PHÒNG' in fix_encoding(title).upper() or 'KIỂM SOÁT BIẾN CHỨNG' in fix_encoding(title).upper(): return 'phong_benh_du_phong'
    if 'TÀI LIỆU THAM KHẢO' in fix_encoding(title).upper(): return 'tai_lieu_tham_khao'
    return 'khac'


def roman_to_int(s: str):
    vals={'I':1,'V':5,'X':10}
    total=0; prev=0
    for ch in reversed(s):
        v=vals.get(ch,0)
        if v<prev: total-=v
        else: total+=v; prev=v
    return total or None

def detect_headings(lines: List[Line]) -> List[Tuple[int,str]]:
    heads=[]
    i=0
    while i<len(lines):
        ln=lines[i]
        if is_roman_heading(ln.text,ln.bold,ln.max_size) or is_reference_heading(ln.text,ln.bold,ln.max_size):
            title=ln.text
            # nối heading xuống dòng nếu dòng kế tiếp cùng trang, bold, uppercase, sát nhau và không phải heading mới.
            if i+1<len(lines):
                nx=lines[i+1]
                same_page=nx.page_pdf==ln.page_pdf
                letters=[c for c in nx.text if c.isalpha()]
                upper_ratio=(sum(1 for c in letters if c.isupper())/len(letters)) if letters else 0
                if same_page and nx.bold and nx.max_size>=11.5 and upper_ratio>=0.75 and nx.y0-ln.y1<28 and not re.match(r'^(?:I|II|III|IV|V|VI|VII|VIII|IX|X)\.\s+',nx.text):
                    # chỉ nối khi dòng hiện tại trông như heading chưa hoàn chỉnh hoặc dòng kế tiếp rất ngắn.
                    if len(nx.text)<90 and not nx.text.startswith(('1.','2.','3.','4.','5.','6.','7.','8.','9.')):
                        title = title + ' ' + nx.text
                        heads.append((i,title))
                        i+=2
                        continue
            heads.append((i,title))
        i+=1
    # loại heading lặp sai do continuation đã được tính như nội dung: chỉ giữ thứ tự đầu tiên theo index
    out=[]; seen_idx=set()
    for idx,t in heads:
        if idx not in seen_idx:
            out.append((idx,t)); seen_idx.add(idx)
    return out


def find_first_section_idx(lines: List[Line]) -> int:
    for i,ln in enumerate(lines):
        if is_roman_heading(ln.text,ln.bold,ln.max_size) and norm_match(ln.text).startswith('I ĐẠI CƯƠNG'):
            return i
    return 0


def make_chunks(section_lines: List[Line], disease_title: str, section_title: str, max_chars=2800, overlap_chars=250):
    # Chunk theo line source, không phát sinh câu mới. overlap cũng theo nguyên line.
    chunks=[]
    i=0
    while i<len(section_lines):
        start=i
        total=0
        end=i
        while end<len(section_lines):
            add=len(section_lines[end].text)+(1 if total else 0)
            if total>0 and total+add>max_chars:
                break
            total+=add; end+=1
        if end==start:
            end=start+1
        selected=section_lines[start:end]
        source_text='\n'.join(x.text for x in selected).strip()
        retrieval_text=f"{disease_title}\n{section_title}\n{source_text}".strip()
        chunks.append((start,end,selected,source_text,retrieval_text))
        if end>=len(section_lines):
            break
        # overlap đủ ~250 ký tự, không cắt giữa dòng
        back=end
        ov=0
        while back>start:
            cand=section_lines[back-1]
            if ov+len(cand.text)>overlap_chars and ov>0:
                break
            ov+=len(cand.text)+1
            back-=1
        i=max(back,start+1)
    return chunks


def write_csv(path: Path, rows: List[Dict], fieldnames: List[str]):
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fieldnames,extrasaction='ignore')
        w.writeheader(); w.writerows(rows)


doc_rows=[]; disease_rows=[]; section_rows=[]; chunk_rows=[]; page_rows=[]; excluded_rows=[]
qa={'version':'v0.1','sources':{},'global':{},'warnings':[]}
anomaly_rows=[]

for cfg in SOURCE_CONFIGS:
    doc=fitz.open(cfg['path'])
    sid=cfg['source_id']; offset=cfg['pdf_to_document_page_offset']
    all_page_lines={p:extract_clean_lines(doc,p,offset) for p in range(1,len(doc)+1)}
    starts=[]
    for idx,name,yhct,expected_doc_page in cfg['diseases']:
        pdf_p,doc_p,_=find_disease_start(doc,cfg,name,expected_doc_page)
        starts.append((idx,name,yhct,expected_doc_page,pdf_p,doc_p))
    # QA expected start page and monotonic
    start_page_mismatch=[x for x in starts if x[3]!=x[5]]
    if cfg['appendix_start_pdf_page']:
        final_end=cfg['appendix_start_pdf_page']-1
    else:
        final_end=len(doc)
    disease_bounds=[]
    for j,x in enumerate(starts):
        end_pdf=(starts[j+1][4]-1) if j+1<len(starts) else final_end
        disease_bounds.append((*x,end_pdf,end_pdf+offset))

    # excluded pages
    first_start=starts[0][4]
    for p in range(1,first_start):
        excluded_rows.append({'source_id':sid,'pdf_page':p,'document_page':p+offset,'reason':'front_matter'})
    if cfg['appendix_start_pdf_page']:
        for p in range(cfg['appendix_start_pdf_page'],len(doc)+1):
            excluded_rows.append({'source_id':sid,'pdf_page':p,'document_page':p+offset,'reason':'appendix_drug_list'})

    # page stats
    for p in range(1,len(doc)+1):
        ls=all_page_lines[p]
        page_rows.append({
            'source_id':sid,'pdf_page':p,'document_page':p+offset,'clean_line_count':len(ls),
            'clean_char_count':sum(len(x.text) for x in ls),
            'contains_bad_encoding_marker':int(any(any(m in x.text for m in BAD_MARKERS) for x in ls))
        })

    source_stats={'pdf_pages':len(doc),'expected_diseases':len(cfg['diseases']),'detected_diseases':len(starts),
                  'start_page_mismatches':len(start_page_mismatch),'diseases':[]}

    for idx,name,yhct,expected_doc_page,start_pdf,start_doc,end_pdf,end_doc in disease_bounds:
        disease_id=f'{sid}_D{idx:02d}'
        full_title=f'{name} ({yhct})' if yhct else name
        lines=[]
        for p in range(start_pdf,end_pdf+1):
            lines.extend(all_page_lines[p])
        first_sec=find_first_section_idx(lines)
        title_lines=lines[:first_sec]
        body_lines=lines[first_sec:]
        heads=detect_headings(body_lines)
        if not heads or not norm_match(heads[0][1]).startswith('I ĐẠI CƯƠNG'):
            qa['warnings'].append(f'{disease_id}: không nhận được I. ĐẠI CƯƠNG làm section đầu')
        # nếu có text trước heading đầu trong body (hiếm), tạo khac; nhưng first_sec đã trỏ đúng I.
        disease_rows.append({
            'disease_id':disease_id,'source_id':sid,'disease_index':idx,'disease_name':name,'yhct_name':yhct,
            'full_title':full_title,'pdf_page_start':start_pdf,'pdf_page_end':end_pdf,
            'document_page_start':start_doc,'document_page_end':end_doc,
            'expected_document_page_start_from_toc':expected_doc_page,
            'title_line_count':len(title_lines),'body_clean_line_count':len(body_lines),
            'body_clean_char_count':sum(len(x.text) for x in body_lines)
        })
        # split sections by heading indices
        sec_records=[]
        for hidx,(line_idx,title) in enumerate(heads):
            next_idx=heads[hidx+1][0] if hidx+1<len(heads) else len(body_lines)
            sec_lines=body_lines[line_idx:next_idx]
            if not sec_lines: continue
            stype=section_type(title)
            section_id=f'{disease_id}_S{hidx+1:02d}'
            secrow={
                'section_id':section_id,'disease_id':disease_id,'source_id':sid,'section_index':hidx+1,
                'section_title':title,'section_type':stype,
                'pdf_page_start':sec_lines[0].page_pdf,'pdf_page_end':sec_lines[-1].page_pdf,
                'document_page_start':sec_lines[0].page_doc,'document_page_end':sec_lines[-1].page_doc,
                'line_count':len(sec_lines),'char_count':sum(len(x.text) for x in sec_lines),
                'retrieval_enabled':0 if stype=='tai_lieu_tham_khao' else 1
            }
            section_rows.append(secrow); sec_records.append((secrow,sec_lines))
            # chunks
            cks=make_chunks(sec_lines,full_title,title)
            for cidx,(a,b,selected,source_text,retrieval_text) in enumerate(cks,1):
                chunk_id=f'{section_id}_C{cidx:03d}'
                chunk_rows.append({
                    'chunk_id':chunk_id,'source_id':sid,'disease_id':disease_id,'section_id':section_id,
                    'disease_name':name,'yhct_name':yhct,'section_title':title,'section_type':stype,
                    'chunk_index_in_section':cidx,
                    'pdf_page_start':selected[0].page_pdf,'pdf_page_end':selected[-1].page_pdf,
                    'document_page_start':selected[0].page_doc,'document_page_end':selected[-1].page_doc,
                    'source_file':cfg['path'].name,'source_year':cfg['year'],
                    'source_ref':f"{sid}:pdf{selected[0].page_pdf}-pdf{selected[-1].page_pdf}",
                    'retrieval_enabled':0 if stype=='tai_lieu_tham_khao' else 1,
                    'source_line_count':len(selected),'source_char_count':len(source_text),
                    'word_count':len(re.findall(r'\S+',source_text)),
                    'sha256':hashlib.sha256(source_text.encode('utf-8')).hexdigest(),
                    'source_text':source_text,'retrieval_text':retrieval_text,
                    '_start_line_in_section':a,'_end_line_in_section':b
                })
        # Phát hiện số thứ tự Roman bất thường trong chính tài liệu nguồn; không tự sửa.
        roman_seq=[]
        for secrow,_sec_lines in sec_records:
            m=re.match(r'^((?:I|II|III|IV|V|VI|VII|VIII|IX|X))\.\s+', secrow['section_title'])
            if m:
                roman_seq.append((secrow,m.group(1),roman_to_int(m.group(1))))
        for pos,(secrow,roman,rv) in enumerate(roman_seq, start=1):
            expected=pos
            kind='roman_sequence_anomaly' if rv!=expected else None
            if kind:
                anomaly_rows.append({
                    'source_id':sid,'disease_id':disease_id,'pdf_page':secrow['pdf_page_start'],
                    'section_title':secrow['section_title'],'anomaly_type':kind,
                    'observed_roman':roman,'observed_value':rv,'expected_value':expected,
                    'action':'preserved_source_no_auto_fix'
                })

        # coverage QA by section lines: every body line belongs to exactly one section range, except continuation-line quirk can be duplicated only as content if title continued.
        section_total=sum(len(x[1]) for x in sec_records)
        disease_info={
            'disease_id':disease_id,'start_pdf':start_pdf,'end_pdf':end_pdf,'sections':len(sec_records),
            'body_lines':len(body_lines),'section_lines_total':section_total,
            'first_section':sec_records[0][0]['section_title'] if sec_records else None,
            'has_references':any(x[0]['section_type']=='tai_lieu_tham_khao' for x in sec_records)
        }
        source_stats['diseases'].append(disease_info)

    source_stats['section_count']=sum(1 for x in section_rows if x['source_id']==sid)
    source_stats['chunk_count']=sum(1 for x in chunk_rows if x['source_id']==sid)
    source_stats['retrieval_chunk_count']=sum(1 for x in chunk_rows if x['source_id']==sid and x['retrieval_enabled']==1)
    source_stats['reference_chunk_count']=sum(1 for x in chunk_rows if x['source_id']==sid and x['retrieval_enabled']==0)
    source_stats['clean_body_pages']=sum((b[6]-b[4]+1) for b in disease_bounds)
    qa['sources'][sid]=source_stats
    doc_rows.append({
        'source_id':sid,'source_file':cfg['path'].name,'title':cfg['title'],'year':cfg['year'],
        'pdf_pages':len(doc),'pdf_to_document_page_offset':offset,
        'disease_count':len(starts),'body_pdf_page_start':starts[0][4],'body_pdf_page_end':final_end,
        'body_document_page_start':starts[0][5],'body_document_page_end':final_end+offset
    })

# ---------- Global QA ----------
# remove internal indices before export after using for QA
chunk_ids=[x['chunk_id'] for x in chunk_rows]
section_ids=[x['section_id'] for x in section_rows]
disease_ids=[x['disease_id'] for x in disease_rows]
qa['global']['disease_count']=len(disease_rows)
qa['global']['section_count']=len(section_rows)
qa['global']['chunk_count']=len(chunk_rows)
qa['global']['retrieval_chunk_count']=sum(x['retrieval_enabled'] for x in chunk_rows)
qa['global']['reference_chunk_count']=len(chunk_rows)-qa['global']['retrieval_chunk_count']
qa['global']['unique_disease_ids']=len(set(disease_ids))
qa['global']['unique_section_ids']=len(set(section_ids))
qa['global']['unique_chunk_ids']=len(set(chunk_ids))
qa['global']['duplicate_disease_ids']=len(disease_ids)-len(set(disease_ids))
qa['global']['duplicate_section_ids']=len(section_ids)-len(set(section_ids))
qa['global']['duplicate_chunk_ids']=len(chunk_ids)-len(set(chunk_ids))
qa['global']['empty_chunks']=sum(1 for x in chunk_rows if not x['source_text'].strip())
qa['global']['invalid_page_ranges']=sum(1 for x in chunk_rows if x['pdf_page_start']>x['pdf_page_end'] or x['document_page_start']>x['document_page_end'])
qa['global']['bad_encoding_chunks']=sum(1 for x in chunk_rows if any(m in x['source_text'] for m in BAD_MARKERS))
qa['global']['watermark_leak_chunks']=sum(1 for x in chunk_rows if 'tuannm.ydct_' in x['source_text'] or 'Nguyen Manh Tuan_' in x['source_text'])
qa['global']['max_chunk_chars']=max(x['source_char_count'] for x in chunk_rows)
qa['global']['median_chunk_chars']=int(statistics.median(x['source_char_count'] for x in chunk_rows))
qa['global']['mean_chunk_chars']=round(statistics.mean(x['source_char_count'] for x in chunk_rows),1)
qa['global']['max_chunk_words']=max(x['word_count'] for x in chunk_rows)
qa['global']['median_chunk_words']=int(statistics.median(x['word_count'] for x in chunk_rows))
qa['global']['metadata_missing_chunks']=sum(1 for x in chunk_rows if not all(str(x[k]).strip() for k in ['chunk_id','source_id','disease_id','section_id','source_file','source_ref','section_title']))
# section first-heading QA and line coverage exact
qa['global']['diseases_without_first_I_dai_cuong']=sum(1 for s in qa['sources'].values() for d in s['diseases'] if not norm_match(d['first_section'] or '').startswith('I ĐẠI CƯƠNG'))
qa['global']['diseases_section_line_mismatch']=sum(1 for s in qa['sources'].values() for d in s['diseases'] if d['body_lines']!=d['section_lines_total'])

# verify each chunk's source_text can be reconstructed exactly from line slices inside its section data export model.
# Our construction is direct; stronger hash/retrieval verification: recompute hash and no accidental mutation.
qa['global']['hash_mismatch_chunks']=sum(1 for x in chunk_rows if hashlib.sha256(x['source_text'].encode('utf-8')).hexdigest()!=x['sha256'])

# export CSVs
write_csv(OUTDIR/'documents.csv',doc_rows,list(doc_rows[0].keys()))
write_csv(OUTDIR/'diseases.csv',disease_rows,list(disease_rows[0].keys()))
write_csv(OUTDIR/'sections.csv',section_rows,list(section_rows[0].keys()))
# drop internal fields
chunk_export=[]
for x in chunk_rows:
    y={k:v for k,v in x.items() if not k.startswith('_')}
    chunk_export.append(y)
write_csv(OUTDIR/'chunks.csv',chunk_export,list(chunk_export[0].keys()))
write_csv(OUTDIR/'page_stats.csv',page_rows,list(page_rows[0].keys()))
write_csv(OUTDIR/'excluded_pages.csv',excluded_rows,list(excluded_rows[0].keys()))
if anomaly_rows:
    write_csv(OUTDIR/'source_structure_anomalies.csv',anomaly_rows,list(anomaly_rows[0].keys()))
else:
    (OUTDIR/'source_structure_anomalies.csv').write_text('source_id,disease_id,pdf_page,section_title,anomaly_type,observed_roman,observed_value,expected_value,action\n',encoding='utf-8-sig')
qa['global']['source_structure_anomaly_count']=len(anomaly_rows)
with (OUTDIR/'chunks.jsonl').open('w',encoding='utf-8') as f:
    for x in chunk_export:
        f.write(json.dumps(x,ensure_ascii=False)+'\n')
with (OUTDIR/'qa_summary.json').open('w',encoding='utf-8') as f:
    json.dump(qa,f,ensure_ascii=False,indent=2)

# QA report
lines=[]
lines.append('# QA REPORT - SRC_001 + SRC_002 corpus preprocessing v0.1')
lines.append('')
lines.append('## Phạm vi')
lines.append('- Chỉ xử lý phần 36 bệnh trong SRC_001 và SRC_002.')
lines.append('- Không chunk phần front matter; SRC_001 cũng loại danh mục dược liệu cuối tài liệu (đã có nguồn chuẩn hóa riêng).')
lines.append('- Xóa watermark xiên/stamp và số trang footer khỏi text; sửa các lỗi mã hóa ký tự rõ ràng của PDF 2025 (ví dụ Ƣ→Ư, ƣ→ư).')
lines.append('')
lines.append('## Kết quả định lượng')
lines.append(f"- Bệnh: {qa['global']['disease_count']} (SRC_001=20, SRC_002=16).")
lines.append(f"- Section: {qa['global']['section_count']}.")
lines.append(f"- Chunk tổng: {qa['global']['chunk_count']}; dùng retrieval: {qa['global']['retrieval_chunk_count']}; tài liệu tham khảo (flag không retrieval): {qa['global']['reference_chunk_count']}.")
lines.append(f"- Độ dài chunk: median {qa['global']['median_chunk_chars']} ký tự / {qa['global']['median_chunk_words']} từ; mean {qa['global']['mean_chunk_chars']} ký tự; max {qa['global']['max_chunk_chars']} ký tự.")
lines.append('')
lines.append('## Kiểm tra ngược')
checks=[
('Disease ID trùng',qa['global']['duplicate_disease_ids']),('Section ID trùng',qa['global']['duplicate_section_ids']),('Chunk ID trùng',qa['global']['duplicate_chunk_ids']),('Chunk rỗng',qa['global']['empty_chunks']),('Page range sai',qa['global']['invalid_page_ranges']),('Ký tự mã hóa lỗi còn sót',qa['global']['bad_encoding_chunks']),('Watermark/stamp còn sót',qa['global']['watermark_leak_chunks']),('Metadata thiếu',qa['global']['metadata_missing_chunks']),('Hash mismatch',qa['global']['hash_mismatch_chunks']),('Bệnh không bắt đầu bằng I. ĐẠI CƯƠNG',qa['global']['diseases_without_first_I_dai_cuong']),('Mismatch số line body vs section',qa['global']['diseases_section_line_mismatch']),('Bất thường số thứ tự section trong nguồn',qa['global']['source_structure_anomaly_count'])]
for name,val in checks:
    lines.append(f"- {name}: {val}")
lines.append('')
lines.append('## Đối chiếu trang bắt đầu theo Mục lục')
for sid,ss in qa['sources'].items():
    lines.append(f"- {sid}: {ss['detected_diseases']}/{ss['expected_diseases']} bệnh; sai trang bắt đầu so với Mục lục = {ss['start_page_mismatches']}.")
lines.append('')
lines.append('## Quy tắc provenance')
lines.append('- Mỗi chunk giữ source_id, tên file, năm, disease_id, section_id, page PDF và page hiển thị của tài liệu.')
lines.append('- source_text chỉ gồm text được lấy từ PDF sau bước làm sạch kỹ thuật; retrieval_text chỉ thêm tiêu đề bệnh + section phía trước source_text để dùng cho embedding/retrieval.')
lines.append('- TÀI LIỆU THAM KHẢO vẫn được lưu nhưng retrieval_enabled=0 để tránh retrieval lấy danh mục tài liệu thay vì nội dung chuyên môn.')
lines.append('')
if qa['warnings']:
    lines.append('## Cảnh báo')
    lines.extend('- '+w for w in qa['warnings'])
else:
    lines.append('## Cảnh báo')
    lines.append('- Không có cảnh báo cấu trúc trong lần chạy này.')
(OUTDIR/'QA_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')

readme=f'''# ViMedGraph SRC_001 + SRC_002 Corpus v0.1

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
'''
(OUTDIR/'README.md').write_text(readme,encoding='utf-8')

print(json.dumps(qa['global'],ensure_ascii=False,indent=2))
for sid,ss in qa['sources'].items():
    print(sid, {k:ss[k] for k in ['pdf_pages','expected_diseases','detected_diseases','start_page_mismatches','section_count','chunk_count','retrieval_chunk_count','reference_chunk_count','clean_body_pages']})
