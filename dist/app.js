'use strict';
const $=id=>document.getElementById(id);
const audio=$('audio');
const playIcon='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>';
const pauseIcon='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 5h4v14H7zm6 0h4v14h-4z"/></svg>';
let lessons=[],current=null,category='All',activeTab='overview',selectToken=0;
const categories=['All','Research','Technology','Nature','Life','Culture'];
const clock=n=>{n=Math.max(0,Math.floor(Number(n)||0));return `${Math.floor(n/60)}:${String(n%60).padStart(2,'0')}`;};
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const minutes=n=>`${Math.floor(n/60)} min`;
function openLibrary(){ $('library').classList.add('open');$('library').setAttribute('role','dialog');$('library').setAttribute('aria-modal','true');$('lesson').inert=true;document.querySelector('.topbar').inert=true;$('scrim').hidden=false;$('close-library').focus(); }
function closeLibrary(){ $('library').classList.remove('open');$('library').removeAttribute('role');$('library').removeAttribute('aria-modal');$('lesson').inert=false;document.querySelector('.topbar').inert=false;$('scrim').hidden=true; }
$('browse-open').onclick=openLibrary;$('close-library').onclick=()=>{closeLibrary();$('browse-open').focus();};$('scrim').onclick=closeLibrary;
function help(){ $('help').showModal(); }
$('help-open').onclick=help;$('first-lesson').onclick=help;
$('help').addEventListener('click',e=>{if(e.target===$('help')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)$('help').close();}});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeLibrary();});
function renderFilters(){
 $('filters').innerHTML=categories.filter(c=>c==='All'||lessons.some(l=>l.category===c)).map(c=>`<button class="filter" type="button" data-category="${c}" aria-pressed="${c===category}">${c==='All'?'All topics':c}</button>`).join('');
 $('filters').querySelectorAll('button').forEach(b=>b.onclick=()=>{category=b.dataset.category;renderFilters();renderList();});
}
function renderList(){
 const filtered=lessons.filter(l=>category==='All'||l.category===category);
 $('collection-meta').textContent=lessons.length?`${filtered.length} ${filtered.length===1?'lesson':'lessons'} · ${Math.round(filtered.reduce((s,l)=>s+l.duration_seconds,0)/60)} minutes of listening`:'0 lessons';
 $('total-count').textContent=lessons.length;$('mobile-count').textContent=lessons.length;
 if(!lessons.length){$('lesson-list').innerHTML='<div class="empty-library"><strong>No lessons yet</strong><p>Your finished lessons will appear here, ready to play.</p><div class="mini-line" aria-hidden="true"></div><div class="mini-line short" aria-hidden="true"></div></div>';return;}
 $('lesson-list').innerHTML=filtered.map(l=>`<div class="lesson-row ${l.id===current?.id?'selected':''}" data-id="${escape(l.id)}"><button class="lesson-select" type="button" data-select="${escape(l.id)}" aria-label="Read ${escape(l.title)}" ${l.id===current?.id?'aria-current="true"':''}><span class="lesson-topic">${escape(l.source?.journal||l.category)}</span><span class="lesson-name">${escape(l.title)}</span><span class="lesson-sub"><span>${minutes(l.duration_seconds)}</span><span class="difficulty" aria-label="Difficulty ${l.difficulty} of 3">${'★'.repeat(l.difficulty)}${'☆'.repeat(3-l.difficulty)}</span></span></button><button class="list-play" type="button" data-play="${escape(l.id)}" aria-label="Play ${escape(l.title)}">${l.id===current?.id&&!audio.paused?pauseIcon:playIcon}</button></div>`).join('');
 $('lesson-list').querySelectorAll('[data-select]').forEach(b=>b.onclick=()=>selectLesson(b.dataset.select,false,true));
 $('lesson-list').querySelectorAll('[data-play]').forEach(b=>b.onclick=()=>{if(current?.id===b.dataset.play)togglePlay();else selectLesson(b.dataset.play,true,true);});
}
function setTab(name,focus=false){
 activeTab=name;
 document.querySelectorAll('[data-tab]').forEach(b=>{const active=b.dataset.tab===name;b.setAttribute('aria-selected',String(active));b.tabIndex=active?0:-1;$(`panel-${b.dataset.tab}`).hidden=!active;if(active&&focus)b.focus();});
}
document.querySelectorAll('[data-tab]').forEach((b,i,all)=>{b.onclick=()=>setTab(b.dataset.tab);b.onkeydown=e=>{let n;if(e.key==='ArrowRight')n=(i+1)%all.length;else if(e.key==='ArrowLeft')n=(i-1+all.length)%all.length;else if(e.key==='Home')n=0;else if(e.key==='End')n=all.length-1;if(n!==undefined){e.preventDefault();setTab(all[n].dataset.tab,true);}};});
function renderTranscript(text,words,vocabulary=[]){
 const terms=(vocabulary.length?vocabulary.flatMap(v=>v.highlight_forms||[v.term]):words.map(w=>w.split(':')[0])).filter(Boolean).sort((a,b)=>b.length-a.length);
 const pattern=terms.length?new RegExp('('+terms.map(t=>t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('|')+')','gi'):null;
 $('transcript').replaceChildren();
 text.trim().split(/\n\s*\n/).forEach(par=>{const p=document.createElement('p');if(pattern){let last=0;for(const m of par.matchAll(pattern)){p.append(document.createTextNode(par.slice(last,m.index)));const mark=document.createElement('mark');mark.textContent=m[0];p.append(mark);last=m.index+m[0].length;}p.append(document.createTextNode(par.slice(last)));}else p.textContent=par;$('transcript').append(p);});
}
function selectLesson(id,play=false,fromUser=false){
 const l=lessons.find(x=>x.id===id);if(!l)return;
 if(current?.id!==id){
  selectToken++;audio.pause();current=l;$('audio-status').textContent='';audio.src=l.audio;audio.playbackRate=Number($('speed').value);$('seek').value=0;$('elapsed').textContent='0:00';$('duration').textContent=clock(l.duration_seconds);
  $('lesson-meta').textContent=`${l.category.toUpperCase()}  ·  ${minutes(l.duration_seconds).toUpperCase()}  ·  ${['EVERYDAY','GUIDED','DEEPER RESEARCH'][l.difficulty-1]}`;
  $('lesson-title').textContent=l.title;$('lesson-summary').textContent=l.summary;$('main-idea').textContent=l.main_idea||l.summary;
  $('scope-note').textContent=l.scope_note||'';$('scope-note').hidden=!l.scope_note;
  $('source-attribution').textContent=l.attribution||'';$('source-attribution').hidden=!l.attribution;
  $('source-license').hidden=!l.source?.license_url;if(l.source?.license_url){$('source-license').textContent=`Original source license: ${l.source.license}`;$('source-license').href=l.source.license_url;}
  $('supporting-sources').hidden=!l.additional_sources?.length;$('supporting-source-list').innerHTML=(l.additional_sources||[]).map(s=>`<li><a href="${escape(s.url)}" target="_blank" rel="noopener noreferrer">${escape(s.title)}</a></li>`).join('');
  $('question').textContent=l.question||'';$('answer').textContent=l.answer||'';$('reflection').hidden=!(l.question&&l.answer);
  $('source').textContent=l.source?.title||l.source_name;$('source').href=l.source_url;
  const journal=l.source?.journal||l.journal||'';const authors=l.source?.authors||l.authors||[];const date=l.source?.publication_date||l.source_published||'';
  const authorText=Array.isArray(authors)?authors.join(', '):authors;
  $('paper-citation').hidden=!journal;$('paper-journal').textContent=journal;$('paper-date').textContent=date;$('paper-authors').textContent=Array.isArray(authors)&&authors.length>3?`${authors.slice(0,3).join(', ')} and colleagues`:authorText;
  $('source-journal').textContent=journal||'Not recorded';$('source-authors').textContent=authorText||'Not recorded';$('source-date').textContent=date||'Not recorded';
  $('source-detail').textContent=[l.source_type,l.source_published?`Published ${l.source_published}`:'',l.source_checked?`Source checked ${l.source_checked}`:''].filter(Boolean).join(' · ');
  $('pdf').href=l.recap;$('download').href=l.audio;$('download').download=`${l.id}.mp3`;
  $('player-caption').textContent=`${clock(l.duration_seconds)} · English narration`;
  renderTranscript(l.transcript,l.words||[],l.vocabulary||[]);
  $('vocabulary').innerHTML=(l.words||[]).map(w=>{const idx=w.indexOf(':');return `<div class="word"><dt>${escape(idx<0?w:w.slice(0,idx))}</dt><dd>${escape(idx<0?'':w.slice(idx+1).trim())}</dd></div>`;}).join('');
  $('play').disabled=false;$('empty-state').hidden=true;$('lesson-content').hidden=false;
  if(fromUser){history.replaceState(null,'',`#${encodeURIComponent(l.id)}`);setTab('overview');}
  if('mediaSession' in navigator&&typeof MediaMetadata!=='undefined'){navigator.mediaSession.metadata=new MediaMetadata({title:l.title,artist:'Listening Library',album:l.category});}
 }
 renderList();closeLibrary();if(fromUser&&matchMedia('(max-width:760px)').matches){$('lesson').scrollIntoView({block:'start'});$('lesson').focus({preventScroll:true});}
 if(play)startPlay();
}
async function startPlay(){if(!current)return;const token=selectToken;$('audio-status').textContent='';try{await audio.play();}catch(e){if(token===selectToken&&e.name!=='AbortError'){$('audio-status').textContent='Audio couldn’t start. Try Play again, or open Download audio below.';}}}
function togglePlay(){if(audio.paused)startPlay();else audio.pause();}
$('play').onclick=togglePlay;
function syncPlayback(){const playing=!audio.paused&&!audio.ended;$('play').innerHTML=playing?pauseIcon:playIcon;$('play').setAttribute('aria-label',playing?'Pause lesson':'Play lesson');$('play-label').textContent=playing?'Now playing':audio.ended?'Play again':'Play lesson';renderList();}
audio.addEventListener('play',syncPlayback);audio.addEventListener('pause',syncPlayback);audio.addEventListener('ended',syncPlayback);
audio.addEventListener('timeupdate',()=>{const duration=Number.isFinite(audio.duration)?audio.duration:current?.duration_seconds||0;$('seek').max=duration;$('seek').value=audio.currentTime;$('seek').setAttribute('aria-valuetext',`${clock(audio.currentTime)} of ${clock(duration)}`);$('elapsed').textContent=clock(audio.currentTime);$('duration').textContent=clock(duration);});
audio.addEventListener('loadedmetadata',()=>{if(Number.isFinite(audio.duration)){$('seek').max=audio.duration;$('duration').textContent=clock(audio.duration);}});
audio.addEventListener('error',()=>{if(current)$('audio-status').textContent='This audio could not be loaded. Try reloading, or ask Max to check this lesson.';});
$('seek').oninput=e=>{if(current&&audio.readyState>0)audio.currentTime=Number(e.target.value);};
$('back').onclick=()=>{if(current)audio.currentTime=Math.max(0,audio.currentTime-15);};
$('forward').onclick=()=>{if(current)audio.currentTime=Math.min(audio.duration||current.duration_seconds,audio.currentTime+15);};
$('speed').onchange=e=>audio.playbackRate=Number(e.target.value);
if('mediaSession' in navigator){for(const [name,handler] of Object.entries({play:startPlay,pause:()=>audio.pause(),seekbackward:()=>{audio.currentTime=Math.max(0,audio.currentTime-15);},seekforward:()=>{audio.currentTime=Math.min(audio.duration||0,audio.currentTime+15);},seekto:d=>{if(Number.isFinite(d.seekTime))audio.currentTime=d.seekTime;}})){try{navigator.mediaSession.setActionHandler(name,handler);}catch{}}}
fetch('catalog.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw new Error('catalog');return r.json();}).then(data=>{if(!Array.isArray(data))throw new Error('catalog');lessons=data;renderFilters();renderList();if(lessons.length){const id=decodeURIComponent(location.hash.slice(1));selectLesson(lessons.some(l=>l.id===id)?id:lessons[0].id);}else{$('empty-state').hidden=false;$('lesson-content').hidden=true;}}).catch(()=>{$('lesson-summary').textContent='The library could not be loaded. Please refresh and try again.';$('lesson-content').hidden=false;document.querySelector('.player').hidden=true;document.querySelector('.tabs').hidden=true;$('panel-overview').hidden=true;$('collection-meta').textContent='Unable to load lessons';});
