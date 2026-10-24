import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

APP=Path(__file__).resolve().parents[1]/'app';sys.path.insert(0,str(APP))
SPEC=importlib.util.find_spec('generation')
if SPEC:import generation
from documents import read_corpus


class CompleteImageTextTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(SPEC,'Incomplete image generation is not handled')

    def test_index_retains_the_completed_retry_instead_of_a_partial_transcription(self):
        calls=[]
        def generate(messages,**kwargs):
            calls.append(kwargs)
            if len(calls)==1:raise generation.IncompleteGeneration('partial: Connector')
            return 'Connector P2\nG7 | THERM_WARN#'
        with tempfile.TemporaryDirectory() as d:
            Image.new('RGB',(32,32),'white').save(Path(d)/'pinout.png')
            docs,errors=read_corpus(Path(d),lambda p:generation.transcribe_complete(generate,[],deadline=100,clock=lambda:0))
        self.assertEqual(errors,[])
        self.assertEqual(docs[0]['text'],'Connector P2\nG7 | THERM_WARN#')
        self.assertEqual(len(calls),2)
        self.assertTrue(all(c['require_complete'] for c in calls))

    def test_repeated_truncation_skips_only_that_image_and_preserves_other_documents(self):
        calls=[]
        def generate(messages,**kwargs):
            calls.append(kwargs);raise generation.IncompleteGeneration('partial')
        with tempfile.TemporaryDirectory() as d:
            Image.new('RGB',(32,32),'white').save(Path(d)/'broken.png')
            (Path(d)/'other.txt').write_text('Independent evidence remains available')
            docs,errors=read_corpus(Path(d),lambda p:generation.transcribe_complete(generate,[],deadline=100,clock=lambda:0))
        self.assertEqual([x['file'] for x in docs],['other.txt'])
        self.assertEqual(len(errors),1);self.assertEqual(len(calls),2)

    def test_retry_uses_only_the_remaining_index_budget(self):
        times=iter([10,48]);calls=[]
        def generate(messages,**kwargs):
            calls.append(kwargs['seconds'])
            if len(calls)==1:raise generation.IncompleteGeneration('partial')
            return 'complete'
        self.assertEqual(generation.transcribe_complete(generate,[],deadline=50,clock=lambda:next(times)),'complete')
        self.assertEqual(calls,[40,2])

    def test_expired_index_does_not_start_another_model_call(self):
        def unexpected(*a,**k):raise AssertionError('Generation started after the deadline')
        with self.assertRaises(TimeoutError):generation.transcribe_complete(unexpected,[],deadline=9,clock=lambda:10)

    def test_completion_requires_an_actual_end_token(self):
        self.assertTrue(generation.ended(7,[5,7]))
        self.assertTrue(generation.ended(7,7))
        self.assertFalse(generation.ended(8,[5,7]))
        self.assertFalse(generation.ended(8,None))


if __name__=='__main__':unittest.main()
