// App logic: theme, auth, analyze, history, dashboard, admin
// ---- users / history (local mock backend) ----
let users=store.get('av_users',[{u:'admin',p:'admin',role:'admin'},{u:'demo',p:'demo',role:'user'}]),me=store.get('av_me',null),hist=store.get('av_hist',[]),cur=null,dir='TD',mid=0;
const save=()=>{store.set('av_users',users);store.set('av_me',me);store.set('av_hist',hist)};
// ---- theme ----
function theme(t){if(t)document.documentElement.dataset.theme=t;const dk=document.documentElement.dataset.theme=='dark'||(!document.documentElement.dataset.theme&&matchMedia('(prefers-color-scheme:dark)').matches);mermaid.initialize({startOnLoad:false,theme:dk?'dark':'default',securityLevel:'loose'});if(cur&&!$('#out').hidden)drawDiagram()}
const st=store.get('av_theme',null);if(st)document.documentElement.dataset.theme=st;theme();
$('#theme').onclick=()=>{const dk=document.documentElement.dataset.theme=='dark'||(!document.documentElement.dataset.theme&&matchMedia('(prefers-color-scheme:dark)').matches);const t=dk?'light':'dark';store.set('av_theme',t);theme(t)};
// ---- nav ----
function page(p){$$('.page').forEach(e=>e.classList.toggle('on',e.id=='p-'+p));$$('#nav button').forEach(b=>b.classList.toggle('on',b.dataset.p==p));({history:renderHist,dash:renderDash,admin:renderAdmin}[p]||(()=>{}))()}
$$('#nav button').forEach(b=>b.onclick=()=>page(b.dataset.p));
function chrome(){$('#navAdmin').hidden=!(me&&me.role=='admin');$('#banner').style.display=me?'none':'flex';$('#who').textContent=me?me.u+(me.role=='admin'?' (admin)':''):'';$('#authBtn').textContent=me?'Log out':'Log in'}
$('#authBtn').onclick=()=>{if(me){me=null;save();chrome();page('analyze')}else openAuth('login')};
let amode='login';function openAuth(m){amode=m;$('#aT').textContent=m=='login'?'Log in':'Create account';$('#aOk').textContent=m=='login'?'Log in':'Sign up';$('#aSw').textContent=m=='login'?'Create an account':'I have an account';$('#aE').style.display='none';$('#auth').classList.add('on')}
$('#aSw').onclick=e=>{e.preventDefault();openAuth(amode=='login'?'reg':'login')};$('#aX').onclick=e=>{e.preventDefault();$('#auth').classList.remove('on')};
$('#aOk').onclick=()=>{const u=$('#aU').value.trim(),p=$('#aP').value,f=users.find(x=>x.u==u);let e='';
 if(!u||!p)e='Enter a username and password.';else if(amode=='login'){if(!f||f.p!=p)e='Wrong username or password.';else me=f}else{if(f)e='That username is taken.';else if(p.length<4)e='Use at least 4 characters.';else{me={u,p,role:'user'};users.push(me)}}
 if(e){$('#aE').textContent=e;$('#aE').style.display='block';return}save();chrome();$('#auth').classList.remove('on');$('#aP').value=''};
// ---- analyze ----
$$('#src button').forEach(b=>b.onclick=()=>{$$('#src button').forEach(x=>x.classList.toggle('on',x==b));$('#urlBox').hidden=b.dataset.s!='url';$('#zipBox').hidden=b.dataset.s!='zip'});
const dr=$('#drop');dr.onclick=()=>$('#zf').click();dr.ondragover=e=>{e.preventDefault();dr.classList.add('hv')};dr.ondragleave=()=>dr.classList.remove('hv');
let zipName='';const setZip=f=>{if(f){window.selectedZip=f;zipName=f.name;dr.firstChild.textContent='Selected: '+f.name}};dr.ondrop=e=>{e.preventDefault();dr.classList.remove('hv');setZip(e.dataTransfer.files[0])};$('#zf').onchange=e=>setZip(e.target.files[0]);
async function run(zip,url){$('#err').style.display='none';$('#empty').hidden=true;$('#out').hidden=true;$('#load').hidden=false;$('#go').disabled=true;
 try{if(zip&&!zipName)throw new Error('Choose a .zip file first.');const r=await api.analyze(url,zip);cur=r;show(r);
  if(me){hist.unshift({id:Date.now(),u:me.u,name:r.name,lang:r.lang,at:Date.now(),result:r});save()}}
 catch(e){$('#err').textContent=e.message;$('#err').style.display='block';$('#empty').hidden=false}
 $('#load').hidden=true;$('#go').disabled=false}
$('#go').onclick=()=>run(!$('#zipBox').hidden,$('#url').value);
$$('[data-smp]').forEach(b=>b.onclick=()=>{$('#url').value='https://github.com/'+SAMPLE_REPOS[b.dataset.smp];page('analyze');run(false,$('#url').value)});
function show(r){$('#out').hidden=false;
 $('#info').innerHTML=`<h3>Repository info</h3><b style="font-size:17px">${esc(r.name)}</b> <span class="badge Info">Public</span><p style="color:var(--mu);margin:6px 0">${esc(r.lang)} · ${Number(r.files)||0} files · ${(Number(r.loc)||0).toLocaleString()} LOC</p><p><b>About:</b> ${esc(r.about)}</p>`;
 const c={};r.risks.forEach(x=>c[x[0]]=(c[x[0]]||0)+1);$('#riskCard').hidden=false;$('#riskSum').innerHTML=['High','Medium','Low','Info'].map(k=>`<span class="badge ${k}" style="margin-right:6px">${c[k]||0} ${k}</span>`).join('');
 $('#riskList').innerHTML=r.risks.slice(0,3).map((x,i)=>`<div class="risk ${esc(x[0])}"><b>${i+1}. ${esc(x[1])}</b> <span class="badge ${esc(x[0])}" style="float:right">${esc(x[0])}</span><br>${esc(x[2])}</div>`).join('');
 tab('overview');renderArchitectureViews(r);drawDiagram();
 $('#tree').innerHTML='<ul>'+tr(r.tree)+'</ul>';
 $('#hot').innerHTML=r.hot.map(h=>`<div class="hs"><code>${esc(h[0])}</code><b>${Number(h[1])||0} deps</b></div>`).join('');$('#cyc').innerHTML=r.cyc.map(x=>`<div class="risk ${x[0]=='N'?'Info':'Medium'}">${esc(x)}</div>`).join('');
 const lc={};r.nodes.forEach(n=>lc[n[2]]=(lc[n[2]]||0)+1);$('#lc').innerHTML=Object.entries(lc).map(([k,v])=>`<div class="hs"><span>${L[k]}</span><b>${v}</b></div>`).join('');
 $('#aiTx').innerHTML=`<div class="result-kicker">${esc(r.ai_source||'AI explanation')}</div><p style="max-width:70ch;font-size:15px;line-height:1.6">${esc(r.ai)}</p><button class="btn sec sm" onclick="navigator.clipboard&&navigator.clipboard.writeText(cur.ai)">Copy summary</button>`}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function renderArchitectureViews(r){
 const byLayer={};r.nodes.forEach(n=>(byLayer[n[2]]??=[]).push(n));
 const deps=Object.entries(byLayer).map(([layer,nodes])=>`<div class="arch-stat"><b>${nodes.length}</b><span>${esc(L[layer]||layer)} modules</span></div>`).join('');
 $('#architectureOverview').innerHTML=`<div class="result-kicker">REPOSITORY BLUEPRINT</div><h3 class="result-title">${esc(r.name)} architecture</h3><p class="result-lead">${esc(r.about)}. This overview is inferred from ${r.nodes.length} mapped components and ${r.edges.length} dependency links.</p><div class="arch-stats">${deps}<div class="arch-stat"><b>${r.hot.length}</b><span>dependency hotspots</span></div><div class="arch-stat"><b>${r.cyc.length}</b><span>cycle findings</span></div></div><div class="result-panel"><div><span class="result-kicker">HOW THE CODE FITS TOGETHER</span><p>${esc(r.ai)}</p></div><div class="overview-callout"><b>Reading the map</b><span>Follow arrows from entry points through core modules to adapters, helpers, and external packages. Use System Architecture for the full dependency graph.</span></div></div>`;
 const specs=[['Entry point','api','The modules that receive requests or expose the project interface.'],['Core processing','core','The central application logic and coordination.'],['Integrations','adapter','Adapters that connect core behavior to runtimes or services.'],['Shared resources','util','Shared helpers used across the dependency graph.']];
 let stages=specs.map(([title,layer,desc])=>({title,desc,items:(byLayer[layer]||[]).map(n=>n[1])})).filter(s=>s.items.length);
 if(!stages.length)stages=[{title:'Mapped components',desc:'The analyzer found these connected components.',items:r.nodes.map(n=>n[1])}];
 const ext=(byLayer.ext||[]).map(n=>n[1]);if(ext.length)stages.push({title:'External dependencies',desc:'Packages and services at the boundary of this repository.',items:ext});
 $('#sessionLifecycle').innerHTML=`<div class="result-kicker">INFERRED EXECUTION PATH</div><h3 class="result-title">Session lifecycle</h3><p class="result-lead">A code-level view of how work can move through this repository, inferred from module layers and dependency links. It is not a live runtime trace.</p><div class="lifecycle-flow">${stages.map((s,i)=>`<article class="lifecycle-step"><div class="lifecycle-step-head"><span>${String(i+1).padStart(2,'0')}</span><small>${i===0?'START':i===stages.length-1?'BOUNDARY':'PROCESS'}</small></div><h4>${esc(s.title)}</h4><p>${esc(s.desc)}</p><div class="module-chips">${s.items.slice(0,5).map(x=>`<span>${esc(x)}</span>`).join('')}${s.items.length>5?`<span>+${s.items.length-5} more</span>`:''}</div></article>`).join('')}</div><div class="result-footnote">For repositories with session or request handlers, use the stage names as an architectural guide and inspect the diagram for the actual dependency paths.</div>`;
 const names=Object.fromEntries(r.nodes.map(n=>[n[0],n[1]]));
 $('#resourceFlow').innerHTML=`<div class="result-kicker">DEPENDENCY &amp; RESOURCE PATHS</div><h3 class="result-title">Resource flow</h3><p class="result-lead">Each connector represents a dependency detected by the analyzer. Together they show which modules pass work or shared resources to other parts of the repository.</p>${r.edges.length?`<div class="resource-flow-list">${r.edges.map(([a,b])=>`<div class="resource-flow-row"><span class="resource-endpoint">${esc(names[a]||a)}</span><span class="resource-arrow" aria-label="depends on">→</span><span class="resource-endpoint target">${esc(names[b]||b)}</span></div>`).join('')}</div>`:'<div class="state">No dependency links were returned for this repository.</div>'}<div class="result-footnote">${r.nodes.length} mapped components · ${r.edges.length} directed dependency links</div>`;
}
function tr(o){return Object.entries(o).map(([k,v])=>typeof v=='string'?`<li>${esc(k)}<span class="lay">${esc(L[v]||v)}</span></li>`:`<li><details open><summary>${esc(k)}/</summary><ul>${tr(v)}</ul></details></li>`).join('')}
function txt(o,p=''){return Object.entries(o).map(([k,v])=>typeof v=='string'?p+'├─ '+k+' ['+L[v]+']\n':p+'├─ '+k+'/\n'+txt(v,p+'│  ')).join('')}
$('#cpTree').onclick=()=>{navigator.clipboard&&navigator.clipboard.writeText(txt(cur.tree));$('#cpTree').textContent='Copied';setTimeout(()=>$('#cpTree').textContent='Copy as text',1200)};
function mmd(){const r=cur;return `graph ${dir}\n`+r.nodes.map(n=>`${n[0]}["${n[1]}"]:::${n[2]}`).join('\n')+'\n'+r.edges.map(e=>`${e[0]} --> ${e[1]}`).join('\n')+`\nclassDef api fill:#dbe7ff,stroke:#2563eb,color:#0f1b33\nclassDef core fill:#d8f5d0,stroke:#3a9d2c,color:#0f1b33\nclassDef adapter fill:#fff3c4,stroke:#c99a00,color:#0f1b33\nclassDef util fill:#e5ddff,stroke:#7c4dff,color:#0f1b33\nclassDef ext fill:#ffd9d9,stroke:#d33,color:#0f1b33`}
async function drawDiagram(){try{const {svg}=await mermaid.render('m'+(++mid),mmd());$('#dg').innerHTML=svg}catch(e){$('#dg').innerHTML='<div class="state">Could not render the diagram.</div>'}}
$$('#dir button').forEach(b=>b.onclick=()=>{dir=b.dataset.d;$$('#dir button').forEach(x=>x.classList.toggle('on',x==b));drawDiagram()});
function dl(n,c,t){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([c],{type:t}));a.download=n;a.click()}
$('#dSvg').onclick=()=>{const s=$('#dg svg');s&&dl('architecture.svg',new XMLSerializer().serializeToString(s),'image/svg+xml')};$('#dMmd').onclick=()=>dl('architecture.mmd',mmd(),'text/plain');
function tab(t){$$('#otabs button').forEach(b=>b.classList.toggle('on',b.dataset.t==t));$$('.t').forEach(e=>e.hidden=e.id!='t-'+t)}$$('#otabs button').forEach(b=>b.onclick=()=>tab(b.dataset.t));
// ---- history / dashboard / admin ----
const mine=()=>me?hist.filter(h=>h.u==me.u):[];const fd=t=>new Date(t).toLocaleDateString();
function renderHist(){const q=$('#hq').value.toLowerCase();if(!me){$('#hist').innerHTML='<div class="state">Log in to save and browse your history.<br><br><button class="btn" onclick="openAuth(\'login\')">Log in</button></div>';return}
 const rows=mine().filter(h=>(h.name+h.lang).toLowerCase().includes(q));$('#hist').innerHTML=rows.length?`<table><tr><th>Repository</th><th>Language</th><th>Date</th><th></th></tr>${rows.map(h=>`<tr><td>${h.name}</td><td>${h.lang}</td><td>${fd(h.at)}</td><td><button class="btn sm" onclick="openH(${h.id})">Open</button> <button class="btn dg sm" onclick="delH(${h.id})">Delete</button></td></tr>`).join('')}</table>`:'<div class="state">No analyses yet. Analyze a repository to see it here.</div>'}
$('#hq').oninput=renderHist;
window.openH=id=>{const h=hist.find(x=>x.id==id);if(!h?.result)return;page('analyze');cur=h.result;$('#empty').hidden=true;show(cur)};window.delH=id=>{hist=hist.filter(x=>x.id!=id);save();renderHist()};
function renderDash(){const m=mine(),lg={};m.forEach(h=>lg[h.lang]=(lg[h.lang]||0)+1);
 $('#dstats').innerHTML=me?`<div class="card stat"><b>${m.length}</b><span>Total analyses</span></div><div class="card stat"><b>${Object.keys(lg).length}</b><span>Languages</span></div><div class="card stat"><b>${m[0]?m[0].name:'–'}</b><span>Most recent</span></div>`:'<div class="card state" style="grid-column:1/-1">Log in to see your dashboard.</div>';
 $('#dlang').innerHTML=Object.entries(lg).map(([k,v])=>`<div class="hs"><span>${k}</span><b>${v}</b></div>`).join('')||'<span style="color:var(--mu)">Nothing yet.</span>';
 $('#drec').innerHTML=m.slice(0,5).map(h=>`<div class="hs"><span>${h.name}</span><span style="color:var(--mu)">${fd(h.at)}</span></div>`).join('')||'<span style="color:var(--mu)">Nothing yet.</span>'}
function renderAdmin(){if(!me||me.role!='admin'){page('analyze');return}
 $('#astats').innerHTML=`<div class="card stat"><b>${users.length}</b><span>Users</span></div><div class="card stat"><b>${hist.length}</b><span>Analyses</span></div>`;
 const days=[...Array(7)].map((_,i)=>{const d=new Date(Date.now()-(6-i)*864e5);return{l:d.toLocaleDateString(undefined,{weekday:'short'}),n:hist.filter(h=>new Date(h.at).toDateString()==d.toDateString()).length}}),mx=Math.max(1,...days.map(d=>d.n));
 $('#achart').innerHTML=days.map(d=>`<div style="height:${d.n/mx*100}%"><em>${d.n}</em><u>${d.l}</u></div>`).join('');
 $('#atab').innerHTML=`<table><tr><th>User</th><th>Role</th><th>Analyses</th></tr>${users.map(u=>`<tr><td>${u.u}</td><td><span class="badge ${u.role=='admin'?'High':'Info'}">${u.role}</span></td><td>${hist.filter(h=>h.u==u.u).length}</td></tr>`).join('')}</table>`}
chrome();
// Deep link from the front page: app.html?sample=axios
const q=new URLSearchParams(location.search).get('sample');if(q&&SAMPLE_REPOS[q])document.querySelector('[data-smp="'+q+'"]').click();
