"""Structure-aware web-page evidence, independent of the unpublished grader CLI."""
import json
import re
from urllib.parse import urljoin,urlsplit,urldefrag,unquote
from bs4 import BeautifulSoup,NavigableString


def _flatten(value,prefix=''):
    if isinstance(value,dict):
        return [line for key,item in value.items() for line in _flatten(item,(prefix+'.' if prefix else '')+str(key))]
    if isinstance(value,list):
        return [line for i,item in enumerate(value) for line in _flatten(item,prefix+'['+str(i)+']')]
    if value is None:return []
    return [prefix+': '+str(value)]


def parse_page(url,html):
    soup=BeautifulSoup(html,'html.parser');structured=[]
    for script in soup.find_all('script',attrs={'type':'application/ld+json'}):
        try:structured.extend(_flatten(json.loads(script.string or script.get_text(),parse_float=str)))
        except (ValueError,TypeError):pass
    for tag in list(soup.find_all(True)):
        if tag.attrs is None:continue
        hidden=tag.has_attr('hidden') or str(tag.get('aria-hidden','')).lower()=='true'
        style=str(tag.get('style','')).lower()
        if hidden or re.search(r'(?:^|;)\s*(?:display\s*:\s*none|visibility\s*:\s*hidden)',style):tag.decompose()
    for tag in soup.find_all(['script','style','template']):tag.decompose()
    base_tag=soup.find('base',href=True);base=urljoin(url,base_tag['href']) if base_tag else url
    links=[];seen={};contact=[]
    for anchor in soup.find_all('a',href=True):
        raw=anchor['href'].strip();scheme=urlsplit(raw).scheme.lower()
        if scheme in ('tel','mailto'):
            contact.append(('Telephone: ' if scheme=='tel' else 'Email: ')+unquote(raw.split(':',1)[1]).split('?',1)[0]);continue
        target=urldefrag(urljoin(base,raw))[0];parsed=urlsplit(target)
        if parsed.scheme not in ('http','https') or not parsed.netloc or parsed.username or parsed.password:continue
        label=anchor.get_text(' ',strip=True)
        if target not in seen:
            item={'url':target,'text':label};seen[target]=item;links.append(item)
        elif label and label not in seen[target]['text']:seen[target]['text']+='; '+label
    for table in reversed(soup.find_all('table')):
        rows=[' | '.join(cell.get_text(' ',strip=True) for cell in row.find_all(['th','td'],recursive=False)) for row in table.find_all('tr')]
        table.replace_with(NavigableString('\n'+'\n'.join(row for row in rows if row.strip())+'\n'))
    text=soup.get_text('\n',strip=True)
    sections=[text]
    if structured:sections.append('[Structured page data]\n'+'\n'.join(structured))
    if contact:sections.append('[Contact link values]\n'+'\n'.join(contact))
    title=soup.title.get_text(' ',strip=True) if soup.title else ''
    return {'url':url,'title':title,'text':'\n'.join(x for x in sections if x),'links':links}
