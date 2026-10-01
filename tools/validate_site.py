#!/usr/bin/env python3
"""Lightweight source and local-asset checks; not a substitute for browser QA."""
import json,re,hashlib
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
class Document(HTMLParser):
 def __init__(self): super().__init__(); self.ids=[]; self.refs=[]; self.assets=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  if 'aria-controls' in a:self.refs.append(a['aria-controls'])
  if tag in ['script','link']:self.assets.append(a.get('src',a.get('href','')))
doc=Document();doc.feed((ROOT/'dist/index.html').read_text())
assert len(doc.ids)==len(set(doc.ids)),'Duplicate element IDs'
used=set(re.findall(r"\$\('([^']+)'\)",(ROOT/'dist/app.js').read_text()))
assert not used-set(doc.ids),f'Missing JavaScript element references: {used-set(doc.ids)}'
assert not set(doc.refs)-set(doc.ids),'Missing tab panels'
for url in doc.assets:
 if url and not url.startswith('data:'):
  assert not url.startswith(('http:','https:','//')),'Unexpected external runtime asset'
  assert (ROOT/'dist'/url).is_file(),f'Missing asset: {url}'
for lesson in json.loads((ROOT/'dist/catalog.json').read_text()):
 for key in ['audio','recap']:
  url=lesson[key]
  assert not url.startswith(('http:','https:','//')),'Lesson asset must be owned by this Site'
  assert (ROOT/'dist'/url).is_file(),f'Missing {key}: {url}'
 if lesson.get('script_sha256'):
  transcript=ROOT/'content/lessons'/lesson['id']/'transcript.txt'
  assert hashlib.sha256(transcript.read_bytes()).hexdigest()==lesson['script_sha256'],'Transcript provenance mismatch'
print('Validated HTML IDs, reader tabs, JavaScript targets, and all local runtime/lesson assets.')
