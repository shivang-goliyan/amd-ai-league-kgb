import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

APP = Path(__file__).resolve().parents[1] / 'app'
sys.path.insert(0, str(APP))
MODULE = importlib.util.find_spec('contract')
if MODULE:
    import contract

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(MODULE, 'The OCR grader contract has not been implemented')

    def test_preserves_chinese_registration_prefix(self):
        self.assertEqual(contract.clean_text('"京 A·12345"'), '京 A·12345')

    def test_removes_model_wrappers_without_removing_sign_words(self):
        self.assertEqual(contract.clean_text('```text\nROAD\nWORK\nAHEAD\n```'), 'ROAD WORK AHEAD')
        self.assertEqual(contract.clean_text('Text: SPEED LIMIT 65'), 'SPEED LIMIT 65')

    def test_does_not_invent_or_correct_identifiers(self):
        self.assertEqual(contract.clean_text('0O1I8B'), '0O1I8B')
        self.assertEqual(contract.clean_text(''), '')

    def test_exact_output_name_and_atomic_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=contract.write_answer('/app/input/sign.v2.TIFF', {'text':'沪 B·88888','confidence':.83},Path(d))
            self.assertEqual(p.name,'sign.v2_output.json')
            self.assertEqual(json.loads(p.read_text())['text'],'沪 B·88888')
            self.assertEqual(len(list(Path(d).iterdir())),1)

    def test_failure_response_is_well_formed(self):
        with tempfile.TemporaryDirectory() as d:
            p=contract.write_answer('/app/input/a.png', {'text':'','confidence':0},Path(d))
            r=json.loads(p.read_text());self.assertIsInstance(r['text'],str);self.assertEqual(r['confidence'],0)

    def test_all_required_formats_and_resize_bound(self):
        with tempfile.TemporaryDirectory() as d:
            for ext,fmt in [('png','PNG'),('jpg','JPEG'),('tiff','TIFF')]:
                p=Path(d)/('input.'+ext);Image.new('RGB',(2300,650),'white').save(p,format=fmt)
                image=contract.load_image(p,max_edge=1600)
                self.assertEqual(image.mode,'RGB');self.assertLessEqual(max(image.size),1600)
                self.assertGreater(min(image.size),0)

    def test_transparent_input_is_composited_on_white(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.png';Image.new('RGBA',(10,10),(0,0,0,0)).save(p)
            self.assertEqual(contract.load_image(p).getpixel((0,0)),(255,255,255))

    def test_uint16_tiff_scales_to_rgb(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.tiff';Image.new('I;16',(10,10),65535).save(p)
            image=contract.load_image(p);self.assertEqual(image.mode,'RGB');self.assertEqual(image.getpixel((0,0)),(255,255,255))

if __name__=='__main__': unittest.main()
