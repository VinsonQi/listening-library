#!/usr/bin/env python3
"""Publish only complete, validated lesson packages into the static Site."""
import json,re,shutil,subprocess
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'content/lessons'; DIST=ROOT/'dist'
CATEGORIES={'Research','Technology','Nature','Life','Culture'}
SLUG=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
def command(*args):
 return subprocess.check_output(args,text=True).strip()
def main():
 catalog=[]
 prepared=[]
 for folder in sorted(SOURCE.iterdir(),reverse=True):
  if not folder.is_dir() or not (folder/'lesson.json').exists():continue
  data=json.loads((folder/'lesson.json').read_text())
  if data.get('published',True) is False:continue
  assert data['id']==folder.name and SLUG.fullmatch(folder.name),f'Invalid ID: {folder}'
  for k in ['title','summary','source_name','source_url','main_idea']:
   assert isinstance(data.get(k),str) and data[k].strip(),f'{folder.name}: missing {k}'
  assert data['category'] in CATEGORIES
  assert data['difficulty'] in (1,2,3)
  assert data['target_minutes'] in (10,30)
  assert urlparse(data['source_url']).scheme=='https' and urlparse(data['source_url']).netloc
  for extra in data.get('additional_sources',[]) + data.get('supporting_sources',[]):
   assert urlparse(extra['url']).scheme=='https' and urlparse(extra['url']).netloc,f'{folder.name}: invalid supporting-source URL'
  for extra_url in [data.get('source',{}).get('license_url')]:
   if extra_url:assert urlparse(extra_url).scheme=='https' and urlparse(extra_url).netloc,f'{folder.name}: invalid license URL'
  assert isinstance(data.get('words'),list) and all(':' in x for x in data['words'])
  paper=data.get('source',{})
  assert isinstance(paper.get('journal'),str) and paper['journal'].strip(),f'{folder.name}: missing journal'
  assert isinstance(paper.get('authors'),list) and paper['authors'] and all(isinstance(a,str) and a.strip() for a in paper['authors']),f'{folder.name}: missing author list'
  assert isinstance(paper.get('publication_date'),str) and paper['publication_date'].strip(),f'{folder.name}: missing publication date'
  for name in ['audio.mp3','transcript.txt','recap.pdf','source-brief.json']:
   assert (folder/name).is_file() and (folder/name).stat().st_size>0,f'{folder.name}: missing {name}'
  transcript=(folder/'transcript.txt').read_text().strip()
  seconds=float(command('ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(folder/'audio.mp3')))
  assert seconds>=data['target_minutes']*60,f'{folder.name}: {seconds:.1f}s below target'
  pdf_text=command('pdftotext',str(folder/'recap.pdf'),'-')
  assert len(pdf_text.split())>=.9*len(transcript.split()),f'{folder.name}: PDF script incomplete'
  assert (folder/'audio.mp3').stat().st_size<25*1024*1024,'Audio exceeds static asset limit; use approved storage before publishing'
  item={**data,'duration_seconds':round(seconds),'audio':f'lessons/{folder.name}/audio.mp3','recap':f'lessons/{folder.name}/recap.pdf','transcript':transcript}
  catalog.append(item);prepared.append(folder)
 catalog.sort(key=lambda item:(item['id'][:10],-int(item.get('sort_order',999))),reverse=True)
 target=DIST/'lessons'
 if target.exists():shutil.rmtree(target)
 target.mkdir(exist_ok=True)
 for folder in prepared:
  out=target/folder.name;out.mkdir()
  for filename in ['audio.mp3','recap.pdf']:shutil.copy2(folder/filename,out/filename)
 (DIST/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
 print(f'Built {len(catalog)} complete lessons. All playback, PDF and text assets are local to this Site.')
if __name__=='__main__':main()
