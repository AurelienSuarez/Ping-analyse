import re
D=""
up=open(D+"montees-sqy-ping.html").read(); dn=open(D+"maintien-sqy-ping.html").read()
style=re.search(r"<style>(.*?)</style>",dn,re.S).group(1)
links="\n".join(re.findall(r"<link[^>]+>",dn))
box=open("weekly_box.html").read() if __import__("os").path.exists("weekly_box.html") else ""
def body(h): return re.search(r'<div class="wrap">(.*)</div>\s*$',h,re.S).group(1)
TABCSS="""
.week{max-width:900px;margin:20px auto 0;padding:14px 16px;background:var(--surface);border:1px solid var(--line);border-radius:6px;display:grid;gap:6px}
.week-wrap{padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.week h2{font-size:1.3rem} .week ul{margin:0;padding-left:1.2em;display:grid;gap:4px} .week .lab{font-size:.74rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:6px 0 0} .week p{margin:0}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--surface)}
.tabs{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--surface);border-bottom:1px solid var(--line)}
.tabs-in{max-width:900px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:flex;gap:4px;align-items:flex-end}
.brand{font-family:var(--display);font-weight:700;font-size:1.15rem;margin-right:auto;padding-block:10px;white-space:nowrap}
.tab{font-family:var(--display);font-size:1.15rem;font-weight:600;color:var(--muted);text-decoration:none;padding:10px 14px 8px;border-bottom:3px solid transparent}
.tab:hover{color:var(--fg)} .tab:focus-visible{outline:2px solid var(--up);outline-offset:-2px}
.tab[aria-selected="true"]{color:var(--fg);border-bottom-color:var(--up)}
.tab.dn[aria-selected="true"]{border-bottom-color:var(--down)}
@media (max-width:420px){.brand{display:none}}
"""
page=f'''<title>Enjeux SQY Ping</title>
<meta name="claude:viewport-fit-sides" content="cover">
{links}
<style>{style}{TABCSS}</style>
<nav class="tabs"><div class="tabs-in" role="tablist" aria-label="Enjeux de la phase">
<span class="brand">SQY Ping · Enjeux</span>
<a class="tab" role="tab" id="t-montee" href="#montee" aria-controls="montee">Montée</a>
<a class="tab dn" role="tab" id="t-descente" href="#descente" aria-controls="descente">Descente</a>
</div></nav>
{"<div class=\"week-wrap\">"+box+"</div>" if box else ""}
<div class="wrap" id="montee" role="tabpanel" aria-labelledby="t-montee">{body(up)}</div>
<div class="wrap" id="descente" role="tabpanel" aria-labelledby="t-descente" hidden>{body(dn)}</div>
<script>
function show(){{const k=location.hash==='#descente'?'descente':'montee';
 for(const id of ['montee','descente']){{document.getElementById(id).hidden=id!==k;document.getElementById('t-'+id).setAttribute('aria-selected',id===k)}}
 window.scrollTo(0,0)}}
window.addEventListener('hashchange',show);show();
</script>'''
open(D+"enjeux-sqy-ping.html","w").write(page)
print(len(page))
