import asyncio
import gzip
import importlib.util
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
SPEC=importlib.util.find_spec('matches.web.core.fetching')
if SPEC:from matches.web.core.fetching import HTTPFetcher
from matches.web.core.agent import WebAgent


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        if self.path=='/redirect':
            self.send_response(302);self.send_header('Location','/contact');self.end_headers();return
        if self.path=='/slow':time.sleep(.2)
        content_type='text/html; charset=utf-8'
        body=b'<a href="/contact">Contact</a>'
        if self.path=='/contact':body=b'<p>Support phone: +1-555-0196</p>'
        if self.path=='/plain':content_type='text/plain; charset=iso-8859-1';body='München <Service>'.encode('iso-8859-1')
        if self.path=='/large':body=b'x'*128
        if self.path=='/binary':content_type='application/octet-stream';body=b'\x00\x01'
        if self.path=='/gzip-large':body=b'x'*128
        self.send_response(200);self.send_header('Content-Type',content_type)
        if self.path.startswith('/gzip'):
            body=gzip.compress(body);self.send_header('Content-Encoding','gzip')
        self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError):pass


class FetchingTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base='http://127.0.0.1:'+str(cls.server.server_port)
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def setUp(self):self.assertIsNotNone(SPEC,'Real bounded HTTP fetching has not been implemented')

    async def test_real_navigation_returns_the_source_that_contains_the_answer(self):
        async def decide(q,pages,remaining):
            if len(pages)==1:return {'answer':'','open_url':'/contact'}
            return {'answer':'+1-555-0196','evidence':[{'file':self.base+'/contact','quote':'Support phone: +1-555-0196'}]}
        result=await WebAgent(HTTPFetcher(),decide).retrieve('Support phone?',[self.base+'/'])
        self.assertEqual(result['answer'],'+1-555-0196');self.assertEqual(result['citations'],[self.base+'/contact'])

    async def test_redirect_records_the_final_source_url(self):
        result=await HTTPFetcher()(self.base+'/redirect',1)
        self.assertEqual(result['url'],self.base+'/contact');self.assertIn('0196',result['html'])

    async def test_plain_text_encoding_and_angle_brackets_are_preserved(self):
        from matches.web.core.pages import parse_page
        result=await HTTPFetcher()(self.base+'/plain',1)
        self.assertIn('München <Service>',parse_page(result['url'],result['html'])['text'])

    async def test_oversized_and_binary_responses_are_skipped(self):
        with self.assertRaises(ValueError):await HTTPFetcher(max_bytes=64)(self.base+'/large',1)
        with self.assertRaises(ValueError):await HTTPFetcher()(self.base+'/binary',1)

    async def test_network_timeout_is_bounded(self):
        start=time.monotonic()
        with self.assertRaises((TimeoutError,OSError)):await HTTPFetcher()(self.base+'/slow',.03)
        self.assertLess(time.monotonic()-start,.15)

    async def test_gzip_is_decoded_and_its_expanded_size_is_bounded(self):
        result=await HTTPFetcher()(self.base+'/gzip',1)
        self.assertIn('/contact',result['html'])
        with self.assertRaises(ValueError):await HTTPFetcher(max_bytes=64)(self.base+'/gzip-large',1)

    async def test_non_http_targets_and_embedded_credentials_are_rejected(self):
        for url in ['file:///etc/hosts','https://user:password@example.test/']:
            with self.assertRaises(ValueError):await HTTPFetcher()(url,1)


if __name__=='__main__':unittest.main()
