"""Exploratory page-retrieval benchmark: 30 queries / 15 paired intents."""
import json,re,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from corpus import weighted_matches
from rank_bm25 import BM25Okapi
import numpy as np
root=Path(__file__).resolve().parents[1]
all_rows=json.loads((root/'data/chunks.json').read_text())
rows=[r for r in all_rows if '(cid:' not in r['content']]
tests=json.loads((root/'experiments/queries.json').read_text())
def tokens(s):return re.findall(r'[a-z0-9]+',s.lower())
bm=BM25Okapi([tokens(r['content']) for r in rows]);details=[]
for q in tests:
 scores=np.array(bm.get_scores(tokens(q['query'])))
 boosts=np.array([3*(r.get('device_category')==q['category'])+2*(r.get('brand','').lower()==q['brand'].lower()) for r in rows])
 rankings={'lexical':weighted_matches(rows,q['query']), 'bm25':[rows[i] for i in np.argsort(-scores,kind='stable')], 'bm25_metadata':[rows[i] for i in np.argsort(-(scores+boosts),kind='stable')]}
 rankings['bm25_exact_manual']=[r for r in rankings['bm25'] if r['title']==q['title']]
 for method,ranking in rankings.items():
  def relevant(r):return r['title']==q['title'] and r['page'] in q['pages']
  rank=next((i+1 for i,r in enumerate(ranking) if relevant(r)),None)
  details.append(dict(query_id=q['id'],group=q['group'],query=q['query'],method=method,hit_at_3=any(relevant(r) for r in ranking[:3]),reciprocal_rank=1/rank if rank else 0,wrong_category_at_3=sum(r['device_category']!=q['category'] for r in ranking[:3]),top3=[{k:r[k] for k in ['id','title','page','content']} for r in ranking[:3]]))
metrics={}
for method in rankings:
 d=[r for r in details if r['method']==method];metrics[method]=dict(queries=len(d),hit_at_3=sum(r['hit_at_3'] for r in d)/len(d),mrr=sum(r['reciprocal_rank'] for r in d)/len(d),wrong_category_top3_rate=sum(r['wrong_category_at_3'] for r in d)/(3*len(d)))
result=dict(corpus_sha256=hashlib.sha256((root/'data/chunks.json').read_bytes()).hexdigest(), query_sha256=hashlib.sha256((root/'experiments/queries.json').read_bytes()).hexdigest(), exact_manual_assumption='Oracle diagnostic: correct manual title supplied from labels; not automatic model recognition', raw_chunks=len(all_rows),usable_chunks=len(rows),excluded_cid_chunks=len(all_rows)-len(rows),caveat='One TP-Link manual; 30 English queries from 15 paired intents. Exploratory, not held-out or six-scenario evaluation.',metrics=metrics,details=details)
(root/'experiments/retrieval-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(metrics,indent=2))
