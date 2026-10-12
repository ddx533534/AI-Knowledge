# 移动端 Wasm 运行时的对照实测缺口

来源文档：d54d1158136448f8d6f773d2e31464a3f8008336bc091ccdc16db1c6ea9d5a98（整页截图）、048761078703df428c11e84444165da8d55e2b2e56502e5d3f72b754365300ed（基础对比表放大截图）。  
记录日期：2026-10-12。对应节点：[[01-Knowledge/wasm-runtime-mobile-support|Wasm 运行时移动端支持与选型]]。
本次对比只沿用原文档的维度，逐格数值取自 webassembly.org、各仓库 README 与两项公开基准。

- 缺移动端一手实测：没有同一机型、同一模块下的 wasm3、WasmKit、WAMR 解释器、WAMR AOT、Wasmtime Pulley 横向对照。节点引用的性能数字全部来自 x86-64 桌面（AMD Ryzen AI 9 HX 470），AOT 与 JIT 类接近原生的结论不能直接搬到 ARM 手机。
- WAMR 与 WasmKit 的逐项提案支持只有各自 README 的自述，webassembly.org 的矩阵未收录这两家，缺第三方交叉验证；WAMR 未列出的项（Multi-value、mutable globals、Multiple Memories 等）不等于不支持，只是没出现在该节。
- 嵌入式体积只有 wasm3（约 64KB 代码 + 10KB 内存，来自 README）与 WAMR（Cortex-M4F 上的 bloaty 统计）两家的官方数字；Wasmtime、Wasmer、WasmEdge、WasmKit 未给出，选型时缺这一维度。
- iOS 可用性分三档：wasm3 与 WasmKit 有官方平台清单；Wasmtime 的 Pulley 与 Wasmer 的解释后端只有维护者答复与发布说明，没有上架应用的公开案例；WasmEdge 不支持 iOS 是据其发布说明中长期缺席推断的。
- WasmKit 的平台要求是 iOS 18+（README），未核实是否存在支持更低版本的分支或历史版本。
- wasm3 的 CVE 是否在 v0.9.0 中完全修复，未逐条比对补丁与漏洞描述；漏洞库条目仍写着项目无活跃维护者。
- 原文档的发布日期与结论原文未能逐字确认，其结论段的措辞只记大意。

这些是资料与验证缺口，不表示用户理解程度。
