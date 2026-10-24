"""Run against an already-started native ROCm service or its running container.

This checks public illustration images only; a perfect public-sample score is
not a claim about the private evaluation set. Image references are CLI inputs.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def normalize(text):
    return ''.join(c for c in text.upper() if not c.isspace() and c not in '-.·_')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--samples',type=Path,required=True)
    parser.add_argument('--container',help='An existing running container with samples mounted at /app/input')
    parser.add_argument('--app',type=Path,default=Path('/app/app.py'))
    parser.add_argument('--output',type=Path,default=Path('/app/output'))
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--kind',choices=['official-public-illustration-only','synthetic-held-out'],default='official-public-illustration-only')
    args=parser.parse_args();cases=json.loads((args.samples/'expected.json').read_text());results=[]
    for case in cases:
        started=time.monotonic();error='';actual='';code=None
        try:
            if args.container:
                cmd=['docker','exec',args.container,'python3','/app/app.py','--input-image','/app/input/'+case['file']]
            else:
                cmd=[sys.executable,str(args.app),'--input-image',str(args.samples/case['file'])]
            result=subprocess.run(cmd,capture_output=True,text=True,timeout=29)
            code=result.returncode
            output_file=Path(case['file']).stem+'_output.json'
            if args.container:
                raw=subprocess.check_output(['docker','exec',args.container,'cat','/app/output/'+output_file],text=True,timeout=2)
            else:raw=(args.output/output_file).read_text()
            actual=json.loads(raw)['text'];assert isinstance(actual,str)
            error=result.stderr[-1000:] if code else ''
        except Exception as exc:error=str(exc)
        elapsed=time.monotonic()-started
        passed=code==0 and elapsed<30 and normalize(actual)==normalize(case['text'])
        row={'file':case['file'],'expected':case['text'],'actual':actual,'seconds':elapsed,'returncode':code,'pass':passed,'error':error}
        results.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
    report={'kind':args.kind,'sample_count':len(cases),'passed':sum(r['pass'] for r in results),'results':results,'max_latency_seconds':max(r['seconds'] for r in results)}
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return 0 if report['passed']==len(cases) else 1

if __name__=='__main__':sys.exit(main())
