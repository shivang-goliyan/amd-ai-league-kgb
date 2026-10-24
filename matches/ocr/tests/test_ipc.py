"""Exercise real Unix sockets and separate CLI processes without downloading model weights."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
APP=Path(__file__).resolve().parents[1]/'app';sys.path.insert(0,str(APP))
MODULE=importlib.util.find_spec('service')
if MODULE:import service

class IPCTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(MODULE,'Resident OCR service has not been implemented')

    def test_multiple_fresh_clients_reuse_one_service(self):
        with tempfile.TemporaryDirectory() as d:
            socket=Path(d)/'ocr.sock';calls=[]
            def recognize(path):
                calls.append(path)
                return {'text':'京 A·12345','confidence':.9}
            server=service.make_server(socket,recognize)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                for name in ['one.png','two.tiff']:
                    env={**os.environ,'OCR_SOCKET':str(socket),'OCR_OUTPUT_DIR':str(Path(d)/'output')}
                    proc=subprocess.run([sys.executable,str(APP/'app.py'),'--input-image','/app/input/'+name],env=env,capture_output=True,text=True,timeout=5)
                    self.assertEqual(proc.returncode,0,proc.stderr)
                    p=Path(d)/'output'/(Path(name).stem+'_output.json')
                    self.assertEqual(json.loads(p.read_text())['text'],'京 A·12345')
                self.assertEqual(calls,['/app/input/one.png','/app/input/two.tiff'])
            finally:server.shutdown();server.server_close();thread.join(timeout=2)

    def test_missing_server_still_writes_failure_json(self):
        with tempfile.TemporaryDirectory() as d:
            env={**os.environ,'OCR_SOCKET':str(Path(d)/'missing.sock'),'OCR_OUTPUT_DIR':d,'OCR_CLIENT_TIMEOUT':'0.2'}
            proc=subprocess.run([sys.executable,str(APP/'app.py'),'--input-image','/app/input/error.jpg'],env=env,capture_output=True,text=True,timeout=3)
            self.assertNotEqual(proc.returncode,0)
            self.assertEqual(json.loads((Path(d)/'error_output.json').read_text())['text'],'')

    def test_recognition_error_does_not_kill_service(self):
        with tempfile.TemporaryDirectory() as d:
            socket=Path(d)/'ocr.sock'
            def recognize(path):
                if path.endswith('broken'):raise ValueError('bad image')
                return {'text':'STOP','confidence':1}
            server=service.make_server(socket,recognize);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                self.assertIn('error',service.request(socket,{'image':'broken'},timeout=1))
                self.assertEqual(service.request(socket,{'image':'good'},timeout=1)['text'],'STOP')
            finally:server.shutdown();server.server_close();thread.join(timeout=2)

if __name__=='__main__':unittest.main()
