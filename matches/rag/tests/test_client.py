import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
APP=Path(__file__).resolve().parents[1]/'app';sys.path.insert(0,str(APP));MODULE=importlib.util.find_spec('rag_transport')
if MODULE:import rag_transport

class ClientTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(MODULE,'RAG socket transport has not been implemented')
    def test_index_and_fresh_query_processes_use_one_service(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);socket=root/'rag.sock';requests=[]
            def handle(payload):
                requests.append(payload)
                if payload['action']=='index':return {'documents':1,'skipped':0}
                return {'answer':'87','citations':['spec.txt'],'confidence':.9}
            server=rag_transport.make_server(socket,handle);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            env={**os.environ,'RAG_SOCKET':str(socket),'RAG_OUTPUT_DIR':str(root/'out')}
            try:
                p=subprocess.run([sys.executable,str(APP/'app.py'),'--index','/app/corpus'],env=env,capture_output=True,text=True,timeout=3);self.assertEqual(p.returncode,0,p.stderr)
                for qid in ['query_01','q.02']:
                    p=subprocess.run([sys.executable,str(APP/'app.py'),'--corpus','/app/corpus','--query-id',qid,'--query','Maximum temperature?'],env=env,capture_output=True,text=True,timeout=3)
                    self.assertEqual(p.returncode,0,p.stderr);data=json.loads((root/'out'/(qid+'_output.json')).read_text());self.assertEqual(data['citations'],['spec.txt'])
                self.assertEqual([r['action'] for r in requests],['index','query','query'])
            finally:server.shutdown();server.server_close();thread.join(timeout=2)

    def test_backend_failure_still_writes_both_required_fields(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);env={**os.environ,'RAG_SOCKET':str(root/'missing'),'RAG_OUTPUT_DIR':d,'RAG_QUERY_TIMEOUT':'.2'}
            p=subprocess.run([sys.executable,str(APP/'app.py'),'--corpus','/app/corpus','--query-id','q_01','--query','Price?'],env=env,capture_output=True,text=True,timeout=3)
            self.assertNotEqual(p.returncode,0);data=json.loads((root/'q_01_output.json').read_text());self.assertEqual(data['answer'],'');self.assertEqual(data['citations'],[])

if __name__=='__main__':unittest.main()
