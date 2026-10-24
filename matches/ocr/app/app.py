"""The grader executes this lightweight client once per image."""
import argparse
import os
import sys
from pathlib import Path
from contract import write_answer
from service import request


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input-image',required=True);args=parser.parse_args()
    status=0
    try:
        answer=request(os.getenv('OCR_SOCKET','/tmp/league-ocr.sock'),{'image':args.input_image},timeout=float(os.getenv('OCR_CLIENT_TIMEOUT','24')))
        if answer.get('error'):raise RuntimeError(answer['error'])
    except Exception as exc:
        print('OCR request failed: '+str(exc),file=sys.stderr);answer={'text':'','confidence':0.0};status=1
    write_answer(args.input_image,answer,Path(os.getenv('OCR_OUTPUT_DIR','/app/output')))
    return status

if __name__=='__main__':sys.exit(main())
