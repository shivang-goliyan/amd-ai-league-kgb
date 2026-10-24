"""Reject fabricated evidence and retain source files supporting the selected value."""
import re
from retrieval import identifiers,tokens

REFUSAL={'answer':'','citations':[],'confidence':0.0}

def _collapse(text):return ' '.join(text.split()).casefold()

def _contains_value(value,text):
    if re.fullmatch(r'\d+(?:\.\d+)?',value):
        return bool(re.search(r'(?<![\w.])'+re.escape(value)+r'(?![\d.])',text))
    norm=lambda s:''.join(c for c in s.upper() if c not in '-.·_')
    v=''.join(norm(value).split());source=norm(text)
    pattern=r'(?<!\w)'+r'\s*'.join(re.escape(c) for c in v)+r'(?!\w)'
    return bool(v and re.search(pattern,source))


def verify(proposal,documents,query):
    if not isinstance(proposal,dict) or not isinstance(proposal.get('answer'),str):return REFUSAL.copy()
    answer=proposal['answer'].strip()
    if not answer:return REFUSAL.copy()
    originals={d['file']:d['text'] for d in documents};proof=[]
    evidence=proposal.get('evidence',[])
    if not isinstance(evidence,list):return REFUSAL.copy()
    for item in evidence:
        if not isinstance(item,dict):continue
        file=item.get('file');quote=item.get('quote')
        if file not in originals or not isinstance(quote,str) or not quote.strip():continue
        if _collapse(quote) not in _collapse(originals[file]):continue
        proof.append({'file':file,'quote':quote,'role':item.get('role')})
    if re.fullmatch(r'Q[1-4]',answer,re.I):
        quarters=set()
        for item in proof:quarters.update(re.findall(r'\b'+re.escape(answer)+r'\s+(?:FY\s*\d{2,4}|20\d{2})\b',item['quote'],re.I))
        if len(quarters)!=1:return REFUSAL.copy()
        answer=quarters.pop()
    candidates=[p for p in proof if p['role']!='bridge' and _contains_value(answer,p['quote'])]
    if not candidates:return REFUSAL.copy()
    query_words=set(tokens(query))
    primary=max(candidates,key=lambda p:len(query_words & set(tokens(p['quote']))))
    retained=[primary];known=identifiers(primary['quote'])-identifiers(query)
    bridges=[p for p in proof if p not in candidates or p['role']=='bridge']
    changed=True
    while changed:
        changed=False
        for item in bridges:
            if item in retained:continue
            ids=identifiers(item['quote'])-identifiers(query)
            if ids & known:
                retained.append(item);known|=ids;changed=True
    confidence=proposal.get('confidence',0.0)
    confidence=max(0,min(1,float(confidence))) if isinstance(confidence,(int,float)) else 0.0
    return {'answer':answer,'citations':sorted({p['file'] for p in retained}),'confidence':confidence}
