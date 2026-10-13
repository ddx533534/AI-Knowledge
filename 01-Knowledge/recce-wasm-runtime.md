---
{
  "id": "recce-wasm-runtime",
  "title": "Recce 运行时选型与 Wasm 执行、隔离机制",
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
    },
    {
      "document_id": "ed977e613aad6e2e4ba89871142fa79b616515629b33c33f87a100599c8538a7",
      "locator": "§3.1–3.3：典型执行路径、AOT 产物与引擎模式；§9 来源 S2–S6"
    },
    {
      "document_id": "ed977e613aad6e2e4ba89871142fa79b616515629b33c33f87a100599c8538a7",
      "locator": "§6：安全优势，区分语言、模块与宿主；§9 来源 S12–S13"
    }
  ],
  "relationships": [],
  "aliases": [
    "Recce与Hermes对比",
    "Rust wasm3动态化容器",
    "字节码预编译与原生 AOT",
    "字节码AOT",
    "Hermes字节码预编译",
    "WebAssembly 线性内存隔离",
    "Wasm线性内存安全",
    "Wasm沙箱边界"
  ],
  "tags": [
    "Recce",
    "React Native",
    "Wasm",
    "Hermes",
    "编译",
    "运行时",
    "安全",
    "FFI"
  ],
  "schema_version": 3,
  "created": "2026-10-13T17:05:00.000000+08:00",
  "updated": "2026-10-13T16:41:48.410478+08:00"
}
---
# Recce 运行时选型与 Wasm 执行、隔离机制

<!-- AI:BEGIN -->
## 结论

Recce 以性能、安全和动态化目标选择 Rust/Wasm 路线，再综合无 JIT 条件下的解释效率与体积选择 wasm3；现有证据不支持它全面优于 Hermes 的普遍结论。理解这条路线要先分清两件事：提前生成的产物是字节码还是机器码，以及隔离由语言、模块还是宿主提供。

## 关键发现

- 选型分三层：性能与安全目标解释 Wasm 路线，包体与解释效率解释具体选 wasm3，Rust 的优势不能全部归因于 Wasm 格式或 wasm3。
- 执行路径要分开看：典型 RN/Hermes Release 构建提前生成字节码以减少启动解析成本，Recce 原型的 Rust 编译产物是 Wasm，由 wasm3 解释执行。
- 无法使用 JIT 不强制要求构建时预编译字节码，解释器同样可以处理设备端输入；仅说 AOT 不足以说明终端是否还需解释执行。
- 线性内存提供了边界检查与 trap，但隔离不等于对象级内存安全，也不自动证明比 JS 引擎更安全；外部能力由宿主导入接口提供。
- 内部原型采用 Native 侧 Diff，2024 年公开的 Recce UI 采用订阅更新、没有 Diff 和 VDOM，两者属于不同阶段。
- 整体页面性能收益不能全部归因于解释器：材料没有给出 wasm3 与 Hermes 同设备、同版本、同业务的对照。

## 证据与分析

直接证据来自归档文档对内部原型截图与公开文章的分层整理，官方材料支持其中部分执行与安全机制。内部截图的日期和版本未知，比较实验和安全评估缺失，因此本节点标记为部分核实。

- 执行路径与产物：归档文档 §3 引用 RN、Meta 与 Wasm 引擎官方材料，区分源码、字节码与机器码；判 Hermes 无 JIT 的结论限定于材料讨论时期，不泛化到所有未来版本或其他运行时。
- 原型与公开实现的差异：文档 §3.1—3.2 说明 Recce 原型的执行路径与 AOT 产物，§5.2—5.3 记录通信机制与证据来源；把后续设计倒推为原型能力会读错。
- 隔离机制：文档 §6 基于 WebAssembly 官方安全与 API 说明，指出超出线性内存的访问触发 trap、线性内存内部仍可能发生对象覆盖，且 Rust 业务代码、Wasm 模块隔离、解释器与 FFI 实现是四个不同安全层次。隔离能否成立取决于执行器与宿主是否正确实现。

引擎体积与业务模块体积要分别统计：引擎小不代表所有业务编译后的 Wasm 模块都小，也不代表 App 总包体必然小于 Hermes 路线。

- [S1] [[05-Research/recce-runtime-selection.md|recce-runtime-selection]]；定位：§1–2：选型层次；§3.1：执行路径；§5.2–5.3：通信与证据；§6–8：安全和阶段边界
- [S2] [[05-Research/recce-runtime-selection.md|recce-runtime-selection]]；定位：§3.1–3.2：Recce 原型执行路径与 AOT 产物
- [S3] [[05-Research/recce-runtime-selection.md|recce-runtime-selection]]；定位：§5.2 与 §6：Wasm 内存访问和模块隔离
- [S4] [[05-Research/recce-runtime-selection.md|recce-runtime-selection]]；定位：§3.1–3.3：典型执行路径、AOT 产物与引擎模式；§9 来源 S2–S6
- [S5] [[05-Research/recce-runtime-selection.md|recce-runtime-selection]]；定位：§6：安全优势，区分语言、模块与宿主；§9 来源 S12–S13

## 建议

- 讨论 AOT 时明确输入、产物、编译时机与终端执行方式，不要用「AOT 了就快」跳过解释执行这一环。
- 补充同设备、明确版本、同业务条件下的 wasm3 与 Hermes 对照，并把执行、通信、内存与 UI 更新成本拆开测量。
- 分别统计引擎体积、业务字节码体积和总包体，不把历史基准泛化到当前业务。
- 评估安全时先定威胁模型，再单独检查宿主导入接口的偏移、边界与生命周期。

<!-- AI:END -->

## 人工笔记

