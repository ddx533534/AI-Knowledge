---
{
  "id": "webassembly-linear-memory-isolation",
  "title": "WebAssembly 线性内存隔离",
  "type": "concept",
  "status": "verified",
  "last_verified": "2026-10-10",
  "sources": [
    {
      "document_id": "ed977e613aad6e2e4ba89871142fa79b616515629b33c33f87a100599c8538a7",
      "locator": "§6：安全优势，区分语言、模块与宿主；§9 来源 S12–S13"
    }
  ],
  "relationships": [],
  "aliases": [
    "Wasm线性内存安全",
    "Wasm沙箱边界"
  ],
  "tags": [
    "WebAssembly",
    "安全",
    "FFI"
  ],
  "schema_version": 2,
  "created": "2026-10-11T22:22:48.180580+08:00",
  "updated": "2026-10-11T22:22:48.194584+08:00"
}
---
# WebAssembly 线性内存隔离

<!-- AI:BEGIN -->
## 结论

Wasm 以验证和线性内存边界检查等机制约束模块执行；隔离不等于对象级内存安全，也不自动证明比 JS 引擎更安全。

## 关键发现

- 超出线性内存的访问会触发 trap，外部能力由宿主导入接口提供。
- 线性内存区域内部仍可能发生对象覆盖与数据破坏。
- Rust业务代码、Wasm模块隔离、解释器和FFI实现是不同安全层次。

## 证据与分析

归档文档 §6 基于 WebAssembly 官方安全与 API 说明。隔离机制的成立依赖执行器和宿主正确实现；现有资料没有 Hermes 对照安全评估。

- [S1] [[05-Research/algorithms-12281f86b27d/recce-runtime-selection--ed977e613aad/原文-recce-runtime-selection.md|原文证据]]；定位：§6：安全优势，区分语言、模块与宿主；§9 来源 S12–S13

## 建议

- 评估安全时明确威胁模型，单独检查宿主接口的偏移、边界与生命周期。

<!-- AI:END -->

## 人工笔记

