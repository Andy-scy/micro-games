#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描 games/,按 families.json 分组,生成街机厅风格合集首页 index.html
系列侧栏过滤 + 密集列表行;点击行弹窗即玩(iframe 加载 games/ 单文件);localStorage 记录试玩进度。"""
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMES = os.path.join(ROOT, "games")
fams = json.load(io.open(os.path.join(ROOT, "families.json"), encoding="utf-8"))


def pad(n):
    return "%03d" % n


def clean(s):
    return re.sub(r"[<>\"'&]", "", s).strip()


data = []
for f in fams:
    games = []
    for n in range(f["start"], f["end"] + 1):
        title = ""
        fp = os.path.join(GAMES, "game-%s.html" % pad(n))
        if os.path.exists(fp):
            html = io.open(fp, "r", encoding="utf-8", errors="replace").read()
            m = re.search(r"<title>([^<]*)</title>", html, re.I)
            if m:
                title = clean(m.group(1))
        games.append([pad(n), title])
    data.append({
        "name": f["name"], "slug": f["slug"], "desc": f["desc"],
        "start": f["start"], "end": f["end"], "games": games,
    })

total_named = sum(1 for fam in data for g in fam["games"] if g[1])
payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

TEMPLATE = u"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>游戏厅 · 1000 合 1</title>
<style>
:root{--bg:#07090d;--bg2:#0b0e14;--panel:#10141c;--line:#1d2330;--txt:#d7dde8;--dim:#6d7889;
--amber:#ffb000;--red:#ff3355;--green:#3dff8f;
--mono:ui-monospace,"Cascadia Code","SF Mono",Consolas,"Courier New",monospace}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--txt);font-family:var(--mono);display:flex;flex-direction:column;overflow:hidden}
::selection{background:var(--amber);color:#000}
#crt{position:fixed;inset:0;pointer-events:none;z-index:40;
background:repeating-linear-gradient(0deg,rgba(255,255,255,.028) 0 1px,transparent 1px 3px),radial-gradient(ellipse at 50% 42%,transparent 58%,rgba(0,0,0,.42))}
.mast{display:flex;align-items:center;gap:22px;padding:14px 20px 12px;border-bottom:2px solid var(--amber);background:var(--bg2);flex-wrap:wrap}
.brand h1{margin:0;font-size:27px;line-height:1;color:var(--amber);letter-spacing:2px;text-shadow:3px 3px 0 #000,1px 0 0 var(--red),-1px 0 0 var(--green);white-space:nowrap}
.brand .sub{margin-top:5px;font-size:10px;letter-spacing:4px;color:var(--dim)}
.searchline{flex:1;min-width:220px;display:flex;align-items:center;gap:8px;background:#000;border:1px solid var(--line);padding:8px 12px}
.searchline .gt{color:var(--amber);font-weight:700}
.searchline input{flex:1;background:transparent;border:0;outline:0;color:var(--txt);font:13px/1.4 var(--mono)}
.searchline input::placeholder{color:var(--dim)}
.leds{display:flex;gap:8px}
.led{background:#000;border:1px solid var(--line);border-radius:2px;padding:6px 10px;font-size:10px;color:var(--dim);letter-spacing:1px;box-shadow:inset 0 0 8px rgba(0,0,0,.8)}
.led b{color:var(--amber);font-weight:400;margin-left:4px}
#wrap{flex:1;display:flex;min-height:0}
#side{width:216px;flex-shrink:0;overflow-y:auto;border-right:1px solid var(--line);padding:8px 0}
#side .cap{padding:8px 14px 4px;font-size:10px;letter-spacing:3px;color:var(--dim)}
.side-item{display:flex;align-items:center;gap:8px;padding:5px 12px 5px 11px;cursor:pointer;color:var(--dim);font-size:12px;border-left:3px solid transparent;white-space:nowrap}
.side-item b{color:var(--amber);font-weight:400;min-width:20px}
.side-item:hover{color:var(--txt);background:var(--panel)}
.side-item.on{color:#000;background:var(--amber);border-left-color:#fff;font-weight:700}
.side-item.on b{color:#000}
#list{flex:1;overflow-y:auto;min-width:0}
.sep{position:sticky;top:0;z-index:2;padding:12px 16px 7px;font-size:11px;letter-spacing:2px;color:var(--amber);background:var(--bg2);border-bottom:1px solid var(--line)}
.sep small{color:var(--dim);letter-spacing:0;margin-left:10px}
.row{display:flex;align-items:center;gap:12px;padding:6px 16px;cursor:pointer;border-bottom:1px solid rgba(255,255,255,.035);min-width:0}
.row .no{color:var(--amber);width:36px;flex-shrink:0;font-size:12px}
.row .nm{flex:1;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.row .tag{color:var(--dim);font-size:10px;flex-shrink:0}
.row:hover{background:var(--amber);box-shadow:inset 3px 0 0 #fff}
.row:hover .no,.row:hover .nm,.row:hover .tag{color:#000;font-weight:700}
.row:hover .nm::before{content:"▶ "}
.row.done .tag::after{content:" ✓";color:var(--green)}
.row:hover.done .tag::after{color:#000}
.statusbar{display:flex;align-items:center;gap:14px;padding:6px 16px;border-top:1px solid var(--line);font-size:10px;color:var(--dim);letter-spacing:1px;background:var(--bg2)}
.statusbar .green{color:var(--green)}
@keyframes blink{50%{opacity:0}}
.blink{animation:blink 1.1s steps(1) infinite}
@media (prefers-reduced-motion:reduce){.blink{animation:none}}
@media (max-width:760px){#side{display:none}.leds{display:none}.mast{gap:12px}}
/* 弹窗即玩 */
#modal{position:fixed;inset:0;background:rgba(3,4,7,.92);z-index:60;display:flex;align-items:stretch;justify-content:center;padding:16px}
#modal[hidden]{display:none}
.mbox{width:min(1020px,100%);display:flex;flex-direction:column;background:var(--bg2);border:1px solid var(--amber);box-shadow:8px 8px 0 #000}
.mhead{display:flex;align-items:center;gap:12px;padding:8px 12px;border-bottom:1px solid var(--line)}
.np{font-size:9px;letter-spacing:3px;color:var(--red)}
#mtitle{font-size:13px;color:var(--amber);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}
.mclose{background:transparent;border:1px solid var(--red);color:var(--red);border-radius:2px;padding:6px 12px;font:12px var(--mono);cursor:pointer;letter-spacing:1px}
.mclose:hover{background:var(--red);color:#000}
.mnew{background:transparent;border:1px solid var(--line);color:var(--dim);border-radius:2px;padding:6px 12px;font:12px var(--mono);cursor:pointer;letter-spacing:1px}
.mnew:hover{border-color:var(--amber);color:var(--amber)}
.pn{display:flex;gap:8px}
.key{background:transparent;border:1px solid var(--amber);color:var(--amber);border-radius:2px;padding:6px 12px;font:12px var(--mono);cursor:pointer;letter-spacing:1px}
.key:hover{background:var(--amber);color:#000}
#iframe{flex:1;border:0;background:#07090d;width:100%}
</style>
</head>
<body>
<div id="crt"></div>
<header class="mast">
  <div class="brand">
    <h1>1000合1</h1>
    <div class="sub">MICRO GAME ARCADE ▸ 游戏厅</div>
  </div>
  <div class="searchline"><span class="gt">&gt;_</span><input id="q" placeholder="搜索 游戏名 / 系列 / 编号…" autocomplete="off" spellcheck="false"></div>
  <div class="leds">
    <div class="led">ROMS<b>1000</b></div>
    <div class="led">SERIES<b>50</b></div>
    <div class="led">CREDIT<b>∞</b></div>
  </div>
</header>
<div id="wrap">
  <nav id="side"><div class="cap">SELECT SERIES</div></nav>
  <main id="list"></main>
</div>
<footer class="statusbar"><span id="stat">READY.</span><span class="green blink">▮</span><span id="prog"></span><span class="spacer"></span><span>点击行投币开机 · ESC 关闭机台</span></footer>
<div id="modal" hidden>
  <div class="mbox">
    <div class="mhead">
      <span class="np">NOW PLAYING</span><span id="mtitle"></span>
      <div class="pn"><button id="prev" class="key">◀</button><button id="next" class="key">▶</button><button id="mnew" class="mnew">新窗口</button><button id="mclose" class="mclose">ESC ✕</button></div>
    </div>
    <iframe id="iframe" title="游戏窗口"></iframe>
  </div>
</div>
<script id="GAMES-DATA" type="application/json">__PAYLOAD__</script>
<script>
var G = JSON.parse(document.getElementById('GAMES-DATA').textContent);
var FLAT = [], IDX = {};
G.forEach(function (fam) {
  fam.games.forEach(function (g) {
    IDX[g[0]] = FLAT.length;
    FLAT.push({ id: g[0], t: g[1], fam: fam.name, slug: fam.slug });
  });
});
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function famName(slug){ for (var i = 0; i < G.length; i++) if (G[i].slug === slug) return G[i].name; return ''; }
var played = {};
try { played = JSON.parse(localStorage.getItem('mg-played-v1') || '{}') || {}; } catch (e) { played = {}; }
var q = document.getElementById('q'), stat = document.getElementById('stat'), prog = document.getElementById('prog');
var side = document.getElementById('side'), listEl = document.getElementById('list');
var famSel = null;

var sbuf = '';
G.forEach(function (fam) {
  sbuf += '<div class="side-item" data-fam="' + fam.slug + '"><b>' + String(fam.start).padStart(3, '0') + '</b>' + esc(fam.name) + '</div>';
});
side.innerHTML += sbuf;

var buf = '';
G.forEach(function (fam) {
  buf += '<div class="sep" data-fam="' + fam.slug + '">' + String(fam.start).padStart(3, '0') + ' ▸ ' + esc(fam.name) + '<small>' + esc(fam.desc) + '</small></div>';
  fam.games.forEach(function (g) {
    var t = g[1] || '(未交付)';
    var key = (g[0] + ' ' + fam.name + ' ' + fam.slug + ' ' + (g[1] || '')).toLowerCase().replace(/"/g, '');
    buf += '<div class="row' + (played[g[0]] ? ' done' : '') + '" data-id="' + g[0] + '" data-fam="' + fam.slug + '" data-key="' + esc(key) + '"><span class="no">' + g[0] + '</span><span class="nm">' + esc(t) + '</span><span class="tag">' + esc(fam.name) + '</span></div>';
  });
});
listEl.innerHTML = buf;

function updateProgress() {
  var n = 0; for (var k in played) if (played[k]) n++;
  prog.textContent = '已通关机台 ' + n + ' / 1000';
}
function applyFilter() {
  var s = q.value.trim().toLowerCase();
  var shown = 0;
  var nodes = listEl.children;
  for (var i = 0; i < nodes.length; i++) {
    var el = nodes[i], isSep = el.classList.contains('sep');
    var famOk = !famSel || el.getAttribute('data-fam') === famSel;
    var keyOk = !s || (el.getAttribute('data-key') || el.textContent).toLowerCase().indexOf(s) !== -1;
    var show = isSep ? (famOk && keyOk && !s) : (famOk && keyOk);
    el.style.display = show ? '' : 'none';
    if (show && !isSep) shown++;
  }
  var label = 'SHOWING ' + shown + ' / 1000';
  if (famSel) label += ' · ' + famName(famSel);
  if (s) label += ' · 搜索“' + s + '”';
  stat.textContent = label;
  var sides = side.querySelectorAll('.side-item');
  for (var j = 0; j < sides.length; j++) {
    sides[j].classList.toggle('on', famSel && sides[j].getAttribute('data-fam') === famSel);
  }
}
side.addEventListener('click', function (e) {
  var it = e.target.closest ? e.target.closest('.side-item') : null;
  if (!it) return;
  var slug = it.getAttribute('data-fam');
  famSel = (famSel === slug) ? null : slug;
  if (famSel) q.value = '';
  applyFilter();
  var first = listEl.querySelector('.row:not([style*="none"])');
  if (first) listEl.scrollTop = first.offsetTop - 60;
});
q.addEventListener('input', function () {
  if (q.value.trim()) famSel = null;
  applyFilter();
});
applyFilter();
updateProgress();

var modal = document.getElementById('modal'), frame = document.getElementById('iframe'),
    mtitle = document.getElementById('mtitle'), cur = -1, curId = '';
frame.addEventListener('load', function () {
  try { frame.contentWindow.focus(); } catch (e) {}
});
function save(){ try { localStorage.setItem('mg-played-v1', JSON.stringify(played)); } catch (e) {} }
function openGame(i) {
  cur = i;
  var g = FLAT[i];
  curId = g.id;
  mtitle.textContent = g.id + ' ' + g.t + ' — ' + g.fam;
  frame.src = 'games/game-' + g.id + '.html';
  modal.hidden = false;
  if (!played[g.id]) {
    played[g.id] = 1; save();
    var row = listEl.querySelector('.row[data-id="' + g.id + '"]');
    if (row) row.classList.add('done');
    updateProgress();
  }
}
function closeModal() {
  modal.hidden = true;
  frame.src = 'about:blank';
  cur = -1; curId = '';
}
listEl.addEventListener('click', function (e) {
  var c = e.target.closest ? e.target.closest('.row') : null;
  if (!c) return;
  openGame(IDX[c.getAttribute('data-id')]);
});
document.getElementById('mclose').addEventListener('click', closeModal);
document.getElementById('mnew').addEventListener('click', function () {
  if (curId) window.open('games/game-' + curId + '.html', '_blank');
});
document.getElementById('prev').addEventListener('click', function () {
  if (cur >= 0) openGame((cur - 1 + FLAT.length) % FLAT.length);
});
document.getElementById('next').addEventListener('click', function () {
  if (cur >= 0) openGame((cur + 1) % FLAT.length);
});
modal.addEventListener('click', function (e) { if (e.target === modal) closeModal(); });
document.addEventListener('keydown', function (e) {
  if (modal.hidden) return;
  if (e.key === 'Escape') closeModal();
  if (e.key === 'ArrowLeft' && cur >= 0) openGame((cur - 1 + FLAT.length) % FLAT.length);
  if (e.key === 'ArrowRight' && cur >= 0) openGame((cur + 1) % FLAT.length);
});
</script>
</body>
</html>
"""

out = TEMPLATE.replace("__PAYLOAD__", payload)
io.open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(out)
print("index.html 生成完毕(街机厅 UI):共 %d 个条目,已命名 %d 款" % (len(fams) * 20, total_named))
