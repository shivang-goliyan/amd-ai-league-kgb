"""Bounded public HTTP reads for seeded web-navigation experiments."""
import asyncio
import gzip
import html
import time
from urllib.parse import urldefrag,urlsplit
from urllib.request import Request,HTTPRedirectHandler,build_opener
from bs4 import UnicodeDammit


def _validate(url):
    url=urldefrag(str(url))[0];parts=urlsplit(url)
    if parts.scheme not in ('http','https') or not parts.netloc or parts.username or parts.password:
        raise ValueError('Expected an HTTP(S) URL without embedded credentials')
    return url


class _Redirect(HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,newurl):
        return super().redirect_request(request,fp,code,msg,headers,_validate(newurl))


class HTTPFetcher:
    def __init__(self,max_bytes=2*1024*1024):
        if max_bytes<=0:raise ValueError('The response byte limit must be positive')
        self.max_bytes=max_bytes

    async def __call__(self,url,timeout):
        url=_validate(url);limit=min(5,float(timeout))
        if limit<=0:raise TimeoutError('No HTTP time budget remains')
        async with asyncio.timeout(limit):
            return await asyncio.to_thread(self._read,url,limit)

    def _read(self,url,timeout):
        deadline=time.monotonic()+timeout
        request=Request(url,headers={'User-Agent':'KGBWebRetriever/0.1','Accept':'text/html,application/xhtml+xml,text/plain','Accept-Encoding':'gzip'})
        with build_opener(_Redirect()).open(request,timeout=timeout) as response:
            content_type=response.headers.get_content_type()
            if content_type not in ('text/html','application/xhtml+xml','text/plain'):
                raise ValueError('Unsupported page media type')
            encoding=response.headers.get('Content-Encoding','identity').lower()
            if encoding not in ('identity','gzip'):raise ValueError('Unsupported response encoding')
            reader=gzip.GzipFile(fileobj=response) if encoding=='gzip' else response
            body=bytearray()
            while True:
                if time.monotonic()>=deadline:raise TimeoutError('HTTP read deadline reached')
                chunk=reader.read1(min(65536,self.max_bytes-len(body)+1))
                if not chunk:break
                body.extend(chunk)
                if len(body)>self.max_bytes:raise ValueError('Page exceeds the response byte limit')
            charset=response.headers.get_content_charset()
            text=UnicodeDammit(bytes(body),known_definite_encodings=[charset] if charset else [],is_html=content_type!='text/plain').unicode_markup
            if text is None:raise ValueError('Page text could not be decoded')
            if content_type=='text/plain':text='<pre>'+html.escape(text)+'</pre>'
            return {'url':_validate(response.geturl()),'html':text}
