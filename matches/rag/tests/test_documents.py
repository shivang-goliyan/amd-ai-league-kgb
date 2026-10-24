import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
APP=Path(__file__).resolve().parents[1]/'app';sys.path.insert(0,str(APP));MODULE=importlib.util.find_spec('documents')
if MODULE:import documents

class DocumentTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(MODULE,'Defensive corpus reader has not been implemented')

    def test_bad_file_and_empty_directory_do_not_stop_walk(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'empty').mkdir();(root/'a.unknown').write_bytes(b'\x00\xff');(root/'broken.pdf').write_bytes(b'invalid PDF');(root/'good.txt').write_text('Maximum temperature: 87')
            docs,errors=documents.read_corpus(root)
            self.assertEqual([x['file'] for x in docs],['good.txt']);self.assertTrue(any(x['file']=='broken.pdf' for x in errors))

    def test_permission_zero_is_skipped_even_in_root_test_environment(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'denied.txt';p.write_text('private');p.chmod(0)
            try:
                docs,errors=documents.read_corpus(root)
                self.assertEqual(docs,[]);self.assertTrue(any(x['file']=='denied.txt' for x in errors))
            finally:p.chmod(0o600)

    def test_py_is_read_as_text_and_never_executed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);sentinel=root/'must-not-exist';(root/'service.py').write_text(f"from pathlib import Path\nPath({str(sentinel)!r}).touch()\nBATCH_TIMEOUT = 271\n")
            docs,_=documents.read_corpus(root);self.assertIn('271',docs[0]['text']);self.assertFalse(sentinel.exists())

    def test_withdrawn_document_is_excluded_without_excluding_its_replacement(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'product_r1_WITHDRAWN.txt').write_text('Limit 72');(root/'product_r2.txt').write_text('Supersedes the previous revision. Limit 87')
            docs,_=documents.read_corpus(root);self.assertEqual([x['file'] for x in docs],['product_r2.txt'])

    def test_csv_keeps_headers_with_each_row(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'tickets.csv').write_text('ticket,release\nBUG-918,5.6.7\n')
            docs,_=documents.read_corpus(root);text=docs[0]['text'];self.assertIn('ticket',text);self.assertIn('BUG-918',text);self.assertIn('release',text);self.assertIn('5.6.7',text)

    def test_images_are_read_through_the_vision_callback(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'label.png').write_bytes(b'fake image for callback plumbing')
            docs,_=documents.read_corpus(root,ocr=lambda p:'Board revision: REV-D7')
            self.assertEqual(docs[0]['file'],'label.png');self.assertIn('REV-D7',docs[0]['text'])

    def test_symlink_outside_corpus_is_not_followed(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
            root=Path(d);p=Path(other)/'outside.txt';p.write_text('outside');(root/'escape.txt').symlink_to(p)
            docs,_=documents.read_corpus(root);self.assertEqual(docs,[])

if __name__=='__main__':unittest.main()
