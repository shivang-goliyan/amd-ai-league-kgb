import importlib.util
import sys
import unittest
from pathlib import Path
APP=Path(__file__).resolve().parents[1]/'app';sys.path.insert(0,str(APP));MODULE=importlib.util.find_spec('retrieval')
if MODULE:import retrieval

class RetrievalTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(MODULE,'Lexical retrieval has not been implemented')

    def test_exact_identifier_beats_common_topic(self):
        docs=[{'file':'a.txt','text':'The cooling fan is replaceable.'},{'file':'b.csv','text':'Part AX-71 has field-replaceable fan FAN-672.'}]
        index=retrieval.Index(docs);self.assertEqual(index.search('Which fan is used in AX-71?',limit=1)[0]['file'],'b.csv')

    def test_late_evidence_is_not_truncated(self):
        text=('Unrelated production event.\n'*1800)+'Default batch timeout is 271 seconds.'
        matches=retrieval.Index([{'file':'long.log','text':text}]).search('What is the default batch timeout?',limit=2)
        self.assertTrue(any('271' in m['text'] for m in matches))

    def test_hop_follows_an_identifier_not_present_in_question(self):
        docs=[{'file':'prod.log','text':'Thermal throttle incident tracked in BUG-918.'},{'file':'bugs.csv','text':'BUG-918 firmware fix release 5.6.7.'}]
        matches=retrieval.Index(docs).context('Which firmware fixed the production thermal throttle?',limit=6)
        self.assertEqual({m['file'] for m in matches},{'prod.log','bugs.csv'})

    def test_empty_index_has_no_candidates(self):self.assertEqual(retrieval.Index([]).context('What is the price?'),[])

if __name__=='__main__':unittest.main()
