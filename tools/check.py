#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微游戏流水线 · 结构与 JS 语法校验器(esprima)
用法: python tools/check.py [起始编号 结束编号]   缺省 = 1..1000
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMES = os.path.join(ROOT, "games")
TOTAL = 1000


def pad(n):
    return "%03d" % n


def check_one(n):
    fp = os.path.join(GAMES, "game-%s.html" % pad(n))
    probs = []
    if not os.path.exists(fp):
        return ["文件缺失"], fp
    with io.open(fp, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()
    if len(html) < 1200:
        probs.append("文件过小(%dB)" % len(html))
    if not re.search(r"<!DOCTYPE\s+html>", html, re.I):
        probs.append("缺少 <!DOCTYPE html>")
    if not re.search(r"</html\s*>", html, re.I):
        probs.append("缺少 </html>")
    if not re.search(r"<html[^>]*lang=[\"']zh", html, re.I):
        probs.append('<html> 缺少 lang="zh-CN"')
    m = re.search(r"<title>([^<]*)</title>", html, re.I)
    if not m or not m.group(1).strip():
        probs.append("缺少非空 <title>")
    if re.search(r"(src|href)\s*=\s*[\"']https?:", html, re.I):
        probs.append("引用外部网络资源")
    if re.search(r"\b(TODO|FIXME)\b|待实现|尚未实现", html):
        probs.append("含未完成标记")
    if re.search(r"\b(alert|confirm|prompt)\s*\(|document\.write\s*\(", html):
        probs.append("使用了 alert/confirm/prompt/document.write")
    scripts = re.findall(r"<script\b([^>]*)>([\s\S]*?)</script>", html, re.I)
    if not scripts:
        probs.append("没有 <script>")
    parts = []
    for attrs, body in scripts:
        if re.search(r"\bsrc\s*=", attrs, re.I):
            probs.append("<script> 带外部 src")
            continue
        parts.append(body + "\n;\n")
    js = "".join(parts)
    if js.strip():
        import esprima
        try:
            esprima.parseScript(js, tolerant=False)
        except Exception as e:  # SyntaxError 等
            msg = re.sub(r"\s+", " ", str(e))[:220]
            probs.append("JS 语法错误: " + msg)
    return probs, fp


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end = int(sys.argv[2]) if len(sys.argv) > 2 else TOTAL
    start = max(1, start)
    end = min(TOTAL, end)
    ok = 0
    missing = 0
    failures = []
    for n in range(start, end + 1):
        probs, fp = check_one(n)
        if probs:
            if probs[0] == "文件缺失":
                missing += 1
            failures.append((pad(n), probs))
        else:
            ok += 1
    print("校验区间 %s-%s:通过 %d,失败 %d(缺失 %d)" % (pad(start), pad(end), ok, len(failures), missing))
    if failures:
        print("--- 失败清单 ---")
        for ident, probs in failures:
            print(ident + ": " + "; ".join(probs))
        sys.exit(1)


if __name__ == "__main__":
    main()
