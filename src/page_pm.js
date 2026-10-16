(function(){
'use strict';
var D=JSON.parse(document.getElementById('pmdata').textContent);
function $(i){return document.getElementById(i);}
function css(v){return getComputedStyle(document.documentElement).getPropertyValue(v).trim();}
var charts={};
function mk(id,cfg){if(!window.Chart)return;if(charts[id])charts[id].destroy();cfg.options=Object.assign({maintainAspectRatio:false,animation:false},cfg.options||{});charts[id]=new Chart($(id),cfg);}
function base(){if(!window.Chart)return;Chart.defaults.font.family='"DM Sans",system-ui,sans-serif';Chart.defaults.font.size=12;Chart.defaults.color=css('--ink2');Chart.defaults.borderColor=css('--rule');}
var S={t:D.launch.t,guard:true,rework:D.assump.rework_min,labor:D.assump.labor};
var A=D.assump,df=D.cat;
/* curve recomputed live from per-threshold, per-category counts so rework cost and guardrail are adjustable */
function point(t){
  var row=D.grid[String(t.toFixed(2))],auto=0,ok=0,saved=0,wrong=0;
  Object.keys(row).forEach(function(c){
    if(S.guard&&c==='Hazmat or compliance')return;
    var r=row[c];auto+=r.n;ok+=r.ok;saved+=r.saved_min;wrong+=r.n-r.ok;});
  var net_min=saved-A.review_min*auto-wrong*S.rework;
  return {t:t,cov:auto/D.total,prec:auto?ok/auto:1,auto:auto/A.weeks,wrong:wrong/A.weeks,hours:net_min/60/A.weeks,usd:net_min/60*S.labor/A.weeks-wrong*A.escalation/A.weeks};
}
var T=[];for(var x=50;x<=99;x++)T.push(x/100);
function pct(v,d){return (v*100).toFixed(d==null?1:d)+'%';}
function usd(v){return (v<0?'-':'')+'$'+Math.abs(Math.round(v)).toLocaleString();}
var marker={id:'marker',afterDatasetsDraw:function(ch){var x=ch.scales.x.getPixelForValue(S.t.toFixed(2)),a=ch.chartArea,c=ch.ctx;
  c.save();c.strokeStyle=css('--ink');c.setLineDash([5,4]);c.lineWidth=1.5;c.beginPath();c.moveTo(x,a.top);c.lineTo(x,a.bottom);c.stroke();c.setLineDash([]);c.fillStyle=css('--ink');c.font='600 12px "DM Sans"';c.textAlign='center';c.fillText('Threshold '+S.t.toFixed(2),Math.min(Math.max(x,a.left+50),a.right-50),a.top-5);c.restore();}};
var guard={id:'guard',afterDatasetsDraw:function(ch,args,o){var y=ch.scales.y.getPixelForValue(0.97),a=ch.chartArea,c=ch.ctx;c.save();c.strokeStyle=css('--bad');c.setLineDash([3,4]);c.beginPath();c.moveTo(a.left,y);c.lineTo(a.right,y);c.stroke();c.setLineDash([]);c.fillStyle=css('--bad');c.font='500 11px "DM Sans"';c.textAlign='left';c.fillText('97% precision floor',a.left+6,y-5);c.restore();}};
function draw(){
  base();var P=T.map(point);
  mk('c-curve',{type:'line',data:{labels:T.map(function(t){return t.toFixed(2);}),datasets:[
    {label:'Precision of auto-resolved tickets',data:P.map(function(p){return p.prec;}),borderColor:css('--c1'),backgroundColor:css('--c1'),pointRadius:0,borderWidth:2.5},
    {label:'Share of all tickets auto-resolved',data:P.map(function(p){return p.cov;}),borderColor:css('--c2'),backgroundColor:css('--c2'),pointRadius:0,borderWidth:2.5,borderDash:[6,4]}]},
   plugins:[marker,guard],options:{layout:{padding:{top:18}},interaction:{mode:'index',intersect:false},plugins:{legend:{position:'bottom',labels:{usePointStyle:true,boxWidth:8}},tooltip:{callbacks:{title:function(i){return 'Confidence threshold '+i[0].label;},label:function(c){return c.dataset.label+': '+pct(c.parsed.y);}}}},
    scales:{x:{title:{display:true,text:'Auto-resolve only if model confidence is at least'},ticks:{maxTicksLimit:10},grid:{display:false}},y:{min:0,max:1,ticks:{callback:function(v){return pct(v,0);}}}}}});
  var best=P.reduce(function(a,b){return b.usd>a.usd?b:a;},P[0]);
  mk('c-net',{type:'line',data:{labels:T.map(function(t){return t.toFixed(2);}),datasets:[{label:'Net value per week',data:P.map(function(p){return p.usd;}),borderColor:css('--c3'),backgroundColor:css('--c3'),pointRadius:0,borderWidth:2.5}]},
   plugins:[marker],options:{layout:{padding:{top:18}},interaction:{mode:'index',intersect:false},plugins:{legend:{display:false},tooltip:{callbacks:{title:function(i){return 'Confidence threshold '+i[0].label;},label:function(c){return 'Net value: '+usd(c.parsed.y)+' per week';}}}},
    scales:{x:{title:{display:true,text:'Confidence threshold'},ticks:{maxTicksLimit:10},grid:{display:false}},y:{title:{display:true,text:'Net value per week after rework and escalations'},ticks:{callback:function(v){return usd(v);}}}}}});
  var p=point(S.t);
  $('r-cov').textContent=pct(p.cov);$('r-prec').textContent=pct(p.prec);$('r-wrong').textContent=p.wrong.toFixed(0);$('r-usd').textContent=usd(p.usd);
  $('r-hours').textContent=p.hours.toFixed(0)+' hours';
  var msg=p.prec>=0.97?'Meets the 97% precision floor.':'Below the 97% precision floor, so this would not pass the launch gate.';
  $('r-msg').innerHTML='At <strong>'+S.t.toFixed(2)+'</strong>, about <strong>'+p.auto.toFixed(0)+'</strong> tickets a week resolve without an agent and <strong>'+p.wrong.toFixed(0)+'</strong> of them are wrong. '+msg+' The value-maximizing threshold with these inputs is <strong>'+best.t.toFixed(2)+'</strong> ('+pct(best.prec)+' precision).';
  $('o-t').textContent=S.t.toFixed(2);$('o-rw').textContent=S.rework+' min';$('o-lb').textContent='$'+S.labor;
}
$('s-t').addEventListener('input',function(){S.t=parseInt(this.value,10)/100;draw();});
$('s-rw').addEventListener('input',function(){S.rework=parseInt(this.value,10);draw();});
$('s-lb').addEventListener('input',function(){S.labor=parseInt(this.value,10);draw();});
Array.prototype.forEach.call(document.querySelectorAll('#g-seg button'),function(b){b.addEventListener('click',function(){S.guard=b.getAttribute('data-g')==='on';
  Array.prototype.forEach.call(document.querySelectorAll('#g-seg button'),function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});draw();});});
/* RICE */
function rice(){
  var rows=D.rice.map(function(f,i){var r=+$('rc-r'+i).value,im=+$('rc-i'+i).value,c=+$('rc-c'+i).value/100,e=Math.max(0.1,+$('rc-e'+i).value);return {name:f.name,score:r*im*c/e};});
  rows.sort(function(a,b){return b.score-a.score;});
  base();mk('c-rice',{type:'bar',data:{labels:rows.map(function(r){return r.name;}),datasets:[{data:rows.map(function(r){return r.score;}),backgroundColor:rows.map(function(_,i){return css(i===0?'--c1':'--rule2');}),borderRadius:4}]},
   options:{indexAxis:'y',plugins:{legend:{display:false},tooltip:{callbacks:{label:function(c){return 'RICE score '+Math.round(c.parsed.x);}}}},scales:{x:{title:{display:true,text:'RICE score: reach x impact x confidence / effort (person-months)'},grid:{color:css('--rule')}},y:{grid:{display:false}}}}});
  $('rice-top').textContent=rows[0].name;
}
Array.prototype.forEach.call(document.querySelectorAll('.rc'),function(i){i.addEventListener('input',rice);});
$('rice-reset').addEventListener('click',function(){D.rice.forEach(function(f,i){$('rc-r'+i).value=f.reach;$('rc-i'+i).value=f.impact;$('rc-c'+i).value=Math.round(f.confidence*100);$('rc-e'+i).value=f.effort;});rice();});
function all(){draw();rice();}
function boot(){if(!window.Chart){setTimeout(boot,100);return;}all();}
try{new MutationObserver(function(){if(window.Chart)all();}).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});}catch(e){}
try{matchMedia('(prefers-color-scheme: dark)').addEventListener('change',function(){if(window.Chart)all();});}catch(e){}
boot();
})();
