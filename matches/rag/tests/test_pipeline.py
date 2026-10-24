import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
APP=Path(__file__).resolve().parents[1]/'app';sys.path.insert(0,str(APP));MODULE=importlib.util.find_spec('pipeline')
if MODULE:import pipeline

class PipelineTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(MODULE,'Resident retrieval pipeline has not been implemented')

    def test_index_is_reused_for_queries_and_written_to_disk(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'corpus';root.mkdir();(root/'spec.txt').write_text('Maximum temperature: 87 C')
            calls=[]
            def generate(question,context):
                calls.append((question,context));return {'answer':'87','evidence':[{'file':'spec.txt','quote':'Maximum temperature: 87 C'}]}
            engine=pipeline.Engine(generate,index_dir=Path(d)/'index')
            report=engine.index(root);self.assertEqual(report['documents'],1)
            (root/'spec.txt').unlink()
            for _ in range(2):self.assertEqual(engine.answer(root,'Maximum temperature?')['answer'],'87')
            self.assertEqual(len(calls),2);self.assertTrue((Path(d)/'index'/'documents.json').is_file())

    def test_queries_cannot_use_an_unindexed_corpus(self):
        with tempfile.TemporaryDirectory() as d:
            engine=pipeline.Engine(lambda q,c:{},index_dir=Path(d)/'index')
            with self.assertRaises(RuntimeError):engine.answer(Path(d)/'unindexed','Question?')

    def test_empty_corpus_refuses_without_calling_model(self):
        with tempfile.TemporaryDirectory() as d:
            def unexpected(q,c):raise AssertionError('Empty corpus should not call the model')
            engine=pipeline.Engine(unexpected,index_dir=Path(d)/'index');engine.index(Path(d))
            self.assertEqual(engine.answer(Path(d),'Price?'),{'answer':'','citations':[],'confidence':0.0})

    def test_proposal_parser_handles_fences_and_refuses_invalid_json(self):
        self.assertEqual(pipeline.parse_proposal('```json\n{"answer":"87","evidence":[]}\n```')['answer'],'87')
        self.assertEqual(pipeline.parse_proposal('not JSON'),{})

if __name__=='__main__':unittest.main()
