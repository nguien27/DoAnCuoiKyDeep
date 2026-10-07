from pathlib import Path
import pandas as pd, json, sys
BASE=Path(__file__).resolve().parent
e=pd.read_csv(BASE/"text_entities.csv")
r=pd.read_csv(BASE/"text_relations.csv")
ge=pd.read_csv(BASE/"extraction_gold_entities.csv")
gr=pd.read_csv(BASE/"extraction_gold_relations.csv")
def score(g,p):
    g=set(g); p=set(p)
    tp=len(g&p); fp=len(p-g); fn=len(g-p)
    precision=tp/(tp+fp) if tp+fp else 0
    recall=tp/(tp+fn) if tp+fn else 0
    f1=2*precision*recall/(precision+recall) if precision+recall else 0
    return dict(tp=tp,fp=fp,fn=fn,precision=precision,recall=recall,f1=f1)
entity_score=score(ge.entity_id,e.entity_id)
rel_score=score(list(zip(gr.head_id,gr.relation,gr.tail_id)),list(zip(r.head_id,r.relation,r.tail_id)))
nodes=set(e.entity_id)
dangling=sum((h not in nodes) or (t not in nodes) for h,t in zip(r.head_id,r.tail_id))
dupe_e=int(e.entity_id.duplicated().sum())
dupe_r=int(r.duplicated(["head_id","relation","tail_id"]).sum())
print("Entity:",entity_score)
print("Relation:",rel_score)
print("Duplicate entities:",dupe_e)
print("Duplicate relations:",dupe_r)
print("Dangling endpoints:",dangling)
if dangling or dupe_e or dupe_r:
    sys.exit(1)
