"""Design tokens shared by the cast picker and the board, so both read as one system.

Light and dark themes: the page follows the operating system unless the viewer
picks one with the theme button (remembered per browser when storage allows).
No web fonts and no external requests: both pages work offline from file://.
"""

TOKENS = r"""
:root{
  --bg:#f5f5f2; --surface:#ffffff; --surface-2:#f0f0ec; --surface-3:#e8e8e3;
  --line:#e2e1db; --line-2:#d3d2cb;
  --text:#16171a; --text-2:#4f535a; --text-3:#858991;
  --accent:#3451f5; --accent-ink:#ffffff; --accent-soft:rgba(52,81,245,.10);
  --good:#108a46; --good-soft:rgba(16,138,70,.11);
  --warn:#b07400; --warn-soft:rgba(176,116,0,.12);
  --bad:#cf2f2f;  --bad-soft:rgba(207,47,47,.10);
  --shadow:0 1px 2px rgba(20,20,30,.05),0 8px 24px -12px rgba(20,20,30,.14);
  --radius:14px; --radius-sm:9px;
  --sans:ui-sans-serif,"Inter","Segoe UI Variable Text","Segoe UI",system-ui,-apple-system,Roboto,"Helvetica Neue",Arial,sans-serif;
  --mono:ui-monospace,"JetBrains Mono","SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
  color-scheme:light;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --bg:#0d0e10; --surface:#15171a; --surface-2:#1b1e22; --surface-3:#23262b;
    --line:#262a30; --line-2:#333840;
    --text:#ececee; --text-2:#a8adb5; --text-3:#6e747c;
    --accent:#8095ff; --accent-ink:#0b0c10; --accent-soft:rgba(128,149,255,.14);
    --good:#3fd68a; --good-soft:rgba(63,214,138,.12);
    --warn:#f2b544; --warn-soft:rgba(242,181,68,.13);
    --bad:#ff6b6b;  --bad-soft:rgba(255,107,107,.12);
    --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px -14px rgba(0,0,0,.6);
    color-scheme:dark;
  }
}
:root[data-theme="dark"]{
  --bg:#0d0e10; --surface:#15171a; --surface-2:#1b1e22; --surface-3:#23262b;
  --line:#262a30; --line-2:#333840;
  --text:#ececee; --text-2:#a8adb5; --text-3:#6e747c;
  --accent:#8095ff; --accent-ink:#0b0c10; --accent-soft:rgba(128,149,255,.14);
  --good:#3fd68a; --good-soft:rgba(63,214,138,.12);
  --warn:#f2b544; --warn-soft:rgba(242,181,68,.13);
  --bad:#ff6b6b;  --bad-soft:rgba(255,107,107,.12);
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px -14px rgba(0,0,0,.6);
  color-scheme:dark;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:var(--bg);color:var(--text);font:15px/1.55 var(--sans);
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
a{color:var(--accent);text-underline-offset:2px}
button,input,select,textarea{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:6px}
.mono{font-family:var(--mono)}
.eyebrow{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--text-3);font-weight:600}
.brand{display:inline-flex;align-items:center;gap:9px;font-weight:700;letter-spacing:-.01em;font-size:14px;color:var(--text)}
.brand svg{display:block}
.iconbtn{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:10px;
  border:1px solid var(--line);background:var(--surface);color:var(--text-2);cursor:pointer}
.iconbtn:hover{color:var(--text);border-color:var(--line-2)}
"""

# The mark: a ring of independent dots around one centre, used in both pages.
MARK_SVG = (
    '<svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">'
    '<circle cx="12" cy="12" r="3.2" fill="currentColor"/>'
    '<g fill="var(--accent)">'
    '<circle cx="12" cy="3.2" r="1.9"/><circle cx="19.6" cy="7.6" r="1.9"/>'
    '<circle cx="19.6" cy="16.4" r="1.9"/><circle cx="12" cy="20.8" r="1.9"/>'
    '<circle cx="4.4" cy="16.4" r="1.9"/><circle cx="4.4" cy="7.6" r="1.9"/></g></svg>'
)

THEME_BUTTON = (
    '<button class="iconbtn" id="theme" type="button" title="Switch light or dark theme" '
    'aria-label="Switch light or dark theme">'
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.5"/>'
    '<path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8'
    'M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg></button>'
)

THEME_JS = r"""
(function(){
  var KEY='focus-swarm.theme', root=document.documentElement;
  try{var t=localStorage.getItem(KEY); if(t==='light'||t==='dark') root.setAttribute('data-theme',t);}catch(e){}
  var q=new URLSearchParams(location.search).get('theme');
  if(q==='light'||q==='dark') root.setAttribute('data-theme',q);
  function current(){
    var t=root.getAttribute('data-theme'); if(t) return t;
    return window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  document.addEventListener('DOMContentLoaded',function(){
    var b=document.getElementById('theme'); if(!b) return;
    b.addEventListener('click',function(){
      var next=current()==='dark'?'light':'dark'; root.setAttribute('data-theme',next);
      try{localStorage.setItem(KEY,next);}catch(e){}
    });
  });
})();
"""
