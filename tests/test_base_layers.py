import importlib.util
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'));MODULE=importlib.util.find_spec('verify_base_layers')
if MODULE:import verify_base_layers as verify

class BaseLayerTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(MODULE,'Registry-config base layer verifier missing')
    def test_preserved_base_with_extra_application_layer(self):
        self.assertTrue(verify.check_layers(['sha256:a','sha256:b'],['sha256:a','sha256:b','sha256:c']))
    def test_flattened_or_changed_base_is_rejected(self):
        with self.assertRaises(ValueError):verify.check_layers(['sha256:a','sha256:b'],['sha256:squashed'])
        with self.assertRaises(ValueError):verify.check_layers(['sha256:a','sha256:b'],['sha256:a','sha256:x','sha256:c'])
    def test_missing_base_layers_is_not_a_pass(self):
        with self.assertRaises(ValueError):verify.check_layers([],['sha256:anything'])

if __name__=='__main__':unittest.main()
