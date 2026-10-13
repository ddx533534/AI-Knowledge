# Recce 的运行时与语言选型：Wasm、wasm3 与 Hermes

整理日期：2026-10-11。

本文整理本次讨论，以用户提供的内部「原型阶段」文档截图为原型实现依据，结合美团 2024 年公开文章和官方资料。内部截图与公开文章描述不同阶段，分别标注，不将后续设计倒推为原型能力。

## 1. 核心结论

Recce 参考 RN 的原生视图与布局能力，重点优化业务逻辑执行、UI 更新和 Native 通信。公开文章将性能与安全优势作为选择「Wasm 为主、JavaScript 为辅」的主要理由；目标 iOS 环境无法使用 JIT、解释效率与引擎体积，则影响具体选择 wasm3。

这是一条合理的架构路线，但文章中的「决定性优势」是团队的选型判断。现有材料支持机制上的优势和 Recce 整体性能收益，尚不能证明所有 Wasm 解释器普遍比 JS 解释器更快、更安全，也不能证明 wasm3 在目标业务中全面优于 Hermes。

## 2. 三个选型层次

| 决策 | 文档中的理由 | 结论边界 |
| --- | --- | --- |
| Wasm 为主、JS 为辅 | 性能、安全、动态化目标；生态成本可接受 | 属于团队面向目标场景的判断，不是所有引擎的普遍排名 |
| Wasm 运行时选择 wasm3 | 在无 JIT 条件下看重解释效率，同时控制引擎体积 | 包体是重要约束，资料未给出其权重或与 Hermes 的完整对照 |
| 上层语言选择 Rust | 性能、类型与内存管理、抽象能力、FFI、生态 | Rust 的优势不能全部归因于 Wasm 格式或 wasm3 |

依据：[美团公开文章 §3.1][S1]；内部截图中的「选择 wasm3 解释器」「Rust 的优点」。

引擎体积与业务模块体积应分别统计。引擎小，不代表所有业务编译后的 Wasm 模块都小，也不代表 App 总包体必然小于 Hermes 路线。

## 3. 字节码预编译、解释执行与 JIT

### 3.1 典型执行路径

```text
Recce 原型：
Rust 源码 → 提前编译成 Wasm 字节码 → 加载/下发 → wasm3 解释执行

RN + Hermes 的典型 Release 构建：
JS 源码 → 提前编译成 Hermes 字节码（.hbc）→ 随包发布 → Hermes 解释执行
```

Wasm 是执行格式，wasm3 是执行器，Rust 是上层源语言。终端不直接解释 Rust 源码。

Hermes 也能处理 JS 源码，并非只能接收预编译字节码。RN 的典型 Release 构建提前生成字节码，是为了降低启动时的解析与编译成本。[S2]

### 3.2 「AOT」需要说明产物

- **提前编译成字节码**：仍由虚拟机解释执行；Hermes 的官方设计说明使用了 AOT 这一表述。[S3]
- **提前编译成原生机器码**：CPU 直接执行；Wasm 运行时所说的 AOT 模式通常属于这一类。
- **JIT**：在运行过程中生成机器码并执行。

因此，本讨论使用「构建时预编译成字节码」描述 Recce 与 Hermes 的共同路径，避免把它误解为业务代码已原生化。

不能 JIT，也不意味着必须预先生成字节码；执行器仍可在设备上解析输入后解释执行。不同输入格式有不同准备成本。

### 3.3 并非所有 Wasm 引擎都只能解释执行

wasm3 采用解释执行；WAMR 支持解释、AOT 与 JIT 等模式；Wasmtime 具有编译执行路径，也提供 Pulley 解释器。[S4][S5][S6]

文档时期的 Hermes 主动选择不使用 JIT，优先优化启动时间、内存和引擎体积。这是引擎设计取舍，并非仅因 iOS 限制。[S3]

## 4. iOS 为什么限制 JIT

普通第三方 iOS App 通常不能在自身进程中随意生成并执行机器码。iOS 的强制代码签名、不可执行内存和权限检查，将动态生成可执行代码的能力置于严格控制之下。[S7][S8]

JIT 在运行时产生的新机器码，需要获得相应执行权限；字节码解释执行则由已签名的原生解释器读取字节码数据，不需要将业务字节码本身标记为 CPU 可执行代码。

「iOS 不允许 JIT」不是绝对命题：Safari 使用 JIT；获得特定授权的替代浏览器引擎也有相应支持。普通 RN/Recce App 不能由此直接获得同样权限。[S8][S9]

RN iOS App 中也存在两类产物：

| 部分 | 发布前产物 | 设备执行方式 |
| --- | --- | --- |
| 原生代码、Hermes 引擎自身 | 已签名的原生机器码 | CPU 直接执行 |
| 典型 Hermes Release 构建的 JS 业务 | Hermes 字节码 | Hermes 解释执行 |

所以，不能笼统称整个 RN App 都是「字节码解释运行」，也不能称 JS 业务已经全部编译成原生机器码。

## 5. Wasm 的性能优势：机制与边界

### 5.1 静态类型降低动态语义处理成本

内部截图以 Wasm 和教学语言 Lox 的加法指令对比说明：Wasm 的 `i32.add`、`f64.add` 等指令确定了数值类型；通用动态语言加法还需要处理类型判断、转换或字符串拼接。

这一机制支持以下推断：同样解释执行时，Rust/Wasm 可能将更多工作提前到编译阶段，减少终端需要处理的动态语义。数值计算、循环与结构化数据处理可能受益。

但 Lox 不代表 Hermes。Hermes 官方字节码已有数值加法 `AddN`，跳过数值类型检查；属性访问 `GetById` 也包含缓存索引。[S10] 不能将 JS 解释器描述为每次操作都完整判断类型或重新查找字典。

### 5.2 Rust 与数据布局的贡献

Rust 提供提前编译优化和明确的数据布局能力。内部原型使用 `#[repr(C)]` 的视图节点，通过 C 风格接口与 Native 交互，探索让 Native 读取 Wasm 线性内存中的视图描述，并在 Native 侧完成 Diff。

这同时优化了执行与通信，不是只更换解释器。Wasm32 地址是线性内存偏移，不能直接当作宿主 64 位指针；读取仍需正确处理基址、边界、对齐和生命周期。不能把「直接访问」扩展为所有跨语言调用都零拷贝、零成本。

依据：内部截图「与 C 交互」「与 Objective-C 交互」「DOM & 布局」「DOM Diff」。

### 5.3 实测证据能说明什么

| 材料 | 支持的结论 | 不能推出的结论 |
| --- | --- | --- |
| wasm3 历史性能测试 | 特定基准与环境下的解释效率 | 当前 iOS 上比 Hermes 快多少 |
| 美团 Recce 页面与业务测试 | 整体架构优化取得性能收益 | 收益全部由 Wasm 解释器产生 |
| 内部原型设计 | 静态类型、内存布局与通信方案有合理机制 | 已提供完整的 Hermes 对照实测 |

wasm3 官方性能页保留了 2019—2020 年数据，并明确说明不代表当前引擎对比；测试中没有 Hermes。[S11]

公开文章还同时改变了 UI 更新、属性编码与跨语言接口，因此其结果不能直接当作 wasm3/Hermes 的单变量实验。[S1]

## 6. 安全优势：区分语言、模块与宿主

Wasm 提供字节码与类型验证、线性内存边界检查、间接调用签名检查等机制。访问超出线性内存的地址会触发 trap；外部能力通过宿主提供的导入接口获得。[S12][S13]

需要区分三层：

| 层次 | 能支持的判断 | 局限 |
| --- | --- | --- |
| Rust 业务代码 | 类型与所有权约束减少部分错误 | `unsafe`、FFI 与业务逻辑仍需正确实现 |
| Wasm 模块隔离 | 限制模块越出线性内存，保护执行边界 | 不自动阻止模块内部相邻对象被覆盖 |
| 执行器与宿主接口 | 正确实现才能兑现隔离机制 | 引擎漏洞、错误指针转换或 FFI 可能破坏边界 |

Wasm 官方明确说明，其内存检查以线性内存区域为粒度，不是每个对象的边界检查。[S12] 内部截图也将 FFI 的安全与兼容问题列为后续研究方向。

正常 JS 代码同样不拥有任意访问宿主内存的能力。因此，Wasm 的隔离机制可以证明它适合动态模块执行，但不足以单独证明它比 Hermes 全面更安全。需要明确威胁模型、版本、开放接口和具体实现。

## 7. 原型与后续公开实现的差别

| 阶段 | 文档描述 |
| --- | --- |
| 内部原型 | 使用视图描述树；Native 侧执行 DOM Diff；移动节点按删除后新增处理；完整框架、多语言和 JIT/AOT 等列为 Future |
| 2024 年公开 Recce UI | Rust UI 路线采用订阅更新，没有 Diff 和 VDOM；另提供 JS 路线以复用前端生态 |

内部原型的限制不能直接套用到后续实现；公开实现也不能倒推为原型已经具备的能力。[S1]

## 8. 尚需补充的证据

若要验证「wasm3 比 Hermes 更快、更安全」，至少需要：

1. 同设备、明确引擎版本、同业务逻辑、相同优化与执行条件的性能对照。
2. 分别测量加载、初始化、计算、内存分配、宿主调用、布局与 UI 提交，隔离收益来源。
3. 分别统计引擎体积、业务字节码体积与总包体。
4. 明确安全威胁模型，检查执行器、线性内存访问与 FFI 边界。

现有材料尚未提供这一级对照。可确认的结论是选型动机和机制依据，不能将团队的架构判断提升为普遍性能或安全定理。

## 9. 来源

内部材料：用户提供的两张「原型阶段」文档截图；日期与版本未知。截图内容仅作为实现与设计证据，其引用书目、Future 项及仓库运行说明不等于本次已完成验证。

- [S1 美团：大前端——如何突破动态化容器的天花板？][S1]，2024-10-18。
- [S2 React Native：Optimizing JavaScript loading][S2]。
- [S3 Meta：Hermes 的设计说明][S3]，2019-07-12，注意历史版本范围。
- [S4 wasm3 官方说明][S4]。
- [S5 WAMR 官方说明][S5]。
- [S6 Wasmtime：Pulley 解释器][S6]，用于说明其他执行路径，不作为原型时期能力证据。
- [S7 Apple：App code signing process][S7]。
- [S8 Apple：Security of runtime process][S8]。
- [S9 Apple：Protecting code compiled just in time][S9]，用于限定浏览器例外，不作为普通 App 权限依据。
- [S10 Hermes 官方字节码定义][S10]。
- [S11 wasm3 历史性能测试][S11]。
- [S12 WebAssembly：Security][S12]。
- [S13 WebAssembly：Portability / API][S13]。

[S1]: https://tech.meituan.com/2024/10/18/Recce-in-meituan.html
[S2]: https://reactnative.dev/docs/optimizing-javascript-loading
[S3]: https://engineering.fb.com/2019/07/12/android/hermes/
[S4]: https://github.com/wasm3/wasm3
[S5]: https://github.com/wasm-micro-runtime/wasm-micro-runtime
[S6]: https://docs.wasmtime.dev/examples-pulley.html
[S7]: https://support.apple.com/guide/security/app-code-signing-process-sec7c917bf14/web
[S8]: https://support.apple.com/en-gb/guide/security/sec15bfe098e/web
[S9]: https://developer.apple.com/documentation/browserenginekit/protecting-code-compiled-just-in-time
[S10]: https://github.com/facebook/hermes/blob/main/include/hermes/BCGen/HBC/BytecodeList.def
[S11]: https://github.com/wasm3/wasm3/blob/main/docs/Performance.md
[S12]: https://webassembly.org/docs/security/
[S13]: https://webassembly.org/docs/portability/
