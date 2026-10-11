---
{
  "id": "strands-box",
  "title": "Strands Box",
  "type": "tool",
  "status": "unverified",
  "last_verified": null,
  "sources": [
    {
      "document_id": "add72e7c471d2bd1e95bad1dadf025d52884f037c1c7c9e4e2249d9f5f6e3f25",
      "locator": "S1：项目定位与预览平台；S3：直接访问与代办请求分工；原始 README 第 26–49 行与 policy.md 第 23–44 行的归档摘录"
    }
  ],
  "relationships": [
    {
      "target": "os-sandbox",
      "type": "uses",
      "explanation": "归档 README 明确说明 Box 结合操作系统隔离与语义策略；policy.md 摘录说明宿主操作系统限制直接访问。此关系表达该历史设计的使用机制，当前实现未重新核实。",
      "sources": [
        {
          "document_id": "add72e7c471d2bd1e95bad1dadf025d52884f037c1c7c9e4e2249d9f5f6e3f25",
          "locator": "S1：项目定位与预览平台；S3：直接访问与代办请求分工；原始 README 第 26–49 行与 policy.md 第 23–44 行的归档摘录"
        }
      ]
    }
  ],
  "aliases": [
    "Box Agent 沙箱"
  ],
  "tags": [
    "安全",
    "历史资料"
  ],
  "schema_version": 2,
  "created": "2026-10-10T10:25:43+08:00",
  "updated": "2026-10-10T10:25:43+08:00"
}
---
# Strands Box

<!-- AI:BEGIN -->
## 结论

历史调研将 Strands Box 描述为结合操作系统隔离和策略检查的 Agent 沙箱。本文保留入门知识和来源，当前实现与平台保证未重新核实。

## 关键发现

- box.toml 限制程序直接可达范围，policy.dw 检查通过 Box 处理的请求。
- 原报告记载直接获准访问的文件不会逐次进入代办请求的策略历史。
- 历史 README 的预览声明为 macOS Apple silicon；不能据此推断其他平台保证。

## 证据与分析

依据归档报告 S1、S3。资料标注 Box 0.1.0 和 commit 331d563e8599b4359f9578ea377fc4f2d0dccce7，原核实日期为 2026-10-09；其中明确记载未运行 Box。本次重建保留证据，不把历史摘录的结构检查称为最新源码核实。

- [S1] [[05-Research/AI-Knowledge-7daee9459306/Strands-Box-设计与架构调研--add72e7c471d/原文-Strands-Box-设计与架构调研.md|原文证据]]；定位：S1：项目定位与预览平台；S3：直接访问与代办请求分工；原始 README 第 26–49 行与 policy.md 第 23–44 行的归档摘录
- [[01-Knowledge/os-sandbox|操作系统沙箱]]：使用；归档 README 明确说明 Box 结合操作系统隔离与语义策略；policy.md 摘录说明宿主操作系统限制直接访问。此关系表达该历史设计的使用机制，当前实现未重新核实。

## 建议

- 结合目标平台重新核实源码、直接权限与策略配置。
- 重新核实后再更新 status 和 last_verified，保留版本差异。

<!-- AI:END -->

## 人工笔记

