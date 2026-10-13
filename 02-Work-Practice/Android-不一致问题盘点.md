# Android 跨端不一致问题：解法清单

核实日期：2026-10-13

材料是内网学城《99.不一致性问题》目录下的 45 篇子文档里与 Android 相关的 32 篇（读取日期 2026-10-13，逐篇读简化版正文），加上挂在其中 6 篇问题下、由本人撰写的 8 份排查文档。

**怎么用**：第 1 章用三个问题判断你手上的问题落在哪条通道，第 2 章按通道找对应解法，第 3 章是能直接抄的写法，第 4 章解释为什么这么修。全文讲「怎么解」，不做篇数分布统计。

**阅读约定**：问题一律用简称；版本号、机型、代码照抄原文未复算；「通道」与「六层」是本文的分析结构，不是文档原文。45 篇的标题都带状态标签（【已解决】/【待解决】/【Hack】），本文一律按正文实际内容判断，不采信标题 —— 其中 3 篇标着【已解决】而正文的「原因 / 解决 / Hack」三节全空。

## 一、先判断：三个问题，四条通道

![图 1：拿到一个不一致问题，按顺序问三个问题，落到四条通道上。判断一「换一份同一版本引擎的原生 demo 还能复现吗」，能复现走升级通道；判断二「框架侧是不是已经写明不改」，是就走换写法通道；判断三「根因写出来了吗」，没写走自己补定位，写了但没版本落点就走先 hack 后等版本。](fig1-routes.svg)

| 通道 | 判据 | 你要做的动作 | 谁来做 |
| --- | --- | --- | --- |
| 升级即解 | 布局、属性、事件类问题；换一份同版本引擎的原生 demo 就能复现 | 升 Recce Native SDK / wasm 到指定版本，业务代码一行不改 | 框架侧发版 |
| 换写法 | 框架侧已经有明确结论：与 RN 一致，或 Android 原生即如此 | 照第 3 章的写法改业务代码，不要等版本 | 业务 |
| 先 hack，后等版本 | 已定位到源码，但修复没有版本落点；或 Native 修了也覆盖不到旧版本 | 先用第 3 章的 hack 顶上，同时把版本推进排期 | 双方 |
| 自己补定位 | 只有现象与录屏，原因一节是空的 | 走完「最小复现 → 读源码 → 给两条带代价的路」 | 谁遇到谁补 |

三个判断按顺序问，不要跳：

1. **换一份同一版本引擎的原生 demo 还能复现吗？** 能复现 → 通道 1，别在属性映射里绕。
2. **框架侧是不是已经写了「不改」？** 写了 → 通道 2，找替代写法，不要等。
3. **根因写出来了吗？** 没写 → 通道 4，先补定位；写了但没有落点 → 通道 3。

一条能带走的判断：**升级版本是唯一能一次解掉一批问题的杠杆。** 1.31 与 1.32 两次跟 Yoga，一次消化掉 absolute 无法隐藏、三边 borderWidth 撑不起视图、display:none 与 absolute 共存的性能问题；1.32 同一轮又修掉 AlignSelf 相反、ResizeMode 系列、visible_area_change 数据异常。这些收益来自引擎本身，不是某一个属性。

## 二、解法清单

同一批问题按现象归类，能更快找到该怎么解：

![图 2：按现象找解法。六行映射，左列是看到的现象，中列是定位第一步，右列是解法动作与落点。宽高不对先在同版本原生 demo 上复现；隐藏后状态丢失先查 display:none 链上的尺寸派生量；两端属性相反要拿 RN 当第三参照；点不到先分清命中由谁决定；只在某机型出现要换成结构性条件；事件数据与单位不对就查默认值、取值域、单位、参照系四件事。](fig2-map.svg)

2.1 到 2.4 是四组解法，按「谁动手」排，从最省事的开始；2.5 是还没有解法的，写清楚缺哪一步。

### 2.1 升级版本就解掉，业务代码不用改（11 条）

| 问题 | 怎么修 | 落点 |
| --- | --- | --- |
| absolute 定位无法用 visible 隐藏 | 借用的 Yoga ≤1.18 有这个 bug，3.2.1 正常。用同一段代码在两版引擎上对照即可确认 | 自打包 Yoga 3.2.1，Recce 1.31 落地 |
| 三边 borderWidth 撑不起视图（Absolute 定位 Border 不一致） | Android 设置 borderWidth 时漏写 left/right/bottom 三个维度到 Yoga 节点，补上这三边的写入 | Recce 1.31 |
| display:none 与 absolute 同用时布局变慢 | 老 Yoga 在「absolute + display:none + 子视图多」时性能差，跟 Yoga 版本更新 | Recce Native 1.32 更新 Yoga |
| AlignSelf::FlexEnd / Center 双端相反 | Recce 解析时把 FlexEnd 与 Center 设置反了一次，iOS 又反一次，两次抵消后只有 Android 是错的；修 Android 侧的解析 | Recce Native 1.32 |
| ResizeMode 设置不生效、动态改属性无效 | 三处一起改：普通图被误判成动画类型；设置数据源后又按图片原始尺寸覆盖一次绘制边界，Stretch 因此失效；改 ResizeMode 没把图片标脏。做法是把图片类父子关系解绑、抽出公共基类重构 | Recce 1.32；业务亟需可在 1.30 上发小版本，需重点回归图片能力 |
| 双端 ResizeMode 默认值不一致 | 对齐双端默认值 | Recce Native 1.32 |
| 1.32 以下 visible_area_change 数据异常 | 两个 rect 各坏一个；返回值单位是 px 不是 dp；is_intersecting 双端参照系不同（Android 相对屏幕、iOS 相对 scroll_view） | Recce Native 1.32 |
| 同层组件被 display:none 后无法布局 | 宿主宽度被置 0 → Recce 按 0 渲染 → 内部自适应把高度撑大 → 与宿主互相触发布局成死循环。Native 侧修，切 tab 渲染错误随之解掉 | 跟宿主 12.29.400：2.5 集成 / 2.20 回归 / 2.25 全量 |
| 分辨率变更时页面尺寸渲染错误 | DisplayMetricsHolder 缓存了 DisplayMetrics，宽高与 margin 的像素换算全走这份缓存；改成 RecceRootView 销毁时清缓存 | 已修，测试包 |
| 交叉检查器偶现 crash | 删除节点从父节点开始，子节点被删后仍触发曝光回调，向上查找时命中空指针；加判空 | Recce Native 发版 + 宿主 12.59.200 起 |
| MaxWidth/MaxHeight 的 undefined 被当成 0 | undefined 类型没被解析，值 0 被当最大宽高写进节点。分两层修：Native 与 iOS 一样解析该类型（**覆盖不到旧版本**）；recce_ui 侧把 undefined 的值由 0 改成 NaN，让下游无法把 0 当有效值用（**能覆盖大部分流量**） | Native 发版 + recce_ui 发版 |

三篇标题标【已解决】但正文三节全空的（label 的 EllipsizeMode::Tail 截断末尾省略号、图片重载用例闪白、Image ResizeMode 三端不一致），给不出解法，实际修复版本见第六章。

### 2.2 要在框架的 Java 层动刀，每条都有代价（3 条）

这三条是本人排查产出，方案各给了两条路，取舍一并列出。

| 问题 | 怎么修 | 代价与注意 |
| --- | --- | --- |
| scroll_view 隐藏再显示后滚动位置被重置 | 改两处：ScrollView 的 onLayoutChange 里加「子布局宽高为 0 就跳过」的判断，不要在这个状态下写回位置；HorizontalScrollView 压根没保存过位置，补上与 ScrollView 一致的保存逻辑 | 滚动动画进行中同时发生布局变化时，理论上可能直接跳到目标位置、动画失效；RN 最新版采取了类似处理 |
| 连续调用 scroll_to 动画失效 | 根因是 smoothScrollBy 距上次滚动不足 250ms 时中止动画、改走 scrollBy（表现上等于 animated 被当成 false）。两条路：① 重写 smoothScrollBy，把间隔缩短到 100ms 或干脆取消间隔、每次先取消上一次动画；② 抄 RN 的做法，不再依赖 OverScroller，改用自定义插值器、两个滚动组件共用一套逻辑 | ① 成本极低、效果符合预期，但改的是系统源码，`mFlingSpan` 那部分够不到，且 100ms 是否够用要看场景；② 精确可控、易调试，但改动大、成本高 |
| 子元素溢出父元素无法点击 | 事件自上而下分发，中间那层容器判定「子树不含触点」就不再往下走。两条路：① TouchDelegate 把父容器热区代理给子视图；② 重写 dispatchTouchEvent 与 onInterceptTouchEvent 自己分发 | ① 需要 recce-ui 新增设置触摸代理的方法；② 所有能当父容器的 view 都会受影响，影响面大 |

### 2.3 框架的结论是「不改」，换业务侧写法（3 条）

| 问题 | 为什么框架不改 | 业务侧怎么写 |
| --- | --- | --- |
| 父级 opacity 表现不一致 | iOS 用 CALayer.opacity 整体应用，Android 用 View.alpha 让每个子视图先各自渲染再合并；Android 的行为与 RN 一致，改它反而离参考标准更远 | 要背景透明就把透明度写进颜色（`BackgroundColor::argb`）；要整体透明用同色遮罩层模拟 |
| input placeholder 折行 | Android 原生就是这个效果，文档给的原生等价实现可以复现 | 自实现一层 placeholder：label 绝对定位叠在 input 上，文本为空时显示 |
| scroll_view 拦截子视图 on_click | Android 把这段手势识别为滑动、不响应点击，旧版本无法解决，native 侧不动 | 升级到 Recce 1.22+ / rust-recce 0.11+ 后改用框架层的 on_touch_end（touch 事件由框架自己做，绕过 native 手势识别）；旧版本用 rui 的 event_bus 直接派发事件，不走 click 冒泡 |

### 2.4 已定位，但还没有版本落点，先按 hack 做（4 条）

| 问题 | 定位到哪一步 | 现在怎么做 | 后续解法 |
| --- | --- | --- | --- |
| 部分机型 Label 裁最后一个字 | 只有现象与最小复现，原因一节为空 | 给 label 显式指定字体：`FontFamily::new("system")` | 待定位 |
| 1.32 的 foreground 回调触发不稳定 | 只写了「Native 修复」，根因未写 | 用 appear 事件代替；或用 `can_i_use::android_foreground()` 判断后订阅 MSI 的 onAppStatusChange 广播 | Native 修复 |
| env 屏幕参数双端不一致 | 根因清楚：Android 的 display_width/height 实际是 window 值，且双端都没传 window 尺寸 | 用 MSI 桥自己取 window 尺寸 | Native 修复 |
| 双端无障碍 | 三件事：聚焦区域与默认值（iOS 必须显式传 `Accessible::bool(true)`）、播报了不可见内容、努比亚机型滑动时布局变化 | 播报不可见内容这一条用 if 条件替代 visible，或直接改文案；聚焦区域与努比亚布局变化判「暂时不好解决」 | 待排期 |

### 2.5 只有现象，缺的是「补一次定位」（8 条）

这 8 条不是难度大，而是没走到「复现 → 读源码 → 给两条路」这一步。缺的动作写清楚，谁都能接着做。

![图 3：只有现象的问题缺的是哪一步。红的三行只有录屏、截图或单据外链，缺的是最小复现加源码定位；橙的一行根因已经写清，只缺解法；灰的三行缺陷在鸿蒙侧，Android 只是参照系。底部说明另行三篇标着已解决而正文三节全空的文档，缺的不是定位，是一次回写。](fig3-gaps.svg)

| 问题 | 文档里有什么 | 要出解法还缺哪一步 |
| --- | --- | --- |
| Android 的滚动事件穿透 | 一段视频 | 做最小复现，顺着触摸链路看事件在哪一层漏出去 |
| label 嵌套 view 展示不一致 | 三端截图 + 最小复现 | 读三端量文本尺寸的代码，确认谁把行高或宽度算错 |
| on_touch 事件不一致 | 现象描述 + 两条单据外链 | 先展开单据看是否已有结论没回写，再补源码定位 |
| image 单边 BorderWidth 与其余两端不一致 | 一条单据外链 | 同上 |
| iOS 多行 Label 嵌套图片行高膨胀 | 根因已写清（TextKit 把 line fragment 撑高），也对比了 Android 与鸿蒙为什么不膨胀 | 只缺解法：按 Android 的「替换字体度量」思路重排 iOS 的附件度量 |
| 鸿蒙下划线间距比另外两端大 | 三端截图 | 鸿蒙侧度量差异；Android 在这里只是参照系 |
| 鸿蒙 borderStyle = Dotted 是圆点 | 一张截图 | 同上 |
| 鸿蒙圆角压缩不一致 | 一张截图 + 复现代码 | 同上 |

## 三、可以直接抄的写法

九段从原文档抄来的写法。每段都标注了什么时候可以撤掉。

### 3.1 隐藏 scroll_view 又不丢滚动位置

不用 `visible` 完全隐藏，改成「高度归零 + 全透明」，位置就不会被布局重置带走：

```rust
styles! {
  fake_invisible { Height::number(0.)  Opacity::number(0.) }
  fake_visible   { Height::auto()     Opacity::number(1.) }
}
```

隐藏的是父布局时绕不过去，要用共享态存位置：**隐藏前把当时的 offset 存下来，on_layout 里判断宽度从 0 变成正数时再恢复**（用 `animated: false` 直接跳，不要放动画）：

```rust
on_layout: move |e| {
  if let Ok(d) = e {
    let w = frame.get().as_ref().width;
    set_frame(d.layout.clone());
    // 宽度从 0 恢复到大于 0，判定为「隐藏 → 显示」
    if w == 0. && d.layout.width > 0. { restore_scroll(); }
  }
}
```

撤掉条件：ScrollView 的位置保存逻辑随版本发出后。

### 3.2 图片 ResizeMode 不生效

在 `on_load` 里强制刷新一次高度，逼它重新按 ResizeMode 计算边界：

```rust
let height = use_state(cx, || Height::number(0.));
image {
  style: { ResizeMode::Stretch  {height} },
  source: "...",
  on_load: move |_| { height.set(Height::auto()) },
}
```

图片本来就是异步加载、从无到有，所以额外刷一次高度没有副作用。撤掉条件：升到 1.32。

### 3.3 MaxWidth/MaxHeight 用了 undefined

不要用 `undefined`，Android 会把它的值 0 当成最大宽高。需要「不限宽」时给一个极大值：

```rust
MaxWidth::number(200.)  Height::number(500.)  Width::auto()

{toggle}.map(|v| match *v {
  true  => MaxWidth::number(99999.),   // 等价于「不限」，不要写 undefined
  false => MaxWidth::number(200.),
})
```

适配所有版本，代价是不美观。撤掉条件：所在 App 版本的 Native 解析了 undefined 类型之后。

### 3.4 部分机型 Label 裁最后一个字

显式指定字体，不再依赖机型默认字体：

```rust
label {
  style: { FontSize::number(14.), FontWeight::N500, FontFamily::new("system") },
  text: "+ 添加新卡",
}
```

### 3.5 foreground 回调触发不稳定

先判断当前 Native 版本有没有这个能力（recce_ui 0.13.6+ 提供 `can_i_use`），没有就绕到 MSI 的广播上：

```rust
if env().os == OS::ANDROID && !can_i_use::android_foreground() {
  use_future!(scope_id, async move {
    // 先随意调一次 MSI 桥，触发 MSI 挂载
    let _ = MSI::subscribe("onAppStatusChange", None, |_, _| {}).await;
    add_app_listeners(AppEventListener::new(
      "onAppStatusChange".to_string(),
      move |event: &AppEvent| { /* app_status 为 Foreground 时做事 */ },
    ));
  });
}
```

更省事的替代：直接用 appear 事件代替 foreground。

### 3.6 env 取不到 window 尺寸

Android 的 `display_width/height` 实际给的是 window 值，而 window 尺寸双端都没传。业务侧用 MSI 桥自己取（MSI 接口 id 1504）。

### 3.7 1.32 以下的 visible_area_change

两个 rect 各坏一个，业务侧可以互补计算；老版本返回 px，记得除 `pixel_ratio` 换成 dp：

```rust
if env().os == OS::ANDROID && !can_i_use::android_visible_area_change_data() {
  let ratio = env().pixel_ratio.unwrap_or(1.);
  // Android 用 interactionClientRect + ScrollView 相对原点偏移；iOS 用 boundingClientRect 减偏移
  let right = env().display_width as f32 - (rect.x as f32 + rect.width as f32) / ratio;
  let top   = rect.y as f32 / ratio + rem(10.) - panel_top;
}
```

### 3.8 input placeholder 折行

像 web 一样自实现一层 placeholder：input 外面套相对定位容器，再叠一个绝对定位的 label，文本为空时显示占位文案：

```rust
view {
  style: { Position::Relative }
  input {
    style: { Width::number(100.), IncludeFontPadding::bool(false), NumberOfLines::s32(1), TextAlignVertical::Center }
    on_change_text: move |t| text.set(t),
  }
  view {
    style: { Position::Absolute, Top::number(0.), Bottom::number(0.), Left::number(5.), AlignItems::Center }
    label { style: { NumberOfLines::s32(1), Color::rgb(0xcccccc) }, text: {is_visible}.map(...) }
  }
}
```

### 3.9 父级整体透明

Android 无法整体变浅，用与背景同色的遮罩层模拟：在最外层加一个 absolute、四边贴合、与背景同色的视图，把 Opacity 设在遮罩上。

## 四、为什么这么修：六层的判断

解法分六层，层与层的分界不是「哪个平台」，而是「这一层做错之后，要在哪一层才能修」。

![图 4：六层判断与修法。1 布局引擎看引擎版本、2 视图树看隐藏引起的尺寸污染、3 属性协议看默认值取值域单位参照系、4 事件分发看命中由谁决定、5 渲染合成看谁在什么时候算尺寸、6 环境设备把机型名单换成结构性条件。左列是判据，右列是修在哪、谁动手。](fig4-fixmap.svg)

前 3 层的问题会随引擎与协议升级整批消失，后 3 层一次只能修一个。1 到 3 层的解法就是 2.1 表里的版本号；4 到 6 层的解法是 2.2 到 2.4 表里的写法与 hack。

### 4.1 布局引擎：先怀疑版本，再怀疑属性

**判断：布局结果不符合预期时，第一动作是在「同一版本引擎的原生 demo」上复现一遍；能复现就是引擎的事，不要在属性映射里绕。**

- absolute 定位无法隐藏，就是这么定下来的：同一段代码在 Yoga 1.18 以下与 3.2.1 上对照，前者黑块仍有宽高、后者没有，结论从「属性没生效」改成「引擎有 bug，升级」。
- 边框宽度撑不起视图，是另一半：Android 侧设置 borderWidth 时漏掉了 left/right/bottom 三个维度对 Yoga 节点的写入 —— 不是引擎算错，是「属性写进节点」这一步漏了。所以修法是补写入，不是换引擎。
- 反向的例子同样有用：小米机型 1px 像素差确认 Android 在原生 Yoga 算完之后又做了一次 round 作差，而 RN 最新版用同一套算法 —— 这里「和 RN 对齐」等于「一起错」，所以结论是给业务 hack 并向 RN 提 issue。

### 4.2 视图树与隐藏语义：Android 的「隐藏」是一次真实的布局塌缩

**判断：Android 把 display:none 表达成「自身与所有子视图置 0×0」，iOS 只改当前视图。所有从尺寸派生的量（可滚动最大距离、自适应高度、传给宿主的组件尺寸）都会被这个 0 污染。**

- 滚动位置重置：ScrollView 给内容布局挂了 onLayoutChange，回调里发现内容高为 0、maxScrollY 也就是 0，于是判定「当前位置越界」并把它写回 0 —— 位置不是没保存，是被自己清掉了。修法是在回调里判断内容尺寸是否为 0，而不是换一种隐藏方式。
- 同层组件白屏与抖动：宿主宽度被置 0 后 Recce 按 0 渲染，内部自适应让高度撑大，与宿主来回触发布局成死循环。三条 hack 的差别在于绕过哪一段：缓存上一次宽度（只改 Recce）、跟随宿主同步宽度（会闪）、通过总线把宿主尺寸直接给 Recce（兼容性最好，但两边都要改）。
- 凡是「隐藏再显示后状态丢失」或「被隐藏的组件显示异常」，先查这条链上有没有尺寸派生量被 0 污染，不要先怀疑隐藏属性的实现差异。

### 4.3 属性协议：跨端 bug 会互相抵消，不能用「二选一」定位

**判断：差异不一定表现为「一端对一端错」，可能是两次错误叠加后的结果，所以必须拿 RN 的行为当第三参照。**

- AlignSelf 是最典型的：Recce 解析时把 FlexEnd 与 Center 设置反了，iOS 端又反了一次，两次抵消后 iOS 是对的、Android 是错的。只看两端结果会得出「iOS 对、Android 错」，根因却在共享的那次解析上加 iOS 的补偿。
- 属性协议要写清四件事，这批问题里四件各出过一次：**默认值**（双端 ResizeMode 默认值不一致）、**取值域**（Android 侧 ResizeMode 只支持四个值，fit_start/fit_end 没有）、**单位**（1.32 以下 interactionClientRect 返回 px 而不是 dp）、**参照系**（同一次曝光，Android 相对屏幕、iOS 相对 scroll_view；env 的 display 在 Android 上其实是 window 值）。
- 类型没被解析会把「未定义」变成「0」：MaxWidth::undefined() 发出的类型是 Undefined、值是 0，Android 不解析这个类型，0 就成了最大宽度。兜底思路值得记住 —— 在 recce_ui 侧把该类型的值改成 NaN，让下游无法把 0 当有效值用，这样不用等旧版本流量退完。

### 4.4 事件分发：先分清「谁来决定命中」

**判断：原生命中受 View 层级与边界裁剪约束；框架层命中可以自定义规则，代价是要一并接管原生本来免费给的那些能力。**

- 原生命中带来的两处限制都有文档：触点落在绝对定位溢出父容器的子元素上时，中间那层容器判定子树不含触点，事件就不再下发；ScrollView 把手势识别成滑动、不响应 click，父级的 click-outside 因此实现不了。
- 绕开的方向也一致：用 on_touch_end 这类由框架自己做的事件，touch 不走原生分发，因此不受原生手势识别限制。1.35 的触摸新架构是同一思路的彻底版本 —— root 统一观察 touch 流、递归命中，把 hitSlop / overflow / clipChildren / transform 都算进去。
- 代价那一侧同样有记录：接管命中之后，多指、无障碍、焦点这些原来由原生隐式提供的能力，变成必须自己补的欠账。
- 反方向的差异别忘：鸿蒙的 touch 默认穿透，同一份代码在那边要「显式拦截」而不是「避免拦截」。

### 4.5 渲染与合成：差异多在「谁在什么时候算尺寸」

**判断：行高、尺寸类的跨端差异，先把这个尺寸在每端分几步算出来；多数差异出在步数不同，不是画法不同。**

- 父级 opacity：iOS 用 CALayer.opacity 在合成时整体应用，Android 用 View.alpha 让每个子视图先各自渲染（含透明度）再合并，父子都设半透明就会叠加变深。这也解释了为什么结论是「不改」—— Android 的行为与 RN 一致。
- 文本内嵌图片的行高是三段式差异：iOS 走 NSTextAttachment（占位符 U+FFFC），图片底边坐在基线上向上占 12pt，而字体 ascender 只有 9.5pt，TextKit 发现这一行需要更多上行空间就把 line fragment 撑高；Android 走 `ReplacementSpan.getSize()`，直接替换字体度量（是替换不是叠加）；鸿蒙的 ImageSpan 是文本节点的一等子节点，同一轮排版里统算所有 span，没有二次修正。
- 图片绘制边界是「在别人的决策点上二次覆盖」：系统已在 updateDrawable 里算好 bounds，Recce 又按图片原始尺寸覆盖了一遍，Stretch 因此失效；配套的第二个坑是设置 ResizeMode 时没把图片标脏，所以动态改属性不重载。

### 4.6 环境与设备：把机型名单换成结构性条件

**判断：这一层的共同形态是「同一份代码在特定机型或特定像素密度下失效」；文档给的 hack 全是「显式声明」，修的时候要把「依赖某个机型默认值」换成结构性条件，否则换机型就复发。**

- 分辨率变更：Android 的 DisplayMetricsHolder 缓存了 DisplayMetrics，margin / width / height 的像素换算全走这份缓存，屏幕参数变了仍按旧值换算 —— 修法是 RecceRootView 销毁时清缓存。
- 像素密度小数：布局结果的宽高是两次 round 作差，遇到小数宽高或小数像素密度就会差 1px，表现为红框与倒三角之间一条缝，只有小数机型上能看见。
- 字体 fallback：部分机型（如小米 MAX）Label 最后一个字被裁，hack 是显式指定 FontFamily。
- 无障碍：聚焦响应区域与点击区域不一致（努比亚偏左、红米正常），且 `accessible` 的默认值双端不一致（iOS 必须显式传 true 才播报）。

## 五、八份排查文档补上的东西

这 8 份挂在 6 个问题下，价值集中在「定位到方法名」这一层 —— 表格里是每份文档补上的定位与顺带产出的东西，解法本身见 2.1 与 2.2。

![图 5：八份排查文档补上的东西。上排两张卡片是 2025 年 1 月的四份与 2025 年 11 到 12 月的四份；下排绿的三行是把现象追到具体源码行为的三次定位，橙的两行是修正既有结论的地方。](fig5-own-work.svg)

| 排查文档 | 挂在哪篇问题下 | 补上的定位 | 顺带产出 |
| --- | --- | --- | --- |
| Android ScrollView(Horizontal) 隐藏后滚动位置被重置问题排查 | scroll_view 隐藏后滚动条位置重置 | ScrollView 的 onLayoutChange 与 maxScrollY 判定；HScrollView 缺保存逻辑 | 改写了父文档「双端 display:none 处理不一致」的归因；文末提出应定期 review RN 上游 |
| ScrollView 多次调用 scroll_to 动画失效问题排查 | 连续调用 scroll_to 动画失效 | smoothScrollBy 的 250ms 间隔降级分支 | 两条方案各列优点与缺点 |
| Android 子元素定位溢出父元素时无法点击问题排查 | 子元素溢出父元素无法点击 | dispatchTouchEvent 自上而下分发与中间层的子树范围判定 | 两条方案及各自影响面 |
| Android 元素 absolute 定位无法隐藏问题排查 | absolute 定位无法用 visible 隐藏 | 两版 engine 对照，定到 Yoga 版本 bug 而非属性映射 | 把结论从「改属性写法」改成「升引擎」 |
| Android 图形按比例缩放后边缘像素渲染不全问题排查 | ResizeMode 设置不生效 | 误判动画类型、二次覆盖 drawable bounds、设置属性未标脏三处 | 图片加载原理梳理与代码坏味道清单 |
| 自测用例 | 同上 | — | 同一问题的验收用例 |
| Android 边框宽度无法撑起视图 | Absolute 定位 Border 不一致 | Android 漏写 left/right/bottom 三边的 borderWidth 到 Yoga 节点 | — |
| Android 小米 K80 机型 1px 像素差 | 同上 | 两次 round 作差，对照原生 Yoga 输出 | 确认 RN 同样算法后向上游提 issue 与 PR |

这 8 份的共同点：都给了最小复现与具体到方法名的定位，方案都列了两条并写明取舍，其中两处直接改写了父文档已有的结论。

## 六、待核实

| # | 事项 |
| --- | --- |
| 1 | 三篇标着【已解决】但正文三节全空的（EllipsizeMode 截断省略号、图片重载闪白、Image ResizeMode 三端不一致），本文按标题口径计入已落地，实际修复版本与根因都未核实 |
| 2 | 45 篇里没有一篇记录「哪个版本上线、灰度比例是多少、线上是否还有复现」，所以本文的「已解决」指文档状态，不等于线上状态 |
| 3 | 两篇只有外链单据的问题（image 单边 BorderWidth、on_touch 事件不一致），单据内容未展开，可能已有结论但文档没回写 |
| 4 | Border 那一支两处口径不一致：子文档写「跟随 recce 1.31 修复」，父文档对 1px 差写「建议业务线 hack」，1.31 是否覆盖这一处未核实 |
| 5 | 鸿蒙三篇（下划线间距、Dotted 圆点、圆角压缩）缺陷在鸿蒙侧，本文按「Android 是参照系」纳入 |
| 6 | 排查文档提到的 RN 上游修复（滚动位置保存、滚动动画插值器）未逐条核对 diff 与对应版本号 |
