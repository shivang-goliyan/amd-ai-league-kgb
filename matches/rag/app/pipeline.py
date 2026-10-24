"""Parse once, retain the index, retrieve and verify each independent query."""
import json
import os
import tempfile
from pathlib import Path
from documents import read_corpus
from retrieval import Index
from evidence import verify,REFUSAL


def parse_proposal(text):
    decoder=json.JSONDecoder()
    for i,char in enumerate(text):
        if char=='{':
            try:
                value,_=decoder.raw_decode(text[i:])
                if isinstance(value,dict):return value
            except ValueError:pass
    return {}


class Engine:
    def __init__(self,generate,ocr=None,index_dir=Path('/app/index')):
        self.generate=generate;self.ocr=ocr;self.index_dir=Path(index_dir);self.corpus=None;self.retriever=None;self.documents=[]

    def index(self,corpus):
        corpus=Path(corpus).resolve();documents,errors=read_corpus(corpus,self.ocr)
        self.index_dir.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(prefix='.documents-',suffix='.json',dir=self.index_dir)
        with os.fdopen(fd,'w',encoding='utf8') as f:json.dump({'corpus':str(corpus),'documents':documents},f,ensure_ascii=False)
        os.replace(tmp,self.index_dir/'documents.json')
        (self.index_dir/'skipped-files.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2))
        self.documents=documents;self.retriever=Index(documents);self.corpus=corpus
        return {'documents':len(documents),'skipped':len(errors)}

    def answer(self,corpus,question):
        if self.corpus!=Path(corpus).resolve() or self.retriever is None:raise RuntimeError('Index this corpus before querying it')
        context=self.retriever.context(question)
        if not context:return REFUSAL.copy()
        proposal=self.generate(question,context)
        return verify(proposal,self.documents,question)
