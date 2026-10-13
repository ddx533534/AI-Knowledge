---
{
  "id": "wasm-runtime-mobile-support",
  "title": "Wasm 运行时移动端支持与选型",
  "type": "comparison",
  "status": "partial",
  "last_verified": "2026-10-12",
  "sources": [
    {
      "document_id": "d54d1158136448f8d6f773d2e31464a3f8008336bc091ccdc16db1c6ea9d5a98",
      "locator": "标题「Wasm 虚拟机现状」；「基础对比」表；「支持功能」表；「性能」；「结论」——本次对比沿用的维度来自这份文档"
    },
    {
      "document_id": "048761078703df428c11e84444165da8d55e2b2e56502e5d3f72b754365300ed",
      "locator": "「基础对比」表：双端支持情况的 iOS 与 Android 两行、执行方式、实现语言"
    }
  ],
  "relationships": [
    {
      "target": "recce-runtime-selection",
      "type": "related_to",
      "explanation": "该对比表用 JIT、AOT、解释执行区分五个运行时，与执行路径分类的概念节点互补",
      "sources": [
        {
          "document_id": "048761078703df428c11e84444165da8d55e2b2e56502e5d3f72b754365300ed",
          "locator": "「基础对比」表：双端支持情况的 iOS 与 Android 两行、执行方式、实现语言"
        }
      ]
    }
  ],
  "aliases": [
    "Wasm 虚拟机现状",
    "Wasm 虚拟机对比"
  ],
  "tags": [
    "WebAssembly",
    "运行时",
    "移动端",
    "选型"
  ],
  "schema_version": 2,
  "created": "2026-10-12T17:15:51.049366+08:00",
  "updated": "2026-10-12T18:51:46.950734+08:00"
}
---
# Wasm 运行时移动端支持与选型

<!-- AI:BEGIN -->
## 结论

沿用原文档的维度（双端支持、执行方式、实现语言、提案支持、性能）重做对比，2026 年的移动端选型分成两条路。iOS 没有 JIT，只能用解释执行，官方可用的只有 wasm3 与 WasmKit（iOS 18+），另可自行接 Wasmtime 的 Pulley 或 Wasmer 5.0 起的解释后端。Android 五家都能跑，还能用 AOT 预编译，WAMR 2.4.4 的 AOT 是原生速度的 1.57 倍、WasmEdge 0.17.0 的 AOT 是 1.74 倍，两者最接近原生。

| 场景 | 首选 | 备选 | 依据 |
| --- | --- | --- | --- |
| iOS App（无 JIT） | wasm3 | WasmKit | 只有这两家在官方平台清单里，且都是解释执行；wasm3 约 64KB 代码、10KB 内存 |
| Android（可 AOT/JIT） | WAMR 2.4.4 AOT | WasmEdge 0.17.0 AOT | AOT 后可到原生速度的 1.4 至 1.8 倍，解释器则慢 10 倍以上 |
| 两端一套代码 | WAMR | Wasmtime | WAMR 官方同时覆盖 Android 与嵌入式；Wasmtime 用 Pulley 进 iOS |
| 需要 GC、SIMD 或多内存 | Wasmtime / WAMR / WasmEdge | Wasmer（无 GC） | wasm3 不支持 GC、SIMD、Relaxed SIMD，多内存与尾调用是新近才补上 |

选型结论：iOS 上优先 wasm3，模块需要 SIMD 或 Memory64 时改用 WasmKit；Android 上优先 WAMR 的 AOT 模式；如果同一份代码要覆盖两端且不依赖 GC，用 wasm3 的解释器最省事，但要接受解释执行的性能代价。

## 关键发现

- 双端支持：iOS 在官方清单里的只有 wasm3 与 WasmKit（iOS 18+）；Android 五家都支持，WAMR 与 WasmEdge 提供官方构建。
- 执行方式：wasm3 与 WasmKit 是纯解释器；Wasmtime 有 Cranelift/Winch JIT、Pulley 解释器与预编译；Wasmer 有 Cranelift/LLVM/Singlepass 加 5.0 起的多种后端；WAMR 与 WasmEdge 覆盖解释器与 AOT，WAMR 另有 Fast JIT 与 LLVM JIT 两级。
- 提案支持：wasm3 缺口最大（无 SIMD、无 GC、无 Relaxed SIMD、无 BigInt，线程只有 atomics），Memory64、多内存、尾调用、宽算术是 0.9.x 才补上的；Wasmtime 除 Type Reflection 外全覆盖；Wasmer 是唯一支持 Stack Switching 的；WasmKit 支持 SIMD、Memory64、Relaxed SIMD，但不支持 GC。
- 性能：2026-06 的桌面基准里，AOT 与 JIT 类都接近原生，Wasmer 7.1.0 为 1.33 倍、WAMR 2.4.4 AOT 1.42 倍、Wasmtime 46.0.0 1.46 倍、WasmEdge 0.17.0 AOT 1.64 倍（各自最佳构建）；纯解释器在迭代与分支密集负载上时间与能耗都超过 10 倍。
- 体积：wasm3 约 64KB 代码加 10KB 内存；WAMR 在 Cortex-M4F 上经典解释器 56.3KB、Fast 解释器 58.9KB、AOT runtime 29.4KB；其余三家没有官方嵌入式体积数字。
- 版本：WAMR 2.4.4、WasmEdge 0.17.0、Wasmer 7.1.0、Wasmtime 46.0.0（2026-06 基准口径）、wasm3 v0.9.1-beta.1（2026-09-10）、WasmKit 标签 0.4.2。

## 证据与分析

维度取自原文档的「基础对比」「支持功能」「性能」三节：双端支持情况、执行方式、实现语言、提案支持、运行性能。原文档是手机截图，表格文字要靠放大图辨认；本次重做只沿用它的维度，数值全部取自 2026-10-12 的一手来源。

### 基础对比

| 运行时 | iOS | Android | 执行方式 | 实现语言 | 2026 版本 |
| --- | --- | --- | --- | --- | --- |
| Wasmtime | 解释（Pulley）或预编译产物可用，官方未列移动端 | 解释 / JIT / AOT | Cranelift JIT、Winch、Pulley 解释器、可预编译 | Rust | 46.0.0 |
| Wasmer | 5.0 起解释模式，后端 V8 / Wasmi / WAMR，官方标注实验性 | JIT / AOT | Cranelift、LLVM、Singlepass，5.0 起后端可插拔 | Rust | 7.1.0 |
| wasm3 | 官方支持（解释器） | 官方支持（解释器） | 纯解释器，不做 JIT | C | v0.9.1-beta.1 |
| WasmEdge | 不支持 | 官方支持，AOT 需显式指定运行模式 | 解释器 + AOT（--run-mode=aot） | C++ | 0.17.0 |
| WAMR | 官方平台清单不含 | 官方支持 | 经典解释器、Fast 解释器、AOT（wamrc）、Fast JIT、LLVM JIT，支持逐级提升 | C | 2.4.4 |
| WasmKit | 支持，要求 iOS 18+ | 支持，Android API 30+ | 解释器（Swift 实现） | Swift | 0.4.2 |

WasmEdge 与 Wasmtime 的 iOS 一行来自外部资料：Wasmtime 的 Pulley 不生成也不跳转本地代码，维护者在 2026-01-07 的 issue #12251 中确认它支持 GC 与异常处理、可在 iOS 上工作；Wasmer 的 iOS 支持来自 5.0 发布说明；WasmEdge 在 2026-05-12 的 0.17.0-rc.1 发布说明里没有出现 iOS。

### 支持功能

下表取自 webassembly.org 的 features.json（2026-10-12 读取）。单元格里的版本号是该站点记录的完全支持起始版本，只有勾号的表示没有记录版本。

| 特性 | Wasmtime | Wasmer | wasm3 | WasmEdge |
| --- | --- | --- | --- | --- |
| JS BigInt to Wasm i64 Integration | ✗ | ✗ | ✗ | ✗ |
| Bulk Memory Operations | ✓ 0.20 | ✓ 1.0 | ✓ 0.5.1 | ✓ 0.7.1 |
| Multi-value | ✓ 0.17 | ✓ 1.0 | ✓ 0.5.1 | ✓ 0.6.2 |
| Import/Export of Mutable Globals | ✓ | ✓ 0.7 | ✓ 0.5.0 | ✓ 0.2.0 |
| Reference Types | ✓ 0.20 | ✓ 2.0 | ✓ 0.9.0 | ✓ 0.7.1 |
| Non-trapping float-to-int Conversions | ✓ | ✓ | ✓ 0.5.0 | ✓ 0.6.2 |
| Sign-extension Operators | ✓ | ✓ | ✓ 0.5.0 | ✓ 0.6.2 |
| Memory64 | ✓ 30 | ✗ | ✓ 0.9.1 | ✗ |
| Multiple Memories | ✓ 15 | ✓ 7.3 | ✓ 0.9.1 | ✓ 0.9.1 |
| Fixed-width SIMD | ✓ 0.33 | ✓ 2.0 | ✗ | ✓ 0.7.2 |
| Tail Calls | ✓ 22 | ✓ 7.1 | ✓ 0.9.0 | ✓ 0.10.0 |
| Threads and Atomics | ✓ 15 | ✓ 4.0 | ⚠ 需 flag | ✓ 0.10.1 |
| Type Reflection | ✗ | ✓ 2.0 | ✗ | ✗ |
| Garbage Collection | ✓ 47 | ✗ | ✗ | ✓ 0.14.0 |
| Relaxed SIMD | ✓ 15 | ✓ 7.1 | ✗ | ✓ 0.14.1 |
| Exception Handling with exnref | ✓ 47 | ✓ 6.0 | ✓ 0.9.1 | ✓ 0.14.0 |
| Extended Constant Expressions | ✓ 25 | ✓ 7.1 | ✓ 0.9.0 | ✓ 0.10.0 |
| Stack Switching | ✗ | ✓ 7.0 | ✓ 0.9.2 | ✗ |
| Wide Arithmetic | ⚠ 需 flag | ✓ 7.1 | ✓ 0.9.2 | ✗ |

该站点没有收录 WAMR 与 WasmKit，这两家按各自仓库 README 记录：

| 运行时 | README 明确列出支持的提案 | README 未列出的项 |
| --- | --- | --- |
| WAMR 2.4.4 | wasm-c-api、128-bit SIMD、Reference Types、Bulk memory operations、共享内存、Memory64、Tail-call、Garbage Collection、Exception Handling、Branch Hinting、Extended Constant Expressions | Multi-value、mutable globals、Non-trapping float-to-int、Sign-extension、Multiple Memories、Relaxed SIMD、Type Reflection 未出现在该节 |
| WasmKit 0.4.2 | Bulk Memory、Exception Handling、Fixed-width SIMD、Mutable Globals、Memory64、Multi-value、Non-trapping Float-to-Int、Reference Types、Sign-extension、Tail Call、Typed Function References、Multiple Memories、Relaxed SIMD、Threads and Atomics、Extended Const、Custom Annotation Syntax；WASI 0.1 大部分系统调用与 WASI Threads | Garbage Collection 与 Branch Hinting 未实现；Component Model 在开发中 |

### 性能与体积

下表性能数据来自 2026-06-23 发布的 libsodium 横向基准，主机是 AMD Ryzen AI 9 HX 470（x86-64 桌面），数值是相对原生构建的倍数，越低越好。WAMR 用 AOT 模式，WasmEdge 显式指定了 AOT 运行模式。

| 运行时 | 2026 版本 | 基线构建（相对原生） | 该运行时最佳构建 | 嵌入式体积 |
| --- | --- | --- | --- | --- |
| Wasmer | 7.1.0 | 2.08 | 1.33（启用 wide_arithmetic） | 无官方数字 |
| WAMR | 2.4.4 | 1.57（AOT） | 1.42（AOT） | Cortex-M4F：经典解释器 56.3KB、Fast 解释器 58.9KB、AOT runtime 29.4KB |
| Wasmtime | 46.0.0 | 2.41 | 1.46（启用 wide_arithmetic） | 无官方数字 |
| WasmEdge | 0.17.0 | 1.74（AOT） | 1.64（AOT） | 无官方数字 |
| wasm3 | v0.9.1-beta.1 | 未纳入该基准 | 未纳入 | 约 64KB 代码 + 10KB 内存 |
| WasmKit | 0.4.2 | 未纳入该基准 | 未纳入 | 无官方数字 |

该基准没有纳入 wasm3 与 WasmKit 这类纯解释器，解释执行的代价要另找依据：IEEE Access 2026 接收的一篇评测（13 个 WASI 兼容运行时、8 个基准、外部功率计测能耗）给出，解释器型运行时在迭代与分支密集负载上时间与能耗都超过 10 倍，而 Wasmtime AOT、WasmEdge AOT、Wasmer LLVM、WAMR AOT 与可移植原生基线相当。两项数据都在桌面 x86-64 上取得，移动端需要自行实测。

### 来源

本次核实于 2026-10-12 通过网页与仓库访问完成，以下页面未归档，仅作为核对来源列出：

- webassembly.org 的 features.json（2026-10-12 读取）：支持功能一节的逐格数据，覆盖 Wasmtime、Wasmer、Wasm3、wasmedge 等运行时，未收录 WAMR 与 WasmKit。
- 00f.net《Performance of WebAssembly runtimes in 2026》（2026-06-23）：libsodium 基准，含 WAMR 2.4.4、WasmEdge 0.17.0、Wasmer 7.1.0、Wasmtime 46.0.0 等版本；wide_arithmetic 把 Wasmtime 与 Wasmer 的差距从 2.41 与 2.08 压到 1.46 与 1.33；WAMR 拒绝该指令（不支持的 opcode 0xfc13）。
- Khan 等《A Taxonomy and Empirical Evaluation of WebAssembly Runtimes for Performance and Energy》（IEEE Access，2026 接收，DOI 10.1109/ACCESS.2026.3733354）：13 个运行时、8 个基准、外部功率计，解释器型运行时在迭代与分支密集负载上超过 10 倍开销。
- WAMR 仓库 README：平台清单含 Android、不含 iOS；运行模式含经典解释器、Fast 解释器、AOT、Fast JIT 与 LLVM JIT；体积数字取自 cortex-m4f 的 bloaty 统计。
- WasmKit 仓库 README：平台 macOS 15+、iOS 18+、tvOS 18+、Android API 30+；提案支持表给出各项的起始版本，Garbage Collection 与 Branch Hinting 未实现。
- wasm3 仓库 README 与 releases 页：系统要求约 64KB 代码与 10KB 内存，可用提案列到宽算术与栈切换，明确说明 iOS 与 WebAssembly 本身无法在运行时生成可执行代码页所以没有 JIT；最新版本 v0.9.1-beta.1（2026-09-10）。
- Wasmtime issue #12251（2026-01-07）：维护者确认 Pulley 支持 GC 与异常处理、执行时不生成或跳转到任何本地代码，可在 iOS 上工作。
- Wasmer 5.0 发布说明（wasmer.io 博客，2024-10-29）：iOS 走解释模式，后端为 V8、Wasmi、WAMR，三个后端标注实验性。
- WasmEdge 0.17.0-rc.1 发布说明（2026-05-12）：与 Android 相关的变更只有示例目录迁移，未出现 iOS。
- CVE-2025-15413、CVE-2025-15572 的漏洞库条目（2026-01、2026-02 发布）：影响 wasm3 0.5.0 及以下；两项都在 v0.9.0 的修复范围内。
- iOS 的 JIT 限制在 2026 年的公开资料中描述不变：App Store 分发的应用不能启用 JIT，只有通过 BrowserEngineKit 接入的替代浏览器引擎例外。

- [S1] Wasm 虚拟机现状（用户提供的整页截图，本库未留存）；定位：标题「Wasm 虚拟机现状」；「基础对比」表；「支持功能」表；「性能」；「结论」——本次对比沿用的维度来自这份文档
- [S2] Wasm 虚拟机现状·基础对比表（用户提供的放大截图，本库未留存）；定位：「基础对比」表：双端支持情况的 iOS 与 Android 两行、执行方式、实现语言
- [[01-Knowledge/recce-runtime-selection|Recce 的运行时与语言选型]]：相关；该对比表用 JIT、AOT、解释执行区分五个运行时，与执行路径分类的概念文档互补

## 建议

- iOS 侧按 wasm3 起步，模块用到 SIMD、Memory64 或 Relaxed SIMD 时换成 WasmKit；两者都是解释执行，性能按解释器的上限预估。
- Android 侧用 WAMR 的 AOT 模式（wamrc 预编译加 iwasm 运行），需要 JIT 时再考虑 Fast JIT 到 LLVM JIT 的逐级提升。
- 模块需要垃圾回收、异常处理或多内存时排除 wasm3，改用 Wasmtime、WasmEdge 或 WAMR；Wasmer 目前没有 GC。
- 不要直接引用桌面基准做移动端决策：在目标机型上按自己的模块测启动耗时、稳态吞吐与包体积，wasm3、WAMR 解释器、WAMR AOT 三个配置先跑一轮。

<!-- AI:END -->

## 人工笔记

