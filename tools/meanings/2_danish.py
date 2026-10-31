import re,json,html
x=open('w/dl/dawiktionary-latest-pages-articles.xml').read()
pages=re.findall(r'<title>(.*?)</title>.*?<text[^>]*>(.*?)</text>',x,re.S)
def clean(s):
    s=html.unescape(s).strip()
    s=re.sub(r"^''\(?([^'()]+)\)?''\s*:?\s*",r'(\1) ',s)
    if re.fullmatch(r"(\([^)]*\) )?(\[\[[^\]]+\]\]\s*)+",s): s=re.sub(r"\]\]\s+\[\[","]], [[",s)
    s=re.sub(r'<ref.*?(</ref>|/>)','',s,flags=re.S); s=re.sub(r'<[^>]+>','',s)
    s=re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]",r'\1',s)
    s=re.sub(r'\{\{(?:l|term|ord)\|[^|}]*\|([^|}]*)[^}]*\}\}',r'\1',s)
    s=re.sub(r'\{\{[^{}]*\}\}','',s); s=s.replace("'''",'').replace("''",'')
    s=re.sub(r'^\((grundbetydning|generelt|almindeligt)\) ','',s); s=re.sub(r'^(\([^)]*\)):',r'\1',s)
    return re.sub(r'\s+',' ',s).strip(' ;,:')
da={}
for t,b in pages:
    if ':' in t: continue
    b=html.unescape(b); m=re.search(r'\{\{=da=\}\}(.*?)(?=\{\{=[a-z-]+=\}\}|$)',b,re.S)
    if not m: continue
    defs=[clean(l[1:]) for l in m.group(1).split('\n') if re.match(r'#[^:*#]',l)]
    defs=[d for d in defs if len(d)>2]
    if defs: da[t]=defs
json.dump(da,open('w/da.json','w'),ensure_ascii=False)
W=set(open('w/words.txt').read().split()); en=json.load(open('w/en.json'))
print(len(da),'direct',sum(w in da for w in W),'via form',sum(w not in da and en['form'].get(w) in da for w in W))
for w in ['hus','læse','bog','vej','glad','skole','udløbsdato']: print(w,da.get(w))
