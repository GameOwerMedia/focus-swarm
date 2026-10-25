#!/usr/bin/env python3
"""
Cast picker: compose the swarm by hand before it runs.

Interactive (serves a local page, writes the config when you press Run):

    python picker.py --outdir <dir> --target <url|path> [--product "Name"]
                     [--targettype live|repo|document] [--port 8137] [--open]

Non-interactive (writes the config straight away, for shortcuts and CI):

    python picker.py --outdir <dir> --target <url> --preset lite --write
    python picker.py --outdir <dir> --target <url> --panels general=4,capital=3 --write

Static (writes picker.html you can open from disk; it downloads run.config.json):

    python picker.py --outdir <dir> --target <url> --static

Writes <outdir>/run.config.json with: target, target_type, product, date,
panels (id -> headcount), panel_order, real_people (panel ids), lang, notes.
The server listens on the loopback interface only, shows its address as
http://localhost:<port>/ and stops itself after the config is saved.
"""

import argparse
import json
import os
import sys
import threading
import webbrowser
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import _common as C
import _theme as T

BIND_HOST = "127.0.0.1"  # loopback only: the page is never reachable from other machines


def local_url(port):
    """The address shown to the user for a picker served on BIND_HOST."""
    return "http://localhost:%d/" % port


LANGS = [("en", "English"), ("de", "Deutsch"), ("es", "Español"), ("fr", "Français"),
         ("it", "Italiano"), ("nl", "Nederlands"), ("pl", "Polski"), ("pt", "Português"),
         ("ja", "日本語"), ("zh", "中文")]


def script_json(obj):
    """JSON that is safe to inline inside a <script> element."""
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")


def build_config(base, panels, lib, real_people=(), lang="en", notes="", mode="custom"):
    known = {p["id"] for p in lib.get("panels", [])}
    unknown = [k for k in panels if k not in known]
    if unknown:
        raise ValueError("unknown panel ids: %s" % ", ".join(unknown))
    allowed_real = {p["id"] for p in lib.get("panels", []) if p.get("can_cast_real_people")}
    bad_real = [k for k in real_people if k not in allowed_real]
    if bad_real:
        raise ValueError("real-people research is not available for: %s" % ", ".join(bad_real))
    cfg = dict(base)
    cfg["panels"] = {k: int(v) for k, v in panels.items() if int(v) > 0}
    cfg["panel_order"] = [p["id"] for p in lib["panels"] if p["id"] in cfg["panels"]]
    cfg["real_people"] = [k for k in real_people if k in cfg["panels"]]
    cfg["lang"] = lang or "en"
    cfg["notes"] = notes or ""
    cfg["mode"] = mode
    return cfg


def render(cfg, lib, static=False):
    data = {"cfg": cfg, "lib": lib, "langs": LANGS, "static": static}
    return PAGE.replace("/*TOKENS*/", T.TOKENS).replace("/*CSS*/", CSS) \
        .replace("<!--MARK-->", T.MARK_SVG).replace("<!--THEME-->", T.THEME_BUTTON) \
        .replace("/*THEME_JS*/", T.THEME_JS).replace("/*DATA*/", script_json(data)) \
        .replace("/*APP*/", APP)


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cast picker</title>
<style>/*TOKENS*//*CSS*/</style>
<script>/*THEME_JS*/</script>
</head><body>
<header class="top">
  <div class="wrap row">
    <span class="brand"><!--MARK-->focus-swarm</span>
    <span class="crumb">cast picker</span>
    <span class="grow"></span>
    <!--THEME-->
  </div>
</header>
<main class="wrap layout">
  <section class="main">
    <div class="intro">
      <p class="eyebrow">Step 1 of 4 &middot; compose the cast</p>
      <h1>Who should visit <span id="product"></span>?</h1>
      <p class="lead">Every person you add becomes a separate agent with its own context. It opens the product on its own, never sees the other reports, and files a structured review.</p>
      <div class="target"><span class="ttype" id="ttype"></span><code id="tval"></code></div>
    </div>

    <div class="presets-head"><h2>Start from a preset</h2><button class="link" id="clear" type="button">Clear all</button></div>
    <div class="presets" id="presets"></div>

    <div id="families"></div>
  </section>

  <aside class="side">
    <div class="sum card">
      <div class="sumhead">
        <div><div class="big" id="total">0</div><div class="eyebrow">agents</div></div>
        <div class="eta" id="eta"></div>
      </div>
      <div class="compbar" id="compbar" aria-hidden="true"></div>
      <ul class="picked" id="picked"></ul>
      <p class="empty" id="emptyhint">Pick a preset or add people to a panel.</p>
      <div class="realwarn" id="realwarn" hidden>
        <b>Real-people research is on.</b> Those panels are profiled from public sources about real, named professionals. Everything they say stays a labelled simulation, and the package is marked for internal use only.
      </div>
      <label class="field"><span class="eyebrow">Report language</span>
        <select id="lang"></select></label>
      <label class="field"><span class="eyebrow">Anything to watch for</span>
        <textarea id="notes" rows="3" placeholder="e.g. check the purchase flow on a phone, pricing is new"></textarea></label>
      <button class="run" id="run" type="button" disabled>Run the swarm</button>
      <p class="fine" id="finehint">Writes run.config.json next to the run. Nothing is sent anywhere else.</p>
    </div>
  </aside>
</main>

<div class="done" id="done" hidden>
  <div class="donecard card">
    <div class="tick" aria-hidden="true"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></div>
    <h2>Cast saved</h2>
    <p id="donetext">Go back to Claude Code. The swarm starts from this cast.</p>
    <pre class="mono" id="donecfg"></pre>
  </div>
</div>

<script>const DATA = /*DATA*/;</script>
<script>/*APP*/</script>
</body></html>
"""

CSS = r"""
.wrap{max-width:1240px;margin:0 auto;padding:0 24px}
.top{border-bottom:1px solid var(--line);background:color-mix(in srgb,var(--bg) 82%,transparent);
  backdrop-filter:saturate(1.4) blur(10px);position:sticky;top:0;z-index:5}
.row{display:flex;align-items:center;gap:14px;height:58px}
.grow{flex:1}
.crumb{color:var(--text-3);font-size:13px;padding-left:14px;border-left:1px solid var(--line)}
.layout{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:32px;align-items:start;padding-top:34px;padding-bottom:80px}
.intro h1{font-size:34px;line-height:1.12;letter-spacing:-.025em;margin:8px 0 10px;font-weight:700}
.intro h1 span{color:var(--accent)}
.lead{color:var(--text-2);max-width:62ch;margin:0 0 18px;font-size:15.5px}
.target{display:inline-flex;align-items:center;gap:10px;background:var(--surface);border:1px solid var(--line);
  border-radius:999px;padding:6px 14px 6px 6px;max-width:100%}
.ttype{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;background:var(--accent-soft);
  color:var(--accent);padding:4px 9px;border-radius:999px}
.target code{font-family:var(--mono);font-size:13px;color:var(--text-2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
h2{font-size:15px;margin:0;letter-spacing:-.01em}
.presets-head{display:flex;align-items:baseline;justify-content:space-between;margin:38px 0 12px}
.link{background:none;border:0;color:var(--text-3);cursor:pointer;font-size:13px;padding:0}
.link:hover{color:var(--text)}
.presets{display:grid;grid-template-columns:repeat(auto-fill,minmax(178px,1fr));gap:10px}
.preset{text-align:left;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-sm);
  padding:12px 14px;cursor:pointer;display:flex;flex-direction:column;gap:8px;transition:border-color .15s,transform .15s}
.preset:hover{border-color:var(--line-2);transform:translateY(-1px)}
.preset.on{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.preset b{font-size:14px;display:flex;justify-content:space-between;gap:8px}
.preset b span{font-family:var(--mono);font-weight:500;color:var(--text-3);font-size:12px}
.dots{display:flex;gap:3px;flex-wrap:wrap}
.dots i{width:7px;height:7px;border-radius:50%;display:block}
.family{margin-top:38px}
.family h2{margin-bottom:4px}
.family p.fdesc{margin:0 0 14px;color:var(--text-3);font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.pcard{position:relative;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  padding:16px 16px 14px;display:flex;flex-direction:column;gap:10px;transition:border-color .15s,box-shadow .15s}
.pcard::before{content:"";position:absolute;left:-1px;top:14px;bottom:14px;width:3px;border-radius:0 3px 3px 0;background:var(--a);opacity:.35}
.pcard.on{border-color:color-mix(in srgb,var(--a) 55%,var(--line));box-shadow:var(--shadow)}
.pcard.on::before{opacity:1}
.ptop{display:flex;align-items:flex-start;gap:12px}
.ptitle{flex:1;min-width:0}
.ptitle h3{margin:0;font-size:15px;letter-spacing:-.01em;display:flex;align-items:center;gap:8px}
.swatch{width:10px;height:10px;border-radius:3px;background:var(--a);flex:none}
.q{margin:6px 0 0;color:var(--text-2);font-size:13.5px;line-height:1.45}
.meta{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:11.5px;color:var(--text-2);background:var(--surface-2);border:1px solid var(--line);
  border-radius:999px;padding:2px 9px;white-space:nowrap}
.chip.blk{color:color-mix(in srgb,var(--a) 70%,var(--text));border-color:color-mix(in srgb,var(--a) 35%,var(--line));
  background:color-mix(in srgb,var(--a) 9%,var(--surface))}
.stepper{display:flex;align-items:center;border:1px solid var(--line);border-radius:10px;overflow:hidden;flex:none;background:var(--surface-2)}
.stepper button{width:30px;height:32px;border:0;background:transparent;cursor:pointer;font-size:17px;color:var(--text-2)}
.stepper button:hover{background:var(--surface-3);color:var(--text)}
.stepper input{width:38px;height:32px;border:0;border-left:1px solid var(--line);border-right:1px solid var(--line);
  background:var(--surface);text-align:center;font-family:var(--mono);font-size:14px;-moz-appearance:textfield}
.stepper input::-webkit-inner-spin-button{-webkit-appearance:none}
details.seats summary{cursor:pointer;font-size:12.5px;color:var(--text-3);list-style:none}
details.seats summary::-webkit-details-marker{display:none}
details.seats summary::before{content:"+ ";font-family:var(--mono)}
details.seats[open] summary::before{content:"\2212  "}
details.seats ol,details.seats ul{margin:8px 0 0;padding-left:20px;color:var(--text-2);font-size:12.5px}
details.seats li{margin:2px 0}
.real{display:flex;align-items:flex-start;gap:10px;padding:10px 12px;border-radius:10px;background:var(--surface-2);
  border:1px dashed var(--line-2);font-size:12.5px;color:var(--text-2);cursor:pointer}
.real input{margin:2px 0 0;accent-color:var(--warn)}
.real b{color:var(--text);font-weight:600}
.real.on{border-style:solid;border-color:color-mix(in srgb,var(--warn) 55%,var(--line));background:var(--warn-soft)}
.side{position:sticky;top:82px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}
.sum{padding:20px}
.sumhead{display:flex;justify-content:space-between;align-items:flex-end}
.big{font-size:46px;line-height:1;font-weight:700;letter-spacing:-.04em;font-variant-numeric:tabular-nums}
.eta{font-size:12.5px;color:var(--text-3);text-align:right;max-width:150px}
.compbar{display:flex;height:8px;border-radius:99px;overflow:hidden;background:var(--surface-2);margin:16px 0 12px;gap:2px}
.compbar i{display:block;height:100%}
.picked{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:6px}
.picked li{display:flex;align-items:center;gap:9px;font-size:13.5px}
.picked li .n{margin-left:auto;font-family:var(--mono);color:var(--text-2)}
.picked li .r{font-size:10.5px;font-weight:700;letter-spacing:.06em;color:var(--warn);text-transform:uppercase}
.empty{color:var(--text-3);font-size:13px;margin:4px 0 0}
.realwarn{margin:14px 0 0;padding:10px 12px;border-radius:10px;background:var(--warn-soft);color:var(--text-2);font-size:12.5px;line-height:1.45}
.realwarn b{color:var(--text)}
.field{display:block;margin-top:16px}
.field .eyebrow{display:block;margin-bottom:6px}
select,textarea{width:100%;background:var(--surface-2);border:1px solid var(--line);border-radius:10px;padding:9px 11px;font-size:14px}
textarea{resize:vertical;min-height:70px}
.run{width:100%;margin-top:18px;height:46px;border:0;border-radius:12px;background:var(--accent);color:var(--accent-ink);
  font-weight:700;font-size:15px;letter-spacing:.01em;cursor:pointer;transition:filter .15s,transform .1s}
.run:hover{filter:brightness(1.07)}
.run:active{transform:translateY(1px)}
.run:disabled{background:var(--surface-3);color:var(--text-3);cursor:not-allowed}
.fine{font-size:12px;color:var(--text-3);margin:10px 0 0;text-align:center}
.done{position:fixed;inset:0;background:color-mix(in srgb,var(--bg) 70%,transparent);backdrop-filter:blur(6px);
  display:flex;align-items:center;justify-content:center;z-index:10;padding:20px}
.done[hidden]{display:none}
.donecard{padding:30px;max-width:520px;width:100%;text-align:center}
.tick{width:52px;height:52px;border-radius:50%;background:var(--good-soft);color:var(--good);display:inline-flex;align-items:center;justify-content:center}
.donecard h2{font-size:22px;margin:14px 0 6px}
.donecard p{color:var(--text-2);margin:0 0 14px}
.donecard pre{text-align:left;background:var(--surface-2);border:1px solid var(--line);border-radius:10px;padding:12px;
  font-size:12px;max-height:220px;overflow:auto;margin:0}
@media (max-width:980px){.layout{grid-template-columns:1fr}.side{position:static}}
@media (max-width:560px){.wrap{padding:0 16px}.intro h1{font-size:27px}.grid{grid-template-columns:1fr}.crumb{display:none}}
"""

APP = r"""
(function(){
const {cfg, lib, langs, static: STATIC} = DATA;
const panels = lib.panels, byId = Object.fromEntries(panels.map(p => [p.id, p]));
const state = {n: {}, real: {}};
const $ = s => document.querySelector(s);
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const KEY = 'focus-swarm.picker.' + cfg.target;

$('#product').textContent = cfg.product || 'your product';
$('#ttype').textContent = cfg.target_type;
$('#tval').textContent = cfg.target;
$('#lang').innerHTML = langs.map(([v, l]) => `<option value="${esc(v)}">${esc(l)}</option>`).join('');

function dots(spec){
  return Object.entries(spec).map(([id, n]) => Array.from({length: Math.min(n, 14)}, () =>
    `<i style="background:${esc((byId[id]||{}).accent||'#888')}"></i>`).join('')).join('');
}
$('#presets').innerHTML = lib.presets.map(p => {
  const n = Object.values(p.panels).reduce((a, b) => a + b, 0);
  const names = Object.entries(p.panels).map(([id, k]) => `${(byId[id]||{}).label||id} ${k}`).join(', ');
  return `<button class="preset" type="button" data-id="${esc(p.id)}" title="${esc(names)}">
    <b>${esc(p.label)}<span>${n}</span></b><span class="dots">${dots(p.panels)}</span></button>`;
}).join('');

const fams = (lib.families && lib.families.length) ? lib.families : [{id: '', label: 'Panels'}];
const famDesc = {use: 'They meet the product in their own life or work.',
                 spread: 'They decide whether it reaches anyone.',
                 decide: 'They can fund it, buy it, approve it or block it.'};
$('#families').innerHTML = fams.map(f => {
  const list = panels.filter(p => (p.family || '') === f.id || (!f.id));
  if (!list.length) return '';
  return `<section class="family"><h2>${esc(f.label)}</h2><p class="fdesc">${esc(famDesc[f.id] || '')}</p>
    <div class="grid">${list.map(card).join('')}</div></section>`;
}).join('');

function card(p){
  const blk = p.extra_block ? `<span class="chip blk">${esc(p.extra_block.label)}</span>` : '';
  const floors = `<span class="chip">${p.min_skeptical} skeptical, ${p.min_hostile} hostile min.</span>`;
  const brief = p.sees_brief ? '<span class="chip" title="Arrives informed: reads the recon brief">reads the brief</span>' : '<span class="chip" title="Arrives cold, like a real visitor">arrives cold</span>';
  const list = p.seats ? `<details class="seats"><summary>${p.seats.length} seats</summary><ol>${p.seats.map(s => `<li>${esc(s)}</li>`).join('')}</ol></details>`
             : (p.spread ? `<details class="seats"><summary>spread rules</summary><ul>${p.spread.map(s => `<li>${esc(s)}</li>`).join('')}</ul></details>` : '');
  const real = p.can_cast_real_people ? `<label class="real" data-real="${esc(p.id)}"><input type="checkbox" data-real="${esc(p.id)}">
     <span><b>Profile real people from public sources.</b> Off by default: personas are fictional. When on, named professionals are researched on the web and simulated, with sources, for internal use only.</span></label>` : '';
  return `<article class="pcard" data-id="${esc(p.id)}" style="--a:${esc(p.accent)}">
    <div class="ptop">
      <div class="ptitle"><h3><span class="swatch"></span>${esc(p.label)}</h3><p class="q">${esc(p.question)}</p></div>
      <div class="stepper"><button type="button" data-d="-1" aria-label="Fewer">&minus;</button>
        <input type="number" min="0" max="30" value="0" data-id="${esc(p.id)}" aria-label="${esc(p.label)} headcount">
        <button type="button" data-d="1" aria-label="More">+</button></div>
    </div>
    <div class="meta">${blk}${brief}${floors}<span class="chip">default ${p.size}</span></div>
    ${list}${real}
  </article>`;
}

function setN(id, v){
  v = Math.max(0, Math.min(30, parseInt(v || 0, 10) || 0));
  if (v) state.n[id] = v; else delete state.n[id];
}
function sync(){
  document.querySelectorAll('.pcard').forEach(c => {
    const id = c.dataset.id, v = state.n[id] || 0;
    c.classList.toggle('on', v > 0);
    c.querySelector('input[type=number]').value = v;
    const r = c.querySelector('input[data-real]');
    if (r){ r.checked = !!state.real[id]; c.querySelector('label.real').classList.toggle('on', !!state.real[id]); }
  });
  const order = panels.map(p => p.id).filter(id => state.n[id]);
  const total = order.reduce((a, id) => a + state.n[id], 0);
  $('#total').textContent = total;
  $('#compbar').innerHTML = order.map(id => `<i style="flex:${state.n[id]};background:${esc(byId[id].accent)}"></i>`).join('');
  $('#picked').innerHTML = order.map(id => `<li><span class="swatch" style="--a:${esc(byId[id].accent)}"></span>${esc(byId[id].label)}
    ${state.real[id] ? '<span class="r">real</span>' : ''}<span class="n">${state.n[id]}</span></li>`).join('');
  $('#emptyhint').hidden = total > 0;
  $('#run').disabled = total === 0;
  $('#realwarn').hidden = !order.some(id => state.real[id]);
  const waves = Math.ceil(total / 8);
  $('#eta').textContent = total ? `${waves} wave${waves > 1 ? 's' : ''} of up to 8 agents, roughly ${waves * 4}-${waves * 8} min` : '';
  document.querySelectorAll('.preset').forEach(b => {
    const p = lib.presets.find(x => x.id === b.dataset.id);
    const same = Object.keys(p.panels).length === order.length && order.every(id => p.panels[id] === state.n[id]);
    b.classList.toggle('on', total > 0 && same);
  });
  try { localStorage.setItem(KEY, JSON.stringify({n: state.n, real: state.real, lang: $('#lang').value, notes: $('#notes').value})); } catch (e) {}
}
function applyPreset(spec){ state.n = {}; Object.entries(spec).forEach(([id, v]) => setN(id, v)); sync(); }

document.addEventListener('click', ev => {
  const pre = ev.target.closest('.preset');
  if (pre){ applyPreset(lib.presets.find(x => x.id === pre.dataset.id).panels); return; }
  const st = ev.target.closest('.stepper button');
  if (st){ const inp = st.parentNode.querySelector('input'); setN(inp.dataset.id, (state.n[inp.dataset.id] || 0) + parseInt(st.dataset.d, 10)); sync(); }
});
document.addEventListener('input', ev => {
  if (ev.target.matches('.stepper input')){ setN(ev.target.dataset.id, ev.target.value); sync(); }
  if (ev.target.matches('#notes')) sync();
});
document.addEventListener('change', ev => {
  if (ev.target.matches('input[data-real]')){
    const id = ev.target.dataset.real;
    if (ev.target.checked) state.real[id] = true; else delete state.real[id];
    if (ev.target.checked && !state.n[id]) setN(id, byId[id].size);
    sync();
  }
  if (ev.target.matches('#lang')) sync();
});
$('#clear').addEventListener('click', () => { state.n = {}; state.real = {}; sync(); });

function config(){
  const order = panels.map(p => p.id).filter(id => state.n[id]);
  const base = Object.assign({}, cfg); delete base.preset; delete base.preselect;
  return Object.assign(base, {
    panels: Object.fromEntries(order.map(id => [id, state.n[id]])),
    panel_order: order,
    real_people: order.filter(id => state.real[id]),
    lang: $('#lang').value, notes: $('#notes').value.trim(),
    mode: (lib.presets.find(p => { const k = Object.keys(p.panels); return k.length === order.length && order.every(id => p.panels[id] === state.n[id]); }) || {id: 'custom'}).id,
    picked_at: new Date().toISOString()
  });
}
function finish(body, text){
  $('#donetext').textContent = text;
  $('#donecfg').textContent = JSON.stringify({panels: body.panels, real_people: body.real_people, lang: body.lang}, null, 2);
  $('#done').hidden = false;
}
$('#run').addEventListener('click', async () => {
  const body = config(), btn = $('#run');
  if (STATIC){
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([JSON.stringify(body, null, 2)], {type: 'application/json'}));
    a.download = 'run.config.json'; a.click();
    finish(body, 'run.config.json was downloaded. Move it into the run folder, then go back to Claude Code.');
    return;
  }
  btn.disabled = true; btn.textContent = 'Saving';
  try {
    const r = await fetch('/run', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
    if (!r.ok) throw new Error('HTTP ' + r.status);
    finish(body, 'Saved to run.config.json. Go back to Claude Code: the swarm starts from this cast.');
  } catch (err) {
    btn.disabled = false; btn.textContent = 'Run the swarm';
    alert('Could not save the cast: ' + err.message);
  }
});
if (STATIC) $('#finehint').textContent = 'Downloads run.config.json. Nothing is sent anywhere.';

try {
  const saved = JSON.parse(localStorage.getItem(KEY) || 'null');
  if (saved){ state.n = saved.n || {}; state.real = saved.real || {}; $('#lang').value = saved.lang || 'en'; $('#notes').value = saved.notes || ''; }
} catch (e) {}
if (!Object.keys(state.n).length && cfg.preselect) state.n = Object.assign({}, cfg.preselect);
if (!Object.keys(state.n).length && cfg.preset){ const p = lib.presets.find(x => x.id === cfg.preset); if (p) state.n = Object.assign({}, p.panels); }
if (cfg.lang && !(function(){ try { return localStorage.getItem(KEY); } catch (e) { return null; } })()) $('#lang').value = cfg.lang;
if (cfg.notes && !$('#notes').value) $('#notes').value = cfg.notes;
sync();
})();
"""


class Handler(BaseHTTPRequestHandler):
    page = b""
    outdir = ""
    lib = None
    on_saved = None

    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?")[0] not in ("/", "/index.html"):
            self._send(404, b"not found", "text/plain")
            return
        self._send(200, self.page, "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/run":
            self._send(404, b"not found", "text/plain")
            return
        n = int(self.headers.get("Content-Length", 0) or 0)
        if n <= 0 or n > 1_000_000:
            self._send(400, b'{"ok":false,"error":"bad length"}', "application/json")
            return
        try:
            cfg = json.loads(self.rfile.read(n).decode("utf-8"))
            if not isinstance(cfg, dict) or not isinstance(cfg.get("panels"), dict) or not cfg["panels"]:
                raise ValueError("panels missing")
            build_config({}, cfg["panels"], self.lib, cfg.get("real_people") or [])
        except (ValueError, TypeError) as exc:
            body = json.dumps({"ok": False, "error": str(exc)}).encode("utf-8")
            self._send(400, body, "application/json")
            return
        path = os.path.join(self.outdir, "run.config.json")
        C.write_json(path, cfg)
        self._send(200, b'{"ok":true}', "application/json")
        print("saved %s" % path)
        print("cast: %s" % json.dumps(cfg.get("panels", {}), ensure_ascii=False))
        if cfg.get("real_people"):
            print("real-people research: %s" % ", ".join(cfg["real_people"]))
        sys.stdout.flush()
        if self.on_saved:
            threading.Timer(0.5, self.on_saved).start()


def parse_panels(spec):
    out = {}
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError("use id=count, e.g. general=4,capital=3 (got %r)" % part)
        k, v = part.split("=", 1)
        out[k.strip()] = int(v)
    return out


def main(argv=None):
    C.utf8_stdout()
    ap = argparse.ArgumentParser(description="Compose the focus-swarm cast and write run.config.json.")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--target", required=True, help="URL, repository path or document path")
    ap.add_argument("--targettype", default="live", choices=["live", "repo", "document"])
    ap.add_argument("--product", default="")
    ap.add_argument("--lang", default="en", help="default report language code")
    ap.add_argument("--port", type=int, default=8137, help="local port (0 picks a free one)")
    ap.add_argument("--open", action="store_true", help="open the picker in the default browser")
    ap.add_argument("--preset", default="", help="preset id to preselect (or to write with --write)")
    ap.add_argument("--panels", default="", help="id=count list, e.g. general=4,capital=3: preselected on the page, or written with --write")
    ap.add_argument("--real-people", default="", help="comma-separated panel ids to profile from public sources")
    ap.add_argument("--notes", default="")
    ap.add_argument("--write", action="store_true", help="write run.config.json now, no page")
    ap.add_argument("--static", action="store_true", help="write picker.html for offline use instead of serving")
    ap.add_argument("--list", action="store_true", help="print panels and presets, then exit")
    ns = ap.parse_args(argv)

    lib = C.load_library()
    if ns.list:
        for p in lib["panels"]:
            print("%-14s %-28s size %-3d %s" % (p["id"], p["label"], p["size"],
                                               "real-people opt-in" if p.get("can_cast_real_people") else ""))
        print()
        for p in lib["presets"]:
            print("%-12s %-16s %s" % (p["id"], p["label"], ", ".join("%s=%d" % kv for kv in p["panels"].items())))
        return 0

    outdir = os.path.abspath(ns.outdir)
    os.makedirs(outdir, exist_ok=True)
    base = {
        "target": ns.target,
        "target_type": ns.targettype,
        "product": ns.product or ns.target,
        "date": date.today().isoformat(),
        "lang": ns.lang,
    }
    real = [x.strip() for x in ns.real_people.split(",") if x.strip()]

    if ns.write:
        if ns.panels:
            panels, mode = parse_panels(ns.panels), "custom"
        else:
            preset = next((p for p in lib["presets"] if p["id"] == (ns.preset or "lite")), None)
            if not preset:
                sys.exit("unknown preset %r (see --list)" % ns.preset)
            panels, mode = preset["panels"], preset["id"]
        try:
            cfg = build_config(base, panels, lib, real, ns.lang, ns.notes, mode)
        except ValueError as exc:
            sys.exit(str(exc))
        path = os.path.join(outdir, "run.config.json")
        C.write_json(path, cfg)
        print("saved %s" % path)
        print("cast: %s (%d agents)" % (json.dumps(cfg["panels"]), sum(cfg["panels"].values())))
        return 0

    if ns.preset:
        base["preset"] = ns.preset
    if ns.panels:
        base["preselect"] = parse_panels(ns.panels)
    if ns.notes:
        base["notes"] = ns.notes
    if ns.static:
        path = os.path.join(outdir, "picker.html")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render(base, lib, static=True))
        print("wrote %s (open it from disk; Run downloads run.config.json)" % path)
        return 0

    Handler.page = render(base, lib).encode("utf-8")
    Handler.outdir = outdir
    Handler.lib = lib
    srv = ThreadingHTTPServer((BIND_HOST, ns.port), Handler)
    Handler.on_saved = srv.shutdown
    url = local_url(srv.server_address[1])
    print("cast picker: %s  (waiting for the cast)" % url)
    sys.stdout.flush()
    if ns.open:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    print("picker closed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
