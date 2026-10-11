---
{
  "id": "bytecode-precompilation-vs-native-aot",
  "title": "字节码预编译与原生 AOT",
  "type": "concept",
  "status": "verified",
  "last_verified": "2026-10-10",
  "sources": [
    {
      "document_id": "ed977e613aad6e2e4ba89871142fa79b616515629b33c33f87a100599c8538a7",
      "locator": "§3.1–3.3：典型执行路径、AOT 产物与引擎模式；§9 来源 S2–S6"
    }
  ],
  "relationships": [],
  "aliases": [
    "字节码AOT",
    "Hermes字节码预编译"
  ],
  "tags": [
    "编译",
    "运行时",
    "Hermes"
  ],
  "schema_version": 2,
  "created": "2026-10-11T22:22:47.993341+08:00",
  "updated": "2026-10-11T22:22:48.109475+08:00"
}
---
# 字节码预编译与原生 AOT

<!-- AI:BEGIN -->
## 结论

提前生成字节码与提前生成原生机器码是不同执行路径；仅说 AOT 不足以说明终端是否还需解释执行。

## 关键发现

- 典型 RN/Hermes Release 构建提前生成字节码，以减少启动时解析和编译成本。
- Recce 原型的 Rust 编译产物是 Wasm，由 wasm3 解释执行。
- 无法使用 JIT 不强制要求构建时预编译字节码；解释器也可处理设备端输入。

## 证据与分析

归档文档 §3 引用了 RN、Meta 和 Wasm 引擎官方材料，区分源码、字节码与机器码。Hermes 无 JIT 的判断限定于材料讨论时期，不泛化到所有未来版本或其他运行时。

- [S1] [[05-Research/algorithms-12281f86b27d/recce-runtime-selection--ed977e613aad/原文-recce-runtime-selection.md|原文证据]]；定位：§3.1–3.3：典型执行路径、AOT 产物与引擎模式；§9 来源 S2–S6

## 建议

- 讨论 AOT 时明确输入、产物、编译时机与终端执行方式。

<!-- AI:END -->

## 人工笔记

