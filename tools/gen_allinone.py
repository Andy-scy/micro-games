#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 1000 款游戏全部内嵌进一个独立 HTML:all-in-one.html
目录点击卡片 -> 改写 location.hash -> 自动"跳转"进入游戏(内嵌 iframe 运行);
支持浏览器前进/后退、Esc 返回、上一款/下一款、搜索过滤。"""
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
total = 0
for f in fams:
    games = []
    for n in range(f["start"], f["end"] + 1):
        fp = os.path.join(GAMES, "game-%s.html" % pad(n))
        title = ""
        src = ""
        if os.path.exists(fp):
            html = io.open(fp, "r", encoding="utf-8", errors="replace").read()
            m = re.search(r"<title>([^<]*)</title>", html, re.I)
            if m:
                title = clean(m.group(1))
            src = html
            total += 1
        games.append([pad(n), title, src])
    data.append({
        "name": f["name"], "slug": f["slug"], "desc": f["desc"],
        "start": f["start"], "end": f["end"], "games": games,
    })

payload = json.dumps(data, ensure_ascii=False)
# 内嵌进 <script> 原文元素:转义所有 '<' 防止 '</script>' 提前闭合
payload = payload.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

TEMPLATE = u"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>单文件合集 · 1000 IN 1</title>
<style>
:root{--bg:#0f1220;--panel:#171b2e;--line:#262c47;--txt:#e8ebf7;--dim:#9aa3c7;--acc:#7c5cff;--acc2:#38e1b0}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--txt);font-family:system-ui,"Segoe UI",Roboto,"Microsoft YaHei",sans-serif;display:flex;flex-direction:column}
header{border-bottom:1px solid var(--line);padding:12px 18px;background:rgba(15,18,32,.96)}
header h1{margin:0;font-size:19px}
header h1 span{color:var(--acc2);font-size:12px;margin-left:8px;font-weight:400}
.bar{display:flex;gap:10px;align-items:center;margin-top:8px;flex-wrap:wrap}
#q{flex:1;min-width:200px;background:var(--panel);border:1px solid var(--line);color:var(--txt);border-radius:10px;padding:8px 12px;font-size:14px;outline:none}
#q:focus{border-color:var(--acc)}
#stat{color:var(--dim);font-size:12px;white-space:nowrap}
button{background:var(--acc);border:0;color:#fff;border-radius:8px;padding:7px 12px;font-size:13px;cursor:pointer;font-family:inherit}
button.ghost{background:transparent;border:1px solid var(--line);color:var(--dim)}
button.ghost:hover{color:var(--txt);border-color:var(--acc)}
#menu{flex:1;overflow-y:auto;max-width:1200px;width:100%;margin:0 auto;padding:6px 18px 40px}
section{margin:22px 0}
section h2{font-size:16px;margin:0 0 4px}
section small{color:var(--dim);font-weight:400;font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:9px;margin-top:9px}
.card{position:relative;text-align:left;background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:9px 11px;color:var(--txt);cursor:pointer;transition:transform .12s,border-color .12s}
.card:hover{border-color:var(--acc);transform:translateY(-2px)}
.card b{color:var(--acc2);font-size:12px;display:block;letter-spacing:.5px}
.card i{font-style:normal;font-size:13px;line-height:1.35;display:block;margin-top:2px}
#play{flex:1;display:flex;flex-direction:column;min-height:0}
#play[hidden]{display:none}
.pbar{display:flex;align-items:center;gap:10px;padding:8px 14px;border-bottom:1px solid var(--line);background:var(--panel)}
#ptitle{flex:1;font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--acc2)}
.pgroup{display:flex;gap:8px}
#gframe{flex:1;border:0;background:#0f1220;width:100%}
#menu.hidden{display:none}
</style>
</head>
<body>
<header>
  <h1>🎮 单文件合集 <span>1000 IN 1 · 全部游戏已内嵌 · 点击卡片自动进入</span></h1>
  <div class="bar"><input id="q" placeholder="搜索:游戏名 / 系列名 / 编号,如 2048、贪吃蛇、385"><span id="stat"></span></div>
</header>
<main id="menu"></main>
<section id="play" hidden>
  <div class="pbar"><button id="back">⌂ 返回目录</button><span id="ptitle"></span><div class="pgroup"><button id="prev" class="ghost">← 上一款</button><button id="next" class="ghost">下一款 →</button></div></div>
  <iframe id="gframe" title="游戏窗口"></iframe>
</section>
<script id="GAMES-DATA" type="application/json">__PAYLOAD__</script>
<script>
var G = JSON.parse(document.getElementById('GAMES-DATA').textContent);
var FLAT = [], IDX = {};
G.forEach(function (fam) {
  fam.games.forEach(function (g) {
    IDX[g[0]] = FLAT.length;
    FLAT.push({ id: g[0], t: g[1], src: g[2], fam: fam.name, slug: fam.slug });
  });
});
function pad3(n){ return ('00' + n).slice(-3); }
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

var menu = document.getElementById('menu');
var buf = '';
G.forEach(function (fam) {
  buf += '<section id="fam-' + fam.slug + '"><h2>' + esc(fam.name) + ' <small>' + pad3(fam.start) + '\\u2013' + pad3(fam.end) + ' · ' + esc(fam.desc) + '</small></h2><div class="grid">';
  fam.games.forEach(function (g) {
    var t = g[1] || '(未交付)';
    var key = (g[0] + ' ' + fam.name + ' ' + fam.slug + ' ' + (g[1] || '')).toLowerCase().replace(/"/g, '');
    buf += '<button class="card" data-id="' + g[0] + '" data-key="' + esc(key) + '"><b>' + g[0] + '</b><i>' + esc(t) + '</i></button>';
  });
  buf += '</div></section>';
});
menu.innerHTML = buf;

var q = document.getElementById('q'), stat = document.getElementById('stat');
stat.textContent = '1000 款 · 50 个系列 · 点击卡片自动进入 · Esc 返回';
q.addEventListener('input', function () {
  var s = q.value.trim().toLowerCase(), shown = 0;
  var secs = menu.querySelectorAll('section');
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

var play = document.getElementById('play'), gframe = document.getElementById('gframe'),
    ptitle = document.getElementById('ptitle'), cur = -1;
var ESC_RELAY = '<script>window.addEventListener("keydown",function(e){if(e.key==="Escape"){try{window.parent.postMessage("mg-esc","*")}catch(err){}}});<\\/script>';
function withRelay(src) {
  return src.replace(/<head(\s[^>]*)?>/i, function (m) { return m + ESC_RELAY; });
}
gframe.addEventListener('load', function () {
  try { gframe.contentWindow.focus(); } catch (e) {}
});
function showPlay(i) {
  cur = i;
  var g = FLAT[i];
  ptitle.textContent = g.id + ' · ' + g.t + '（' + g.fam + '）';
  gframe.srcdoc = withRelay(g.src);
  play.hidden = false;
  menu.classList.add('hidden');
  window.scrollTo(0, 0);
}
function showMenu() {
  cur = -1;
  play.hidden = true;
  menu.classList.remove('hidden');
  gframe.srcdoc = '';
}
function route() {
  var m = /^#g-(\\d{3})$/.exec(location.hash || '');
  if (m && IDX[m[1]] != null) showPlay(IDX[m[1]]);
  else showMenu();
}
window.addEventListener('hashchange', route);
menu.addEventListener('click', function (e) {
  var c = e.target.closest ? e.target.closest('.card') : null;
  if (!c) return;
  location.hash = 'g-' + c.getAttribute('data-id');
});
document.getElementById('back').addEventListener('click', function () {
  if (location.hash) location.hash = '';
  else route();
});
document.getElementById('prev').addEventListener('click', function () {
  if (cur >= 0) location.hash = 'g-' + FLAT[(cur - 1 + FLAT.length) % FLAT.length].id;
});
document.getElementById('next').addEventListener('click', function () {
  if (cur >= 0) location.hash = 'g-' + FLAT[(cur + 1) % FLAT.length].id;
});
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape' && cur >= 0) {
    if (location.hash) location.hash = '';
  }
});
window.addEventListener('message', function (e) {
  if (e.data === 'mg-esc' && cur >= 0 && location.hash) location.hash = '';
});
route();
</script>
</body>
</html>
"""

out = TEMPLATE.replace("__PAYLOAD__", payload)
io.open(os.path.join(ROOT, "all-in-one.html"), "w", encoding="utf-8").write(out)
print("all-in-one.html 生成完毕:内嵌 %d 款游戏,文件 %.1f MB" % (total, len(out.encode("utf-8")) / 1048576.0))
