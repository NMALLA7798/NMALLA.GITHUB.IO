(function(){
var font='"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif';
var BU={'Retail':'--c1','E-commerce':'--c2','Wholesale':'--c3','Subscriptions':'--c4'};
var reg={};
var state={thr:60,target:'95',bu:'All',p:0,v:0,c:0,m:0,dim:'Channel'};
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
    ctx.save();ctx.fillStyle=css('--ink');ctx.font='500 12px '+font;ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillText(ds.endLabel||ds.label,p.x+8,p.y+(ds.endNudge||0));ctx.restore();});}};

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


/* ---------- Project 3: business analysis ---------- */
var BAd=D.ba;
function isDark(){var t=document.documentElement.getAttribute('data-theme');if(t)return t==='dark';return !!(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches);}
function lerp(a,b,t){return Math.round(a+(b-a)*t);}
function heatRamp(){return isDark()?{lo:[13,54,107],hi:[134,182,239]}:{lo:[205,226,251],hi:[16,66,129]};}
function heatColor(v){var r=heatRamp(),t=Math.max(0,Math.min(1,(v-50)/50));return {bg:'rgb('+lerp(r.lo[0],r.hi[0],t)+','+lerp(r.lo[1],r.hi[1],t)+','+lerp(r.lo[2],r.hi[2],t)+')',t:t};}
function buildHeat(){
  var el=$('heat');if(!el)return;var dark=isDark(),h='<table><thead><tr><th class="hc">Cohort</th><th class="hn">Paying</th>';
  for(var m=1;m<=12;m++){h+='<th title="Months since first payment">M'+m+'</th>';}
  h+='</tr></thead><tbody>';
  BAd.heat.forEach(function(row){
    h+='<tr><th class="hc" scope="row">'+row.cohort+'</th><td class="hn">'+row.size+'</td>';
    for(var m=1;m<=12;m++){var v=row.ret[m];
      if(v==null){h+='<td class="empty"></td>';}
      else{var c=heatColor(v),txt=dark?(c.t>=.5?'#0b0b0b':'#f0efec'):(c.t>=.6?'#ffffff':'#0b0b0b');
        h+='<td style="background:'+c.bg+';color:'+txt+'" title="'+row.cohort+' cohort, month '+m+': '+v+'% still subscribed (n='+row.size+')">'+Math.round(v)+'</td>';}}
    h+='</tr>';});
  h+='</tbody></table>';el.innerHTML=h;
  var r=heatRamp(),bar=$('heat-bar');if(bar)bar.style.background='linear-gradient(90deg,rgb('+r.lo.join(',')+'),rgb('+r.hi.join(',')+'))';
}
function buildTrend(){
  var t=BAd.trend;
  mk('c-trend',{type:'line',data:{labels:t.map(function(r){return r.month;}),datasets:[
    {label:'Activation rate',endLabel:'Activation',endNudge:10,data:t.map(function(r){return r.activation_pct;}),borderColor:css('--c1'),backgroundColor:css('--c1'),borderWidth:2.5,pointRadius:0,pointHoverRadius:4},
    {label:'Paid social share of signups',endLabel:'Paid social share',endNudge:-10,data:t.map(function(r){return r.paid_social_share_pct;}),borderColor:css('--c2'),backgroundColor:css('--c2'),borderWidth:2.5,pointRadius:0,pointHoverRadius:4}]},
    options:Object.assign(base(),{layout:{padding:{top:4,right:112}},interaction:{mode:'index',intersect:false},plugins:{legend:legend(),tooltip:tip({label:function(c){return c.dataset.label+': '+c.parsed.y+'%';}})},
      scales:{x:ax(null,{grid:{display:false},ticks:{maxTicksLimit:8}}),y:ax('Percent of signups',{ticks:{callback:pct}},{min:0,max:60})}}),plugins:[endLabels]});
}
function buildFunnel(){
  var f=BAd.funnel;
  mk('c-funnel',{type:'bar',data:{labels:f.map(function(r){return r.channel;}),datasets:[
    {label:'Activated within 7 days',data:f.map(function(r){return r.activation_pct;}),backgroundColor:css('--c1'),borderRadius:{topRight:3,bottomRight:3}},
    {label:'Started paying',data:f.map(function(r){return r.paid_pct;}),backgroundColor:css('--c2'),borderRadius:{topRight:3,bottomRight:3}},
    {label:'Still paying at day 90',data:f.map(function(r){return r.retained_pct_of_signups;}),backgroundColor:css('--c3'),borderRadius:{topRight:3,bottomRight:3}}]},
    options:Object.assign(base(),{indexAxis:'y',layout:{padding:{top:4,right:24}},interaction:{mode:'index',intersect:false},plugins:{legend:legend(),tooltip:tip({label:function(c){return c.dataset.label+': '+c.parsed.x+'% of signups';}})},
      scales:{x:ax('Share of channel signups',{ticks:{callback:pct}},{min:0,max:70}),y:ax(null,{grid:{display:false}})}}),
    plugins:[valueLabels(function(v){return v+'%';},true)]});
}
function churnRows(){
  var rows=BAd.segments[state.dim].slice();
  if(state.dim==='Channel'){rows.sort(function(a,b){return b.churn6_pct-a.churn6_pct;});}
  return rows;
}
function buildChurn(){
  var rows=churnRows(),avg=BAd.overall_churn6;
  mk('c-churn',{type:'bar',data:{labels:rows.map(function(r){return r.segment;}),datasets:[{data:rows.map(function(r){return r.churn6_pct;}),backgroundColor:rows.map(function(r){return css(r.churn6_pct>avg?'--c2':'--c1');}),borderRadius:{topLeft:3,topRight:3},barPercentage:.65}]},
    options:Object.assign(base(),{layout:{padding:{top:20,right:8}},plugins:{legend:{display:false},tooltip:tip({label:function(c){var r=rows[c.dataIndex];return r.churn6_pct+'% churned within 6 months ('+r.customers.toLocaleString()+' customers)';}}),
      refLines:{lines:[{axis:'y',value:avg,label:'All customers '+avg+'%'}]}},
      scales:{x:ax(null,{grid:{display:false}}),y:ax('Churned within 6 months',{ticks:{callback:pct}},{min:0,max:50})}}),
    plugins:[refLines,valueLabels(function(v){return v+'%';})]});
}
function churnRead(){
  var rows=churnRows().slice().sort(function(a,b){return b.churn6_pct-a.churn6_pct;}),hi=rows[0],lo=rows[rows.length-1];
  $('seg-read').innerHTML='Highest: <strong>'+hi.segment+'</strong> at <strong>'+hi.churn6_pct+'%</strong>. Lowest: <strong>'+lo.segment+'</strong> at <strong>'+lo.churn6_pct+'%</strong>. That is '+(hi.churn6_pct/lo.churn6_pct).toFixed(1)+' times the churn.';
}
var errBars={id:'errBars',afterDatasetsDraw:function(chart){
  var ctx=chart.ctx,y=chart.scales.y,ds=chart.data.datasets[0],meta=chart.getDatasetMeta(0);
  meta.data.forEach(function(el,i){var ci=ds.ci[i],lo=y.getPixelForValue(ci[0]),hi=y.getPixelForValue(ci[1]);
    ctx.save();ctx.strokeStyle=css('--ink');ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(el.x,lo);ctx.lineTo(el.x,hi);ctx.moveTo(el.x-8,lo);ctx.lineTo(el.x+8,lo);ctx.moveTo(el.x-8,hi);ctx.lineTo(el.x+8,hi);ctx.stroke();
    ctx.fillStyle=css('--ink');ctx.font='600 13px '+font;ctx.textAlign='center';ctx.textBaseline='bottom';ctx.fillText(ds.data[i]+'%',el.x,hi-6);ctx.restore();});}};
function buildAB(){
  var e=BAd.experiment;
  mk('c-ab',{type:'bar',data:{labels:['Control','Checklist'],datasets:[{data:[e.act_control,e.act_variant],ci:[e.ci_control,e.ci_variant],backgroundColor:[css('--c1'),css('--c2')],barPercentage:.5,borderRadius:{topLeft:3,topRight:3}}]},
    options:Object.assign(base(),{layout:{padding:{top:24,right:8}},plugins:{legend:{display:false},tooltip:tip({label:function(c){var ci=c.dataset.ci[c.dataIndex];return c.parsed.y+'% activated (95% CI '+ci[0]+'% to '+ci[1]+'%)';}})},
      scales:{x:ax(null,{grid:{display:false}}),y:ax('Activated within 7 days',{ticks:{callback:pct}},{min:0,max:60})}}),plugins:[errBars]});
}
function wrapText(s,n){var w=s.split(' '),out=[],line='';w.forEach(function(x){if((line+' '+x).trim().length>n){out.push(line.trim());line=x;}else{line+=' '+x;}});if(line.trim())out.push(line.trim());return out;}
var bubbleLabels={id:'bubbleLabels',afterDatasetsDraw:function(chart){
  var I=BAd.initiatives,meta=chart.getDatasetMeta(0),ctx=chart.ctx;
  meta.data.forEach(function(el,i){var v=I[i].impact,t=I[i].short+' ('+(v<0?'-':'')+'$'+Math.abs(Math.round(v/1000))+'K)';
    ctx.save();ctx.fillStyle=css('--ink');ctx.font='500 12px '+font;ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillText(t,el.x+el.options.radius+6,el.y);ctx.restore();});}};
function buildPrio(){
  var I=BAd.initiatives,maxC=Math.max.apply(null,I.map(function(i){return i.customers;}));
  mk('c-prio',{type:'bubble',data:{datasets:[{label:'Initiatives',data:I.map(function(i){return {x:i.effort,y:i.impact/1000,r:6+22*Math.sqrt(i.customers/maxC)};}),
      backgroundColor:I.map(function(i){return rgba(css(i.impact<0?'--bad':'--c1'),.55);}),borderColor:I.map(function(i){return css(i.impact<0?'--bad':'--c1');}),borderWidth:2}]},
    options:Object.assign(base(),{layout:{padding:{top:8,right:8}},plugins:{legend:{display:false},
      tooltip:tip({title:function(it){return I[it[0].dataIndex].short;},label:function(c){var i=I[c.dataIndex],o=['Impact $'+Math.round(i.impact/1000)+'K a year'+(i.impact_low!=null?' (range $'+Math.round(i.impact_low/1000)+'K to $'+Math.round(i.impact_high/1000)+'K)':''),'Effort '+i.effort+' of 5','Customers affected: '+i.customers.toLocaleString()];return o.concat(wrapText(i.basis,46));}}),
      refLines:{lines:[{axis:'y',value:0,label:'Break-even'}]}},
      scales:{x:ax('Effort (1 low to 5 high, my estimate)',{ticks:{stepSize:1,callback:function(v){return Number.isInteger(v)?v:'';}}},{min:0.5,max:5}),y:ax('Revenue impact a year, $K',{ticks:{callback:function(v){return (v<0?'-':'')+'$'+Math.abs(v)+'K';}}},{min:-12,max:48})}}),
    plugins:[refLines,bubbleLabels]});
}

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
    {label:'Other three units (average)',endLabel:'Other units',data:oth,borderColor:css('--ink2'),backgroundColor:css('--ink2'),borderWidth:2,pointRadius:0,pointHoverRadius:4}]},
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
  buildSup();buildSvc();buildBridge();buildRest();buildHeat();buildTrend();buildFunnel();buildChurn();buildAB();buildPrio();buildFlCpm();buildFlLane();buildFlMaint();buildFlAge();buildFlScat();buildFlPay();
}


/* ---------- Project 4: fleet ---------- */
var FL=D.fl, FS={lane:'All',m:'events',s:'All',p:'Long-haul',diesel:FL.calc.defaults.diesel,prem:FL.calc.defaults.premium,util:0,soft:FL.calc.defaults.software};
var TCOL={AI:'--c1',Conventional:'--c3'};
function usd0(v){return (v<0?'-':'')+'$'+Math.abs(Math.round(v)).toLocaleString();}
function usdK(v){return (v<0?'-':'')+'$'+(Math.abs(v)/1000).toFixed(0)+'K';}
var CATS=[['depreciation','Depreciation','--c1'],['fuel','Fuel','--c4'],['driver','Driver','--c3'],['maintenance','Maintenance','--c2'],['insurance','Insurance','--axis'],['software','Software and telematics','--muted'],['other','Tolls and other','--line']];
var revMarks={id:'revMarks',afterDatasetsDraw:function(chart,args,o){
  var ctx=chart.ctx,x=chart.scales.x,meta=chart.getDatasetMeta(0);
  meta.data.forEach(function(el,i){var px=x.getPixelForValue(o.rev[i]),h=el.height/2+6;
    ctx.save();ctx.strokeStyle=css('--ink');ctx.lineWidth=2.5;ctx.beginPath();ctx.moveTo(px,el.y-h);ctx.lineTo(px,el.y+h);ctx.stroke();
    ctx.fillStyle=css('--ink');ctx.font='600 12px '+font;ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillText('Revenue $'+o.rev[i].toFixed(2),px+6,el.y-h+2);ctx.restore();});}};
function buildFlCpm(){
  var c=FL.cpm[FS.lane],T=['AI','Conventional'],lab=['AI-equipped','Conventional'];
  mk('c-fl-cpm',{type:'bar',data:{labels:lab,datasets:CATS.map(function(k){return {label:k[1],data:T.map(function(t){return c[t][k[0]];}),backgroundColor:css(k[2]),borderWidth:1,borderColor:css('--surface')};})},
   options:Object.assign(base(),{indexAxis:'y',layout:{padding:{top:4,right:20}},plugins:{legend:legend(),tooltip:tip({label:function(x){return x.dataset.label+': $'+x.parsed.x.toFixed(2)+' per mile';}}),revMarks:{rev:T.map(function(t){return c[t].revenue;})}},
    scales:{x:ax('Dollars per mile',{ticks:{callback:function(v){return '$'+v.toFixed(2);}}},{stacked:true,min:0}),y:ax(null,{grid:{display:false}},{stacked:true})}}),plugins:[revMarks]});
}
function flCpmRead(){
  var a=FL.cpm[FS.lane].AI,c=FL.cpm[FS.lane].Conventional;
  $('fl-cpm-read').innerHTML='<strong>'+FS.lane+'</strong>: AI costs <strong>$'+a.total_cost.toFixed(2)+'</strong> per mile against <strong>$'+c.total_cost.toFixed(2)+'</strong>, with revenue near $'+a.revenue.toFixed(2)+'. Profit per vehicle-month: <strong>'+usd0(a.profit_pvm)+'</strong> AI vs <strong>'+usd0(c.profit_pvm)+'</strong> conventional.';
}
var ciBars={id:'ciBars',afterDatasetsDraw:function(chart){
  var ctx=chart.ctx,y=chart.scales.y,ds=chart.data.datasets[0],meta=chart.getDatasetMeta(0);
  meta.data.forEach(function(el,i){var ci=ds.ci[i],lo=y.getPixelForValue(ci[0]),hi=y.getPixelForValue(ci[1]);
    ctx.save();ctx.strokeStyle=css('--ink');ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(el.x,lo);ctx.lineTo(el.x,hi);ctx.moveTo(el.x-8,lo);ctx.lineTo(el.x+8,lo);ctx.moveTo(el.x-8,hi);ctx.lineTo(el.x+8,hi);ctx.stroke();
    var v=ds.data[i];ctx.fillStyle=css('--ink');ctx.font='600 13px '+font;ctx.textAlign='center';
    if(v>=0){ctx.textBaseline='bottom';ctx.fillText(usd0(v),el.x+30,hi-4);}else{ctx.textBaseline='top';ctx.fillText(usd0(v),el.x+30,lo+4);}ctx.restore();});}};
function buildFlLane(){
  var st=FL.stats,L=['Long-haul','Regional','Urban'],lab=L.concat(['All, adjusted']);
  var d=L.map(function(l){return Math.round(st.lane[l].diff);}).concat([Math.round(st.adjusted)]);
  var ci=L.map(function(l){return [st.lane[l].lo,st.lane[l].hi];}).concat([[st.adj_lo,st.adj_hi]]);
  mk('c-fl-lane',{type:'bar',data:{labels:lab,datasets:[{data:d,ci:ci,backgroundColor:d.map(function(v,i){return css(i===3?'--muted':(v>=0?'--c1':'--c2'));}),barPercentage:.5,borderRadius:3}]},
   options:Object.assign(base(),{layout:{padding:{top:26,right:30,bottom:10}},plugins:{legend:{display:false},tooltip:tip({label:function(c){var k=c.dataset.ci[c.dataIndex];return usd0(c.parsed.y)+' per vehicle-month (95% CI '+usd0(k[0])+' to '+usd0(k[1])+')';}})},
    scales:{x:ax(null,{grid:{display:false}}),y:ax('AI minus conventional, profit per vehicle-month',{ticks:{callback:function(v){return usd0(v);}}})}}),plugins:[ciBars]});
}
var KINDS=['Preventive','Corrective','Breakdown','Sensor refresh'];
function flMaintVal(t,k){var m=FL.maint[t].kinds[k],mi=FL.cpm.All[t].vehicle_months*FL.cpm.All[t].miles_pm;
  if(FS.m==='events')return m.per_100k;if(FS.m==='cost')return m.avg_cost;return m.downtime/mi*1e5;}
function flMaintFmt(v){if(FS.m==='events')return v.toFixed(2);if(FS.m==='cost')return usd0(v);return v.toFixed(0)+' h';}
function buildFlMaint(){
  var T=['AI','Conventional'],name={AI:'AI-equipped',Conventional:'Conventional'};
  mk('c-fl-maint',{type:'bar',data:{labels:KINDS,datasets:T.map(function(t){return {label:name[t],data:KINDS.map(function(k){return flMaintVal(t,k);}),backgroundColor:css(TCOL[t]),borderRadius:{topLeft:3,topRight:3},barPercentage:.8,categoryPercentage:.7};})},
   options:Object.assign(base(),{layout:{padding:{top:22,right:8}},plugins:{legend:legend(),tooltip:tip({label:function(c){return c.dataset.label+': '+flMaintFmt(c.parsed.y);}})},
    scales:{x:ax(null,{grid:{display:false}}),y:ax(FS.m==='events'?'Events per 100,000 miles':(FS.m==='cost'?'Average cost per event':'Downtime hours per 100,000 miles'),{ticks:{callback:function(v){return FS.m==='cost'?usd0(v):v;}}},{min:0})}}),
   plugins:[valueLabels(function(v){return v>0?flMaintFmt(v):'';})]});
}
function flMaintRead(){
  var a=KINDS.reduce(function(s,k){return s+flMaintVal('AI',k);},0),c=KINDS.reduce(function(s,k){return s+flMaintVal('Conventional',k);},0);
  var txt=FS.m==='events'?'Breakdowns are the costly event: AI '+flMaintVal('AI','Breakdown').toFixed(2)+' vs conventional '+flMaintVal('Conventional','Breakdown').toFixed(2)+' per 100,000 miles.':
    FS.m==='cost'?'Preventive and corrective work costs more on AI units and breakdowns cost about the same. Sensor refreshes alone average '+usd0(flMaintVal('AI','Sensor refresh'))+'.':
    'AI units lose '+(a).toFixed(0)+' hours per 100,000 miles to the shop against '+(c).toFixed(0)+' conventional, with sensor refreshes adding a long outage each time.';
  $('fl-m-read').innerHTML=txt;
}
function buildFlAge(){
  var A=FL.age;
  mk('c-fl-age',{type:'line',data:{labels:A.labels,datasets:[
    {label:'AI-equipped',endLabel:'AI-equipped',data:A.AI,borderColor:css(TCOL.AI),backgroundColor:css(TCOL.AI),pointStyle:'circle',pointRadius:5,borderWidth:2.5,spanGaps:false},
    {label:'Conventional',endLabel:'Conventional',data:A.Conventional,borderColor:css(TCOL.Conventional),backgroundColor:css(TCOL.Conventional),pointStyle:'rect',pointRadius:5,borderWidth:2.5,borderDash:[6,4],spanGaps:false}]},
   options:Object.assign(base(),{layout:{padding:{top:8,right:8}},interaction:{mode:'index',intersect:false},plugins:{legend:legend(),tooltip:tip({label:function(c){return c.parsed.y==null?'':c.dataset.label+': $'+c.parsed.y.toFixed(3)+' per mile';}})},
    scales:{x:ax('Vehicle age when the cost was incurred',{grid:{display:false}}),y:ax('Maintenance cost per mile',{ticks:{callback:function(v){return '$'+v.toFixed(2);}}},{min:0})}})});
}
function flScatPts(t){return FL.vehicles.filter(function(v){return v.type===t&&(FS.s==='All'||v.lane===FS.s);}).map(function(v){return {x:v.age,y:v.profit,id:v.id,lane:v.lane};});}
function buildFlScat(){
  mk('c-fl-scat',{type:'scatter',data:{datasets:[
    {label:'AI-equipped',data:flScatPts('AI'),backgroundColor:css(TCOL.AI),pointStyle:'circle',pointRadius:5,pointHoverRadius:8},
    {label:'Conventional',data:flScatPts('Conventional'),backgroundColor:css(TCOL.Conventional),pointStyle:'rect',pointRadius:5,pointHoverRadius:8}]},
   options:Object.assign(base(),{plugins:{legend:legend(),tooltip:tip({label:function(c){var p=c.raw;return p.id+' ('+p.lane+'): '+usd0(p.y)+' profit, '+p.x+' months old';}})},
    scales:{x:ax('Vehicle age (months)',{grid:{display:false}},{min:0}),y:ax('Operating profit, last 12 months',{ticks:{callback:function(v){return usdK(v);}}},{min:0})}})});
}
function flScatRead(){
  var out=['AI','Conventional'].map(function(t){var p=flScatPts(t).map(function(v){return v.y;});var m=p.length?p.reduce(function(a,b){return a+b;},0)/p.length:0;return [t,p.length,m];});
  $('fl-s-read').innerHTML=out.map(function(o){return '<strong>'+(o[0]==='AI'?'AI-equipped':'Conventional')+'</strong>: '+o[1]+' tractors, average '+usd0(o[2])+' a year. ';}).join('');
}
/* payback calculator (mirrors fleet/02_analyze.py) */
function flUnit(lane,typ,age){
  var c=FL.calc.cells[lane+'|'+typ],m=c.miles*(1+(typ==='AI'?FS.util/100:0)),
      maint=Math.max(0.03,c.maint_pm+FL.calc.slope[typ]*(age-c.mean_age));
  return m*(c.rev_pm-c.gal_pm*FS.diesel-c.driver_pm-c.other_pm-maint)-c.ins-(typ==='AI'?FS.soft:c.software);
}
function flProject(){
  var T=['AI','Conventional'],life=FL.calc.life_months,r=FL.calc.rate/12,acq={},cum={},npv={},lane=FS.p;
  T.forEach(function(t){var c=FL.calc.cells[lane+'|'+t];acq[t]=c.acq+(t==='AI'?FS.prem-FL.fleet.premium:0);cum[t]=[-acq[t]];npv[t]=-acq[t];});
  for(var m=1;m<=life;m++){T.forEach(function(t){var cash=flUnit(lane,t,m);cum[t].push(cum[t][m-1]+cash);npv[t]+=cash/Math.pow(1+r,m);});}
  T.forEach(function(t){var res=FL.calc.cells[lane+'|'+t].resid*acq[t];cum[t][life]+=res;npv[t]+=res/Math.pow(1+r,life);});
  var diff=cum.AI.map(function(v,i){return v-cum.Conventional[i];}),pay=-1;
  for(var i=0;i<diff.length;i++){if(diff[i]>=0){pay=i;break;}}
  return {diff:diff,pay:pay,npv:npv.AI-npv.Conventional};
}
function buildFlPay(){
  var P=flProject(),labels=P.diff.map(function(_,i){return i;});
  mk('c-fl-pay',{type:'line',data:{labels:labels,datasets:[{label:'AI minus conventional, cumulative cash per truck',data:P.diff,borderColor:css('--c1'),backgroundColor:rgba(css('--c1').indexOf('#')===0?css('--c1'):'#2a78d6',.12),fill:{target:{value:0},above:rgba('#2a78d6',.14),below:rgba('#d95926',.14)},pointRadius:0,borderWidth:2.5,tension:0}]},
   options:Object.assign(base(),{layout:{padding:{top:8,right:8}},interaction:{mode:'index',intersect:false},plugins:{legend:{display:false},tooltip:tip({title:function(i){return 'Month '+i[0].label;},label:function(c){return usd0(c.parsed.y)+' cumulative advantage';}})},
    scales:{x:ax('Months in service',{grid:{display:false},ticks:{maxTicksLimit:8}}),y:ax('Cumulative cash advantage',{ticks:{callback:function(v){return usdK(v);}}})}})});
}
function flPayRead(){
  var P=flProject();
  $('fl-diesel-out').textContent='$'+FS.diesel.toFixed(2);$('fl-prem-out').textContent=usd0(FS.prem);$('fl-util-out').textContent=(FS.util>0?'+':'')+FS.util+'%';$('fl-soft-out').textContent=usd0(FS.soft);
  $('fl-npv').textContent=(P.npv>=0?'+':'-')+usd0(Math.abs(P.npv))+' per truck';
  $('fl-pay').textContent=P.pay<0?'No payback within the 7-year life on '+FS.p+' lanes.':'Payback after '+P.pay+' months on '+FS.p+' lanes.';
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
  on('seg-sel','change',function(){state.dim=$('seg-sel').value;churnRead();buildChurn();});
  on('copy-email','click',function(){
    var btn=$('copy-email');
    function fallback(){var r=document.createRange();r.selectNodeContents($('email-text'));var sel=window.getSelection();sel.removeAllRanges();sel.addRange(r);btn.textContent='Selected, now copy';}
    function ok(){btn.textContent='Copied';setTimeout(function(){btn.textContent='Copy email';},1800);}
    try{navigator.clipboard.writeText($('email-text').textContent).then(ok,fallback);}catch(e){fallback();}
  });
  function segWire(id,attr,key,after){Array.prototype.forEach.call(document.querySelectorAll('#'+id+' button'),function(b){b.addEventListener('click',function(){
    FS[key]=b.getAttribute(attr);Array.prototype.forEach.call(document.querySelectorAll('#'+id+' button'),function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});after();});});}
  segWire('fl-lane','data-l','lane',function(){flCpmRead();buildFlCpm();});
  segWire('fl-m','data-m','m',function(){flMaintRead();buildFlMaint();});
  segWire('fl-s','data-s','s',function(){flScatRead();buildFlScat();});
  segWire('fl-p','data-p','p',function(){flPayRead();buildFlPay();});
  [['fl-diesel','diesel',1],['fl-prem','prem',1],['fl-util','util',1],['fl-soft','soft',1]].forEach(function(a){on(a[0],'input',function(){FS[a[1]]=parseFloat($(a[0]).value);flPayRead();buildFlPay();});});
  on('fl-reset','click',function(){FS.diesel=FL.calc.defaults.diesel;FS.prem=FL.calc.defaults.premium;FS.util=0;FS.soft=FL.calc.defaults.software;
    $('fl-diesel').value=FS.diesel.toFixed(2);$('fl-prem').value=FS.prem;$('fl-util').value=0;$('fl-soft').value=FS.soft;flPayRead();buildFlPay();});
  /* theme toggle */
  var tb=$('theme-btn');
  function effective(){var t=document.documentElement.getAttribute('data-theme');if(t)return t;return (window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';}
  function label(){if(tb)tb.textContent=effective()==='dark'?'Light mode':'Dark mode';}
  if(tb){tb.addEventListener('click',function(){document.documentElement.setAttribute('data-theme',effective()==='dark'?'light':'dark');label();});}
  label();
  try{window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',function(){label();if(window.Chart)build();});}catch(e){}
  new MutationObserver(function(){label();if(window.Chart)build();}).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
}

supRead();svcRead();bridgeRead();scenRead();churnRead();flCpmRead();flMaintRead();flScatRead();flPayRead();wire();
function boot(){if(!window.Chart){setTimeout(boot,100);return;}build();}
boot();
})();
