import importlib.util
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'core'));MODULE=importlib.util.find_spec('agent')
if MODULE:import agent

class AgentTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):self.assertIsNotNone(MODULE,'Bounded web navigation has not been implemented')

    async def test_follows_discovered_contact_link_and_verifies_answer(self):
        fetched=[]
        async def fetch(url,timeout):
            fetched.append(url)
            return {'url':url,'html':'<a href="/contact">Contact</a>' if url.endswith('/') else '<p>Support telephone: +1-555-0199</p>'}
        async def decide(query,pages,remaining):
            if len(pages)==1:return {'answer':'','evidence':[],'open_url':'https://example.test/contact'}
            return {'answer':'+1-555-0199','evidence':[{'file':'https://example.test/contact','quote':'Support telephone: +1-555-0199'}]}
        result=await agent.WebAgent(fetch,decide).retrieve('What is the support phone number?',['https://example.test/'])
        self.assertEqual(result['answer'],'+1-555-0199');self.assertEqual(result['citations'],['https://example.test/contact']);self.assertEqual(len(fetched),2)

    async def test_undiscovered_model_url_is_never_fetched(self):
        fetched=[]
        async def fetch(url,timeout):fetched.append(url);return {'url':url,'html':'<p>Home</p>'}
        async def decide(q,p,r):return {'answer':'','open_url':'https://unseen.test/secret'}
        result=await agent.WebAgent(fetch,decide).retrieve('Phone?',['https://example.test/'])
        self.assertEqual(fetched,['https://example.test/']);self.assertEqual(result['answer'],'')

    async def test_hallucinated_value_is_refused(self):
        async def fetch(url,timeout):return {'url':url,'html':'<p>Price: 123</p>'}
        async def decide(q,p,r):return {'answer':'999','evidence':[{'file':'https://example.test/','quote':'Price: 123'}]}
        result=await agent.WebAgent(fetch,decide).retrieve('Price?',['https://example.test/']);self.assertEqual(result['answer'],'');self.assertEqual(result['citations'],[])

    async def test_fetch_and_decision_budget_is_enforced(self):
        import asyncio,time
        async def fetch(url,timeout):await asyncio.sleep(1);return {'url':url,'html':'late'}
        async def decide(q,p,r):raise AssertionError('Should time out before decision')
        started=time.monotonic();result=await agent.WebAgent(fetch,decide,timeout=.03).retrieve('Question?',['https://example.test/'])
        self.assertLess(time.monotonic()-started,.3);self.assertEqual(result['answer'],'')

    async def test_page_cap_and_loop_avoidance(self):
        fetched=[]
        async def fetch(url,timeout):fetched.append(url);return {'url':url,'html':'<a href="/next">next</a><a href="/">home</a>'}
        async def decide(q,p,r):return {'answer':'','open_url':'https://example.test/next'}
        result=await agent.WebAgent(fetch,decide,max_pages=1).retrieve('Question?',['https://example.test/']);self.assertEqual(len(fetched),1);self.assertEqual(result['citations'],[])

    async def test_redirect_does_not_consume_two_page_slots(self):
        fetched=[]
        async def fetch(url,timeout):
            fetched.append(url)
            if len(fetched)==1:return {'url':'https://example.test/home','html':'<a href="/contact">Contact</a>'}
            return {'url':url,'html':'<p>Warranty: 37 months</p>'}
        async def decide(q,p,r):
            if len(p)==1:return {'answer':'','open_url':'https://example.test/contact'}
            return {'answer':'37','evidence':[{'file':'https://example.test/contact','quote':'Warranty: 37 months'}]}
        result=await agent.WebAgent(fetch,decide,max_pages=2).retrieve('Warranty?',['http://short.test/'])
        self.assertEqual(len(fetched),2);self.assertEqual(result['answer'],'37')

    async def test_package_import_works_in_a_fresh_process(self):
        import subprocess
        p=subprocess.run([sys.executable,'-c','from matches.web.core.agent import WebAgent'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)

    async def test_search_callback_supplies_initial_urls(self):
        async def search(query,remaining):return ['https://example.test/']
        async def fetch(url,timeout):return {'url':url,'html':'<p>Warranty: 37 months</p>'}
        async def decide(q,p,r):return {'answer':'37','evidence':[{'file':'https://example.test/','quote':'Warranty: 37 months'}]}
        result=await agent.WebAgent(fetch,decide,search=search).retrieve('How many months is the warranty?')
        self.assertEqual(result['answer'],'37')

    async def test_unread_link_cited_by_the_model_is_fetched_before_answering(self):
        fetched=[]
        async def fetch(url,timeout):
            fetched.append(url)
            return {'url':url,'html':'<a href="/cases/CASE-72">CASE-72 fix record</a>' if len(fetched)==1 else '<p>CASE-72 fixed in release 5.8.2</p>'}
        async def decide(q,pages,remaining):
            if len(pages)==1:return {'answer':'CASE-72','evidence':[{'file':'https://demo.test/cases/CASE-72','quote':'CASE-72 fix record'}]}
            return {'answer':'5.8.2','evidence':[{'file':'https://demo.test/cases/CASE-72','quote':'CASE-72 fixed in release 5.8.2'}]}
        result=await agent.WebAgent(fetch,decide).retrieve('Which release fixed CASE-72?',['https://demo.test/'])
        self.assertEqual(result['answer'],'5.8.2');self.assertEqual(len(fetched),2)

    async def test_an_unlinked_citation_is_not_a_navigation_permission(self):
        fetched=[]
        async def fetch(url,timeout):fetched.append(url);return {'url':url,'html':'<p>Home</p>'}
        async def decide(q,p,r):return {'answer':'999','evidence':[{'file':'https://unseen.test/record','quote':'Price: 999'}]}
        result=await agent.WebAgent(fetch,decide).retrieve('Price?',['https://demo.test/'])
        self.assertEqual(result['answer'],'');self.assertEqual(fetched,['https://demo.test/'])

    async def test_mapping_evidence_survives_navigation_to_the_lookup_result(self):
        async def fetch(url,timeout):
            return {'url':url,'html':'<p>Orion device fault: CASE-72</p><a href="/case">Fix record</a>' if url.endswith('/') else '<p>CASE-72 fixed in release 5.8.2</p>'}
        async def decide(q,pages,remaining):
            if len(pages)==1:
                return {'answer':'CASE-72','evidence':[{'file':'https://demo.test/','quote':'Orion device fault: CASE-72','role':'bridge'},{'file':'https://demo.test/case','quote':'Fix record','role':'answer'}]}
            return {'answer':'5.8.2','evidence':[{'file':'https://demo.test/case','quote':'CASE-72 fixed in release 5.8.2','role':'answer'}]}
        result=await agent.WebAgent(fetch,decide).retrieve('Which release fixed the Orion device fault?',['https://demo.test/'])
        self.assertEqual(result['answer'],'5.8.2');self.assertEqual(set(result['citations']),{'https://demo.test/','https://demo.test/case'})

        direct=await agent.WebAgent(fetch,decide).retrieve('Which release fixed CASE-72?',['https://demo.test/'])
        self.assertEqual(direct['citations'],['https://demo.test/case'])

if __name__=='__main__':unittest.main()
