(function(){
function $(i){return document.getElementById(i);}
var D=JSON.parse(document.getElementById('hdata').textContent);
/* mini threshold demo */
var s=$('m-t');if(s){function upd(){var t=parseInt(s.value,10)/100,r=D.curve[String(t.toFixed(2))];
  $('m-tv').textContent=t.toFixed(2);$('m-cov').textContent=(r.cov*100).toFixed(1)+'%';$('m-prec').textContent=(r.prec*100).toFixed(1)+'%';
  var ok=r.prec>=0.97;$('m-flag').textContent=ok?'Passes the 97% precision gate':'Fails the 97% precision gate';$('m-flag').style.color=ok?'var(--good)':'var(--bad)';}
  s.addEventListener('input',upd);upd();}
/* skills -> case study */
var chips=document.querySelectorAll('.skill');
function show(k){var c=D.skills[k];$('case-t').textContent=k;$('case-p').textContent=c.text;var l=$('case-l');l.textContent=c.link_label;l.setAttribute('href',c.href);
  Array.prototype.forEach.call(chips,function(x){x.setAttribute('aria-pressed',x.getAttribute('data-k')===k?'true':'false');});}
Array.prototype.forEach.call(chips,function(b){b.addEventListener('click',function(){show(b.getAttribute('data-k'));});});
show('SQL');
})();
