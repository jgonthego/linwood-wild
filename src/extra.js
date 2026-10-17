/* Linwood Wild extras: photo gallery, bird journal (on-device only), describe-a-bird search. No server, no keys. */
(function(){
"use strict";
var LW,BYID={},TRAITS=null,GAL=null,galP=null,trP=null;
var LICN={"cc0":["CC0","https://creativecommons.org/publicdomain/zero/1.0/"],"cc-by":["CC BY","https://creativecommons.org/licenses/by/4.0/"],
  "cc-by-sa":["CC BY-SA","https://creativecommons.org/licenses/by-sa/4.0/"],"cc-by-nc":["CC BY-NC","https://creativecommons.org/licenses/by-nc/4.0/"]};
function $(q,r){return (r||document).querySelector(q);}
function $$(q,r){return Array.prototype.slice.call((r||document).querySelectorAll(q));}
function esc(s){return LW.esc(s);}
function loadJSON(u){return fetch(u).then(function(r){if(!r.ok)throw new Error(u+" "+r.status);return r.json();});}
function gal(){return galP||(galP=loadJSON("data/gallery.json").then(function(g){GAL=g;return g;}));}
function traits(){return trP||(trP=loadJSON("data/traits.json").then(function(t){TRAITS=t;return t;}));}
function purl(u){return u.charAt(0)==="@"?"https://inaturalist-open-data.s3.amazonaws.com/photos/"+u.slice(1):u;}
function sz(u,size){return purl(u).replace("/medium.","/"+size+".");}

/* ---------- modal shell (Android back button closes it) ---------- */
var modal=null,modalOpen=false;
function openModal(html,cls){
  if(!modal){modal=document.createElement("div");modal.className="lwmodal";modal.setAttribute("role","dialog");modal.setAttribute("aria-modal","true");
    modal.innerHTML='<div class="lwm-back" data-close></div><div class="lwm-box"><button type="button" class="lwm-x" data-close aria-label="Close">\u2715</button><div class="lwm-in"></div></div>';
    document.body.appendChild(modal);
    modal.addEventListener("click",function(e){if(e.target.closest("[data-close]"))closeModal();});
    document.addEventListener("keydown",function(e){if(modalOpen&&e.key==="Escape")closeModal();});
    window.addEventListener("popstate",function(){if(modalOpen)hideModal();});}
  modal.className="lwmodal "+(cls||"");
  $(".lwm-in",modal).innerHTML=html;
  if(!modalOpen){history.pushState({lwm:1},"");}
  modalOpen=true;modal.style.display="flex";document.body.classList.add("noscroll");
  setTimeout(function(){var x=$(".lwm-x",modal);if(x)x.focus();},30);
  return $(".lwm-in",modal);
}
function hideModal(){modalOpen=false;if(modal)modal.style.display="none";document.body.classList.remove("noscroll");}
function closeModal(){if(!modalOpen)return;hideModal();if(history.state&&history.state.lwm)history.back();}

/* ---------- 1. PHOTO GALLERY ---------- */
function openGallery(id){
  var s=BYID[id];if(!s)return;
  var box=openModal('<div class="gal"><h3 class="gt">'+esc(LW.name(s))+'</h3><p class="gsci">'+esc(s.sci)+'</p><p class="empty">Loading photos…</p></div>',"m-gal");
  Promise.all([gal(),s.g==="birds"?traits().catch(function(){return {};}):Promise.resolve({})]).then(function(r){
    if(!modalOpen)return;renderGallery(box,s,r[0][id]||{},(r[1]||{})[id]||{});
  }).catch(function(e){box.innerHTML='<p class="empty">Could not load the gallery ('+esc(e.message)+').</p>';});
}
function renderGallery(box,s,g,t){
  var groups=[],all=[];
  function add(key,title,arr){if(!arr||!arr.length)return;var start=all.length;
    arr.forEach(function(p){all.push({u:p[0],a:p[1],l:p[2],o:p[3],t:p[4]||[],grp:title});});groups.push({title:title,start:start,n:arr.length,key:key});}
  var isB=s.g==="birds";
  if(isB){add("m","Male",g.m);add("f","Female",g.f);add("j","Juvenile",g.j);}
  add("x",isB?"More photos (no sex / age / pose label)":"Photos",g.x);
  if(!all.length&&s.ph){all.push({u:s.ph.url,a:s.ph.attr,l:null,lic:s.ph.license,lu:s.ph.license_url,t:[],grp:"Photo"});groups.push({title:"Photo",start:0,n:1});}
  var status="";
  if(isB){
    var hm=!!(g.m&&g.m.length),hf=!!(g.f&&g.f.length);
    if(!hm&&!hf)status='<p class="gstat">Male/female look alike or no labeled photos — no openly licensed research-grade iNaturalist photos of this bird carry a Male or Female annotation.</p>';
    else if(!hf)status='<p class="gstat">No openly licensed photos annotated <b>Female</b> on iNaturalist.</p>';
    else if(!hm)status='<p class="gstat">No openly licensed photos annotated <b>Male</b> on iNaturalist.</p>';
  }
  var note=t.sex?'<details class="gnote" open><summary>How to tell male vs female</summary><p>“'+esc(t.sex)+'”</p><p class="sinfo">Quoted from <a href="'+esc(t.wurl||s.wiki_url||"#")+'" target="_blank" rel="noopener">Wikipedia</a> (<a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener license">CC BY-SA</a>).</p></details>':"";
  var h='<div class="gal"><h3 class="gt">'+esc(LW.name(s))+'</h3><p class="gsci">'+esc(s.sci)+' · <span class="tx-'+s.lik+'">'+LW.LIK[s.lik]+'</span></p>'+
    '<div class="gstage"><button type="button" class="gnav gprev" aria-label="Previous photo">\u2039</button><figure class="gmain"><img alt=""><figcaption></figcaption></figure><button type="button" class="gnav gnext" aria-label="Next photo">\u203A</button></div>'+
    '<div class="gthumbs">'+groups.map(function(gr){return '<div class="ggrp"><div class="ggt">'+esc(gr.title)+' <span>'+gr.n+'</span></div><div class="ggr">'+
      all.slice(gr.start,gr.start+gr.n).map(function(p,i){return '<button type="button" class="gth" data-i="'+(gr.start+i)+'" aria-label="'+esc(gr.title)+' photo '+(i+1)+'"><img loading="lazy" src="'+esc(sz(p.u,"small"))+'" alt=""></button>';}).join("")+'</div></div>';}).join("")+'</div>'+
    status+note+
    (isB?'<p class="sinfo">Labels come only from iNaturalist annotations (Sex, Life Stage) on research-grade observations — nothing is guessed. iNaturalist has no annotation for pose (flight, perched, back, front) or breeding plumage, so those photos stay unlabeled. In look-alike species an observer’s Male/Female annotation may rest on behavior (singing, egg-laying) rather than a visible difference.'+
      (g.nm!=null?' Annotated research-grade observations with open-licence photos on iNaturalist: '+LW.fmt(g.nm||0)+' male · '+LW.fmt(g.nf||0)+' female · '+LW.fmt(g.nj||0)+' juvenile.':'')+'</p>':'')+
    '<div class="gact"><button type="button" class="logbtn" data-log="'+s.id+'">+ Log this '+(isB?"bird":"sighting")+'</button><a href="'+LW.turl(s)+'" target="_blank" rel="noopener">iNaturalist page \u2197</a></div></div>';
  box.innerHTML=h;
  if(!all.length){$(".gstage",box).outerHTML='<p class="empty">No openly licensed photos available.</p>';return;}
  var cur=0,img=$(".gmain img",box),cap=$(".gmain figcaption",box);
  function show(i){cur=(i+all.length)%all.length;var p=all[cur];
    img.src=sz(p.u,"large");img.alt=LW.name(s)+(p.t.length?" — "+p.t.join(", "):"")+" photo";
    var lic=p.l?LICN[p.l]:[p.lic,p.lu];
    cap.innerHTML=(p.t.length?p.t.map(function(x){return '<span class="glab gl-'+x.toLowerCase()+'">'+esc(x)+'</span>';}).join(""):'<span class="glab gl-none">'+(s.g==="birds"?"Unlabeled":"Photo")+'</span>')+
      ' <span class="gcount">'+(cur+1)+' / '+all.length+'</span><br><span class="gattr">'+esc(p.a)+(lic&&lic[0]?' · <a href="'+esc(lic[1])+'" target="_blank" rel="noopener license">'+esc(lic[0])+'</a>':'')+
      (p.o?' · <a href="https://www.inaturalist.org/observations/'+p.o+'" target="_blank" rel="noopener">observation</a>':'')+'</span>';
    $$(".gth",box).forEach(function(b){b.classList.toggle("on",+b.getAttribute("data-i")===cur);});}
  $(".gprev",box).onclick=function(){show(cur-1);};$(".gnext",box).onclick=function(){show(cur+1);};
  $$(".gth",box).forEach(function(b){b.onclick=function(){show(+b.getAttribute("data-i"));};});
  var x0=null;img.addEventListener("touchstart",function(e){x0=e.touches[0].clientX;},{passive:true});
  img.addEventListener("touchend",function(e){if(x0==null)return;var dx=e.changedTouches[0].clientX-x0;if(Math.abs(dx)>40)show(cur+(dx<0?1:-1));x0=null;});
  modal.onkeydown=function(e){if(e.key==="ArrowRight")show(cur+1);if(e.key==="ArrowLeft")show(cur-1);};
  show(0);
}

/* ---------- 2. BIRD JOURNAL (localStorage + IndexedDB, this device only) ---------- */
var JKEY="lw-journal-v1",DBN="lw-journal",WHERE=["Yard","Feeder","Flyover","Other"];
function jload(){try{return JSON.parse(localStorage.getItem(JKEY)||"[]");}catch(e){return [];}}
function jsave(a){localStorage.setItem(JKEY,JSON.stringify(a));}
function uid(){return "j"+Date.now().toString(36)+Math.random().toString(36).slice(2,7);}
var dbp=null;
function db(){return dbp||(dbp=new Promise(function(res,rej){if(!window.indexedDB)return rej(new Error("no IndexedDB"));
  var r=indexedDB.open(DBN,1);r.onupgradeneeded=function(){r.result.createObjectStore("photos");};r.onsuccess=function(){res(r.result);};r.onerror=function(){rej(r.error);};}));}
function idb(mode,fn){return db().then(function(d){return new Promise(function(res,rej){var tx=d.transaction("photos",mode),st=tx.objectStore("photos"),q=fn(st);
  tx.oncomplete=function(){res(q&&q.result);};tx.onerror=function(){rej(tx.error);};});});}
function putPhoto(id,blob){return idb("readwrite",function(st){return st.put(blob,id);});}
function getPhoto(id){return idb("readonly",function(st){return st.get(id);});}
function delPhoto(id){return idb("readwrite",function(st){return st.delete(id);});}
function resize(file,max){return new Promise(function(res,rej){var u=URL.createObjectURL(file),im=new Image();
  im.onload=function(){var k=Math.min(1,max/Math.max(im.width,im.height)),c=document.createElement("canvas");c.width=Math.round(im.width*k);c.height=Math.round(im.height*k);
    c.getContext("2d").drawImage(im,0,0,c.width,c.height);URL.revokeObjectURL(u);c.toBlob(function(b){b?res(b):rej(new Error("resize failed"));},"image/jpeg",0.82);};
  im.onerror=function(){URL.revokeObjectURL(u);rej(new Error("not an image"));};im.src=u;});}
function blobToData(b){return new Promise(function(res){var r=new FileReader();r.onload=function(){res(r.result);};r.readAsDataURL(b);});}
function dataToBlob(d){var p=d.split(","),bin=atob(p[1]),a=new Uint8Array(bin.length);for(var i=0;i<bin.length;i++)a[i]=bin.charCodeAt(i);return new Blob([a],{type:(p[0].match(/:(.*?);/)||[])[1]||"image/jpeg"});}
function pad(n){return (n<10?"0":"")+n;}
function today(){var d=new Date();return d.getFullYear()+"-"+pad(d.getMonth()+1)+"-"+pad(d.getDate());}
function nowT(){var d=new Date();return pad(d.getHours())+":"+pad(d.getMinutes());}
function download(name,text,type){var b=new Blob([text],{type:type}),a=document.createElement("a");a.href=URL.createObjectURL(b);a.download=name;document.body.appendChild(a);a.click();
  setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},1500);}
function csvCell(v){v=v==null?"":String(v);return /[",\n\r]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v;}
function parseCSV(t){var rows=[],row=[],f="",q=false;for(var i=0;i<t.length;i++){var c=t[i];
  if(q){if(c==='"'){if(t[i+1]==='"'){f+='"';i++;}else q=false;}else f+=c;}
  else if(c==='"')q=true;else if(c===","){row.push(f);f="";}else if(c==="\n"||c==="\r"){if(c==="\r"&&t[i+1]==="\n")i++;row.push(f);rows.push(row);row=[];f="";}else f+=c;}
  if(f!==""||row.length){row.push(f);rows.push(row);}return rows.filter(function(r){return r.length>1||r[0];});}
var CSVCOLS=["id","date","time","species","scientific_name","inat_taxon_id","count","where","notes","has_photo","created","updated"];

var J={el:null,view:"list",edit:null};
function spLabel(e){return e.sp&&BYID[e.sp]?LW.name(BYID[e.sp]):(e.name||"Unknown");}
function renderJournal(){
  var sec=$("#journal");if(!sec)return;J.el=sec;
  var box=$("#journalBox");
  box.innerHTML='<div class="jbanner">\uD83D\uDD12 <b>Saved on this device only.</b> Your journal lives in this browser’s storage on this phone/computer. Nothing is uploaded or published — and clearing browser data deletes it, so export a backup now and then.</div>'+
    '<div class="jtabs" role="tablist"><button type="button" data-v="add">+ New sighting</button><button type="button" data-v="list">Timeline</button><button type="button" data-v="life">Life list</button><button type="button" data-v="backup">Backup</button></div><div class="jview"></div>';
  $$(".jtabs button",box).forEach(function(b){b.onclick=function(){J.edit=null;jshow(b.getAttribute("data-v"));};});
  jshow(J.view);
}
function jshow(v,prefill){
  J.view=v;var box=$("#journalBox"),view=$(".jview",box);
  $$(".jtabs button",box).forEach(function(b){b.classList.toggle("on",b.getAttribute("data-v")===v);b.setAttribute("aria-selected",b.getAttribute("data-v")===v);});
  if(v==="add")jform(view,prefill);else if(v==="life")jlife(view);else if(v==="backup")jbackup(view);else jlist(view);
}
function acList(q){q=q.trim().toLowerCase();if(!q)return [];var out=[];
  LW.species.forEach(function(s){var n=(s.com||"").toLowerCase(),sc=s.sci.toLowerCase(),i=n.indexOf(q),j=sc.indexOf(q);
    if(i<0&&j<0)return;var sc0=(i===0?0:i>0?(n.charAt(i-1)===" "||n.charAt(i-1)==="-"?1:2):3)+(s.g==="birds"?0:4)+({likely:0,possible:.3,rare:.6})[s.lik];out.push([sc0,s]);});
  out.sort(function(a,b){return a[0]-b[0]||(b[1].A+b[1].B)-(a[1].A+a[1].B);});return out.slice(0,8).map(function(x){return x[1];});}
function jform(view,prefill){
  var e=J.edit?jload().filter(function(x){return x.id===J.edit;})[0]:null;
  var sp=e?e.sp:(prefill||null),nm=e?spLabel(e):(sp&&BYID[sp]?LW.name(BYID[sp]):"");
  view.innerHTML='<form class="jform" autocomplete="off">'+
    '<label class="jsp">Species<div class="acw"><input name="sp" required placeholder="Start typing… or Unknown" value="'+esc(nm)+'" aria-autocomplete="list"><ul class="ac" role="listbox"></ul></div>'+
    '<button type="button" class="unk">Unknown</button></label>'+
    '<div class="jrow"><label>Date<input type="date" name="date" required value="'+esc(e?e.date:today())+'"></label><label>Time<input type="time" name="time" value="'+esc(e?e.time:nowT())+'"></label><label>Count<input type="number" name="count" min="1" step="1" value="'+(e?e.count:1)+'" inputmode="numeric"></label></div>'+
    '<fieldset class="jwhere"><legend>Where (no GPS)</legend>'+WHERE.map(function(w){return '<label><input type="radio" name="where" value="'+w+'"'+((e?e.where:"Yard")===w?" checked":"")+'><span>'+w+'</span></label>';}).join("")+'</fieldset>'+
    '<label>Notes<textarea name="notes" rows="3" placeholder="Behavior, plumage, what it was eating…">'+esc(e?e.notes:"")+'</textarea></label>'+
    '<label class="jph">Photo (optional, kept on this device, resized to 1280 px)<input type="file" name="photo" accept="image/*"></label><div class="jprev"></div>'+
    '<div class="jbtns"><button type="submit" class="more jsave">'+(e?"Save changes":"Save sighting")+'</button>'+(e?'<button type="button" class="jcancel">Cancel</button>':'')+'</div><p class="jmsg" aria-live="polite"></p></form>';
  var f=$("form",view),inp=f.elements.sp,ac=$(".ac",f),chosen=sp,pblob=null,keepPhoto=e&&e.photo,removePhoto=false;
  if(e&&e.photo)getPhoto(e.id).then(function(b){if(b){$(".jprev",f).innerHTML='<img src="'+URL.createObjectURL(b)+'" alt="Saved photo"><button type="button" class="jrmph">Remove photo</button>';
    $(".jrmph",f).onclick=function(){removePhoto=true;keepPhoto=false;$(".jprev",f).innerHTML="";};}}).catch(function(){});
  function drawAC(){var l=acList(inp.value);ac.innerHTML=l.map(function(s,i){return '<li role="option" data-id="'+s.id+'"'+(i===0?' class="hi"':'')+'>'+esc(LW.name(s))+' <i>'+esc(s.sci)+'</i>'+(s.g!=="birds"?' <small>'+esc(s.g)+'</small>':'')+'</li>';}).join("");ac.style.display=l.length?"block":"none";}
  inp.addEventListener("input",function(){chosen=null;drawAC();});
  inp.addEventListener("keydown",function(ev){if(ev.key==="Enter"&&ac.style.display==="block"){var h=$(".hi",ac);if(h){ev.preventDefault();pick(+h.getAttribute("data-id"));}}
    if(ev.key==="ArrowDown"||ev.key==="ArrowUp"){var li=$$("li",ac),i=li.indexOf($(".hi",ac));if(!li.length)return;ev.preventDefault();if(i>=0)li[i].classList.remove("hi");i=(i+(ev.key==="ArrowDown"?1:-1)+li.length)%li.length;li[i].classList.add("hi");}});
  inp.addEventListener("blur",function(){setTimeout(function(){ac.style.display="none";},200);});
  ac.addEventListener("mousedown",function(ev){var li=ev.target.closest("li");if(li){ev.preventDefault();pick(+li.getAttribute("data-id"));}});
  function pick(id){chosen=id;inp.value=LW.name(BYID[id]);ac.style.display="none";}
  $(".unk",f).onclick=function(){chosen=null;inp.value="Unknown";ac.style.display="none";};
  f.elements.photo.onchange=function(){var fl=this.files[0];if(!fl)return;$(".jmsg",f).textContent="Resizing photo…";
    resize(fl,1280).then(function(b){pblob=b;removePhoto=false;$(".jprev",f).innerHTML='<img src="'+URL.createObjectURL(b)+'" alt="New photo preview">';$(".jmsg",f).textContent="Photo ready ("+Math.round(b.size/1024)+" KB).";})
      .catch(function(err){$(".jmsg",f).textContent="Couldn’t read that photo: "+err.message;});};
  if($(".jcancel",f))$(".jcancel",f).onclick=function(){J.edit=null;jshow("list");};
  f.onsubmit=function(ev){ev.preventDefault();
    var v=inp.value.trim();if(!v){inp.focus();return;}
    if(!chosen&&v.toLowerCase()!=="unknown"){var ex=LW.species.filter(function(s){return (s.com||"").toLowerCase()===v.toLowerCase()||s.sci.toLowerCase()===v.toLowerCase();})[0];if(ex)chosen=ex.id;}
    var all=jload(),now=new Date().toISOString(),ent=e?all.filter(function(x){return x.id===e.id;})[0]:{id:uid(),created:now};
    var s=chosen?BYID[chosen]:null;
    ent.sp=s?s.id:null;ent.name=s?LW.name(s):(v.toLowerCase()==="unknown"?"Unknown":v);ent.sci=s?s.sci:"";
    ent.date=f.elements.date.value;ent.time=f.elements.time.value;ent.count=Math.max(1,parseInt(f.elements.count.value,10)||1);
    ent.where=(f.querySelector('input[name="where"]:checked')||{}).value||"Other";ent.notes=f.elements.notes.value.trim();ent.updated=now;
    var ops=[];
    if(pblob){ent.photo=true;ops.push(putPhoto(ent.id,pblob));}else if(removePhoto){ent.photo=false;ops.push(delPhoto(ent.id));}else ent.photo=!!keepPhoto;
    if(!e)all.push(ent);
    Promise.all(ops).catch(function(err){ent.photo=false;alert("Photo couldn’t be stored on this device: "+err.message);}).then(function(){jsave(all);J.edit=null;jshow("list");});
  };
  if(!nm)setTimeout(function(){inp.focus();},50);
}
function jsorted(){return jload().sort(function(a,b){return (b.date+" "+(b.time||"")).localeCompare(a.date+" "+(a.time||""));});}
function jlist(view){
  var a=jsorted();
  if(!a.length){view.innerHTML='<p class="empty">No sightings yet. Hit <b>+ New sighting</b> or tap <b>+ Log this bird</b> on any card.</p>';return;}
  var h='<p class="sinfo">'+a.length+' sighting'+(a.length>1?"s":"")+' · newest first</p><ol class="jtl">',last="";
  a.forEach(function(e){var s=e.sp&&BYID[e.sp];
    if(e.date!==last){h+='<li class="jday">'+esc(fmtDate(e.date))+'</li>';last=e.date;}
    h+='<li class="jent" data-id="'+esc(e.id)+'">'+(e.photo?'<img class="jimg" data-ph="'+esc(e.id)+'" alt="Your photo">':s&&s.ph?'<img src="'+esc(s.ph.sq||s.ph.url)+'" alt="" class="jstock" title="Stock photo: '+esc(s.ph.attr)+'">':'<div class="noimg">?</div>')+
      '<div class="jtx"><b>'+esc(spLabel(e))+'</b>'+(e.count>1?' <span class="jc">×'+e.count+'</span>':'')+'<div class="jmeta">'+esc(e.time||"")+' · '+esc(e.where)+(s?' · <span class="tx-'+s.lik+'">'+LW.LIK[s.lik]+'</span>':e.name!=="Unknown"?' · not on the site list':'')+'</div>'+
      (e.notes?'<div class="jnotes">'+esc(e.notes)+'</div>':'')+'</div><div class="jact"><button type="button" class="jed">Edit</button><button type="button" class="jdel">Delete</button></div></li>';});
  view.innerHTML=h+'</ol>';
  $$("img[data-ph]",view).forEach(function(im){getPhoto(im.getAttribute("data-ph")).then(function(b){if(b)im.src=URL.createObjectURL(b);}).catch(function(){});});
  $$(".jed",view).forEach(function(b){b.onclick=function(){J.edit=b.closest("li").getAttribute("data-id");jshow("add");};});
  $$(".jdel",view).forEach(function(b){b.onclick=function(){var id=b.closest("li").getAttribute("data-id");if(!confirm("Delete this sighting from this device?"))return;
    jsave(jload().filter(function(x){return x.id!==id;}));delPhoto(id).catch(function(){});jshow("list");};});
}
function fmtDate(d){var p=d.split("-");if(p.length<3)return d;var dt=new Date(+p[0],+p[1]-1,+p[2]);return dt.toLocaleDateString("en-US",{weekday:"short",month:"short",day:"numeric",year:"numeric"});}
function jlife(view){
  var a=jload(),m={},unk=0;
  a.forEach(function(e){if(!e.sp&&(e.name||"Unknown")==="Unknown"){unk++;return;}var k=e.sp?"t"+e.sp:"n"+e.name.toLowerCase();
    var r=m[k]||(m[k]={e:e,n:0,tot:0,first:e.date,last:e.date});r.n++;r.tot+=e.count||1;if(e.date<r.first)r.first=e.date;if(e.date>r.last)r.last=e.date;});
  var rows=Object.keys(m).map(function(k){return m[k];}).sort(function(x,y){return x.first.localeCompare(y.first);});
  var birds=rows.filter(function(r){return r.e.sp&&BYID[r.e.sp]&&BYID[r.e.sp].g==="birds";}).length;
  if(!rows.length){view.innerHTML='<p class="empty">Your life list fills up as you log sightings.'+(unk?" ("+unk+" unknown sighting"+(unk>1?"s":"")+" so far.)":"")+'</p>';return;}
  view.innerHTML='<div class="jlstat"><div><b>'+rows.length+'</b><span>species logged</span></div><div><b>'+birds+'</b><span>of '+LW.birds.length+' site birds</span></div><div><b>'+a.length+'</b><span>sightings</span></div>'+(unk?'<div><b>'+unk+'</b><span>unknown</span></div>':'')+'</div>'+
    '<table class="jlife"><thead><tr><th>#</th><th>Species</th><th>Sightings</th><th>Birds counted</th><th>First</th><th>Last</th></tr></thead><tbody>'+
    rows.map(function(r,i){return '<tr><td>'+(i+1)+'</td><td><b>'+esc(spLabel(r.e))+'</b>'+(r.e.sci?'<br><i>'+esc(r.e.sci)+'</i>':'')+'</td><td>'+r.n+'</td><td>'+r.tot+'</td><td>'+esc(r.first)+'</td><td>'+esc(r.last)+'</td></tr>';}).join("")+'</tbody></table>';
}
function jbackup(view){
  view.innerHTML='<div class="jbk"><h4>Export</h4><p class="sinfo">Downloads a file to this device. Keep it somewhere safe (Google Drive, email it to yourself…).</p>'+
    '<label class="jinc"><input type="checkbox" class="incph" checked> Include photos in the JSON backup</label>'+
    '<div class="jbtns"><button type="button" class="more exj">Export JSON</button><button type="button" class="more exc">Export CSV (spreadsheet, no photos)</button></div>'+
    '<h4>Import</h4><p class="sinfo">JSON or CSV made by this journal. Entries are merged: same ID → newer edit wins.</p><input type="file" class="imf" accept=".json,.csv,application/json,text/csv"><p class="jmsg" aria-live="polite"></p>'+
    '<h4>Storage</h4><p class="sinfo jst">Checking…</p></div>';
  var msg=$(".jmsg",view);
  $(".exj",view).onclick=function(){var a=jload(),inc=$(".incph",view).checked,out={app:"linwood-wild-journal",version:1,exported:new Date().toISOString(),note:"Private bird journal backup. Saved on device only.",entries:a,photos:{}};
    var ps=inc?a.filter(function(e){return e.photo;}).map(function(e){return getPhoto(e.id).then(function(b){return b?blobToData(b).then(function(d){out.photos[e.id]=d;}):null;}).catch(function(){});}):[];
    Promise.all(ps).then(function(){download("bird-journal-"+today()+".json",JSON.stringify(out,null,1),"application/json");});};
  $(".exc",view).onclick=function(){var rows=[CSVCOLS.join(",")];jsorted().forEach(function(e){rows.push([e.id,e.date,e.time,spLabel(e),e.sci,e.sp||"",e.count,e.where,e.notes,e.photo?"yes":"no",e.created,e.updated].map(csvCell).join(","));});
    download("bird-journal-"+today()+".csv","\uFEFF"+rows.join("\r\n"),"text/csv");};
  $(".imf",view).onchange=function(){var fl=this.files[0];if(!fl)return;var r=new FileReader();r.onload=function(){
    try{var txt=String(r.result).replace(/^\uFEFF/,""),inc=[],photos={};
      if(/^\s*[\[{]/.test(txt)){var d=JSON.parse(txt);inc=Array.isArray(d)?d:(d.entries||[]);photos=d.photos||{};}
      else{var rows=parseCSV(txt),hd=rows.shift().map(function(x){return x.trim().toLowerCase();});
        inc=rows.map(function(rw){var o={};hd.forEach(function(k,i){o[k]=rw[i];});var tid=+o.inat_taxon_id||null;
          return {id:o.id||uid(),date:o.date,time:o.time||"",sp:tid&&BYID[tid]?tid:null,name:o.species||"Unknown",sci:o.scientific_name||"",count:+o.count||1,where:WHERE.indexOf(o.where)>=0?o.where:"Other",notes:o.notes||"",photo:false,created:o.created||new Date().toISOString(),updated:o.updated||new Date().toISOString()};});}
      var cur=jload(),by={},added=0,upd=0;cur.forEach(function(e){by[e.id]=e;});
      var ops=[];
      inc.forEach(function(e){if(!e||!e.date)return;if(!e.id)e.id=uid();if(e.sp&&!BYID[e.sp])e.sp=null;e.photo=!!(e.photo&&photos[e.id])||(by[e.id]&&by[e.id].photo)||false;
        if(photos[e.id])ops.push(putPhoto(e.id,dataToBlob(photos[e.id])));
        if(!by[e.id]){cur.push(e);by[e.id]=e;added++;}else if((e.updated||"")>(by[e.id].updated||"")){Object.assign(by[e.id],e);upd++;}});
      Promise.all(ops).then(function(){jsave(cur);msg.textContent="Imported: "+added+" new, "+upd+" updated.";});
    }catch(err){msg.textContent="Couldn’t import that file: "+err.message;}};r.readAsText(fl);};
  var st=$(".jst",view),a=jload();
  var t=a.length+" sightings ("+a.filter(function(e){return e.photo;}).length+" with photos) on this device.";
  if(navigator.storage&&navigator.storage.persisted){navigator.storage.persisted().then(function(p){st.textContent=t+(p?" Browser has granted persistent storage.":" Tip: export backups — the browser may clear site data if storage runs low.");});}else st.textContent=t;
}
function logBird(id){var sec=$("#journal");if(!sec)return;closeModal();J.edit=null;jshow("add",id);sec.scrollIntoView({behavior:"smooth"});}

/* ---------- 3. DESCRIBE-A-BIRD SEARCH ---------- */
var COLORS=["red","orange","yellow","olive","green","blue","brown","rufous","buff","gray","black","white","pink","purple","iridescent"];
var SYN={red:"red",crimson:"red",scarlet:"red",cherry:"red",ruby:"red",reddish:"red",redbird:"red",
  orange:"orange",orangey:"orange",orangish:"orange",tangerine:"orange",
  yellow:"yellow",yellowish:"yellow",gold:"yellow",golden:"yellow",lemon:"yellow",
  olive:"olive",greenish:"olive",green:"green",emerald:"green",
  blue:"blue",bluish:"blue",azure:"blue",navy:"blue",teal:"blue",
  brown:"brown",brownish:"brown",drab:"brown",dusky:"brown",mottled:"brown",
  rufous:"rufous",rusty:"rufous",rust:"rufous",chestnut:"rufous",cinnamon:"rufous",russet:"rufous",auburn:"rufous",copper:"rufous",
  buff:"buff",buffy:"buff",tan:"buff",beige:"buff",cream:"buff",fawn:"buff",sandy:"buff",
  gray:"gray",grey:"gray",grayish:"gray",greyish:"gray",slate:"gray",silver:"gray",ash:"gray",
  black:"black",blackish:"black",dark:"black",jet:"black",white:"white",whitish:"white",snowy:"white",
  pink:"pink",pinkish:"pink",rosy:"pink",rose:"pink",purple:"purple",purplish:"purple",violet:"purple",
  iridescent:"iridescent",glossy:"iridescent",shiny:"iridescent",metallic:"iridescent"};
var NEAR={red:["rufous","pink","orange"],rufous:["red","orange","brown"],orange:["rufous","red","yellow"],yellow:["olive","orange"],olive:["yellow","green"],green:["olive","iridescent"],
  blue:["gray","purple"],brown:["rufous","buff"],buff:["brown"],gray:["blue","white"],black:["iridescent"],white:["gray"],pink:["red","purple"],purple:["iridescent","blue","pink"],iridescent:["purple","green","black"]};
var PART={cap:"cap",crown:"cap",head:"head",hood:"head",throat:"throat",chin:"throat",breast:"breast",chest:"breast",front:"breast",belly:"belly",underparts:"belly",underside:"belly",tummy:"belly",
  back:"back",wing:"wing",wings:"wing",tail:"tail",rump:"rump",bill:"bill",beak:"bill",legs:"legs",leg:"legs",feet:"legs",eye:"eye",eyes:"eye",face:"face",cheek:"face",cheeks:"face",neck:"neck",nape:"neck",
  shoulder:"shoulder",shoulders:"shoulder",epaulets:"shoulder",capped:"cap",crowned:"cap",crested:"crest",headed:"head",hooded:"head",throated:"throat",breasted:"breast",chested:"breast",bellied:"belly",
  backed:"back",winged:"wing",tailed:"tail",billed:"bill",rumped:"rump",eyed:"eye",necked:"neck",shouldered:"shoulder",faced:"face",cheeked:"face",masked:"mask",mask:"mask",crest:"crest",bib:"bib",flanks:"flanks",sides:"flanks",patch:"patch",stripe:"stripe",band:"band"};
var PARTALT={cap:["cap","crown","head","crest"],head:["head","cap","crown","hood","crest","face"],breast:["breast","throat","belly"],belly:["belly","breast","flanks"],throat:["throat","bib","breast"],
  face:["face","mask","cheek"],wing:["wing","wingbars","shoulder"],neck:["neck","nape","collar"],eye:["eye","eyering"],mask:["mask","face"],shoulder:["shoulder","wing"],crest:["crest","cap","head"],bib:["bib","throat"],flanks:["flanks","belly"]};
var PATTERN={streaked:"streaked",streaky:"streaked",streaks:"streaked",striped:"streaked",stripes:"streaked",stripy:"streaked",streak:"streaked",
  spotted:"spotted",spots:"spotted",spotty:"spotted",speckled:"spotted",speckles:"spotted",dotted:"spotted",
  barred:"barred",bars:"barred",banded:"barred",plain:"plain"};
var MARKW=[[/\b(crest(ed)?|tuft(ed)?|mohawk|crested)\b/,"crest"],[/\bwing ?bars?\b/,"wingbars"],[/\beye ?rings?\b|\bspectacles\b/,"eyering"],[/\b(eye ?stripes?|eyebrows?|eye ?brows?|supercilium)\b/,"eyestripe"],
  [/\blong[- ]tail(ed)?\b/,"long-tail"],[/\b(fork(ed)?|split)[- ]tail(ed)?\b|\bforked\b/,"forked-tail"],[/\blong[- ]legs?(ged)?\b|\bstilts?\b/,"long-legs"],[/\blong[- ]neck(ed)?\b/,"long-neck"],
  [/\blong[- ](bill|beak)(ed)?\b/,"long-bill"],[/\b(curved|down-?curved|decurved)( bill| beak)?\b/,"curved-bill"],[/\bhook(ed)?( bill| beak)?\b/,"hooked-bill"],
  [/\b(thick|cone|conical|seed)[- ]?(bill|beak)\b|\bfinch[- ]bill\b/,"conical-bill"],[/\bmasks?(ed)?\b/,"mask"],[/\b(ear ?tufts|horns)\b/,"ear-tufts"],[/\bbibs?\b/,"bib"],[/\biridescent|glossy|shiny\b/,"iridescent"],
  [/\bshort[- ]tail(ed)?\b|\bstubby tail\b/,"short-tail"],[/\b(cocked|upturned|raised) tail\b/,"cocked-tail"],[/\btail[- ]?(wag|bob|pump)\w*\b/,"tail-wagging"]];
var SIZEW=[[/\b(tiny|teeny|very small|hummingbird[- ]sized?|kinglet[- ]sized?)\b/,"tiny"],[/\b(small|little|smallish|sparrow[- ]sized?|chickadee[- ]sized?|finch[- ]sized?)\b/,"small"],
  [/\b(medium|mid-sized|robin[- ]sized?|jay[- ]sized?|starling[- ]sized?|cardinal[- ]sized?)\b/,"medium"],[/\b(big|biggish|large-ish)\b/,"big"],[/\b(large|crow[- ]sized?|pigeon[- ]sized?|gull[- ]sized?|hawk[- ]sized?|duck[- ]sized?)\b/,"large"],
  [/\b(huge|very large|very big|giant|enormous|goose[- ]sized?|heron[- ]sized?|eagle[- ]sized?)\b/,"huge"]];
var SIZER={tiny:[0,11.5],small:[11.5,20],medium:[19,30],large:[30,56],big:[29,999],huge:[55,999]},SIZES=["tiny","small","medium","large","huge"];
var BEHW=[[/\b(feeders?|bird ?feeders?|suet|seed|sunflower)\b/,"feeder"],[/\b(ground|lawn|grass|hopping|walking|scratching|on the deck)\b/,"ground"],[/\b(trunk|climbing|creeping|bark|tree trunk|woodpecker-like)\b/,"trunk"],
  [/\b(flying over|flyover|fly-over|overhead|flying by|flew over|in flight)\b/,"flyover"],[/\b(soaring|circling|gliding|riding thermals)\b/,"soaring"],[/\b(swimming|floating|paddling|on the water)\b/,"swimming"],
  [/\b(diving|dove in|plunging|dives)\b/,"diving"],[/\b(wading|standing in (the )?water|in the shallows|stalking)\b/,"wading"],[/\b(hovering|hovers|hovered)\b/,"hovering"],[/\b(flocks?|group|bunch|crowd)\b/,"flocks"],
  [/\b(night|nocturnal|at dusk|after dark|hooting)\b/,"night"],[/\b(catching insects|fly-?catching|sallying|darting)\b/,"flycatching"],[/\b(wires?|power ?lines?|utility lines?)\b/,"wires"],[/\b(probing|poking|in the mud)\b/,"probing"],[/\b(bushes|shrubs?|hedges?|thicket)\b/,"shrubs"]];
var HABW=[[/\b(yard|backyard|garden|deck|porch|house)\b/,"yard"],[/\b(woods|forest|trees|woodland)\b/,"woods"],[/\b(marsh|salt ?marsh|reeds|cattails|wetland)\b/,"marsh"],[/\b(water|pond|lake|bay|creek|lagoon|river|ocean)\b/,"water"],
  [/\b(field|meadow|farm|open country)\b/,"field"],[/\b(beach|shore|sand|mudflat|mud ?flat|coast)\b/,"beach"],[/\b(sky|high up)\b/,"sky"]];
var STOP={a:1,an:1,the:1,bird:1,birds:1,with:1,and:1,"&":1,of:1,on:1,in:1,at:1,its:1,it:1,is:1,has:1,had:1,was:1,that:1,very:1,kind:1,some:1,like:1,looks:1,looked:1,i:1,saw:1,see:1,seen:1,my:1,to:1,sort:1,mostly:1,all:1,over:1,by:1,little:1,big:1,small:1,large:1,tiny:1,medium:1,huge:1,sized:1,size:1,colored:1,coloured:1,color:1,colour:1};
function parseQuery(q){
  q=" "+q.toLowerCase().replace(/[^a-z0-9\- ]+/g," ").replace(/\s+/g," ")+" ";
  var r={colors:[],combos:[],pats:[],marks:[],size:null,beh:[],hab:[],words:[]};
  SIZEW.forEach(function(x){if(!r.size&&x[0].test(q))r.size=x[1];});
  MARKW.forEach(function(x){if(x[0].test(q)&&r.marks.indexOf(x[1])<0)r.marks.push(x[1]);});
  BEHW.forEach(function(x){if(x[0].test(q))r.beh.push(x[1]);});
  HABW.forEach(function(x){if(x[0].test(q))r.hab.push(x[1]);});
  var tk=q.trim().split(/[ ]+/);
  var pend=[];   // colours / patterns waiting for a body part ("black cap", "streaky chest", "red and black wings")
  for(var i=0;i<tk.length;i++){var t=tk[i],c=SYN[t],p=PART[t],pt=PATTERN[t];
    if(t.indexOf("-")>0){var hp=t.split("-");if(SYN[hp[0]]&&PART[hp[1]]){r.combos.push(SYN[hp[0]]+"-"+PART[hp[1]]);if(r.colors.indexOf(SYN[hp[0]])<0)r.colors.push(SYN[hp[0]]);continue;}
      if(SYN[hp[0]]&&SYN[hp[1]]){[hp[0],hp[1]].forEach(function(x){if(r.colors.indexOf(SYN[x])<0)r.colors.push(SYN[x]);});continue;}
      Array.prototype.splice.apply(tk,[i+1,0].concat(hp.filter(Boolean)));continue;}
    if(c){if(r.colors.indexOf(c)<0&&!(c==="black"&&t==="dark"))r.colors.push(c);pend.push(c);continue;}
    if(pt){pend.push("#"+pt);if(r.pats.indexOf(pt)<0)r.pats.push(pt);continue;}
    if(p){pend.forEach(function(x){r.combos.push((x.charAt(0)==="#"?x.slice(1):x)+"-"+p);});
      if(!pend.length&&p==="crest"&&r.marks.indexOf("crest")<0)r.marks.push("crest");
      pend=[];continue;}
    if(t==="and"||t==="or"||t==="ish"||t==="light"||t==="bright"||t==="pale"||t==="with"||t==="a"||t==="its"||t==="bit")continue;
    pend=[];
    if(!STOP[t]&&t.length>2&&!/^\d+$/.test(t))r.words.push(t);
  }
  // colour combos describe a part, not the whole bird: "small brown bird with streaky chest and red cap" -> body colours = brown
  r.body=r.colors.filter(function(c){return !r.combos.some(function(k){return k.split("-")[0]===c;})||tk.indexOf("bird")>tk.indexOf(c)&&tk.indexOf("bird")>=0;});
  return r;
}
function hasMark(T,re){return T.k.some(function(m){return re.test(m);});}
function score(s,T,Q,o){
  var sc=0,why=[],miss=[];
  if(!T)return null;
  var cs=T.c,fcs=T.fc||[];
  Q.body.forEach(function(c){
    if(cs.indexOf(c)>=0){sc+=cs[0]===c?4:3;why.push(c);}
    else if(fcs.indexOf(c)>=0){sc+=2;why.push(c+" (female/young)");}
    else if(c==="dark"){}
    else if((NEAR[c]||[]).some(function(n){return cs.indexOf(n)>=0;})||T.k.some(function(m){return m.split("-")[0]===c;})){sc+=1;why.push("~"+c);}
    else{sc-=2;miss.push("not "+c);}});
  Q.combos.forEach(function(k){var p=k.split("-"),col=p[0],part=p[1],alts=PARTALT[part]||[part];
    var isPat=["streaked","spotted","barred","plain"].indexOf(col)>=0,re;
    if(isPat){re=new RegExp("^("+(col==="streaked"?"streaked|striped|black-streaks|rufous-streaked|streaks":col)+")-?("+alts.join("|")+")?");
      var hit=T.k.some(function(m){var q=m.split("-");return (q[0]===col||(col==="streaked"&&/streak|stripe/.test(q[0]))||(col==="spotted"&&/spot/.test(q[0]))||(col==="barred"&&/barr/.test(q[0])))&&(q.length===1||alts.indexOf(q[q.length-1])>=0);});
      if(hit){sc+=5;why.push(col+" "+part);}else if(T.k.some(function(m){return m.indexOf(col.slice(0,4))>=0;})){sc+=1.5;why.push("~"+col);}else{sc-=1.5;miss.push("no "+col+" "+part);}return;}
    var exact=T.k.some(function(m){var q=m.split("-");return q[0]===col&&alts.indexOf(q[q.length-1])>=0;});
    var near=!exact&&T.k.some(function(m){var q=m.split("-");return (NEAR[col]||[]).indexOf(q[0])>=0&&alts.indexOf(q[q.length-1])>=0;});
    var other=T.k.some(function(m){var q=m.split("-");return q[0]!==col&&SYN[q[0]]&&alts.slice(0,1).indexOf(q[q.length-1])>=0;});
    if(exact){sc+=5.5;why.push(col+" "+part);}else if(near){sc+=2.5;why.push("~"+col+" "+part);}else{sc-=other?2:1;miss.push("no "+col+" "+part);}
  });
  Q.pats.forEach(function(p){if(Q.combos.some(function(k){return k.indexOf(p+"-")===0;}))return;
    if(hasMark(T,new RegExp(p==="streaked"?"streak|stripe":p==="spotted"?"spot":p==="barred"?"barr":"^plain"))){sc+=3;why.push(p);}else{sc-=1;miss.push("not "+p);}});
  Q.marks.forEach(function(m){var re={crest:/(^|-)crest$|^crest/,"wingbars":/wingbar/,"eyering":/eyering|spectacles/,"eyestripe":/eyestripe|eyebrow/,"long-tail":/long-tail|pointed-tail/,"mask":/mask/,
      "ear-tufts":/ear-tufts|horns/,"bib":/bib|throat/,"iridescent":/iridescent/}[m]||new RegExp("^"+m);
    if(hasMark(T,re)||(m==="iridescent"&&cs.indexOf("iridescent")>=0)){sc+=3.5;why.push(m.replace("-"," "));}else{sc-=1.5;miss.push("no "+m.replace("-"," "));}});
  if(Q.size&&T.len){var R=SIZER[Q.size],L=T.len;
    if(L>=R[0]&&L<=R[1]){sc+=3;why.push(Q.size+" ("+Math.round(L)+" cm)");}
    else{var d=L<R[0]?(R[0]-L)/R[0]:(L-R[1])/R[1];if(d<0.25){sc+=1;why.push("~"+Q.size);}else{sc-=Math.min(5,2+d*3);miss.push(Math.round(L)+" cm long");}}}
  Q.beh.forEach(function(b){if((T.b||[]).indexOf(b)>=0){sc+=2;why.push(b);}else sc-=0.75;});
  Q.hab.forEach(function(h){if((T.h||[]).indexOf(h)>=0){sc+=1.5;why.push(h);}else sc-=0.5;});
  var nm=(s.com+" "+s.sci+" "+(s.family_com||"")).toLowerCase();
  Q.words.forEach(function(w){var ww=w.replace(/s$/,"");if(new RegExp("\\b"+ww).test(nm)){sc+=6;why.push("name: "+w);}});
  var prior=s.lik==="likely"?2:s.lik==="possible"?1:0;
  if(o.month){var mv=s.m[LW.CUR]||0;prior+=mv>0?Math.min(2.5,Math.log(1+mv)/Math.LN10*1):-2;}
  return {s:s,sc:sc+prior,raw:sc,why:why,miss:miss};
}
function describeSearch(Q,o){
  var res=LW.birds.map(function(s){return score(s,TRAITS[s.id],Q,o);}).filter(Boolean);
  res.sort(function(a,b){return b.sc-a.sc||b.s.A-a.s.A;});return res;
}
var CHIPS={size:[["tiny","Tiny (<12 cm)"],["small","Small (sparrow)"],["medium","Medium (robin/jay)"],["large","Large (crow/gull)"],["huge","Huge (heron/goose)"]],
  color:COLORS.filter(function(c){return c!=="olive";}).concat(["olive"]),
  mark:[["crest","Crest"],["black cap","Black cap"],["red cap","Red cap/crown"],["streaked breast","Streaky chest"],["spotted breast","Spotted chest"],["wingbars","Wing bars"],["eyering","Eye ring"],["mask","Mask"],["long tail","Long tail"],["forked tail","Forked tail"],["long legs","Long legs"],["long bill","Long bill"],["curved bill","Curved bill"],["hooked bill","Hooked bill"],["conical bill","Thick seed bill"]],
  beh:[["feeder","At the feeder"],["ground","On the ground"],["climbing trunk","Climbing trunks"],["flying over","Flying over"],["soaring","Soaring"],["swimming","Swimming"],["diving","Diving"],["wading","Wading"],["hovering","Hovering"],["flock","In a flock"],["night","At night"]],
  hab:[["yard","Yard"],["woods","Trees/woods"],["marsh","Marsh"],["water","Water/bay"],["field","Field"],["beach","Beach/shore"]]};
var SW={red:"#e0352b",orange:"#ff8a1f",yellow:"#ffd52e",olive:"#8a8f3a",green:"#2fa84f",blue:"#2f7de1",brown:"#7a5230",rufous:"#b5502a",buff:"#d8b98a",gray:"#8d9590",black:"#111",white:"#f4f4f4",pink:"#f28bb0",purple:"#7d4bc2",iridescent:"linear-gradient(135deg,#2b6 0,#36c 50%,#a3c 100%)"};
function renderDescribe(){
  var box=$("#describeBox");if(!box)return;
  function chipRow(key,label,arr){return '<div class="drow"><span class="dlab">'+label+'</span><div class="chips" data-k="'+key+'">'+arr.map(function(x){var v=Array.isArray(x)?x[0]:x,l=Array.isArray(x)?x[1]:x;
    return '<button type="button" class="chip" data-v="'+esc(v)+'" aria-pressed="false">'+(key==="color"?'<i style="background:'+SW[v]+'"></i>':'')+esc(l)+'</button>';}).join("")+'</div></div>';}
  box.innerHTML='<form class="dform" role="search"><input type="search" class="dq" placeholder="e.g. small brown bird with streaky chest and red cap" aria-label="Describe the bird"><button type="submit" class="more dgo">Find it</button></form>'+
    '<div class="dex">Try: <button type="button">red bird with crest</button><button type="button">small black and white bird at feeder with black cap</button><button type="button">blue bird with crest</button><button type="button">big white bird wading in the marsh</button><button type="button">small brown bird with streaky chest and red cap</button></div>'+
    '<details class="dfil"><summary>Pick traits instead</summary>'+chipRow("size","Size",CHIPS.size)+chipRow("color","Main colors",CHIPS.color)+chipRow("mark","Markings",CHIPS.mark)+chipRow("beh","Behavior / where seen",CHIPS.beh)+chipRow("hab","Habitat",CHIPS.hab)+'</details>'+
    '<label class="dmon"><input type="checkbox" class="dm" checked> Favor birds that are around in <b>'+LW.MONL[LW.CUR]+'</b></label> <button type="button" class="dclr">Clear</button>'+
    '<div class="dres" aria-live="polite"></div>';
  var q=$(".dq",box),res=$(".dres",box),tm,shownN=10,lastQ=null,lastR=[];
  function chipText(){var parts=[];$$(".chips",box).forEach(function(c){var k=c.getAttribute("data-k"),on=$$(".chip.on",c).map(function(b){return b.getAttribute("data-v");});
    if(!on.length)return;if(k==="color")parts.push(on.join(" and ")+" bird");else if(k==="size")parts.push(on[0]);else parts.push("with "+on.join(" and "));});return parts.join(" ");}
  function run(){var text=(q.value+" "+chipText()).trim();if(!text){res.innerHTML='<p class="empty">Describe what you saw, or pick some traits.</p>';return;}
    traits().then(function(){var Q=parseQuery(text),o={month:$(".dm",box).checked},r=describeSearch(Q,o);shownN=10;lastQ=Q;lastR=r.slice(0,40);draw(Q,lastR.slice(0,shownN));}).catch(function(e){res.innerHTML='<p class="empty">Trait data failed to load ('+esc(e.message)+').</p>';});}
  function draw(Q,r){
    var heard=[].concat(Q.size?[Q.size]:[],Q.body,Q.combos.map(function(x){return x.replace("-"," ");}),Q.pats.filter(function(p){return !Q.combos.some(function(k){return k.indexOf(p)===0;});}),Q.marks.map(function(m){return m.replace("-"," ");}),Q.beh,Q.hab,Q.words.map(function(w){return "“"+w+"”";}));
    var top=r.length?r[0].sc:0;
    res.innerHTML='<p class="sinfo">Understood: '+(heard.length?heard.map(function(h){return '<span class="dh">'+esc(h)+'</span>';}).join(" "):"nothing yet — try colors, size, markings")+'</p><ol class="dlist">'+
      r.map(function(x,i){var s=x.s,T=TRAITS[s.id],pct=Math.max(4,Math.min(100,Math.round(100*x.sc/(top||1))));
        return '<li class="dcard"><span class="drk">'+(i+1)+'</span>'+(s.ph?'<button type="button" class="dph" data-gal="'+s.id+'" aria-label="Photos of '+esc(LW.name(s))+'"><img loading="lazy" src="'+esc(s.ph.sq||s.ph.url)+'" alt="'+esc(LW.name(s))+'"></button>':'<div class="noimg">?</div>')+
          '<div class="dtx"><b><a href="'+LW.turl(s)+'" target="_blank" rel="noopener">'+esc(LW.name(s))+'</a></b> <span class="tx-'+s.lik+'">'+LW.LIK[s.lik]+'</span>'+(s.m[LW.CUR]>0?' <span class="dnow">around in '+LW.MON[LW.CUR]+'</span>':' <span class="dno">not usually in '+LW.MON[LW.CUR]+'</span>')+
          '<div class="dbar"><i style="width:'+pct+'%"></i></div><div class="dwhy">'+x.why.slice(0,7).map(function(w){return '<span class="ok">\u2713 '+esc(w)+'</span>';}).join("")+x.miss.slice(0,3).map(function(w){return '<span class="no">\u2717 '+esc(w)+'</span>';}).join("")+'</div>'+
          '<div class="dmeta">'+esc(s.season||"")+(T&&T.len?' · ~'+Math.round(T.len)+' cm':'')+(T&&T.q==="wiki"?' · <span title="Traits parsed from Wikipedia text, lower quality">auto traits</span>':'')+'</div></div>'+
          '<div class="dact">'+(s.snd?LW.playBtn(s,"mini"):'')+'<button type="button" class="logbtn" data-log="'+s.id+'">+ Log</button></div></li>';}).join("")+'</ol>'+
      (r.length<lastR.length?'<button type="button" class="more dmore">Show more matches</button>':'');
    var mb=$(".dmore",res);if(mb)mb.onclick=function(){shownN+=10;draw(lastQ,lastR.slice(0,shownN));};
  }
  $(".dform",box).onsubmit=function(e){e.preventDefault();run();};
  q.addEventListener("input",function(){clearTimeout(tm);tm=setTimeout(run,250);});
  $$(".dex button",box).forEach(function(b){b.onclick=function(){q.value=b.textContent;run();};});
  $$(".chip",box).forEach(function(b){b.onclick=function(){var row=b.parentNode;if(row.getAttribute("data-k")==="size")$$(".chip",row).forEach(function(x){if(x!==b){x.classList.remove("on");x.setAttribute("aria-pressed","false");}});
    b.classList.toggle("on");b.setAttribute("aria-pressed",b.classList.contains("on"));run();};});
  $(".dm",box).onchange=run;
  $(".dclr",box).onclick=function(){q.value="";$$(".chip.on",box).forEach(function(b){b.classList.remove("on");b.setAttribute("aria-pressed","false");});res.innerHTML="";};
  window.LWsearch=function(t,month){return traits().then(function(){return describeSearch(parseQuery(t),{month:month!==false}).slice(0,10).map(function(x){return LW.name(x.s)+" "+x.sc.toFixed(1);});});};
}

/* ---------- wiring ---------- */
document.addEventListener("click",function(e){
  var g=e.target.closest&&e.target.closest("[data-gal]");if(g){e.preventDefault();openGallery(+g.getAttribute("data-gal"));return;}
  var l=e.target.closest&&e.target.closest("[data-log]");if(l){e.preventDefault();logBird(+l.getAttribute("data-log"));}
});
function init(){LW=window.LW;LW.species.forEach(function(s){BYID[s.id]=s;});renderDescribe();renderJournal();traits().catch(function(){});}
if(window.LW)init();else document.addEventListener("lw-data",init);
})();
