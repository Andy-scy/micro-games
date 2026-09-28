#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""依据 families.json 生成 50 份智能体专属目标存档 goals/goal-NN-slug.md"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fams = json.load(io.open(os.path.join(ROOT, "families.json"), encoding="utf-8"))
out_dir = os.path.join(ROOT, "goals")
os.makedirs(out_dir, exist_ok=True)


def pad(n):
    return "%03d" % n


for f in fams:
    goal = (
        u"独立交付 games/ 下 game-%s.html 至 game-%s.html 共 20 款「%s」系列微游戏:"
        u"全部单文件、零外部依赖、中文界面、完整可玩、JS 语法零错误,20 款机制两两互异;"
        u"交付前运行 python tools/check.py %d %d 自检并修复至全绿;"
        u"最终报告 20 行「编号 中文名 — 一句话玩法」清单。"
        % (pad(f["start"]), pad(f["end"]), f["name"], f["start"], f["end"])
    )
    body = (
        u"# 智能体 %02d · 专属 GOAL\n\n"
        u"- 系列:%s(%s)— %s\n"
        u"- 编号区间:game-%s.html – game-%s.html\n"
        u"- 规范:见 SPEC.md\n\n"
        u"## GOAL(唯一目标)\n\n%s\n"
        % (f["n"], f["name"], f["slug"], f["desc"], pad(f["start"]), pad(f["end"]), goal)
    )
    path = os.path.join(out_dir, "goal-%02d-%s.md" % (f["n"], f["slug"]))
    io.open(path, "w", encoding="utf-8").write(body)

print("已生成 %d 份智能体目标 -> goals/" % len(fams))
