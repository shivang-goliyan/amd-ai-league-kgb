"""Exact grader invocation contract; this client never loads model weights."""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from rag_transport import request


def main():
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True);group.add_argument('--index',type=Path);group.add_argument('--query');parser.add_argument('--corpus',type=Path);parser.add_argument('--query-id');args=parser.parse_args()
    socket=os.getenv('RAG_SOCKET','/tmp/league-rag.sock')
    if args.index is not None:
        result=request(socket,{'action':'index','corpus':str(args.index)},timeout=540)
        if result.get('error'):raise RuntimeError(result['error'])
        print(json.dumps(result));return 0
    if args.corpus is None or not args.query_id:parser.error('Queries require --corpus and --query-id')
    if Path(args.query_id).name!=args.query_id or args.query_id in ('.','..'):parser.error('Invalid query-id')
    status=0
    try:
        result=request(socket,{'action':'query','corpus':str(args.corpus),'query':args.query},timeout=float(os.getenv('RAG_QUERY_TIMEOUT','24')))
        if result.get('error'):raise RuntimeError(result['error'])
    except Exception as exc:
        print('RAG query failed: '+str(exc),file=sys.stderr);result={'answer':'','citations':[],'confidence':0.0};status=1
    out=Path(os.getenv('RAG_OUTPUT_DIR','/app/output'));out.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.',suffix='.tmp',dir=out)
    try:
        with os.fdopen(fd,'w',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False);f.write('\n')
        os.replace(tmp,out/(args.query_id+'_output.json'))
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return status

if __name__=='__main__':sys.exit(main())
