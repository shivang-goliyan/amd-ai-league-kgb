import importlib.util
import sys
import unittest
from pathlib import Path
APP=Path(__file__).resolve().parents[1]/'app';sys.path.insert(0,str(APP));MODULE=importlib.util.find_spec('evidence')
if MODULE:import evidence

class EvidenceTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(MODULE,'Evidence verification has not been implemented')

    def test_unsupported_answer_is_refused(self):
        result=evidence.verify({'answer':'900','evidence':[{'file':'spec.txt','quote':'Maximum temperature: 87 C'}]},[{'file':'spec.txt','text':'Maximum temperature: 87 C'}],'Maximum temperature?')
        self.assertEqual(result['answer'],'');self.assertEqual(result['citations'],[])

    def test_fabricated_quote_is_refused(self):
        result=evidence.verify({'answer':'87','evidence':[{'file':'spec.txt','quote':'Maximum temperature: 87 C'}]},[{'file':'spec.txt','text':'Maximum temperature: 72 C'}],'Maximum temperature?')
        self.assertEqual(result['citations'],[])

    def test_literal_value_cites_only_the_proven_source(self):
        docs=[{'file':'spec.txt','text':'Maximum temperature: 87 C'},{'file':'notes.txt','text':'Cooling overview'}]
        p={'answer':'87','evidence':[{'file':'spec.txt','quote':'Maximum temperature: 87 C'},{'file':'notes.txt','quote':'Cooling overview'}]}
        self.assertEqual(evidence.verify(p,docs,'Maximum temperature?')['citations'],['spec.txt'])

    def test_number_is_not_allowed_to_match_a_larger_number(self):
        docs=[{'file':'spec.txt','text':'Maximum temperature: 187 C'}]
        p={'answer':'87','evidence':[{'file':'spec.txt','quote':'Maximum temperature: 187 C'}]}
        self.assertEqual(evidence.verify(p,docs,'Maximum temperature?')['answer'],'')

    def test_two_hop_chain_keeps_both_necessary_files(self):
        docs=[{'file':'prod.log','text':'Thermal throttle incident tracked in BUG-918.'},{'file':'bugs.csv','text':'BUG-918 firmware fix release 5.6.7.'}]
        p={'answer':'5.6.7','evidence':[{'file':x['file'],'quote':x['text']} for x in docs]}
        self.assertEqual(set(evidence.verify(p,docs,'Which firmware fixed the production thermal throttle?')['citations']),{'prod.log','bugs.csv'})

    def test_provided_identifier_does_not_need_an_extra_bridge_citation(self):
        docs=[{'file':'prod.log','text':'Thermal throttle incident tracked in BUG-918.'},{'file':'bugs.csv','text':'BUG-918 firmware fix release 5.6.7.'}]
        p={'answer':'5.6.7','evidence':[{'file':x['file'],'quote':x['text']} for x in docs]}
        self.assertEqual(evidence.verify(p,docs,'Which firmware fixed BUG-918?')['citations'],['bugs.csv'])

    def test_missing_source_path_is_refused(self):
        p={'answer':'87','evidence':[{'file':'../outside.txt','quote':'temperature 87'}]}
        self.assertEqual(evidence.verify(p,[],'Temperature?')['answer'],'')

    def test_quarter_is_completed_from_its_unique_source_qualifier(self):
        docs=[{'file':'plan.docx','text':'AX-71 enters sampling in Q2 FY28.'}]
        p={'answer':'Q2','evidence':[{'file':'plan.docx','quote':docs[0]['text']}]}
        self.assertEqual(evidence.verify(p,docs,'In which quarter does AX-71 enter sampling?')['answer'],'Q2 FY28')

if __name__=='__main__':unittest.main()
