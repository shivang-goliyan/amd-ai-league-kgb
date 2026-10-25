"""Bounded page-navigation/evidence core; grader adapter and GPU wiring pending."""
import asyncio
from collections import deque
from urllib.parse import urlsplit,urldefrag,urljoin
if __package__:
    from .pages import parse_page
else:
    from pages import parse_page
from matches.rag.app.evidence import verify,REFUSAL


def _http_url(url):
    url=urldefrag(str(url))[0];parts=urlsplit(url)
    return url if parts.scheme in ('http','https') and parts.netloc and not parts.username and not parts.password else None


class WebAgent:
    def __init__(self,fetch,decide,search=None,max_pages=6,timeout=24):
        self.fetch=fetch;self.decide=decide;self.search=search;self.max_pages=max_pages;self.timeout=timeout;self.trace=[]

    async def retrieve(self,query,start_urls=None):
        self.trace=[];loop=asyncio.get_running_loop();deadline=loop.time()+self.timeout
        def remaining():return max(0,deadline-loop.time())
        try:
            async with asyncio.timeout(self.timeout):
                seeds=list(start_urls or [])
                if not seeds and self.search:seeds=await self.search(query,remaining())
                frontier=deque(x for u in seeds[:self.max_pages] if (x:=_http_url(u)));seen=set();pages=[];allowed=set(frontier);attempts=0;bridge_memory=[]
                while frontier and attempts<self.max_pages:
                    url=frontier.popleft()
                    if url in seen:continue
                    seen.add(url);attempts+=1
                    try:
                        response=await self.fetch(url,min(5,remaining()))
                        final=_http_url(response['url'])
                        if not final:continue
                        page=parse_page(final,response['html']);pages.append(page);seen.add(final)
                        allowed.update(link['url'] for link in page['links']);self.trace.append({'action':'read','url':final})
                    except (OSError,ValueError,KeyError):continue
                    proposal=await self.decide(query,pages,remaining())
                    suggestions=[]
                    if isinstance(proposal,dict):
                        suggestions.append(proposal.get('open_url'))
                        evidence=proposal.get('evidence')
                        if isinstance(evidence,list):
                            suggestions.extend(x.get('file') for x in evidence if isinstance(x,dict))
                            known={p['url']:p['text'] for p in pages}
                            for item in evidence:
                                if not isinstance(item,dict) or item.get('role')!='bridge':continue
                                file=item.get('file');quote=item.get('quote')
                                if isinstance(file,str) and file in known and isinstance(quote,str) and quote and quote in known[file]:
                                    remembered={'file':file,'quote':quote,'role':'bridge'}
                                    if remembered not in bridge_memory:bridge_memory.append(remembered)
                    candidate=None
                    for suggestion in suggestions:
                        if not isinstance(suggestion,str):continue
                        target=_http_url(urljoin(page['url'],suggestion))
                        if target in allowed and target not in seen:candidate=target;break
                    if candidate:
                        frontier.appendleft(candidate);continue
                    if isinstance(proposal,dict) and isinstance(proposal.get('evidence'),list) and bridge_memory:
                        proposal=dict(proposal);proposal['evidence']=list(proposal['evidence'])
                        proposal['evidence'].extend(x for x in bridge_memory if x not in proposal['evidence'])
                    result=verify(proposal,[{'file':p['url'],'text':p['text']} for p in pages],query)
                    if result['answer']:return result
        except TimeoutError:self.trace.append({'action':'deadline'})
        return REFUSAL.copy()
