import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
SPEC=importlib.util.find_spec('matches.web.core.decision')
if SPEC:from matches.web.core.decision import ModelDecision
from matches.web.core.agent import WebAgent


class DecisionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):self.assertIsNotNone(SPEC,'Resident model decision wiring is not implemented')

    async def test_model_receives_real_links_then_produces_a_grounded_answer(self):
        calls=[]
        def generate(messages,**kwargs):
            data=json.loads(messages[-1]['content']);calls.append((data,kwargs))
            if len(calls)==1:
                self.assertIn('https://demo.test/contact',[x['url'] for x in data['links']])
                return '{"answer":"","evidence":[],"open_url":"https://demo.test/contact"}'
            return json.dumps({'answer':'37 months','evidence':[{'file':'https://demo.test/contact','quote':'Warranty: 37 months'}]})
        async def fetch(url,timeout):return {'url':url,'html':'<a href="/contact">Contact</a>' if url.endswith('/') else '<p>Warranty: 37 months</p>'}
        result=await WebAgent(fetch,ModelDecision(generate)).retrieve('Warranty term?',['https://demo.test/'])
        self.assertEqual(result['answer'],'37 months');self.assertEqual(result['citations'],['https://demo.test/contact'])
        self.assertEqual(len(calls),2);self.assertTrue(all(k['seconds']<=12 for _,k in calls))

    async def test_late_relevant_evidence_survives_prompt_size_limits(self):
        captured=[]
        def generate(messages,**kwargs):captured.append(messages[-1]['content']);return '{"answer":"","evidence":[]}'
        page={'url':'https://demo.test/catalog','title':'Catalog','links':[],'text':('Generic navigation and unrelated information.\n'*1800)+'\nZX-91 support warranty: 43 months'}
        await ModelDecision(generate)("What is the ZX-91 warranty?",[page],10)
        self.assertLess(len(captured[0]),25000);self.assertIn('43 months',captured[0])

    async def test_expired_budget_does_not_start_gpu_work(self):
        def unexpected(*a,**k):raise AssertionError('Model started after deadline')
        self.assertEqual(await ModelDecision(unexpected)('Question?',[],.2),{})

    async def test_incomplete_model_json_does_not_become_an_action(self):
        self.assertEqual(await ModelDecision(lambda *a,**k:'{"open_url":')('Question?',[],10),{})

    async def test_navigation_does_not_return_an_intermediate_lookup_key_as_the_answer(self):
        proposal={'answer':'CASE-72','evidence':[],'open_url':'https://demo.test/cases/CASE-72'}
        result=await ModelDecision(lambda *a,**k:json.dumps(proposal))('Which release fixed the fault?',[],20)
        self.assertEqual(result,{'open_url':'https://demo.test/cases/CASE-72'})

    async def test_available_budget_allows_the_final_evidence_object_to_finish(self):
        def generate(messages,**kwargs):
            if kwargs['seconds']<10:return '{"evidence":['
            return '{"evidence":[],"answer":"complete"}'
        self.assertEqual((await ModelDecision(generate)('Question?',[],20))['answer'],'complete')

    async def test_generation_keeps_time_for_the_total_agent_deadline(self):
        budgets=[]
        def generate(messages,**kwargs):budgets.append(kwargs['seconds']);return '{}'
        await ModelDecision(generate)('Question?',[],3)
        self.assertEqual(budgets,[2])


if __name__=='__main__':unittest.main()
