---
{
  "id": "os-sandbox",
  "title": "操作系统沙箱",
  "type": "concept",
  "status": "unverified",
  "last_verified": null,
  "sources": [
    {
      "document_id": "add72e7c471d2bd1e95bad1dadf025d52884f037c1c7c9e4e2249d9f5f6e3f25",
      "locator": "S1：项目定位与预览平台；S3：直接访问与代办请求分工；原始 README 第 26–49 行与 policy.md 第 23–44 行的归档摘录"
    }
  ],
  "relationships": [],
  "aliases": [],
  "tags": [
    "安全",
    "历史资料"
  ],
  "schema_version": 2,
  "created": "2026-10-10T10:25:43+08:00",
  "updated": "2026-10-10T10:25:43+08:00"
}
---
# 操作系统沙箱

<!-- AI:BEGIN -->
## 结论

在已归档的 Strands Box 设计中，操作系统沙箱负责限制程序的直接文件访问和执行范围。本文解释该历史资料中的机制，未重新核实平台实现。

## 关键发现

- 直接访问范围由 box.toml 声明并在启动前固定。
- 直接访问与通过受信任组件请求代办操作走不同的检查路径。

## 证据与分析

依据历史报告 S1、S3 的原文摘录。报告记录 Box 0.1.0，来源 commit 为 331d563e8599b4359f9578ea377fc4f2d0dccce7，原核实日期为 2026-10-09。本次只读取归档材料，不声明重新验证源码或运行效果，也不把两条路径的机制泛化为所有沙箱。

- [S1] [[05-Research/AI-Knowledge-7daee9459306/Strands-Box-设计与架构调研--add72e7c471d/原文-Strands-Box-设计与架构调研.md|原文证据]]；定位：S1：项目定位与预览平台；S3：直接访问与代办请求分工；原始 README 第 26–49 行与 policy.md 第 23–44 行的归档摘录

## 建议

- 使用前重新核实目标平台的实现、测试和实际限制。

<!-- AI:END -->

## 人工笔记

