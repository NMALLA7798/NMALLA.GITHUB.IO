(function(){
var font='"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif';
var BU={'Retail':'--c1','E-commerce':'--c2','Wholesale':'--c3','Subscriptions':'--c4'};
var reg={};
var state={thr:60,target:'95',bu:'All',p:0,v:0,c:0,m:0};
var S=D.sc,F=D.fn;
function $(id){return document.getElementById(id);}
function css(n){return getComputedStyle(document.documentElement).getPropertyValue(n).trim();}
function rgba(hex,a){var n=parseInt(hex.replace('#',''),16);return 'rgba('+(n>>16&255)+','+(n>>8&255)+','+(n&255)+','+a+')';}
function mk(id,cfg){var el=$(id);if(!el||!window.Chart)return;if(reg[id]){reg[id].destroy();}reg[id]=new Chart(el,cfg);}
function tip(cb,extra){return Object.assign({backgroundColor:css('--surface'),titleColor:css('--ink'),bodyColor:css('--ink2'),borderColor:css('--axis'),borderWidth:1,padding:10,cornerRadius:4,boxPadding:4,callbacks:cb||{}},extra||{});}
function ax(title,o,extra){o=o||{};var a={grid:Object.assign({color:css('--line'),drawTicks:false},o.grid||{}),border:{color:css('--axis')},ticks:Object.assign({color:css('--ink2'),padding:6},o.ticks||{}),title:{display:!!title,text:title||'',color:css('--ink2')}};return Object.assign(a,extra||{});}
function legend(filter){return {position:'top',align:'start',labels:{usePointStyle:true,boxWidth:8,boxHeight:8,color:css('--ink2'),filter:filter}};}
function base(){return {maintainAspectRatio:false,animation:false,layout:{padding:{top:4,right:4}}};}
function pct(v){return v+'%';}
function mm(v,d){return (v<0?'-':'')+'$'+Math.abs(v).toFixed(d==null?2:d)+'M';}
function sgn(v,d){return (v>=0?'+':'-')+'$'+Math.abs(v).toFixed(d==null?2:d)+'M';}

/* ---------- chart plugins ---------- */
var refLines={id:'refLines',afterDatasetsDraw:function(chart,args,opts){
  var L=(opts&&opts.lines)||[],ctx=chart.ctx,a=chart.chartArea,x=chart.scales.x,y=chart.scales.y;
  L.forEach(function(l){ctx.save();ctx.strokeStyle=css('--ink2');ctx.fillStyle=css('--ink2');ctx.lineWidth=1;ctx.setLineDash([5,4]);ctx.font='11px '+font;ctx.beginPath();
    if(l.axis==='y'){var py=y.getPixelForValue(l.value);ctx.moveTo(a.left,py);ctx.lineTo(a.right,py);ctx.stroke();ctx.setLineDash([]);ctx.textAlign='left';ctx.textBaseline='bottom';ctx.fillText(l.label,a.left+6,py-4);}
    else{var px=x.getPixelForValue(l.value);ctx.moveTo(px,a.top);ctx.lineTo(px,a.bottom);ctx.stroke();ctx.setLineDash([]);ctx.textAlign='left';
      if(l.pos==='bottom'){ctx.textBaseline='bottom';ctx.fillText(l.label,px+6,a.bottom-6);}else{ctx.textBaseline='bottom';ctx.fillText(l.label,px+4,a.top-4);}}
    ctx.restore();});}};

function valueLabels(fmt,horizontal){return {id:'valueLabels',afterDatasetsDraw:function(chart){
  var ctx=chart.ctx;chart.data.datasets.forEach(function(ds,di){var meta=chart.getDatasetMeta(di);if(meta.hidden)return;
    meta.data.forEach(function(el,i){var v=ds.data[i];if(v==null)return;var t=fmt(v,i,di);if(!t)return;
      ctx.save();ctx.fillStyle=css('--ink');ctx.font='600 12px '+font;
      if(horizontal){var neg=(Array.isArray(v)?0:v)<0;ctx.textBaseline='middle';ctx.textAlign=neg?'right':'left';ctx.fillText(t,el.x+(neg?-6:6),el.y);}
      else{ctx.textAlign='center';ctx.textBaseline='bottom';ctx.fillText(t,el.x,Math.min(el.y,el.base)-5);}
      ctx.restore();});});}};}

var endLabels={id:'endLabels',afterDatasetsDraw:function(chart){var ctx=chart.ctx;
  chart.data.datasets.forEach(function(ds,i){var meta=chart.getDatasetMeta(i);if(meta.hidden)return;var j=-1;
    for(var k=ds.data.length-1;k>=0;k--){if(ds.data[k]!=null){j=k;break;}}if(j<0)return;var p=meta.data[j];
    ctx.save();ctx.fillStyle=css('--ink');ctx.font='500 12px '+font;ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillText(ds.endLabel||ds.label,p.x+8,p.y);ctx.restore();});}};

/* ---------- Project 1: supplier chart + threshold slider ---------- */
var supRows=S.scorecard.slice().sort(function(a,b){return a.otif_pct-b.otif_pct;});
function buildSup(){
  var rows=supRows;
  mk('c-suppliers',{type:'bar',data:{labels:rows.map(function(r){return r.supplier_name+' ('+r.country+')';}),
    datasets:[{data:rows.map(function(r){return r.otif_pct;}),backgroundColor:rows.map(function(r){return css(r.otif_pct<state.thr?'--c2':'--c1');}),borderRadius:{topRight:3,bottomRight:3},barPercentage:.72}]},
    options:Object.assign(base(),{indexAxis:'y',layout:{padding:{top:20,right:12}},
      plugins:{legend:{display:false},tooltip:tip({label:function(c){var r=rows[c.dataIndex];return ['OTIF '+r.otif_pct+'% (on time '+r.on_time_pct+'%, in full '+r.in_full_pct+'%)',r.pos+' POs, '+r.spend_share_pct+'% of spend','Average delay '+r.avg_delay_days+' days'];}}),
        refLines:{lines:[{axis:'x',value:state.thr,label:state.thr+'% threshold'}]}},
      scales:{x:ax('OTIF %',{ticks:{callback:pct}},{min:0,max:100}),y:ax(null,{grid:{display:false},ticks:{autoSkip:false,font:{size:11}}})}}),plugins:[refLines]});
}
function supRead(){
  var tot=0,tl=0,rs=0,rl=0,n=0;
  S.scorecard.forEach(function(r){var late=r.pos*(100-r.on_time_pct)/100;tot+=r.spend;tl+=late;if(r.otif_pct<state.thr){n++;rs+=r.spend;rl+=late;}});
  $('sup-read').innerHTML='<strong>'+n+' of '+S.scorecard.length+'</strong> suppliers fall below '+state.thr+'% OTIF. They hold <strong>'+(100*rs/tot).toFixed(1)+'%</strong> of spend and cause <strong>'+(tl?(100*rl/tl).toFixed(1):'0.0')+'%</strong> of late deliveries.';
}

/* ---------- Project 1: service-level chart + target selector ---------- */
function tgt(){return S.sim.targets.filter(function(t){return t.key===state.target;})[0];}
function buildSvc(){
  var s=S.sim,t=tgt();
  mk('c-service',{type:'bar',data:{labels:[['All Class A','('+s.n_a_skus+' SKUs)'],['From at-risk suppliers','('+s.n_a_problem+' SKUs)'],['From other suppliers','('+s.n_a_other+' SKUs)']],datasets:[
    {label:'Current rule',data:[s.service_now_pct,s.service_now_problem_pct,s.service_now_other_pct],backgroundColor:css('--c1'),borderRadius:{topLeft:3,topRight:3}},
    {label:'Safety stock for '+t.label+' target',data:[t.service_pct,t.service_problem_pct,t.service_other_pct],backgroundColor:css('--c2'),borderRadius:{topLeft:3,topRight:3}}]},
    options:Object.assign(base(),{layout:{padding:{top:20,right:4}},plugins:{legend:legend(),tooltip:tip({label:function(c){return c.dataset.label+': '+c.parsed.y+'% of cycles without a stockout';}})},
      scales:{x:ax(null,{grid:{display:false}}),y:ax('Cycle service level',{ticks:{callback:pct}},{min:0,max:100})}}),plugins:[valueLabels(function(v){return v+'%';})]});
}
function svcRead(){
  var s=S.sim,t=tgt();
  $('svc-read').innerHTML='At a <strong>'+t.label+'</strong> target, simulated service on Class A rises from '+s.service_now_pct+'% to <strong>'+t.service_pct+'%</strong>. It costs <strong>+'+t.inv_increase_pct+'%</strong> Class A inventory (<strong>+$'+Math.round(t.inv_increase_usd/1000)+'K</strong> on $'+(s.inventory_now_usd/1e6).toFixed(2)+'M).';
  Array.prototype.forEach.call(document.querySelectorAll('#svc-seg button'),function(b){b.setAttribute('aria-pressed',b.getAttribute('data-t')===state.target?'true':'false');});
}

/* ---------- Project 2: EBITDA bridge + business-unit filter ---------- */
function bridgeParts(){
  var t,start,end;
  if(state.bu==='All'){t=F.bridge.total;start=F.bridge.start;end=F.bridge.end;}
  else{t=F.by_bu.filter(function(r){return r.bu===state.bu;})[0];var y=F.ytd.filter(function(r){return r.bu===state.bu;})[0];start=y.ebitda_bud;end=y.ebitda_act;}
  return {t:t,start:start,end:end};
}
function buildBridge(){
  var bp=bridgeParts(),t=bp.t;
  var steps=[['Volume',t.volume_effect],['Price',t.price_effect],['Unit cost',t.cost_effect],['Marketing',t.marketing_effect],['Payroll & other',t.payroll_other_effect]];
  var run=bp.start/1e6,data=[[0,run]],colors=[css('--c1')],labels=['Budget EBITDA'],vals=[run];
  steps.forEach(function(st){var nxt=run+st[1]/1e6;data.push([Math.min(run,nxt),Math.max(run,nxt)]);colors.push(css(st[1]>=0?'--good':'--bad'));labels.push(st[0]);vals.push(st[1]/1e6);run=nxt;});
  data.push([0,bp.end/1e6]);colors.push(css('--c1'));labels.push('Actual EBITDA');vals.push(bp.end/1e6);
  function sg(v,i){return (i===0||i===vals.length-1)?mm(v):sgn(v);}
  mk('c-bridge',{type:'bar',data:{labels:labels,datasets:[{data:data,backgroundColor:colors,borderRadius:3,barPercentage:.7}]},
    options:Object.assign(base(),{layout:{padding:{top:22,right:4}},plugins:{legend:{display:false},tooltip:tip({label:function(c){return sg(vals[c.dataIndex],c.dataIndex);}})},
      scales:{x:ax(null,{grid:{display:false},ticks:{autoSkip:false,maxRotation:0,font:{size:11}}}),y:ax('EBITDA, Jan to Sep 2026',{ticks:{callback:function(v){return '$'+v+'M';}}},{beginAtZero:true})}}),
    plugins:[{id:'bl',afterDatasetsDraw:function(chart){var ctx=chart.ctx,meta=chart.getDatasetMeta(0);meta.data.forEach(function(el,i){ctx.save();ctx.fillStyle=css('--ink');ctx.font='600 12px '+font;ctx.textAlign='center';ctx.textBaseline='bottom';ctx.fillText(sg(vals[i],i),el.x,Math.min(el.y,el.base)-5);ctx.restore();});}}]});
}
function bridgeRead(){
  var bp=bridgeParts(),name=state.bu==='All'?'All business units':state.bu;
  $('bu-read').innerHTML='<strong>'+name+'</strong>: budget '+mm(bp.start/1e6)+', actual <strong>'+mm(bp.end/1e6)+'</strong>, variance <strong>'+sgn((bp.end-bp.start)/1e6)+'</strong>.';
}

/* ---------- Project 2: live scenario ---------- */
function scenEbitda(p,v,c,m){var P=F.forecast.parts;
  var rev=P.rev*(1+v/100),cogs=P.cogs*(1+v/100)*(1+c/100),mkt=P.mkt*(1+v/100)*(1+m/100);
  return rev*(1+p/100)-cogs-mkt-P.fixed;}
function scenRead(){
  var P=F.forecast.parts,e=scenEbitda(state.p,state.v,state.c,state.m),d=e-P.ebitda;
  $('sc-val').textContent=mm(e/1e6,1);
  $('sc-delta').textContent=Math.abs(d)<5000?'Same as the base case':sgn(d/1e6,2)+' vs base ('+(d>0?'+':'')+(100*d/P.ebitda).toFixed(1)+'%)';
}
function fmtPct(v){return (v>0?'+':'')+Number(v).toFixed(1)+'%';}

/* ---------- remaining charts ---------- */
function buildRest(){
  mk('c-otif',{type:'line',data:{labels:S.monthly.map(function(m){return m.month;}),datasets:[
    {label:'Monthly OTIF',data:S.monthly.map(function(m){return m.otif;}),borderColor:css('--c1'),backgroundColor:css('--c1'),borderWidth:1.5,pointRadius:3,pointHoverRadius:5},
    {label:'3-month average',data:S.monthly.map(function(m,i){return i<2?null:m.avg3;}),borderColor:css('--c2'),backgroundColor:css('--c2'),borderWidth:3,pointRadius:0,pointHoverRadius:4,tension:.2}]},
    options:Object.assign(base(),{interaction:{mode:'index',intersect:false},plugins:{legend:legend(),tooltip:tip({label:function(c){return c.dataset.label+': '+c.parsed.y+'%';}})},
      scales:{x:ax(null,{grid:{display:false},ticks:{maxTicksLimit:8}}),y:ax('OTIF %',{ticks:{callback:pct}},{min:60,max:90})}})});

  mk('c-pareto',{type:'line',data:{datasets:[{label:'Cumulative share of demand value',data:S.pareto,borderColor:css('--c1'),backgroundColor:css('--c1'),borderWidth:2.5,pointRadius:0,pointHoverRadius:4}]},
    options:Object.assign(base(),{layout:{padding:{top:20,right:12}},interaction:{mode:'nearest',axis:'x',intersect:false},
      plugins:{legend:{display:false},tooltip:tip({title:function(i){return 'Top '+i[0].parsed.x+' SKUs';},label:function(c){return c.parsed.y+'% of demand value';}}),
        refLines:{lines:[{axis:'y',value:80,label:'80% of value'},{axis:'y',value:95,label:'95% of value'},
          {axis:'x',value:S.abcA,label:'Class A: '+S.abcA+' SKUs',pos:'bottom'},{axis:'x',value:S.abcAB,label:'A+B: '+S.abcAB+' SKUs',pos:'bottom'}]}},
      scales:{x:ax('SKUs ranked by 2025 demand value',{ticks:{stepSize:25}},{type:'linear',min:0,max:150}),y:ax('Cumulative share of value',{ticks:{callback:pct}},{min:0,max:100})}}),plugins:[refLines]});

  var fs=S.fc.series;
  mk('c-forecast',{type:'line',data:{labels:fs.weeks.map(function(w){return w.slice(5);}),datasets:[
    {label:'Actual',data:fs.actual,borderColor:css('--c1'),backgroundColor:css('--c1'),borderWidth:2.5,pointRadius:3,pointHoverRadius:5},
    {label:S.fc.labels.trend_season,data:fs.trend_season,borderColor:css('--c2'),backgroundColor:css('--c2'),borderWidth:2.5,pointRadius:3,pointHoverRadius:5},
    {label:S.fc.labels.naive,data:fs.naive,borderColor:css('--ink2'),backgroundColor:css('--ink2'),borderWidth:1.5,borderDash:[6,4],pointRadius:0,pointHoverRadius:4}]},
    options:Object.assign(base(),{interaction:{mode:'index',intersect:false},plugins:{legend:legend(),tooltip:tip({label:function(c){return c.dataset.label+': '+c.parsed.y.toLocaleString()+' units';}})},
      scales:{x:ax('Week starting (2025, MM-DD)',{grid:{display:false}}),y:ax('Units per week',{ticks:{callback:function(v){return (v/1000).toFixed(0)+'k';}}})}})});

  var qs=[];F.margin.forEach(function(r){if(qs.indexOf(r.qtr)<0)qs.push(r.qtr);});
  var bus=['Retail','E-commerce','Wholesale','Subscriptions'];
  mk('c-margin',{type:'line',data:{labels:qs,datasets:bus.map(function(bu){var rr=F.margin.filter(function(r){return r.bu===bu;});
    return {label:bu,data:rr.map(function(r){return r.a;}),budget:rr.map(function(r){return r.b;}),borderColor:css(BU[bu]),backgroundColor:css(BU[bu]),borderWidth:2.5,pointRadius:0,pointHoverRadius:4,tension:.15};})},
    options:Object.assign(base(),{layout:{padding:{top:4,right:96}},interaction:{mode:'index',intersect:false},plugins:{legend:legend(),tooltip:tip({label:function(c){return c.dataset.label+': '+c.parsed.y+'% (budget '+c.dataset.budget[c.dataIndex]+'%)';}})},
      scales:{x:ax(null,{grid:{display:false},ticks:{maxTicksLimit:8}}),y:ax('Gross margin',{ticks:{callback:pct}},{min:0,max:100})}}),plugins:[endLabels]});

  var wh=F.dso.filter(function(r){return r.bu==='Wholesale';});
  var ms=wh.map(function(r){return r.month.slice(0,7);});
  var oth=ms.map(function(m){var v=F.dso.filter(function(r){return r.bu!=='Wholesale'&&r.month.slice(0,7)===m;}).map(function(r){return r.v;});return +(v.reduce(function(a,c){return a+c;},0)/v.length).toFixed(1);});
  mk('c-dso',{type:'line',data:{labels:ms,datasets:[
    {label:'Wholesale',data:wh.map(function(r){return r.v;}),borderColor:css('--c3'),backgroundColor:css('--c3'),borderWidth:3,pointRadius:0,pointHoverRadius:4},
    {label:'Other three units (average)',endLabel:'Other units',data:oth,borderColor:css('--c1'),backgroundColor:css('--c1'),borderWidth:2,pointRadius:0,pointHoverRadius:4}]},
    options:Object.assign(base(),{layout:{padding:{top:4,right:84}},interaction:{mode:'index',intersect:false},plugins:{legend:legend(),tooltip:tip({label:function(c){return c.dataset.label+': '+c.parsed.y+' days';}})},
      scales:{x:ax(null,{grid:{display:false},ticks:{maxTicksLimit:8}}),y:ax('Days sales outstanding (3-month average)',{},{min:0,max:70})}}),plugins:[endLabels]});

  var h=F.monthly,fm=F.forecast,n=h.length;
  var lbl=h.map(function(r){return r.month.slice(0,7);}).concat(fm.months);
  var act=h.map(function(r){return r.rev/1e6;}).concat(fm.months.map(function(){return null;}));
  var last=act[n-1],pad=function(arr){return Array(n-1).fill(null).concat([last]).concat(arr.map(function(v){return v/1e6;}));};
  var names=['Actual','Forecast','80% low','80% high'];
  mk('c-fan',{type:'line',data:{labels:lbl,datasets:[
    {label:'Actual',data:act,borderColor:css('--c1'),backgroundColor:css('--c1'),borderWidth:2.5,pointRadius:0,pointHoverRadius:4},
    {label:'Forecast',data:pad(fm.rev),borderColor:css('--c2'),backgroundColor:css('--c2'),borderWidth:2.5,borderDash:[6,4],pointRadius:0,pointHoverRadius:4},
    {label:'80% low',data:pad(fm.lo),borderWidth:0,pointRadius:0,pointHoverRadius:0,fill:false},
    {label:'80% interval',data:pad(fm.hi),borderWidth:0,pointRadius:0,pointHoverRadius:0,fill:'-1',backgroundColor:rgba(css('--c2'),.2)}]},
    options:Object.assign(base(),{interaction:{mode:'index',intersect:false},plugins:{legend:legend(function(i){return i.text!=='80% low';}),tooltip:tip({label:function(c){return names[c.datasetIndex]+': '+mm(c.parsed.y);}})},
      scales:{x:ax(null,{grid:{display:false},ticks:{maxTicksLimit:9}}),y:ax('Monthly revenue',{ticks:{callback:function(v){return '$'+v+'M';}}},{min:0})}})});

  var tr=F.tornado;
  mk('c-tornado',{type:'bar',data:{labels:tr.map(function(r){return r.driver;}),datasets:[
    {label:'Favorable',data:tr.map(function(r){return r.up/1e6;}),backgroundColor:css('--c1'),barPercentage:.7},
    {label:'Unfavorable',data:tr.map(function(r){return r.down/1e6;}),backgroundColor:css('--c2'),barPercentage:.7}]},
    options:Object.assign(base(),{indexAxis:'y',layout:{padding:{top:4,right:16}},plugins:{legend:legend(),tooltip:tip({label:function(c){return c.dataset.label+': '+sgn(c.parsed.x)+' EBITDA';}})},
      scales:{x:ax('Change in next-12-month EBITDA, $M',{ticks:{callback:function(v){return (v>0?'+':'')+v;}}},{stacked:true,min:-2.8,max:2.8}),y:ax(null,{grid:{display:false},ticks:{autoSkip:false}},{stacked:true})}}),
    plugins:[valueLabels(function(v){return (v>=0?'+':'-')+'$'+Math.abs(v).toFixed(1)+'M';},true)]});
}

function build(){
  Chart.defaults.font.family=font;Chart.defaults.font.size=12;Chart.defaults.color=css('--ink2');Chart.defaults.borderColor=css('--line');
  Object.keys(reg).forEach(function(k){reg[k].destroy();delete reg[k];});
  buildSup();buildSvc();buildBridge();buildRest();
}

/* ---------- controls ---------- */
function on(id,ev,fn){var el=$(id);if(el)el.addEventListener(ev,fn);}
function wire(){
  on('thr','input',function(){state.thr=+$('thr').value;$('thr-out').textContent=state.thr+'%';supRead();buildSup();});
  Array.prototype.forEach.call(document.querySelectorAll('#svc-seg button'),function(b){
    b.addEventListener('click',function(){state.target=b.getAttribute('data-t');svcRead();buildSvc();});});
  on('bu-sel','change',function(){state.bu=$('bu-sel').value;bridgeRead();buildBridge();});
  [['sl-p','p'],['sl-v','v'],['sl-c','c'],['sl-m','m']].forEach(function(pair){
    on(pair[0],'input',function(){state[pair[1]]=+$(pair[0]).value;$(pair[0]+'-out').textContent=fmtPct(state[pair[1]]);scenRead();});});
  on('sc-reset','click',function(){[['sl-p','p'],['sl-v','v'],['sl-c','c'],['sl-m','m']].forEach(function(pair){state[pair[1]]=0;$(pair[0]).value=0;$(pair[0]+'-out').textContent=fmtPct(0);});scenRead();});
  /* theme toggle */
  var tb=$('theme-btn');
  function effective(){var t=document.documentElement.getAttribute('data-theme');if(t)return t;return (window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';}
  function label(){if(tb)tb.textContent=effective()==='dark'?'Light mode':'Dark mode';}
  if(tb){tb.addEventListener('click',function(){document.documentElement.setAttribute('data-theme',effective()==='dark'?'light':'dark');label();});}
  label();
  try{window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',function(){label();if(window.Chart)build();});}catch(e){}
  new MutationObserver(function(){label();if(window.Chart)build();}).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
}

supRead();svcRead();bridgeRead();scenRead();wire();
function boot(){if(!window.Chart){setTimeout(boot,100);return;}build();}
boot();
})();
