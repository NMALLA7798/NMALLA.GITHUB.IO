"""Shared design tokens, helpers and page wrappers for the personal site (home, PM case, analytics case studies)."""
import html

CSS = r"""
/* Layout: one calm column (max 1040px). Numbered sections, quiet rules, one cobalt accent used for actions and data. */
:root{--bg:#fafbfc;--panel:#ffffff;--ink:#12161c;--ink2:#4a5360;--muted:#6b7482;--rule:#e2e6ec;--rule2:#c9d0da;
--accent:#2447e0;--accent-ink:#ffffff;--accent-soft:#e8edfd;--warm:#c77700;--good:#0d8a5f;--bad:#c2392f;
--c1:#2447e0;--c2:#d9531e;--c3:#0f9d78;--c4:#d99a00;
--display:"Bricolage Grotesque","DM Sans",system-ui,sans-serif;--sans:"DM Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"JetBrains Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0d1117;--panel:#151b23;--ink:#e9edf2;--ink2:#b7c0cc;--muted:#8f9aa8;--rule:#232b36;--rule2:#34404e;
--accent:#7f9bff;--accent-ink:#0b1020;--accent-soft:#1a2440;--warm:#f0b04a;--good:#3fd19b;--bad:#ff7a6e;--c1:#7f9bff;--c2:#ff8a5c;--c3:#3fd1a4;--c4:#f0c24a;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0d1117;--panel:#151b23;--ink:#e9edf2;--ink2:#b7c0cc;--muted:#8f9aa8;--rule:#232b36;--rule2:#34404e;
--accent:#7f9bff;--accent-ink:#0b1020;--accent-soft:#1a2440;--warm:#f0b04a;--good:#3fd19b;--bad:#ff7a6e;--c1:#7f9bff;--c2:#ff8a5c;--c3:#3fd1a4;--c4:#f0c24a;color-scheme:dark}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:72px}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.65 var(--sans);-webkit-font-smoothing:antialiased}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:20;background:var(--bg)}
a{color:var(--accent)}a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid var(--accent);outline-offset:2px;border-radius:4px}
.wrap{max-width:1040px;margin:0 auto;padding-left:max(18px,env(safe-area-inset-left,0px));padding-right:max(18px,env(safe-area-inset-right,0px))}
nav.top{position:sticky;top:env(safe-area-inset-top,0px);z-index:10;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--rule)}
nav.top .wrap{display:flex;align-items:center;gap:22px;min-height:58px}
.brand{font:700 1.02rem var(--display);color:var(--ink);text-decoration:none;white-space:nowrap}
.tag{color:var(--muted);font-size:.82rem;white-space:nowrap}
.links{display:flex;gap:20px;margin-left:auto;overflow-x:auto;scrollbar-width:none;min-width:0;align-items:center}
.links a{color:var(--ink2);text-decoration:none;font-size:.92rem;white-space:nowrap}.links a:hover{color:var(--ink)}
.btn{display:inline-flex;align-items:center;gap:8px;font:600 .92rem var(--sans);padding:10px 18px;border-radius:999px;border:1px solid var(--rule2);background:transparent;color:var(--ink);text-decoration:none;cursor:pointer}
.btn.primary{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.btn.small{padding:6px 12px;font-size:.82rem}
.hero{padding:64px 0 28px;display:grid;grid-template-columns:auto minmax(0,1fr);gap:32px;align-items:center}
.mono-badge{width:116px;height:116px;border-radius:28px;background:var(--accent);color:var(--accent-ink);display:grid;place-items:center;font:700 2.6rem var(--display);letter-spacing:-.04em}
.eyebrow{font:500 .76rem var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--accent);margin:0 0 8px}
h1{font:700 clamp(2.4rem,6vw,4.2rem)/1.02 var(--display);letter-spacing:-.035em;margin:0 0 14px;text-wrap:balance}
.lede{font-size:clamp(1.05rem,2vw,1.28rem);color:var(--ink2);max-width:62ch;margin:0}
.stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border:1px solid var(--rule);border-radius:14px;background:var(--panel);margin:12px 0 22px}
.stat{padding:18px 22px;border-left:1px solid var(--rule)}.stat:first-child{border-left:0}
.stat b{display:block;font:700 1.9rem var(--display);letter-spacing:-.02em;font-variant-numeric:tabular-nums}.stat span{font-size:.86rem;color:var(--ink2)}
.cta{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.flow{margin:34px 0 8px;padding:22px;border:1px solid var(--rule);border-radius:14px;background:var(--panel)}
.flow h2{font:600 .78rem var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:0 0 16px}
.nodes{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:0;align-items:stretch}
.node{position:relative;padding:14px 14px 14px 14px;border:1px solid var(--rule2);border-radius:10px;margin-right:22px;background:var(--bg)}
.node:last-child{margin-right:0}.node:not(:last-child)::after{content:"";position:absolute;right:-22px;top:50%;width:22px;height:2px;background:var(--accent)}
.node:not(:last-child)::before{content:"";position:absolute;right:-22px;top:calc(50% - 4px);border:5px solid transparent;border-left:7px solid var(--accent);border-right:0}
.node b{display:block;font:700 .98rem var(--display)}.node small{display:block;color:var(--ink2);font-size:.8rem;line-height:1.4;margin-top:4px}
.node em{display:block;font:500 .72rem var(--mono);color:var(--accent);font-style:normal;margin-top:8px}
.cap{color:var(--muted);font-size:.86rem;margin:14px 0 0}
section.sec{padding:60px 0 10px}
.sh{display:flex;align-items:baseline;gap:14px;margin:0 0 22px}.sh .n{font:500 .85rem var(--mono);color:var(--accent)}.sh h2{font:700 clamp(1.6rem,3.4vw,2.2rem) var(--display);letter-spacing:-.02em;margin:0;text-wrap:balance}
.feat{border:1px solid var(--rule);border-radius:16px;background:var(--panel);padding:26px;display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:28px}
.feat h3{font:700 1.5rem/1.2 var(--display);margin:6px 0 10px;letter-spacing:-.015em}.feat p{margin:0 0 12px;color:var(--ink2)}
.badge{display:inline-block;font:500 .72rem var(--mono);padding:3px 9px;border-radius:999px;background:var(--accent-soft);color:var(--accent);margin-right:6px}
.badge.w{background:transparent;border:1px solid var(--rule2);color:var(--muted)}
.pills{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 0}.pill{font:500 .74rem var(--mono);padding:3px 9px;border:1px solid var(--rule2);border-radius:6px;color:var(--ink2)}
.demo{border:1px solid var(--rule);border-radius:12px;padding:16px;background:var(--bg)}
.demo .lab{font:500 .72rem var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.demo input[type=range]{width:100%;accent-color:var(--accent)}
.big{font:700 2rem var(--display);font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:16px}
.grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.card{border:1px solid var(--rule);border-radius:14px;background:var(--panel);padding:20px;min-width:0;display:flex;flex-direction:column;gap:8px}
.card h3{font:700 1.08rem/1.3 var(--display);margin:0}.card p{margin:0;color:var(--ink2);font-size:.95rem}
.card .metric{font:700 1.5rem var(--display);color:var(--ink);letter-spacing:-.01em;margin-top:auto}.card .metric small{display:block;font:400 .8rem var(--sans);color:var(--muted)}
a.card{color:inherit;text-decoration:none}a.card:hover{border-color:var(--accent)}
.services .card h3{font-size:1rem}
.timeline{display:grid;gap:0;border-left:2px solid var(--rule2);margin-left:6px}
.job{padding:0 0 26px 24px;position:relative}.job::before{content:"";position:absolute;left:-7px;top:7px;width:12px;height:12px;border-radius:50%;background:var(--accent);border:2px solid var(--bg)}
.job h3{font:700 1.15rem var(--display);margin:0}.job .when{font:500 .78rem var(--mono);color:var(--muted)}
.job ul{margin:8px 0 0;padding-left:1.1rem;color:var(--ink2)}.job li{margin-bottom:6px;font-size:.97rem}
.cols3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
.col h3{font:600 .78rem var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:0 0 10px}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{font:500 .86rem var(--sans);padding:7px 13px;border-radius:999px;border:1px solid var(--rule2);background:var(--panel);color:var(--ink);cursor:pointer}
.chip[aria-pressed="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.case{margin-top:20px;padding:20px;border:1px solid var(--rule);border-left:4px solid var(--accent);border-radius:10px;background:var(--panel);min-height:7.5rem}
.case h3{margin:0 0 6px;font:700 1.1rem var(--display)}.case p{margin:0 0 10px;color:var(--ink2)}
.about p{max-width:64ch;color:var(--ink2)}
.contact{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:16px}
.contact code{font:500 .95rem var(--mono);padding:8px 12px;border:1px solid var(--rule2);border-radius:8px;background:var(--panel)}
footer{margin-top:70px;border-top:1px solid var(--rule);padding:26px 0 56px;color:var(--muted);font-size:.86rem}
footer .wrap{display:flex;flex-wrap:wrap;gap:8px 24px;justify-content:space-between}
.theme{font:inherit;font-size:.82rem;background:transparent;border:1px solid var(--rule2);color:var(--ink2);border-radius:999px;padding:5px 12px;cursor:pointer}
/* case-study page */
.page-h{padding:52px 0 10px}.crumb{font:500 .8rem var(--mono);color:var(--muted);text-decoration:none}
.page-h h1{font-size:clamp(2rem,4.6vw,3.2rem)}
.meta{color:var(--muted);font-size:.9rem;margin:10px 0 0}
.tldr{border:1px solid var(--rule);border-left:4px solid var(--accent);border-radius:10px;background:var(--panel);padding:20px 22px;margin:26px 0}
.tldr h2{font:600 .78rem var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}.tldr p{margin:0 0 8px}.tldr ul{margin:8px 0 0;padding-left:1.1rem}
h2.s{font:700 1.6rem var(--display);letter-spacing:-.02em;margin:46px 0 8px}h3.s{font:700 1.1rem var(--display);margin:22px 0 6px}
.lead{color:var(--ink2);max-width:68ch;margin:0 0 14px}
.panel{border:1px solid var(--rule);border-radius:14px;background:var(--panel);padding:20px;margin:16px 0}
.ctl{display:grid;grid-template-columns:150px minmax(0,1fr) 78px;gap:12px;align-items:center;margin:8px 0;font-size:.92rem}
.ctl output{text-align:right;font:600 .9rem var(--mono)}.ctl input{width:100%;accent-color:var(--accent)}
.seg{display:inline-flex;flex-wrap:wrap;max-width:100%;border:1px solid var(--rule2);border-radius:8px;overflow:hidden}.seg button{font:500 .84rem var(--mono);background:transparent;color:var(--ink);border:0;padding:7px 12px;cursor:pointer}.seg button+button{border-left:1px solid var(--rule2)}.seg button[aria-pressed="true"]{background:var(--ink);color:var(--bg)}
.read{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0;border:1px solid var(--rule);border-radius:12px;margin:14px 0}
.read div{padding:12px 16px;border-left:1px solid var(--rule)}.read div:first-child{border-left:0}.read b{display:block;font:700 1.5rem var(--display);font-variant-numeric:tabular-nums}.read span{font-size:.8rem;color:var(--muted)}
.cv{position:relative;height:320px}.cv.tall{height:360px}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:.92rem}th,td{padding:9px 10px;border-bottom:1px solid var(--rule);text-align:left;vertical-align:top}th{font:600 .78rem var(--sans);color:var(--muted)}td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
td input[type=number]{width:72px;font:inherit;padding:4px 6px;border:1px solid var(--rule2);border-radius:6px;background:var(--bg);color:var(--ink)}
.phases{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.phase{border:1px solid var(--rule);border-radius:12px;background:var(--panel);padding:16px}.phase .p{font:500 .74rem var(--mono);color:var(--accent)}.phase h3{font:700 1rem var(--display);margin:4px 0 6px}.phase p{margin:0 0 8px;font-size:.9rem;color:var(--ink2)}.phase .gate{font-size:.82rem;color:var(--muted);border-top:1px solid var(--rule);padding-top:8px}
.note{font-size:.86rem;color:var(--muted)}
@media(max-width:820px){.hero{grid-template-columns:minmax(0,1fr);padding-top:40px}.mono-badge{width:84px;height:84px;font-size:1.9rem;border-radius:20px}
.feat,.grid3,.grid2,.cols3,.phases{grid-template-columns:minmax(0,1fr)}.nodes{grid-template-columns:minmax(0,1fr);gap:20px}.node{margin-right:0}.node:not(:last-child)::after{right:auto;left:50%;top:auto;bottom:-20px;width:2px;height:20px}.node:not(:last-child)::before{right:auto;left:calc(50% - 4px);top:auto;bottom:-24px;border:5px solid transparent;border-top:7px solid var(--accent);border-bottom:0}
.stats{grid-template-columns:minmax(0,1fr)}.stat{border-left:0;border-top:1px solid var(--rule)}.stat:first-child{border-top:0}.tag{display:none}.read{grid-template-columns:repeat(2,minmax(0,1fr))}.read div:nth-child(3){border-left:0;border-top:1px solid var(--rule)}.read div:nth-child(4){border-top:1px solid var(--rule)}.ctl{grid-template-columns:minmax(0,1fr) 70px}.ctl label{grid-column:1/-1}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=DM+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">')
THEME_JS = r"""
(function(){var tb=document.getElementById('theme');if(!tb)return;
function eff(){var t=document.documentElement.getAttribute('data-theme');if(t)return t;return (window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';}
function lab(){tb.textContent=eff()==='dark'?'Light mode':'Dark mode';}
try{var s=localStorage.getItem('th');if(s)document.documentElement.setAttribute('data-theme',s);}catch(e){}
tb.addEventListener('click',function(){var n=eff()==='dark'?'light':'dark';document.documentElement.setAttribute('data-theme',n);try{localStorage.setItem('th',n);}catch(e){}lab();});lab();})();
"""
COPY_JS = r"""
(function(){var b=document.getElementById('copy-email'),t=document.getElementById('email-text');if(!b||!t)return;
b.addEventListener('click',function(){function ok(){b.textContent='Copied';setTimeout(function(){b.textContent='Copy email';},1800);}
function fb(){var r=document.createRange();r.selectNodeContents(t);var s=window.getSelection();s.removeAllRanges();s.addRange(r);b.textContent='Selected, now copy';}
try{navigator.clipboard.writeText(t.textContent).then(ok,fb);}catch(e){fb();}});})();
"""

def head(title, desc):
    return (f'<title>{html.escape(title)}</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
            f'<meta name="description" content="{html.escape(desc)}">\n{FONTS}\n<style>{CSS}</style>\n')

def fragment(title, desc, body):
    return head(title, desc) + body

def full(title, desc, body, lang_theme=True):
    h = head(title, desc).replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            + h + '</head><body>\n' + body + '\n</body></html>\n')

def to_full(fragment_html):
    """Turn a published fragment (title/meta/style first, then body) into a standalone document."""
    i = fragment_html.index("</style>") + len("</style>")
    h = fragment_html[:i].replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            + h + '</head><body>' + fragment_html[i:] + '\n</body></html>\n')

EMAIL = "malla.nischal@outlook.com"
LINKEDIN = "https://www.linkedin.com/in/nischal-malla/"
