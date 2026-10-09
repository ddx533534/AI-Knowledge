---
title: "Strands Box 平台保护差异"
type: learning-gap
status: open
created: "2026-10-09"
updated: "2026-10-09"
sources:
  - "vault:05-Research/Strands Box 设计与架构调研.md"
---

# Strands Box 平台保护差异

<!-- AI:BEGIN -->
## 为什么需要

理解 Box 架构时，需要区分设计目标与各平台真实保证，避免把后端存在误写成所有平台能力一致。

## 已有证据

[[05-Research/Strands Box 设计与架构调研|证据报告]] 的 S1 记录 macOS Apple silicon 本地预览声明，S13 记录 Linux 后端模块存在。[[02-Frameworks/Strands Box|入门笔记]] 保留了这一范围限制。

## 待解问题

- 两平台的直接文件、执行和网络限制有哪些实际差异？
- 哪些保证由对应测试固定，哪些只是设计文档声明？
- Linux 后端的运行条件与支持范围是什么？

## 建议核实路径

建议单独读取 containment 的平台实现及对应测试，结合用户使用的平台运行代表性验证。相关源码位置：`/Users/dudongxu/Desktop/codex/box/crates/containment/src/backend/`。本次未完成完整的平台比较，也未执行这些测试。

## 用户掌握程度

未知。这里记录的是资料核实缺口，不是对用户知识水平的判断。
<!-- AI:END -->

## 人工笔记

