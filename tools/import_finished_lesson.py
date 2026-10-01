#!/usr/bin/env python3
"""Copy a completed production package into the library without rewriting narration."""
import argparse,json,hashlib,shutil,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('--date',required=True);a=p.parse_args()
ROOT=Path(__file__).resolve().parents[1];src=a.input.resolve()
for name in ['metadata.json','script.txt','source-brief.json','audio.mp3','recap.pdf','audio-generation.json','audio-quality-check.json','pdf-qa.json']:
 assert (src/name).is_file(),f'Incomplete package: {name}'
m=json.loads((src/'metadata.json').read_text());raw=(src/'script.txt').read_bytes();digest=hashlib.sha256(raw).hexdigest();assert digest==m['script_sha256']
generation=json.loads((src/'audio-generation.json').read_text());assert generation['scriptSHA256']==digest,'Audio narration input differs from displayed script'
qa=json.loads((src/'audio-quality-check.json').read_text());assert qa['scriptMatchesGeneration'] and qa['mp3MatchesGeneration'] and qa['meetsMinimumDuration'],'Audio quality gate failed'
assert qa['mp3SHA256']==hashlib.sha256((src/'audio.mp3').read_bytes()).hexdigest(),'Audio QA is stale'
pdfqa=json.loads((src/'pdf-qa.json').read_text());assert pdfqa['full_script_verified'] and pdfqa['all_characters_within_page_bounds'],'PDF quality gate failed'
assert pdfqa['pdf_sha256']==hashlib.sha256((src/'recap.pdf').read_bytes()).hexdigest(),'PDF QA is stale'
assert not pdfqa.get('visual_review','Pending').startswith('Pending'),'PDF visual inspection is not complete'
slug=m.get('slug') or m.get('id') or src.name
if not slug.startswith(a.date+'-'):slug=a.date+'-'+slug
assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug)
if m.get('supporting_sources') and not m.get('additional_sources'):
 m['additional_sources']=[{**x,'purpose':x.get('purpose') or x.get('role','')} for x in m['supporting_sources']]
s=m['source'];assert s['journal'] and s['authors'] and s['publication_date']
meta={**m,'id':slug,'title':m.get('title',m.get('lesson_title')),'category':'Research','difficulty':2,'target_minutes':10,'main_idea':m.get('main_idea') or m['summary'],'source_name':s['title'],'source_url':s['url'],'source_type':m.get('paper_type') or 'Peer-reviewed research','source_published':s['publication_date'],'source_checked':s.get('accessed_on') or m.get('checked_on'),'words':[v['term']+': '+v['definition'] for v in m['vocabulary']],'published':True,'voice':{'model':'Kokoro-82M v1.0 full-precision ONNX','voice':'af_heart','speed':1.0,'type':'synthetic neural narration'}}
out=ROOT/'content/lessons'/slug;out.mkdir(parents=True,exist_ok=True);(out/'lesson.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');shutil.copy2(src/'script.txt',out/'transcript.txt')
for name in ['source-brief.json','audio.mp3','recap.pdf','audio-generation.json','audio-quality-check.json','pdf-qa.json']:
 shutil.copy2(src/name,out/name)
print(json.dumps({'lesson':slug,'source':str(src),'copied_to':str(out),'script_sha256':digest}))
