"""Bounded lexical retrieval preserving identifiers and late-file evidence."""
import math
import re
from collections import Counter

STOP=set('a an the what which who is are was were in on of for to from with and or does did when how by at it this that as'.split())
WORD=re.compile(r'[A-Za-z0-9]+(?:[-_.#][A-Za-z0-9]+)*#?|[\u3400-\u9fff]+')
ID=re.compile(r'\b[A-Z][A-Z0-9]*(?:[-_][A-Z0-9]+)+#?')


def tokens(text):
    result=[]
    for word in WORD.findall(text.casefold()):
        if word not in STOP:result.append(word)
        if re.search(r'[-_.#]',word):result.extend(x for x in re.findall(r'[a-z0-9]+',word) if x not in STOP)
    return result


def identifiers(text):return {x.casefold().rstrip('#') for x in ID.findall(text)}

class Index:
    def __init__(self,documents):
        self.documents=documents;self.chunks=[];self.df=Counter()
        for doc in documents:
            text=doc['text']
            for start in range(0,len(text),1500):
                span=text[start:start+1800]
                if not span.strip():continue
                count=Counter(tokens(span+' '+doc['file']));self.df.update(count.keys())
                self.chunks.append({'file':doc['file'],'text':span,'terms':count,'length':sum(count.values())})
        self.avg=sum(x['length'] for x in self.chunks)/max(1,len(self.chunks))

    def search(self,query,limit=12):
        terms=set(tokens(query));ranked=[];n=len(self.chunks)
        for ordinal,c in enumerate(self.chunks):
            score=0.0
            for term in terms:
                f=c['terms'].get(term,0)
                if f:
                    idf=math.log(1+(n-self.df[term]+.5)/(self.df[term]+.5))
                    score+=idf*f*2.2/(f+1.2*(.25+.75*c['length']/max(1,self.avg)))
            if score:ranked.append((score,-ordinal,c))
        ranked.sort(key=lambda x:(x[0],x[1]),reverse=True)
        return [{'file':c['file'],'text':c['text'],'score':s} for s,_,c in ranked[:limit]]

    def context(self,query,limit=20):
        primary=self.search(query,limit=min(10,limit));result=list(primary)
        bridge=set().union(*(identifiers(x['text']) for x in primary)) if primary else set()
        bridge-=identifiers(query)
        bridge=sorted(bridge,key=lambda x:self.df.get(x,0))[:12]
        if bridge:
            for chunk in self.search(' '.join(bridge),limit=limit):
                if not any(x['file']==chunk['file'] and x['text']==chunk['text'] for x in result):result.append(chunk)
                if len(result)>=limit:break
        return result[:limit]
