#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描 games/,按 families.json 分组,生成自包含合集首页 index.html"""
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
        "n": f["n"], "name": f["name"], "slug": f["slug"], "desc": f["desc"],
        "start": f["start"], "end": f["end"], "games": games,
    })

total_done = sum(1 for fam in data for g in fam["games"] if g[1])
payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")

TEMPLATE = u"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>微游戏合集 · 1000 IN 1</title>
<style>
:root{--bg:#0f1220;--panel:#171b2e;--line:#262c47;--txt:#e8ebf7;--dim:#9aa3c7;--acc:#7c5cff;--acc2:#38e1b0}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font-family:system-ui,"Segoe UI",Roboto,"Microsoft YaHei",sans-serif}
.top{position:sticky;top:0;z-index:5;background:rgba(15,18,32,.94);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);padding:14px 18px}
.top h1{margin:0;font-size:20px}
.top h1 span{color:var(--acc2);font-size:13px;margin-left:8px;font-weight:400}
.bar{display:flex;gap:12px;align-items:center;margin-top:10px;flex-wrap:wrap}
#q{flex:1;min-width:220px;background:var(--panel);border:1px solid var(--line);color:var(--txt);border-radius:10px;padding:9px 12px;font-size:14px;outline:none}
#q:focus{border-color:var(--acc)}
#stat{color:var(--dim);font-size:13px;white-space:nowrap}
.progress{height:6px;background:var(--panel);border-radius:4px;margin-top:10px;overflow:hidden}
#pbar{height:100%;width:0;background:linear-gradient(90deg,var(--acc),var(--acc2))}
#ptext{font-size:12px;color:var(--dim);margin-top:5px;display:block}
main{max-width:1200px;margin:0 auto;padding:8px 18px 40px}
section{margin:26px 0}
section h2{font-size:17px;margin:0 0 4px}
section small{color:var(--dim);font-weight:400;font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-top:10px}
.card{position:relative;text-align:left;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 12px;color:var(--txt);cursor:pointer;transition:transform .12s,border-color .12s;font-family:inherit}
.card:hover{border-color:var(--acc);transform:translateY(-2px)}
.card b{color:var(--acc2);font-size:12px;display:block;letter-spacing:.5px}
.card i{font-style:normal;font-size:13px;line-height:1.35;display:block;margin-top:3px}
.card.done::after{content:"✓";position:absolute;top:8px;right:10px;color:var(--acc2);font-weight:700}
.card.empty{opacity:.4;cursor:default}
#modal{position:fixed;inset:0;background:rgba(5,7,15,.82);display:flex;align-items:center;justify-content:center;z-index:9;padding:18px}
#modal[hidden]{display:none}
.mbox{width:min(960px,100%);height:min(720px,92vh);background:var(--panel);border:1px solid var(--line);border-radius:14px;display:flex;flex-direction:column;overflow:hidden}
.mhead{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border-bottom:1px solid var(--line);gap:10px}
.mhead span{font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mhead div{display:flex;gap:8px;flex-shrink:0}
iframe{flex:1;border:0;background:#0f1220;width:100%}
button{background:var(--acc);border:0;color:#fff;border-radius:8px;padding:7px 12px;font-size:13px;cursor:pointer}
button.ghost{background:transparent;border:1px solid var(--line);color:var(--dim)}
</style>
</head>
<body>
<header class="top">
  <h1>🎮 微游戏合集 <span>1000 IN 1 · 每款一个独立 HTML 文件 · 离线可玩</span></h1>
  <div class="bar"><input id="q" placeholder="搜索:游戏名 / 系列名 / 编号,如 2048、贪吃蛇、385"><span id="stat"></span></div>
  <div class="progress"><div id="pbar"></div></div><span id="ptext"></span>
</header>
<main id="root"></main>
<div id="modal" hidden>
  <div class="mbox">
    <div class="mhead"><span id="mtitle"></span><div><button id="mnew" class="ghost">新窗口打开</button><button id="mclose">关闭 ✕</button></div></div>
    <iframe id="mframe" title="游戏窗口"></iframe>
  </div>
</div>
<script>
var DATA = __PAYLOAD__;
var played = {};
try { played = JSON.parse(localStorage.getItem('mg-played-v1') || '{}') || {}; } catch (e) { played = {}; }
function pad3(n){ return ('00' + n).slice(-3); }
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
var root = document.getElementById('root');
var buf = '';
DATA.forEach(function (f) {
  buf += '<section id="fam-' + f.slug + '"><h2>' + f.n + ' · ' + esc(f.name) +
         ' <small>' + pad3(f.start) + '\\u2013' + pad3(f.end) + ' · ' + esc(f.desc) + '</small></h2><div class="grid">';
  f.games.forEach(function (g) {
    var id = g[0], t = g[1] || '(未交付)';
    var cls = 'card' + (g[1] ? '' : ' empty') + (played[id] ? ' done' : '');
    var key = (id + ' ' + f.name + ' ' + f.slug + ' ' + (g[1] || '')).toLowerCase().replace(/"/g, '');
    buf += '<button class="' + cls + '" data-id="' + id + '" data-title="' + esc(t) + '" data-key="' + esc(key) + '"><b>' + id + '</b><i>' + esc(t) + '</i></button>';
  });
  buf += '</div></section>';
});
root.innerHTML = buf;

var q = document.getElementById('q'), stat = document.getElementById('stat');
stat.textContent = '1000 款 · 50 个系列 · 点击卡片即玩';
q.addEventListener('input', function () {
  var s = q.value.trim().toLowerCase(), shown = 0;
  var secs = document.querySelectorAll('section');
  for (var i = 0; i < secs.length; i++) {
    var sec = secs[i], vis = 0;
    var cards = sec.querySelectorAll('.card');
    for (var j = 0; j < cards.length; j++) {
      var c = cards[j];
      var show = !s || (c.getAttribute('data-key') || '').indexOf(s) !== -1;
      c.style.display = show ? '' : 'none';
      if (show) vis++;
    }
    sec.style.display = vis ? '' : 'none';
    shown += vis;
  }
  stat.textContent = '匹配 ' + shown + ' / 1000';
});

var modal = document.getElementById('modal'), mframe = document.getElementById('mframe'),
    mtitle = document.getElementById('mtitle'), currentFile = '';
function save(){ try { localStorage.setItem('mg-played-v1', JSON.stringify(played)); } catch (e) {} }
function updateProgress(){
  var n = 0; for (var k in played) if (played[k]) n++;
  document.getElementById('pbar').style.width = (n / 10) + '%';
  document.getElementById('ptext').textContent = '已试玩 ' + n + ' / 1000(' + Math.round(n / 10) + '%)· 打开过的游戏自动标记 ✓';
}
root.addEventListener('click', function (e) {
  var c = e.target.closest ? e.target.closest('.card') : null;
  if (!c || c.classList.contains('empty')) return;
  var id = c.getAttribute('data-id');
  currentFile = 'games/game-' + id + '.html';
  mtitle.textContent = id + ' · ' + c.getAttribute('data-title');
  mframe.src = currentFile;
  modal.hidden = false;
  if (!played[id]) { played[id] = 1; save(); c.classList.add('done'); }
  updateProgress();
});
function closeModal(){ modal.hidden = true; mframe.src = 'about:blank'; }
document.getElementById('mclose').onclick = closeModal;
document.getElementById('mnew').onclick = function () { if (currentFile) window.open(currentFile, '_blank'); };
modal.addEventListener('click', function (e) { if (e.target === modal) closeModal(); });
document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !modal.hidden) closeModal(); });
updateProgress();
</script>
</body>
</html>
"""

out = TEMPLATE.replace("__PAYLOAD__", payload)
io.open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(out)
print("index.html 生成完毕:共 %d 个条目,已命名 %d 款" % (len(fams) * 20, total_done))
