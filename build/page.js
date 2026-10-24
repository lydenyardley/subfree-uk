(function(){
var D=/*@@DATA@@*/{},CHECKED='@@CHECKED@@';
var $=function(s,c){return (c||document).querySelector(s)},$$=function(s,c){return Array.prototype.slice.call((c||document).querySelectorAll(s))};
var root=document.documentElement,mq=window.matchMedia('(prefers-color-scheme: dark)'),tb=$('#theme');
function isDark(){var t=root.getAttribute('data-theme');return t?t==='dark':mq.matches}
function syncTheme(){var d=isDark();tb.lastChild.textContent=d?'Light mode':'Dark mode';tb.title=d?'Switch to light mode':'Switch to dark mode';tb.setAttribute('aria-label',tb.title)}
tb.onclick=function(){var n=isDark()?'light':'dark';root.setAttribute('data-theme',n);try{localStorage.setItem('theme',n)}catch(e){}syncTheme()};
if(mq.addEventListener)mq.addEventListener('change',syncTheme);
syncTheme();
var narrow=window.matchMedia('(max-width:820px)'),small=window.matchMedia('(max-width:520px)'),filters=$('#filters'),srcs=$('#sources');
function fitFilters(){filters.open=!small.matches}
function fitSources(){srcs.open=!narrow.matches}
function fitSortKeys(){$$('#tbl thead th button').forEach(function(b){if(narrow.matches)b.setAttribute('tabindex','-1');else b.removeAttribute('tabindex')})}
if(small.addEventListener)small.addEventListener('change',fitFilters);
if(narrow.addEventListener)narrow.addEventListener('change',fitSortKeys);
if(narrow.addEventListener)narrow.addEventListener('change',fitSources);
addEventListener('beforeprint',function(){srcs.open=true});
fitFilters();fitSortKeys();fitSources();
var tbl=$('#tbl'),items=$$('tbody.item',tbl),minEl=$('#f-min'),maxEl=$('#f-max'),minOut=$('#f-min-out'),maxOut=$('#f-max-out'),fill=$('#f-fill');
var live=$('#live'),liveT,liveClearT,announce=false,lastN=0,nearPick=null;
function say(m){clearTimeout(liveT);clearTimeout(liveClearT);liveT=setTimeout(function(){live.textContent='';liveT=setTimeout(function(){live.textContent=m;liveClearT=setTimeout(function(){live.textContent=''},4000)},60)},300)}
var skey='keep3',sdir=1,SDEF={keep3:1,price:1,score:-1,recv:-1,nosub3:1,sub3:1,model:1};
// The note under the sort control names the figure the order follows, and the
// bold figure in each row is that figure. A list that reads as broken has an
// explanation next to the control that broke it.
var SORT_NOTES={
 keep3:'Order: 3-year cost to keep recordings (the bold figure).',
 nosub3:'Order: 3-year cost with no plan (the bold figure).',
 sub3:'Order: 3-year cost with a plan (the bold figure).',
 price:'Order: price, low to high.',
 score:'Order: free-feature score, high to low.',
 recv:'Order: records free first.',
 model:'Order: model name, A to Z.'
};
function markSort(){
 var note=$('#sortnote');
 if(note)note.textContent=SORT_NOTES[skey]||'';
 items.forEach(function(t){
  var cells=t.querySelectorAll('.c-nosub,.c-sub');
  for(var i=0;i<cells.length;i++)cells[i].classList.remove('keep');
  var cell=null;
  if(skey==='keep3')cell=t.querySelector(t.dataset.keep==='sub'?'.c-sub':'.c-nosub');
  else if(skey==='nosub3')cell=t.querySelector('.c-nosub');
  else if(skey==='sub3')cell=t.querySelector('.c-sub');
  if(cell)cell.classList.add('keep');
 });
}
function apply(){
 var lo0=+minEl.min,hi0=+maxEl.max,lo=+minEl.value,hi=+maxEl.value;
 if(lo>hi){lo=hi;minEl.value=hi}
 minEl.style.zIndex=lo>=hi?2:1;
 minOut.textContent='£'+lo;maxOut.textContent='£'+hi;
 fill.style.left=((lo-lo0)/(hi0-lo0)*100)+'%';
 fill.style.width=((hi-lo)/(hi0-lo0)*100)+'%';
 var rec=$('#f-rec').checked,ha=$('#f-ha').checked,pw=$$('.f-pw:checked').map(function(x){return x.value}),n=0;
 function ok(t,plo,phi){return (!rec||t.dataset.rec==='yes')&&(!ha||+t.dataset.ha>0)&&(+t.dataset.price>=plo&&+t.dataset.price<=phi)&&
  (!pw.length||pw.some(function(p){return t.dataset.power.split(' ').indexOf(p)>-1}))}
 items.forEach(function(t){var show=ok(t,lo,hi);t.hidden=!show;if(show)n++});
 $('#count').textContent=n; $('#empty').hidden=n>0;
 var near=null;
 if(!n){
  var bestD=Infinity;
  items.forEach(function(t){
   if(!ok(t,lo0,hi0))return;
   var p=+t.dataset.price,d=p<lo?lo-p:p>hi?p-hi:0;
   if(d<bestD||(d===bestD&&p<+(near?near.dataset.price:Infinity))){bestD=d;near=t}
  });
 }
 nearPick=near;
 var nb=$('#near'),et=$('#empty-txt');
 nb.hidden=!near;
 if(near){
  var nm=near.querySelector('.brand').textContent+' '+near.querySelector('.mname').textContent;
  var pr='£'+(+near.dataset.price).toFixed(2).replace(/\\.00$/,'');
  var p=+near.dataset.price,st=+minEl.step||5,base=+minEl.min;
  // The button says which control it moves, so one tap is enough to recover.
  if(p>+maxEl.value)nb.textContent='Raise the maximum to £'+(base+Math.ceil((p-base)/st)*st);
  else if(p<+minEl.value)nb.textContent='Lower the minimum to £'+(base+Math.floor((p-base)/st)*st);
  else nb.textContent='Show '+nm+' at '+pr;
  // The message names the filter that emptied the list, not just that it is empty.
  var why=['no doorbell costs between £'+lo+' and £'+hi];
  if(rec)why.push('none records free with no extra kit');
  if(ha)why.push('none works locally with Home Assistant');
  if(pw.length)why.push('none is '+(pw.length>1?'either ':'')+pw.join(' or '));
  var msg=why.join(', and ')+'.';
  et.textContent=msg.charAt(0).toUpperCase()+msg.slice(1)+(near?' The closest is '+nm+' at '+pr+'.':'');
 }else et.textContent='Nothing matches those filters.';
 if(announce&&n!==lastN)say(n?n+' of '+items.length+' doorbells shown':'No doorbells match those filters');
 lastN=n;
 var s=items.slice().sort(function(a,b){
  var x=skey==='model'?a.dataset.model:+a.dataset[skey],y=skey==='model'?b.dataset.model:+b.dataset[skey];
  if(x<y)return -sdir;if(x>y)return sdir;return +a.dataset.keep3-+b.dataset.keep3;
 });
 s.forEach(function(t){tbl.appendChild(t)});
 $$('#tbl thead th[data-sort]').forEach(function(th){th.setAttribute('aria-sort',th.dataset.sort===skey?(sdir>0?'ascending':'descending'):'none')});
 $('#sort').value=skey;
 markSort();
}
$$('#controls input').forEach(function(el){el.addEventListener('input',apply);el.addEventListener('change',apply)});
// The track is decorative and its inputs ignore pointer events, so a click
// there is a shortcut for "move the handle nearest this spot".
$('.dual-track').addEventListener('click',function(ev){
 var r=this.getBoundingClientRect();
 if(!r.width)return;
 var v=+minEl.min+Math.min(1,Math.max(0,(ev.clientX-r.left)/r.width))*(+maxEl.max-+minEl.min);
 var lo=+minEl.value,hi=+maxEl.value;
 // Two handles on one spot cannot be told apart by distance, so a click to
 // the right of them moves the maximum and a click to the left moves the
 // minimum. Without that, a range dragged shut could not be opened by the
 // pointer again: both sat at the minimum and the nearest one always won.
 var el=lo>=hi?(v>hi?maxEl:minEl):Math.abs(v-lo)<=Math.abs(v-hi)?minEl:maxEl;
 el.value=v;apply();el.focus({preventScroll:true});
});
$('#sort').onchange=function(){skey=this.value;sdir=SDEF[skey];apply()};
$$('#tbl thead th[data-sort] button').forEach(function(b){b.onclick=function(){
 var k=b.parentNode.dataset.sort;
 if(k===skey)sdir=-sdir;else{skey=k;sdir=SDEF[k]}
 apply();
}});
$('#reset').onclick=function(){$$('#controls input[type=checkbox]').forEach(function(c){c.checked=false});minEl.value=minEl.min;maxEl.value=maxEl.max;skey='keep3';sdir=1;apply()};
// The chevron is the whole control now, so its name has to say what it does:
// an icon alone leaves a screen reader with a nameless button.
$$('button.more').forEach(function(b){b.onclick=function(){
 var d=document.getElementById(b.getAttribute('aria-controls')),o=b.getAttribute('aria-expanded')==='true';
 b.setAttribute('aria-expanded',!o);
 // The panel is hidden by the `js` class rather than the `hidden`
 // attribute, so a reader without JavaScript gets every panel open.
 d.classList.toggle('open',!o);
}});
var reduce=window.matchMedia('(prefers-reduced-motion: reduce)');
// A footnote marker in a row jumps to its numbered entry, and on a phone the
// list is a closed disclosure. Chromium opens one for a jump it is asked to
// make; not every engine does, so the list is opened here and the navigation
// then scrolls to the entry wherever it has landed.
document.addEventListener('click',function(ev){
 var link=ev.target.closest('a.fn');
 if(link&&srcs&&!srcs.open)srcs.open=true;
});
$$('a.jump').forEach(function(a){a.addEventListener('click',function(ev){
 var rows=a.dataset.ids.split(' ').map(function(id){return document.getElementById('m-'+id)});
 if(rows.some(function(r){return r.hidden}))$('#reset').click();
 rows.sort(function(x,y){return x.compareDocumentPosition(y)&4?-1:1});
 ev.preventDefault();
 rows[0].scrollIntoView({behavior:reduce.matches?'auto':'smooth',block:'center'});
 if(history.replaceState)history.replaceState(null,'',location.pathname+location.search+'#'+rows[0].id);
 rows.forEach(function(r){r.classList.remove('flash');void r.offsetWidth;r.classList.add('flash');clearTimeout(r._ft);r._ft=setTimeout(function(){r.classList.remove('flash')},1900)});
 var vis=$$('#tbl tbody.item:not([hidden])'),pos=vis.indexOf(rows[0]),vt=rows[0].querySelector('.vtag');
 say(D[rows[0].dataset.id].name+(vt?', '+vt.textContent.toLowerCase():'')+', row '+(pos+1)+' of '+vis.length);
 var cb=rows[0].querySelector('input.cmp'); if(cb)cb.focus({preventScroll:true});
})});
// The row labels are the table's own words, so the second view does not make
// the reader relearn the two cost columns.
var PINNED=['Records free?','Price','3-year cost, no plan','3-year cost, with plan'],diffOnly=false;
var ROWS=[['Records free?','rec'],['Price','price'],['Free features','score'],['3-year cost, no plan','nosub3'],['3-year cost, with plan','sub3'],['Best for','best'],['Main catch','catch'],['Power','power'],['Storage','storage'],['Live view','live'],['Motion alerts','alerts'],['Smart detection','ai'],['History, no plan','history'],['Behind the paywall','paywalled'],['Plans','plan'],['Home Assistant','ha'],['Wi-Fi','wifi']];
function esc(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML}
// The records-free marker is the one the list uses, so a "No" reads the same
// in both places. A missing feature is marked, not left to the wording.
// "None" is a drawback in most rows, but not in the two where it is good
// news: no plan to buy, and nothing held back. Marking those red would warn
// the reader off the cheapest option on the page.
function cmpCell(key,v,d){
 if(key==='rec')return '<span class="rec rec-'+(d.recCls||'yes')+'">'+esc(v)+'</span>';
 if(key!=='plan'&&key!=='paywalled'&&/^None\b/.test(v))return '<span class="cmp-no">'+esc(v)+'</span>';
 return esc(v);
}
function sel(){return $$('input.cmp:checked').map(function(c){return c.value})}
// The comparison is wider than a phone, and a table that is cut off with no
// sign of it reads as a table that ends there. The cue names the column that
// is off the edge, and an edge fade says there is more.
var cmpScroll=$('.cmp-scroll'),cmpCue=$('#cmp-cue');
function cmpCueUpdate(){
 if(!cmpScroll||!cmpCue)return;
 var wrap=cmpScroll.parentNode;
 if(cmpScroll.scrollWidth-cmpScroll.clientWidth<=2){cmpCue.hidden=true;wrap.classList.remove('more');return}
 var box=cmpScroll.getBoundingClientRect(),ths=cmpScroll.querySelectorAll('#cmp-table thead th'),name='';
 for(var i=1;i<ths.length;i++){
  var r=ths[i].getBoundingClientRect(),nameEl=ths[i].querySelector('.cmp-name'),t=((nameEl||ths[i]).textContent||'').trim();
  // The column worth naming is the first one the reader cannot read: one cut
  // off by the edge with less than 60% of itself showing. Counting any column
  // that merely starts past the edge named the third model while the second
  // was a 47px sliver, and a column that is half in view is already readable.
  var seen=Math.min(r.right,box.right)-Math.max(r.left,box.left);
  if(r.right>box.right+1&&seen<r.width*0.6){name=t;break}
 }
 if(name){cmpCue.textContent='Swipe to see '+name;cmpCue.hidden=false;wrap.classList.add('more')}
 else{cmpCue.hidden=true;wrap.classList.remove('more')}
}
if(cmpScroll){cmpScroll.addEventListener('scroll',cmpCueUpdate);addEventListener('resize',cmpCueUpdate)}
// The cue needs the width of a table that has just been built, so it costs a
// layout. Ask for it on the frame after the table is on screen, not in the
// middle of the open.
var cuePending=false;
function queueCue(){
 if(cuePending)return;cuePending=true;
 requestAnimationFrame(function(){cuePending=false;cmpCueUpdate()});
}
function cmpIds(){return sel().slice(0,3)}
function shareUrl(){var s=cmpIds();return location.origin+location.pathname+(s.length?'?cmp='+s.join(','):'')}
function syncUrl(){
 var s=cmpIds(),u=location.pathname+(s.length?'?cmp='+s.join(','):'')+location.hash;
 try{if(history.replaceState)history.replaceState(null,'',u)}catch(e){}
}
function capSay(m){var el=$('#cmp-cap');if(!el)return;el.textContent=m;el.hidden=!m}
function tray(){
 var s=sel();
 $('#tray').hidden=s.length===0||!$('#compare').hidden;
 $('#tray-txt').textContent=s.length===1?'1 selected (tick 1 or 2 more)':s.length>=3?'3 selected (maximum, untick one to swap)':s.length?'2 selected':'';
 $('#tray-go').disabled=s.length<2;
 var ib=$('#cmp-inline');$('#cmp-sep').hidden=ib.hidden=s.length<2;ib.textContent='Compare '+s.length;
 // Unticking below two closes the panel without stealing focus from the box
 // the reader is on, so this path never touches focus.
 if(!$('#compare').hidden){
  if(s.length>=2)render();
  else{$('#compare').hidden=true;$('#tray').hidden=s.length===0}
 }
 say(s.length===0?'Comparison cleared':s.length===3?'3 selected. That is the maximum; untick one to swap.':s.length+' selected');
 if(s.length<3)capSay('');
 syncUrl();
}
// What the table was last built from. Rebuilding the same three columns costs a
// layout of 72 cells, and the open already asks for that once.
var built='';
function buildCmp(){
 var s=sel();
 if(s.join()===built)return;
 built=s.join();
 var h='<caption class="vh">Side-by-side comparison of '+s.length+' doorbells</caption><thead><tr><th scope="col"><span class="vh">Spec</span></th>'+s.map(function(id){
  var d=D[id],tone=d.tone?' data-v="'+esc(d.tone)+'"':'';
  // Every column carries the badge line, written or not, so the photos below
  // it start on one row: an empty badge is the same box as a written one.
  return '<th scope="col" data-id="'+esc(id)+'"'+tone+'><span class="cmp-name">'+esc(d.name)+'</span><span class="vtag'+(d.vtag?' v-'+esc(d.tone):'')+'">'+(d.vtag?esc(d.vtag):'')+'</span>'+(d.img?'<span class="cmp-photo"><button type="button" class="zoom" data-full="'+esc(d.imgLg)+'" data-name="'+esc(d.name)+'" aria-label="View '+esc(d.name)+' photo"><img src="'+esc(d.img)+'" width="45" height="60" alt="" loading="lazy" decoding="async"><span class="zi" aria-hidden="true"></span></button></span>':'')+'</th>';
 }).join('')+'</tr></thead><tbody>';
 var keep=s.map(function(id){return D[id].keep3}),valid=keep.filter(function(v){return typeof v==='number'&&isFinite(v)}),low=valid.length?Math.min.apply(null,valid):Infinity;
 // The cheapest column can be scrolled out of view, so a delta names the model
 // it is measured against. "+£15.00" without a baseline is not a comparison.
 var lowId=null;
 s.forEach(function(id){var v=D[id].keep3;if(typeof v==='number'&&isFinite(v)&&(lowId===null||v<D[lowId].keep3))lowId=id});
 h+='<tr class="cmp-cost" data-pin="1"><th scope="row">Cheapest way to record for 3 years</th>'+s.map(function(id){var v=D[id].keep3;
  if(typeof v!=='number'||!isFinite(v))return '<td>no plan</td>';
  var cheapest=Math.abs(v-low)<0.005;
  // The total first, then what it is made of. The difference stays, but as
  // the secondary figure, because the total is the one a reader compares.
  return '<td><b>'+m3(v)+'</b> <span class="cmp-diff">'+(cheapest?'cheapest of these 3':'+£'+(v-low).toFixed(2)+' more than '+esc(cmpName(lowId)))+'</span> <span class="cmp-basis">'+esc(D[id].keepNote)+'</span></td>';
 }).join('')+'</tr>';
 var dupes=0;
 ROWS.forEach(function(r){
  var vals=s.map(function(id){return D[id][r[1]]}),pin=PINNED.indexOf(r[0])>-1,same=vals.every(function(v){return v===vals[0]});
  if(same&&!pin)dupes++;
  h+='<tr'+(pin?' data-pin="1"':'')+(same&&!pin?' data-same="1"':'')+'><th scope="row">'+r[0]+'</th>'+s.map(function(id){var v=D[id][r[1]];
   // A plan figure bought in euros is not a UK quote, so the comparison says so
   // in the row rather than leaving the caveat to a footnote.
   if(r[1]==='plan'&&D[id].region==='EU')v+=' (EU price)';
   return '<td>'+cmpCell(r[1],v,D[id])+'</td>'}).join('')+'</tr>';
 });
 $('#cmp-table').innerHTML=h+'</tbody>';
 if(!dupes)diffOnly=false;
 $('#cmp-diff-w').hidden=!dupes;
 $('#cmp-dupes').textContent=dupes?'('+dupes+' identical)':'';
 $('#cmp-diff').checked=diffOnly;
 applyDiff();
}
function render(){
 buildCmp();
 $('#compare').hidden=false;
 queueCue();
}
// Identical rows are the one part of a comparison that carries no decision, so
// they can go. The four that do carry one stay even when they match.
function applyDiff(){$$('#cmp-table tbody tr[data-same]').forEach(function(tr){tr.hidden=diffOnly})}
$('#cmp-diff').onchange=function(){diffOnly=this.checked;applyDiff()};
// The fourth box is refused, and says why. Turning every other box pale
// instead makes a live control look broken and hides the reason. The refusal
// is for a reader's tap: a script that sets the selection (a shared link, a
// test) is not second-guessed, and the box that goes back is the one tapped.
function cmpChange(ev){
 var checked=$$('input.cmp').filter(function(b){return b.checked}),refused=false;
 if(checked.length>3&&ev&&ev.isTrusted&&ev.target&&ev.target.checked){
  ev.target.checked=false;refused=true;
  capSay('You can compare 3. Untick one to swap.');
 }
 tray();
 // After tray(), because its own announcement would replace this one.
 if(refused)say('You can compare 3. Untick one to swap.');
}
$$('input.cmp').forEach(function(c){c.addEventListener('change',cmpChange)});
// The three ticked rows fly into their columns. A view-transition name can sit
// on one element at a time, so each half carries it in turn: the table's copy
// while the old frame is captured, the header's copy in the frame after the
// update. The table's copy steps out of the picture for the length of the
// transition; left in, it would be painted in place and in the air at once.
function morphRow(id,mode){
 var row=document.getElementById('m-'+id);
 var th=document.querySelector('#cmp-table thead th[data-id="'+id+'"]');
 // A row hidden by a filter has no box to name, and a named box that is not
 // there would only cost a capture that never happens.
 if(!row||!th||row.hidden)return;
 [[row.querySelector('.mname'),th.querySelector('.cmp-name'),'cmp-n-'+id],
  [row.querySelector('.ph-sm'),th.querySelector('.cmp-photo img'),'cmp-p-'+id]].forEach(function(pair){
  var from=pair[0],to=pair[1],name=pair[2];
  if(!from||!to)return;
  from.style.viewTransitionName=mode==='table'?name:'';
  to.style.viewTransitionName=mode==='head'?name:'';
  // The half that is not carrying the name is the one painted in place, so it
  // is taken out of the picture; both sides are cleared by 'off', including the
  // header's, or the next open would land its name on a hidden box.
  from.style.visibility=mode==='head'?'hidden':'';
  to.style.visibility=mode==='table'?'hidden':'';
 });
}
// A name may sit on one element only, so a transition that starts before the
// last one cleaned up would be skipped whole. Every path that changes the
// panel clears the pairs first.
var flying=[];
function landRows(){flying.forEach(function(id){morphRow(id,'off')});flying=[]}
function showCompare(){
 // Already open: take the reader back to it rather than rebuilding it.
 if(!$('#compare').hidden){$('#compare').scrollIntoView({behavior:reduce.matches?'auto':'smooth',block:'start'});$('#cmp-h').focus({preventScroll:true});return}
 // The table is built before the transition starts, not inside it. The build
 // is the expensive half of the open, and a view transition lays the new frame
 // out for its snapshot: doing the two together ran a task over the budget.
 // The panel is hidden while this runs, and it is hidden in the snapshot of
 // the old frame either way, so the morph starts from the same picture.
 buildCmp();
 var ids=sel(),fly=!!(document.startViewTransition&&!reduce.matches);
 // The tray leaves and its place is taken by the compare header: the same box
 // stops being one control and starts being another. Scroll first, so both
 // snapshots are taken from the reader's final position.
 function go(smooth){
  render();tray();
  $('#compare').scrollIntoView({behavior:smooth?'smooth':'auto',block:'start'});
  // The button that opened this is hidden now, so hand focus to the panel's
  // heading. Not the section: its name would be every cell in the table.
  $('#cmp-h').focus({preventScroll:true});
 }
 if(fly){
  flying=ids.slice();
  ids.forEach(function(id){morphRow(id,'table')});
  var vt=document.startViewTransition(function(){ids.forEach(function(id){morphRow(id,'head')});go(false)});
  // A skipped or interrupted transition still has to give the table its names
  // back, so the cleanup does not wait on the promise alone.
  setTimeout(landRows,700);
  if(vt.finished&&vt.finished.then)vt.finished.then(landRows,landRows);
 }else go(!reduce.matches);
 say('Side-by-side comparison of '+sel().length+' doorbells');
}
// Closing runs the same pairs back: the header's copy carries the name while
// the open frame is captured, the row's copy in the frame after the panel goes.
// Anything else would have the row fade in under a name that never left.
function closeCompare(){
 if($('#compare').hidden)return;
 var ids=sel(),fly=!!(document.startViewTransition&&!reduce.matches);
 landRows();
 var go=function(){
  $('#compare').hidden=true;tray();
  if(!$('#tray').hidden)$('#tray-go').focus({preventScroll:true});
 };
 if(!fly){go();return}
 flying=ids.slice();
 ids.forEach(function(id){morphRow(id,'head')});
 var vt=document.startViewTransition(function(){ids.forEach(function(id){morphRow(id,'table')});go()});
 setTimeout(landRows,700);
 if(vt.finished&&vt.finished.then)vt.finished.then(landRows,landRows);
}
function clearAll(){
 // Both Clear buttons are about to be hidden, so focus needs somewhere real.
 var inside=$('#compare').contains(document.activeElement)||$('#tray').contains(document.activeElement);
 landRows();
 $$('input.cmp').forEach(function(c){c.checked=false});$('#compare').hidden=true;tray();
 if(inside){var f=document.querySelector('input.cmp');if(f)f.focus({preventScroll:true})}
}
$('#tray-go').onclick=showCompare;
$('#cmp-inline').onclick=showCompare;
$('#tray-clear').onclick=clearAll;
$('#cmp-clear').onclick=clearAll;
$('#cmp-close').onclick=closeCompare;
function m3(x){return '£'+(+x).toFixed(2)}
// The delta's baseline, in the shortest name that still says which model: the
// cheapest cell is often off the phone's edge, and every brand here ships a
// "Video Doorbell", which is the part worth dropping.
function cmpName(id){return id?D[id].name.replace(' Video Doorbell',''):''}
function shortlist(){
 return 'SubFree UK shortlist, checked '+CHECKED+'\n'+shareUrl()+'\n\n'+sel().map(function(id){var d=D[id];
  return d.name+'\n'+d.price+' · 3-year cost to keep recordings '+(typeof d.keep3==='number'&&isFinite(d.keep3)?m3(d.keep3):'no plan')+'\nBest for: '+d.best+'\nMain catch: '+d.catch;
 }).join('\n\n');
}
function legacyCopy(text){
 var t=document.createElement('textarea');t.value=text;t.setAttribute('readonly','');t.style.position='fixed';t.style.top='-1000px';
 document.body.appendChild(t);t.select();var ok=false;try{ok=document.execCommand('copy')}catch(e){}
 document.body.removeChild(t);return ok;
}
var copyBtn=$('#cmp-copy'),noteEl=$('#cmp-note'),noteT,noteT2;
function copyNote(m){
 noteEl.textContent=m;noteEl.hidden=false;noteEl.classList.remove('out');
 clearTimeout(noteT);clearTimeout(noteT2);
 noteT=setTimeout(function(){
  if(reduce.matches){noteEl.hidden=true;return}
  noteEl.classList.add('out');
  noteT2=setTimeout(function(){noteEl.hidden=true;noteEl.classList.remove('out')},400);
 },6000);
}
copyBtn.onclick=function(){
 var text=shortlist(),n=sel().length;
 function ok(){copyNote('Copied '+n+' model'+(n===1?'':'s')+' as Markdown, with prices and the date checked. Paste it into a message or a note.')}
 function fail(){copyNote('Copying is blocked in this browser. Select the table text and copy it by hand instead.')}
 if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(text).then(ok,function(){legacyCopy(text)?ok():fail()});
 else legacyCopy(text)?ok():fail();
};
$('#empty-reset').onclick=function(){$('#reset').click()};
$('#near').onclick=function(){
 if(!nearPick)return;
 var p=+nearPick.dataset.price,st=+minEl.step||5,base=+minEl.min;
 if(p<+minEl.value)minEl.value=base+Math.floor((p-base)/st)*st;
 else if(p>+maxEl.value)maxEl.value=base+Math.ceil((p-base)/st)*st;
 apply();
};
var lb=$('#lightbox'),lbBox=$('#lb-img'),lbName=$('#lb-name'),lbImg;
document.addEventListener('click',function(ev){
 var b=ev.target.closest('.zoom');
 if(!b)return;
 if(!lbImg){
  lbImg=document.createElement('img');
  lbImg.width=360;lbImg.height=480;lbImg.decoding='async';
  lbBox.appendChild(lbImg);
 }
 lbImg.src=b.dataset.full;
 lbImg.alt=b.dataset.name;
 lbName.textContent=b.dataset.name;
 if(lb.showModal)lb.showModal();
});
$('#lb-close').onclick=function(){lb.close()};
$('#lb-x').onclick=function(){lb.close()};
// A tap outside the photo closes the lightbox: the backdrop, the space around
// the image, or the button in the corner. The bar stays, because the name in
// it is there to be read.
lb.addEventListener('click',function(ev){
 if(ev.target===lb){lb.close();return}
 if(ev.target.closest('#lb-x')||ev.target.closest('.lb-bar'))return;
 if(ev.target.tagName!=='IMG')lb.close();
});
// Back to top, once the reader is into the table. The button appears when the
// sentinel above the table has scrolled past, and takes the reader and the
// keyboard back to the heading at the top.
var totop=$('#totop'),sent=$('#totop-s');
if(totop&&sent){
 // A scroll listener rather than an IntersectionObserver: the observer only
 // reports a change, and a jump from above the sentinel to below it (End, a
 // link, a restored scroll position) never crosses it at all, so the button
 // would stay hidden. One rect read a frame, through rAF, costs nothing.
 var totopT=0;
 function totopUpdate(){
  if(totopT)return;
  totopT=requestAnimationFrame(function(){totopT=0;totop.hidden=sent.getBoundingClientRect().top>=-1});
 }
 addEventListener('scroll',totopUpdate,{passive:true});
 addEventListener('resize',totopUpdate);
 totopUpdate();
 totop.onclick=function(){
  window.scrollTo({top:0,behavior:reduce.matches?'auto':'smooth'});
  var h=document.querySelector('h1');
  if(h){h.setAttribute('tabindex','-1');h.focus({preventScroll:true})}
 };
}
apply();announce=true;
var shared='';
try{shared=decodeURIComponent((location.search.match(/[?&]cmp=([^&]*)/)||[])[1]||'')}catch(e){shared=''}
if(shared){
 var ids=[];
 shared.split(',').forEach(function(id){if(D[id]&&ids.indexOf(id)<0&&ids.length<3)ids.push(id)});
 if(ids.length){
  $$('input.cmp').forEach(function(c){c.checked=ids.indexOf(c.value)>-1});
  if(ids.length>1)render();
  tray();
 }
 syncUrl();
}
})();