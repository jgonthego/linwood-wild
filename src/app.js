(function(){
"use strict";
var MON=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
var MONL=["January","February","March","April","May","June","July","August","September","October","November","December"];
var CUR=new Date().getMonth();
var LIK={likely:"Likely",possible:"Possible",rare:"Rare"};
var LIKO={likely:0,possible:1,rare:2};
var GANGS={
  yard:{name:"The Locals",desc:"Yard & neighborhood birds — songbirds, woodpeckers, doves, hummingbirds.",c:"#c6ff3d"},
  marsh:{name:"Marsh Mafia",desc:"Flyovers & nearby marsh — herons, egrets, gulls, terns, shorebirds and ducks that work the nearby salt marsh or pass overhead.",c:"#3fd0ff"},
  raptor:{name:"Sky Predators",desc:"Hawks, eagles, falcons, ospreys, owls & vultures.",c:"#ff4f2e"}
};
var PAGE=48;
function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
function fmt(n){return Number(n).toLocaleString("en-US");}
function name(s){return s.com||s.sci;}
function turl(s){return "https://www.inaturalist.org/taxa/"+s.id;}
function el(tag,cls,html){var e=document.createElement(tag);if(cls)e.className=cls;if(html!=null)e.innerHTML=html;return e;}
function unit(s){return s.g==="birds"?" per 10k bird records":" records";}

function season(s){
  var mx=Math.max.apply(null,s.m)||1,h='<div class="season" role="img" aria-label="Months recorded nearby: '+
    esc(s.m.map(function(v,i){return v?MON[i]:null;}).filter(Boolean).join(", ")||"none")+'">';
  for(var i=0;i<12;i++){var a=s.m[i]?(0.18+0.82*s.m[i]/mx).toFixed(2):0;
    h+='<span class="'+(i===CUR?"cur":"")+'" style="--a:'+a+'" title="'+MON[i]+': '+s.m[i]+unit(s)+'"></span>';}
  return h+'</div><div class="mlab">'+MON.map(function(m){return "<span>"+m[0]+"</span>";}).join("")+'</div>';
}
function photoHtml(s){
  if(!s.ph)return '<div class="noimg" aria-hidden="true">?</div>';
  return '<img loading="lazy" decoding="async" src="'+esc(s.ph.url)+'" alt="'+esc(name(s))+' photo">';
}
function attrHtml(s){
  if(!s.ph)return '<div class="attr">No openly licensed photo available on iNaturalist.</div>';
  return '<div class="attr">Photo: '+esc(s.ph.attr)+' · <a href="'+esc(s.ph.license_url)+'" rel="noopener license" target="_blank">'+esc(s.ph.license)+'</a></div>';
}
var AUD=new Audio(),AUDBTN=null;AUD.preload="none";
function stopAud(){AUD.pause();if(AUDBTN){AUDBTN.classList.remove("on");AUDBTN.textContent="\u25B6";AUDBTN.setAttribute("aria-label",AUDBTN.getAttribute("data-l"));}AUDBTN=null;}
AUD.addEventListener("ended",stopAud);
function playBtn(s,cls){
  var l="Play "+(s.snd.kind?s.snd.kind.toLowerCase():"sound")+" of "+name(s);
  return '<button type="button" class="play '+(cls||"")+'" data-snd="'+esc(s.snd.file)+'" data-l="'+esc(l)+'" aria-label="'+esc(l)+'">\u25B6</button>';
}
function toggle(btn){
  if(AUDBTN===btn){stopAud();return;}
  stopAud();AUD.src=btn.getAttribute("data-snd");
  var p=AUD.play();if(p&&p.catch)p.catch(function(){stopAud();});
  AUDBTN=btn;btn.classList.add("on");btn.textContent="\u25A0";btn.setAttribute("aria-label","Stop");
}
document.addEventListener("click",function(e){var b=e.target.closest&&e.target.closest("button.play[data-snd]");if(b){e.preventDefault();toggle(b);}});
function sndHtml(s){
  if(!s.snd)return "";
  var a=s.snd;
  return '<div class="snd">'+playBtn(s)+'<div class="sinfo"><b>'+(a.kind||"Sound")+'</b> · '+esc(a.where)+(a.date?" ("+esc(a.date.slice(0,4))+")":"")+
    '<br>'+esc(a.attr)+' · <a href="'+esc(a.license_url)+'" target="_blank" rel="noopener license">'+esc(a.license)+'</a> · <a href="'+esc(a.obs)+'" target="_blank" rel="noopener">source</a></div></div>';
}
function evid(s){
  return '<div class="evid" title="GBIF records since 2000 (eBird, iNaturalist, museums)">Records: <b>'+fmt(s.A)+'</b> ≤2 km · <b>'+fmt(s.B)+'</b> ≤8 km · <b>'+fmt(s.C)+'</b> ≤15 km</div>';
}
function card(s){
  var c=el("article","card");
  var badge='<span class="badge b-'+s.lik+'">'+LIK[s.lik]+'</span>'+(s.logged?'<span class="badge2" title="Research-grade iNaturalist sightings within ~5 km (mainland)">Logged near here: '+s.logged+'</span>':'');
  var fact=s.fact?'<details class="fx"><summary>Fun fact</summary><p class="fact">'+esc(s.fact)+
    (s.wiki_url?' <a href="'+esc(s.wiki_url)+'" target="_blank" rel="noopener">— Wikipedia</a>':'')+'</p></details>':"";
  var where=s.cat?'<div class="where w-'+s.cat+'">'+(s.cat==="marsh"?"Flyover / nearby marsh":s.cat==="raptor"?"Raptor":"Yard &amp; neighborhood")+'</div>':'';
  c.innerHTML='<button type="button" class="ph" data-gal="'+s.id+'" aria-label="Open photo gallery: '+esc(name(s))+'">'+photoHtml(s)+badge+(s.ph?'<span class="galhint" aria-hidden="true">'+(s.g==="birds"?"\u2642\u2640 ":"")+'PHOTOS</span>':'')+'</button>'+
    '<div class="cb"><h3><a href="'+turl(s)+'" target="_blank" rel="noopener">'+esc(name(s))+'</a></h3>'+
    '<div class="sci">'+esc(s.sci)+'</div>'+
    '<div class="meta"><span class="sea">'+esc(s.season||"")+'</span><span>'+esc(s.family_com||s.family||"")+'</span></div>'+
    where+season(s)+evid(s)+sndHtml(s)+fact+'<button type="button" class="logbtn" data-log="'+s.id+'">+ Log this '+(s.g==="birds"?"bird":"sighting")+'</button>'+attrHtml(s)+'</div>';
  return c;
}

function renderHero(birds){
  var box=document.getElementById("heroPics");
  birds.filter(function(s){return s.ph&&s.lik==="likely";}).sort(function(a,b){return b.A-a.A;}).slice(0,4).forEach(function(s,i){
    var f=el("figure","hp hp"+i);
    f.innerHTML='<a href="'+turl(s)+'" data-gal="'+s.id+'"><img src="'+esc(s.ph.url)+'" alt="'+esc(name(s))+'"></a><figcaption><b>'+esc(name(s))+'</b><span>'+esc(s.ph.attr)+' · '+esc(s.ph.license)+'</span></figcaption>';
    box.appendChild(f);});
}
function renderNow(birds){
  var m=CUR;
  document.getElementById("nowMonth").textContent=MONL[m];
  Array.prototype.forEach.call(document.querySelectorAll(".nowm"),function(e){e.textContent=MONL[m];});
  var list=birds.filter(function(s){return s.m[m]>0&&s.lik!=="rare";}).sort(function(a,b){return b.m[m]-a.m[m];});
  var ol=document.getElementById("nowList"),shown=0;
  function more(k){
    list.slice(shown,shown+k).forEach(function(s,i){
      var li=el("li");
      li.innerHTML='<span class="rk">'+(shown+i+1)+'</span>'+(s.ph?'<button type="button" class="nowph" data-gal="'+s.id+'" aria-label="Photos of '+esc(name(s))+'"><img loading="lazy" src="'+esc(s.ph.sq||s.ph.url)+'" alt="'+esc(name(s))+'" title="Photo: '+esc(s.ph.attr)+' ('+esc(s.ph.license)+')"></button>':'<div class="noimg">?</div>')+
        '<div><div class="nm"><a href="'+turl(s)+'" target="_blank" rel="noopener">'+esc(name(s))+'</a></div><div class="sc">'+esc(s.sci)+'</div><div class="ct"><span class="tx-'+s.lik+'">'+LIK[s.lik]+'</span> · '+s.m[m]+' per 10k</div></div>'+(s.snd?playBtn(s):"");
      ol.appendChild(li);});
    shown+=k;
    if(shown>=list.length&&btn)btn.remove();
  }
  var btn=el("button","more","Show more "+MONL[m]+" birds ("+list.length+" total)");
  btn.type="button";btn.onclick=function(){more(24);};
  ol.after(btn);more(12);
}
function renderQuiz(birds){
  var box=document.getElementById("quizBox");
  var pool=birds.filter(function(s){return s.lik==="likely"&&s.m[CUR]>0;});
  var withSnd=pool.filter(function(s){return s.snd;});
  if(withSnd.length<4||pool.length<4){box.innerHTML='<p class="empty">Not enough recordings for this month yet.</p>';return;}
  var score=0,tries=0,streak=0,last=null;
  box.innerHTML='<div class="qtop"><button type="button" class="play qplay" aria-label="Play mystery bird">\u25B6</button>'+
    '<div class="qscore"><span>Score</span><b class="qs">0 / 0</b></div><div class="qscore"><span>Streak</span><b class="qk">0</b></div></div>'+
    '<div class="qopts"></div><div class="qres" aria-live="polite"></div><button type="button" class="more qnext">Next bird →</button>'+
    '<p class="sinfo">'+withSnd.length+' likely '+MONL[CUR]+' birds are in the quiz. Credits appear after you answer.</p>';
  var qb=box.querySelector(".qplay"),opts=box.querySelector(".qopts"),res=box.querySelector(".qres"),nx=box.querySelector(".qnext");
  function shuffle(a){for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1)),t=a[i];a[i]=a[j];a[j]=t;}return a;}
  function round(){
    stopAud();res.innerHTML="";nx.style.visibility="hidden";
    var ans;do{ans=withSnd[Math.floor(Math.random()*withSnd.length)];}while(ans===last&&withSnd.length>1);last=ans;
    var others=shuffle(pool.filter(function(s){return s!==ans&&name(s)!==name(ans);})).slice(0,3);
    qb.setAttribute("data-snd",ans.snd.file);qb.setAttribute("data-l","Play mystery bird");
    opts.innerHTML="";
    shuffle([ans].concat(others)).forEach(function(s){
      var b=el("button",null,esc(name(s)));b.type="button";
      b.onclick=function(){
        tries++;var ok=s===ans;if(ok){score++;streak++;}else streak=0;
        Array.prototype.forEach.call(opts.children,function(x){x.disabled=true;if(x.textContent===name(ans))x.classList.add("right");});
        if(!ok)b.classList.add("wrong");
        box.querySelector(".qs").textContent=score+" / "+tries;box.querySelector(".qk").textContent=streak;
        res.innerHTML=(ans.ph?'<img src="'+esc(ans.ph.sq||ans.ph.url)+'" alt="'+esc(name(ans))+'">':'')+(ok?"Nailed it! ":"Nope — ")+
          'that was a <a href="'+turl(ans)+'" target="_blank" rel="noopener">'+esc(name(ans))+'</a>.'+
          '<div class="sinfo">Recording: '+esc(ans.snd.attr)+' · <a href="'+esc(ans.snd.license_url)+'" target="_blank" rel="noopener license">'+esc(ans.snd.license)+'</a> · <a href="'+esc(ans.snd.obs)+'" target="_blank" rel="noopener">source</a>'+
          (ans.ph?'<br>Photo: '+esc(ans.ph.attr)+' · '+esc(ans.ph.license):'')+'</div>';
        nx.style.visibility="visible";
      };
      opts.appendChild(b);});
  }
  nx.onclick=round;round();
}
function renderGangs(birds){
  var g=document.getElementById("gangGrid");
  var lp=birds.filter(function(s){return s.lik!=="rare";}),tot=lp.length;
  var bar=el("div","bar");bar.setAttribute("role","img");var parts=[];
  Object.keys(GANGS).forEach(function(k){
    var arr=lp.filter(function(s){return s.cat===k;});
    var nl=arr.filter(function(s){return s.lik==="likely";}).length;
    parts.push(GANGS[k].name+" "+arr.length);
    var i=el("i");i.style.width=(100*arr.length/tot)+"%";i.style.background=GANGS[k].c;i.title=GANGS[k].name+": "+arr.length+" species";bar.appendChild(i);
    var d=el("div","gang");d.style.setProperty("--c",GANGS[k].c);
    d.innerHTML='<h3>'+GANGS[k].name+'</h3><div class="gn">'+arr.length+'</div><div class="gd">likely or possible species ('+nl+' likely)<br>'+esc(GANGS[k].desc)+'</div><ol>'+
      arr.slice(0,8).map(function(s){return '<li><a href="'+turl(s)+'" target="_blank" rel="noopener">'+esc(name(s))+'</a> <span>'+esc(s.season)+'</span></li>';}).join("")+'</ol>';
    var b=el("button",null,"See all "+arr.length+" →");b.type="button";
    b.onclick=function(){var sel=document.querySelector('#birds select[data-f="cat"]');sel.value=k;sel.dispatchEvent(new Event("change"));document.getElementById("birds").scrollIntoView();};
    d.appendChild(b);g.appendChild(d);
  });
  bar.setAttribute("aria-label",parts.join(", "));g.before(bar);
}
function renderGhosts(birds){
  var arr=birds.filter(function(s){return s.lik==="rare";}).sort(function(a,b){return (b.A+b.B+b.C)-(a.A+a.B+a.C);});
  var box=document.getElementById("ghostList");
  if(!arr.length){box.innerHTML='<p class="empty">None.</p>';return;}
  arr.forEach(function(s){
    var d=el("div","ghost");
    d.innerHTML='<b><a href="'+turl(s)+'" target="_blank" rel="noopener">'+esc(name(s))+'</a></b><i>'+esc(s.sci)+'</i>'+
      '<small>'+fmt(s.A)+' ≤2 km · '+fmt(s.B)+' ≤8 km · '+fmt(s.C)+' ≤15 km</small>'+(s.snd?playBtn(s,"mini"):"");
    box.appendChild(d);});
}
function renderGroup(sec,items,isBirds){
  var seasons=isBirds?["Year-round","Summer","Winter","Migrant","Irregular"]:[];
  var ctl=el("div","ctl");
  ctl.innerHTML='<input type="search" placeholder="Search '+items.length+' species…" aria-label="Search species">'+
    '<select data-f="lik" aria-label="Likelihood"><option value="">Likely + possible + rare</option><option value="likely">Likely</option><option value="possible">Possible</option><option value="rare">Rare</option><option value="lp">Likely + possible</option></select>'+
    (isBirds?'<select data-f="sea" aria-label="Season"><option value="">Any season</option>'+seasons.map(function(x){return '<option>'+x+'</option>';}).join("")+'</select>'+
    '<select data-f="cat" aria-label="Bird crew"><option value="">All crews</option><option value="yard">The Locals (yard)</option><option value="marsh">Marsh Mafia (flyovers / nearby marsh)</option><option value="raptor">Sky Predators (raptors)</option></select>':'')+
    '<select data-f="mon" aria-label="Month"><option value="">Any month</option>'+MONL.map(function(m,i){return '<option value="'+i+'">Seen in '+m+'</option>';}).join("")+'</select>'+
    '<select data-f="sort" aria-label="Sort"><option value="l">Most likely first</option><option value="now">Hot this month</option><option value="a">A–Z</option><option value="r">Rarest first</option></select>'+
    '<span class="cnt"></span>';
  var grid=el("div","grid"),btn=el("button","more","Show more");btn.type="button";
  sec.appendChild(ctl);sec.appendChild(grid);sec.appendChild(btn);
  var q=ctl.querySelector("input"),f={};
  ["lik","sea","cat","mon","sort"].forEach(function(k){f[k]=ctl.querySelector('[data-f="'+k+'"]');});
  var cnt=ctl.querySelector(".cnt"),cur=[],shown=0;
  function tot(s){return s.A*100+s.B*10+s.C;}
  function apply(){
    var t=q.value.trim().toLowerCase(),lk=f.lik.value,se=f.sea?f.sea.value:"",c=f.cat?f.cat.value:"",mo=f.mon.value,so=f.sort.value;
    cur=items.filter(function(s){
      if(lk==="lp"){if(s.lik==="rare")return false;}else if(lk&&s.lik!==lk)return false;
      if(se&&s.season!==se)return false;
      if(c&&s.cat!==c)return false;
      if(mo!==""&&!s.m[+mo])return false;
      if(t&&(s.com+" "+s.sci+" "+(s.family||"")+" "+(s.family_com||"")+" "+(s.order||"")).toLowerCase().indexOf(t)<0)return false;
      return true;});
    cur.sort(so==="a"?function(a,b){return name(a).localeCompare(name(b));}:
             so==="r"?function(a,b){return LIKO[b.lik]-LIKO[a.lik]||tot(a)-tot(b);}:
             so==="now"?function(a,b){return b.m[CUR]-a.m[CUR]||LIKO[a.lik]-LIKO[b.lik];}:
             function(a,b){return LIKO[a.lik]-LIKO[b.lik]||tot(b)-tot(a);});
    grid.innerHTML="";shown=0;
    cnt.textContent=cur.length+" of "+items.length+" species";
    if(!cur.length)grid.innerHTML='<p class="empty">Nothing matches. Try another search.</p>';
    more();
  }
  function more(){
    var fr=document.createDocumentFragment();
    cur.slice(shown,shown+PAGE).forEach(function(s){fr.appendChild(card(s));});
    grid.appendChild(fr);shown+=PAGE;
    btn.style.display=shown<cur.length?"":"none";
    btn.textContent="Show more ("+(cur.length-Math.min(shown,cur.length))+" left)";
  }
  btn.onclick=more;
  var tm;q.addEventListener("input",function(){clearTimeout(tm);tm=setTimeout(apply,150);});
  ["lik","sea","cat","mon","sort"].forEach(function(k){if(f[k])f[k].addEventListener("change",apply);});
  apply();
}

fetch("data/species.json").then(function(r){if(!r.ok)throw new Error(r.status);return r.json();}).then(function(d){
  var by={};d.species.forEach(function(s){(by[s.g]=by[s.g]||[]).push(s);});
  var birds=by.birds||[];
  window.LW={species:d.species,birds:birds,esc:esc,name:name,turl:turl,el:el,fmt:fmt,CUR:CUR,MON:MON,MONL:MONL,LIK:LIK,playBtn:playBtn};
  document.dispatchEvent(new Event("lw-data"));
  renderHero(birds);renderNow(birds);renderQuiz(birds);renderGangs(birds);renderGhosts(birds);
  Array.prototype.forEach.call(document.querySelectorAll(".grp"),function(sec){
    var g=sec.getAttribute("data-g"),items=by[g]||[];
    var c={likely:0,possible:0,rare:0};items.forEach(function(s){c[s.lik]++;});
    sec.appendChild(el("p","sub",items.length+" species: <b class='lk'>"+c.likely+" likely</b> · <b class='ps'>"+c.possible+" possible</b> · <b class='rr'>"+c.rare+" rare</b>. Tap a name for its iNaturalist page; bars show which months it turns up nearby (red outline = this month)."));
    renderGroup(sec,items,g==="birds");
  });
  if(location.hash.length>1){var t=document.getElementById(location.hash.slice(1));if(t)t.scrollIntoView();}
}).catch(function(e){
  document.querySelector("main").insertAdjacentHTML("afterbegin",'<p class="empty">Could not load species data ('+esc(e.message)+').</p>');
});
})();
