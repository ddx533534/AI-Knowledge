---
{
  "id": "recce-runtime-selection",
  "title": "Recce 运行时与语言选型",
  "type": "architecture",
  "status": "partial",
  "last_verified": "2026-10-10",
  "sources": [
    {
      "document_id": "ed977e613aad6e2e4ba89871142fa79b616515629b33c33f87a100599c8538a7",
      "locator": "§1–2：选型层次；§3.1：执行路径；§5.2–5.3：通信与证据；§6–8：安全和阶段边界"
    },
    {
      "document_id": "ed977e613aad6e2e4ba89871142fa79b616515629b33c33f87a100599c8538a7",
      "locator": "§3.1–3.2：Recce 原型执行路径与 AOT 产物"
    },
    {
      "document_id": "ed977e613aad6e2e4ba89871142fa79b616515629b33c33f87a100599c8538a7",
      "locator": "§5.2 与 §6：Wasm 内存访问和模块隔离"
    }
  ],
  "relationships": [
    {
      "target": "bytecode-precompilation-vs-native-aot",
      "type": "uses",
      "explanation": "Recce 原型将 Rust 预编译为 Wasm 字节码，再由 wasm3 解释执行，是字节码预编译路径。",
      "sources": [
        {
          "document_id": "ed977e613aad6e2e4ba89871142fa79b616515629b33c33f87a100599c8538a7",
          "locator": "§3.1–3.2：Recce 原型执行路径与 AOT 产物"
        }
      ]
    },
    {
      "target": "webassembly-linear-memory-isolation",
      "type": "uses",
      "explanation": "Recce 的 Wasm 动态模块路线采用 Wasm 隔离机制；Native 交互和 FFI 仍需检查边界。",
      "sources": [
        {
          "document_id": "ed977e613aad6e2e4ba89871142fa79b616515629b33c33f87a100599c8538a7",
          "locator": "§5.2 与 §6：Wasm 内存访问和模块隔离"
        }
      ]
    }
  ],
  "aliases": [
    "Recce与Hermes对比",
    "Rust wasm3动态化容器"
  ],
  "tags": [
    "Recce",
    "React Native",
    "Wasm",
    "Hermes"
  ],
  "schema_version": 2,
  "created": "2026-10-11T22:23:01.522539+08:00",
  "updated": "2026-10-11T22:23:01.537542+08:00"
}
---
# Recce 运行时与语言选型

<!-- AI:BEGIN -->
## 结论

Recce 以性能、安全和动态化目标选择 Rust/Wasm 路线，再综合无 JIT 条件下的解释效率与体积选择 wasm3；现有证据不支持其全面优于 Hermes 的普遍结论。

## 关键发现

- 性能和安全目标解释 Wasm 路线，包体与解释效率解释具体 wasm3 选择。
- 内部原型采用 Native 侧 Diff；2024 年公开 Recce UI 采用订阅更新、没有 Diff 和 VDOM。
- 整体页面性能收益不能全部归因于解释器，材料未给出 wasm3/Hermes 同条件对照。

## 证据与分析

直接证据来自归档文档对内部原型截图与公开文章的分层整理；官方材料支持部分执行和安全机制。内部截图日期与版本未知，比较实验和安全评估缺失，故标记 partial。

- [S1] [[05-Research/algorithms-12281f86b27d/recce-runtime-selection--ed977e613aad/原文-recce-runtime-selection.md|原文证据]]；定位：§1–2：选型层次；§3.1：执行路径；§5.2–5.3：通信与证据；§6–8：安全和阶段边界
- [S2] [[05-Research/algorithms-12281f86b27d/recce-runtime-selection--ed977e613aad/原文-recce-runtime-selection.md|原文证据]]；定位：§3.1–3.2：Recce 原型执行路径与 AOT 产物
- [S3] [[05-Research/algorithms-12281f86b27d/recce-runtime-selection--ed977e613aad/原文-recce-runtime-selection.md|原文证据]]；定位：§5.2 与 §6：Wasm 内存访问和模块隔离
- [[01-Knowledge/bytecode-precompilation-vs-native-aot|字节码预编译与原生 AOT]]：使用；Recce 原型将 Rust 预编译为 Wasm 字节码，再由 wasm3 解释执行，是字节码预编译路径。
- [[01-Knowledge/webassembly-linear-memory-isolation|WebAssembly 线性内存隔离]]：使用；Recce 的 Wasm 动态模块路线采用 Wasm 隔离机制；Native 交互和 FFI 仍需检查边界。

## 建议

- 补充同设备、同版本条件下的 wasm3/Hermes 对照，并拆分执行、通信、内存与 UI 成本。
- 分别测量引擎、业务模块和总包体，不将历史基准泛化到当前业务。

<!-- AI:END -->

## 人工笔记

