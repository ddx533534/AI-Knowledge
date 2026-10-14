# Android 跨端不一致问题：解法清单

核实日期：2026-10-13；第四章的机制与业界对照补于 2026-10-14。材料：《99.不一致性问题》45 篇子文档中 Android 相关的 32 篇（读取日期 2026-10-13），加上本人撰写、挂在其中 6 篇问题下的 8 份排查文档。

32 篇里 29 篇能归到下面五组；另 3 篇（EllipsizeMode 截断省略号、图片重载闪白、Image ResizeMode 三端不一致）标着【已解决】而正文的「原因 / 解决 / Hack」三节全空，给不出解法，见第六章。

问题一律用简称，版本号、机型、代码照抄原文未复算。「通道」是本文的分析结构，不是文档原文；45 篇的标题都带状态标签（【已解决】/【待解决】/【Hack】），本文一律按正文实际内容判断，不采信标题。

第四章的业界对照只用公开上游来源（Yoga / AOSP / React Native / RNGH / AndroidX 源码与规范），每条附链接可点开复核；与 Recce 自身实现的对应关系凡未核实的都写在第六章。

## 一、一张表看完：三个问题，四条通道

![图 1：拿到一个不一致问题，按顺序问三个问题，落到四条通道上。判断一「换一份同一版本引擎的原生 demo 还能复现吗」，能复现走升级通道；判断二「框架侧是不是已经写明不改」，是就走换写法通道；判断三「根因写出来了吗」，没写走自己补定位，写了但没版本落点就走先 hack 后等版本。](fig1-routes.svg)

| 通道 | 判据 | 条数 | 你要做的动作 | 谁动手 |
| --- | --- | --- | --- | --- |
| 升级即解 | 布局、属性、事件类问题；换一份同版本引擎的原生 demo 就能复现 | 11 | 升 Recce Native SDK / wasm 到 2.1 里的版本号，业务代码一行不改 | 框架侧发版 |
| 换写法 | 框架侧已有明确结论：与 RN 一致，或 Android 原生即如此 | 3 | 照第 3 章改业务代码，不要等版本 | 业务 |
| 先 hack，后等版本 | 已定位到源码，但修复没有版本落点；或 Native 修了也覆盖不到旧版本 | 4 | 先用第 3 章的 hack 顶上，同时把版本推进排期 | 双方 |
| 自己补定位 | 只有现象与录屏，原因一节是空的 | 8 | 走完「最小复现 → 读源码 → 给两条带代价的路」 | 谁遇到谁补 |

三个问题按表里的顺序问，不要跳 —— 尤其第 2 问，最容易白等版本。另有 3 条已定位、但要修在框架的 Java 层且各有两条路（2.2），不走这四条通道。

**一条能带走的判断**：升级版本是唯一能一次解掉一批问题的杠杆。1.31 与 1.32 两次跟 Yoga，一次消化掉 absolute 无法隐藏、三边 borderWidth 撑不起视图、display:none 与 absolute 共存的性能问题；1.32 同一轮又修掉 AlignSelf 相反、ResizeMode 系列、visible_area_change 数据异常。收益来自引擎本身，不是某一个属性。

## 二、解法清单

四组按「谁动手」排，从最省事的开始；2.5 是还没有解法的，写清缺哪一步。第三列写根因落在代码的哪一层 —— 它决定了修法能不能搬到别的属性上。

![图 2：按现象找解法。六行映射，左列是看到的现象，中列是定位第一步，右列是解法动作与落点。宽高不对先在同版本原生 demo 上复现；隐藏后状态丢失先查 display:none 链上的尺寸派生量；两端属性相反要拿 RN 当第三参照；点不到先分清命中由谁决定；只在某机型出现要换成结构性条件；事件数据与单位不对就查默认值、取值域、单位、参照系四件事。](fig2-map.svg)

### 2.1 升级版本就解掉，业务代码不用改（11 条）

| 问题 | 怎么修 | 根因落点（代码级） | 落点 |
| --- | --- | --- | --- |
| absolute 定位无法用 visible 隐藏 | 借用的 Yoga ≤1.18 有这个 bug，3.2.1 正常。用同一段代码在两版引擎上对照即可确认 | 引擎自身的绝对定位计算路径，上游 PR #1068 修的正是这里 | 自打包 Yoga 3.2.1，Recce 1.31 落地 |
| 三边 borderWidth 撑不起视图（Absolute 定位 Border 不一致） | Android 设置 borderWidth 时漏写 left/right/bottom 三个维度到 Yoga 节点，补上这三边的写入 | 样式 → Yoga 节点的写入层，只写了 top 一边 | Recce 1.31 |
| display:none 与 absolute 同用时布局变慢 | 老 Yoga 在「absolute + display:none + 子视图多」时性能差，跟 Yoga 版本更新 | display:none 走的「整棵子树归零」重算（见 4.1） | Recce Native 1.32 更新 Yoga |
| AlignSelf::FlexEnd / Center 双端相反 | Recce 解析时把 FlexEnd 与 Center 设置反了一次，iOS 又反一次，两次抵消后只有 Android 是错的；修 Android 侧的解析 | Recce 自己的样式解析层，不在引擎 | Recce Native 1.32 |
| ResizeMode 设置不生效、动态改属性无效 | 三处一起改：普通图被误判成动画类型；设置数据源后又按图片原始尺寸覆盖一次绘制边界，Stretch 因此失效；改 ResizeMode 没把图片标脏。做法是把图片类父子关系解绑、抽出公共基类重构 | 图片组件的类型判定、边界计算、脏标记三处 | Recce 1.32；业务亟需可在 1.30 上发小版本，需重点回归图片能力 |
| 双端 ResizeMode 默认值不一致 | 对齐双端默认值 | 双端各自把默认值写死在绘制层（业界参照值是 `cover`，见 4.2） | Recce Native 1.32 |
| 1.32 以下 visible_area_change 数据异常 | 两个 rect 各坏一个；返回值单位是 px 不是 dp；is_intersecting 双端参照系不同（Android 相对屏幕、iOS 相对 scroll_view） | 几何数据产出的三件事：rect、单位、参照系 | Recce Native 1.32 |
| 同层组件被 display:none 后无法布局 | 宿主宽度被置 0 → Recce 按 0 渲染 → 内部自适应把高度撑大 → 与宿主互相触发布局成死循环。Native 侧修，切 tab 渲染错误随之解掉 | 零尺寸进入布局后又反算出新尺寸，形成回环 | 跟宿主 12.29.400：2.5 集成 / 2.20 回归 / 2.25 全量 |
| 分辨率变更时页面尺寸渲染错误 | DisplayMetricsHolder 缓存了 DisplayMetrics，宽高与 margin 的像素换算全走这份缓存；改成 RecceRootView 销毁时清缓存 | 像素换算的缓存生命周期 | 已修，测试包 |
| 交叉检查器偶现 crash | 删除节点从父节点开始，子节点被删后仍触发曝光回调，向上查找时命中空指针；加判空 | 节点销毁与曝光回调的时序 | Recce Native 发版 + 宿主 12.59.200 起 |
| MaxWidth/MaxHeight 的 undefined 被当成 0 | undefined 类型没被解析，值 0 被当最大宽高写进节点。分两层修：Native 与 iOS 一样解析该类型（**覆盖不到旧版本**）；recce_ui 侧把 undefined 的值由 0 改成 NaN，让下游无法把 0 当有效值用（**能覆盖大部分流量**） | 属性解析层把「未定义」丢了（业界表示法是 NaN，见 4.1） | Native 发版 + recce_ui 发版 |

### 2.2 要在框架的 Java 层动刀，每条都有代价（3 条）

三条都是本人排查产出，各给两条路，取舍一并列出。

| 问题 | 怎么修 | 根因落点（代码级） | 代价与注意 |
| --- | --- | --- | --- |
| scroll_view 隐藏再显示后滚动位置被重置 | 改两处：ScrollView 的 onLayoutChange 里加「子布局宽高为 0 就跳过」的判断，不要在这个状态下写回位置；HorizontalScrollView 压根没保存过位置，补上与 ScrollView 一致的保存逻辑 | 布局回调在子视图还是 0×0 时就把位置写回去了 | 滚动动画进行中同时发生布局变化时，理论上可能直接跳到目标位置、动画失效；RN 最新版采取了类似处理（`isContentReady()`，见 4.1） |
| 连续调用 scroll_to 动画失效 | 根因是 smoothScrollBy 距上次滚动不足 250ms 时中止动画、改走 scrollBy（表现上等于 animated 被当成 false）。两条路：① 重写 smoothScrollBy，把间隔缩短到 100ms 或干脆取消间隔、每次先取消上一次动画；② 抄 RN 的做法，不再依赖 OverScroller，改用自定义插值器、两个滚动组件共用一套逻辑 | AOSP `ScrollView.smoothScrollBy` 里的 `ANIMATED_SCROLL_GAP = 250`，且该方法是 `final` | ① 成本极低、效果符合预期，但改的是系统源码，`mFlingSpan` 那部分够不到，且 100ms 是否够用要看场景；② 精确可控、易调试，但改动大、成本高。RN 实际走的就是 ②（见 4.1） |
| 子元素溢出父元素无法点击 | 事件自上而下分发，中间那层容器判定「子树不含触点」就不再往下走。两条路：① TouchDelegate 把父容器热区代理给子视图；② 重写 dispatchTouchEvent 与 onInterceptTouchEvent 自己分发 | 原生命中判定只认子视图自身的 bounds（`ViewGroup.isTransformedTouchPointInView` → `child.pointInView`），溢出部分天然落空 | ① 需要 recce-ui 新增设置触摸代理的方法；② 所有能当父容器的 view 都会受影响，影响面大。上游有第三条路（见 4.2） |

### 2.3 框架的结论是「不改」，换业务侧写法（3 条）

| 问题 | 为什么框架不改 | 业务侧怎么写 |
| --- | --- | --- |
| 父级 opacity 表现不一致 | iOS 用 CALayer.opacity 整体应用，Android 用 View.alpha 让每个子视图先各自渲染再合并；Android 的行为与 RN 一致，改它反而离参考标准更远 | 要背景透明就把透明度写进颜色（`BackgroundColor::argb`）；要整体透明用同色遮罩层模拟 |
| input placeholder 折行 | Android 原生就是这个效果，文档给的原生等价实现可以复现 | 自实现一层 placeholder：label 绝对定位叠在 input 上，文本为空时显示 |
| scroll_view 拦截子视图 on_click | Android 把这段手势识别为滑动、不响应点击，旧版本无法解决，native 侧不动 | 升级到 Recce 1.22+ / rust-recce 0.11+ 后改用框架层的 on_touch_end（touch 事件由框架自己做，绕过 native 手势识别）；旧版本用 rui 的 event_bus 直接派发事件，不走 click 冒泡 |

### 2.4 已定位，但还没有版本落点，先按 hack 做（4 条）

| 问题 | 定位到哪一步 | 现在怎么做 | 后续解法 |
| --- | --- | --- | --- |
| 部分机型 Label 裁最后一个字 | 只有现象与最小复现，原因一节为空；机制上属机型默认字体的度量差异 | 给 label 显式指定字体：`FontFamily::new("system")` | 待定位 |
| 1.32 的 foreground 回调触发不稳定 | 只写了「Native 修复」，根因未写；对应的是 Native 侧没接 Android 生命周期回调 | 用 appear 事件代替；或用 `can_i_use::android_foreground()` 判断后订阅 MSI 的 onAppStatusChange 广播 | Native 修复；业界正解是接 `ProcessLifecycleOwner`（见 4.2） |
| env 屏幕参数双端不一致 | 根因清楚：Android 的 display_width/height 实际是 window 值，且双端都没传 window 尺寸；窗口值与屏幕值本就是两套量 | 用 MSI 桥自己取 window 尺寸 | Native 修复；业界做法见 4.2 |
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

九段写法，先看撤掉条件，再往下抄：

| # | 写法 | 什么时候可以撤掉 |
| --- | --- | --- |
| 3.1 | 隐藏 scroll_view 又不丢滚动位置 | ScrollView 的位置保存逻辑随版本发出后 |
| 3.2 | 图片 ResizeMode 不生效 | 升到 1.32 |
| 3.3 | MaxWidth/MaxHeight 用了 undefined | 所在 App 版本的 Native 解析了 undefined 类型之后 |
| 3.4 | 部分机型 Label 裁最后一个字 | 待定位，长期保留 |
| 3.5 | foreground 回调触发不稳定 | Native 修复后 |
| 3.6 | env 取不到 window 尺寸 | Native 补传 window 尺寸后 |
| 3.7 | 1.32 以下的 visible_area_change | 升到 1.32 |
| 3.8 | input placeholder 折行 | 框架不改，长期保留 |
| 3.9 | 父级整体透明 | 框架不改，长期保留 |

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

图片本来就是异步加载、从无到有，所以额外刷一次高度没有副作用。

### 3.3 MaxWidth/MaxHeight 用了 undefined

不要用 `undefined`，Android 会把它的值 0 当成最大宽高。需要「不限宽」时给一个极大值：

```rust
MaxWidth::number(200.)  Height::number(500.)  Width::auto()

{toggle}.map(|v| match *v {
  true  => MaxWidth::number(99999.),   // 等价于「不限」，不要写 undefined
  false => MaxWidth::number(200.),
})
```

适配所有版本，代价是不美观。

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

## 四、技术思路与业界方案

上面给的是「怎么修」，这一章补三件事：根因落在代码哪一层、上游在同一位置怎么实现、有没有现成更优的路。出处全部是公开上游源码与规范（2026-10-14 抓取）。

### 4.1 四条值得记住的机制

**① display:none 在 Yoga 里就是「整棵子树归零」。** 上游源码中 `Display::None` 走 `zeroOutLayoutRecursively()`：把该节点 layout 清空、宽高显式置 0、标记 `hasNewLayout`，然后**递归**对全部子节点做同样的事。所以「隐藏 = 自身与所有子视图变 0×0」是引擎的官方语义，不是 Android 端的怪癖 —— 五章第一条通则的问题根在这里。同一处历史上与 absolute 定位冲突（绝对定位又算出真实尺寸，盖掉了 0×0），上游由 PR [#1068](https://github.com/facebook/yoga/pull/1068) 修复。出处：[CalculateLayout.cpp 的 zeroOutLayoutRecursively](https://github.com/joevilches/yoga/blob/2b08ba4eff24d1155c29aeb7b4dacb70aaa0a1c2/yoga/algorithm/CalculateLayout.cpp)。

**② 「未定义」的正规表示是 NaN，不是 0。** `YGUndefined` 的定义就是 `quiet_NaN()`；现代 Yoga 把尺寸包成 `StyleSizeLength` / `StyleLength`（`FloatOptional` + `Unit`），`undefined()` 是一个合法状态，传入 NaN 会被归一成 `Unit::Undefined`。也就是说「不限宽」在这套类型系统里有位置，被解析成 0 属于解析层丢了信息 —— 2.1 最后一条那个「把 0 改成 NaN」的兜底，方向与上游一致。出处：[YGValue.h](https://raw.githubusercontent.com/facebook/react-native/main/packages/react-native/ReactCommon/yoga/yoga/YGValue.h)、[StyleSizeLength.h](https://raw.githubusercontent.com/facebook/react-native/main/packages/react-native/ReactCommon/yoga/yoga/style/StyleSizeLength.h)；另注 `YGFloatOptional` 已改名 `FloatOptional`（[#39196](https://github.com/facebook/react-native/issues/39196)）。

**③ ScrollView 的 250ms 有两个来源，而且方法不可重写。** AOSP `ScrollView.smoothScrollBy` 声明为 `public final`（子类改不了），函数体里 `ANIMATED_SCROLL_GAP = 250`：距上次滚动 ≤250ms 时直接 `mScroller.abortAnimation()` 再 `scrollBy`，表现上正是「animated 被当成 false」；`OverScroller.DEFAULT_DURATION` 同样是 250。出处：[ScrollView.java](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/master/core/java/android/widget/ScrollView.java)、[OverScroller.java](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/master/core/java/android/widget/OverScroller.java)。这解释了 2.2 第二条为什么「改系统源码」那条路够不到 `mFlingSpan` 以外的东西。

**④ RN 对③选的是「不用 OverScroller」，而且装的是普通插值器。** RN 的 `ReactScrollViewHelper.smoothScrollTo` 不走 `smoothScrollTo`，而是对 `scrollY` 起一个 `ObjectAnimator`（`defaultFlingAnimator`），时长由 `OverScrollerDurationGetter` 反射读 AOSP 默认值兜底；`ReactScrollView` 里明确注释「`smoothScrollTo` is final，所以我们另开 `reactSmoothScrollTo`」。**注意 RN 并没有设置自定义 `Interpolator`**，用的是 ObjectAnimator 默认的加速减速 —— 2.2 第二条的路 ② 落到代码上就是这个形态，不必自己写插值器。出处：[ReactScrollView.kt](https://raw.githubusercontent.com/facebook/react-native/main/packages/react-native/ReactAndroid/src/main/java/com/facebook/react/views/scroll/ReactScrollView.kt)、[ReactScrollViewHelper.kt](https://raw.githubusercontent.com/facebook/react-native/main/packages/react-native/ReactAndroid/src/main/java/com/facebook/react/views/scroll/ReactScrollViewHelper.kt)。

**⑤ 「宽高为 0 就不写回滚动位置」是 RN 的既有实现。** `ReactScrollView.onLayout` 只在 `isContentReady()` 为真时才滚到 pending 值，而 `isContentReady()` 的实现就是 `child != null && child.width != 0 && child.height != 0`；内容未就绪时目标位置被暂存为 pending。该逻辑由 commit [4846f1b](https://github.com/facebook/react-native/commit/4846f1bf18636e3b22bd4ddb72e9adeb156313ae) 引入、[be260b9](https://github.com/facebook/react-native/commit/be260b9f479a3b55ee43d2959d2c49fd3c1eb4ac) 修过，iOS 侧 [47903d0](https://github.com/facebook/react-native/commit/47903d0c62de9399a5cd0993a59e4af0bdea4f0c) 是明确对齐 Android 的对等实现。2.2 第一条的修法与它同源。

### 4.2 业界在同一位置怎么做

| 我们这件事 | 上游/业界现在的做法 | 差异在哪 | 能不能借鉴 |
| --- | --- | --- | --- |
| 子元素溢出父元素点不到（2.2 第三条） | RN 另建了一层命中判定：`TouchTargetHelper` 自根向下 DFS，逐层判 pointerEvents 四个值、hitSlop、overflow 与 clipChildren、transform 矩阵求逆；原生分发照旧。专门修「父容器外的子视图可点」的上游 commit 是 [e35a963](https://github.com/facebook/react-native/commit/e35a963bfb9)（#29039） | 我们动的是 Android 原生分发链（dispatchTouchEvent / onInterceptTouchEvent）；RN 不动原生分发，只在「事件该给谁」这一层自己算 | 值得。RN 那层是独立的纯判定函数，改动面收在一个文件里，不必替所有能当父容器的 View 兜底 —— 正是路 ② 的风险所在。代价是自己维护一套与 pointerEvents / hitSlop / overflow / transform 对齐的判定，并跟着属性协议演进。出处：[TouchTargetHelper.kt](https://raw.githubusercontent.com/facebook/react-native/main/packages/react-native/ReactAndroid/src/main/java/com/facebook/react/uimanager/TouchTargetHelper.kt) |
| 父容器抢手势（2.3 第三条） | RNGH 3.3.0 的 `NativeViewGestureHandler`：用 `view.onInterceptTouchEvent()` 判断是否该激活，包裹时调 `requestDisallowInterceptTouchEvent(true)`，子手势再用 `blocksExternalGesture` 反向压制父滚动容器；「可否被抢占」由 `disallowInterruption` 显式声明 | 我们用 rui 的 event_bus 直接派发事件，绕过 native 手势识别 | 借它的判据而不是实现：「父容器可否被抢」应该是子视图声明出来的属性，而不是靠换一条事件通道绕过去。我们升到 on_touch_end 已是同一方向。出处：[RNGH Native gesture](https://docs.swmansion.com/react-native-gesture-handler/docs/gestures/native-gesture/) |
| 前后台状态（2.4 foreground） | RN 的 `AppStateModule` 实现 `LifecycleEventListener`（onHostResume→active、onHostPause→background）与 `WindowFocusChangeListener`；Android 官方推荐的「整个应用前后台」判据是 `androidx.lifecycle.ProcessLifecycleOwner` + `DefaultLifecycleObserver`，`ON_STOP` 会延迟 700ms 派发以覆盖配置变更引起的 Activity 重建 | 我们退到订阅 MSI 广播 | 值得。ProcessLifecycleOwner 的语义就是整个进程的前后台，比订阅广播稳；注意它在多进程下不知道其他进程，也不追求毫秒级精度。出处：[AppStateModule.kt](https://raw.githubusercontent.com/facebook/react-native/main/packages/react-native/ReactAndroid/src/main/java/com/facebook/react/modules/appstate/AppStateModule.kt)、[ProcessLifecycleOwner.kt](https://raw.githubusercontent.com/androidx/androidx/androidx-main/lifecycle/lifecycle-process/src/main/java/androidx/lifecycle/ProcessLifecycleOwner.kt) |
| env 的窗口尺寸（2.4 第三条） | Android 官方口径：多数场景用 `getCurrentWindowMetrics()`（API 30+，非全屏也正确），返回的 bounds **不扣除** WindowInsets 需自减，密度取 `Configuration#densityDpi`；`Display.getSize` / `getRealSize` 分别自 API 30 / 31 弃用。RN 的 `DeviceInfoModule` 走 Jetpack `WindowMetricsCalculator.computeCurrentWindowMetrics`，取不到才回落 `resources.displayMetrics`，屏幕尺寸另走 `screenPhysicalPixels` | 我们只下发了一套值，取到的是 window 值却当屏幕值用 | 值得。窗口与屏幕本就是两套量，上游是分开下发的。出处：[WindowManager](https://developer.android.com/reference/kotlin/android/view/WindowManager)、[多窗口适配](https://developer.android.google.cn/develop/ui/views/layout/support-multi-window-mode)、[DeviceInfoModule.kt](https://raw.githubusercontent.com/facebook/react-native/main/packages/react-native/ReactAndroid/src/main/java/com/facebook/react/modules/deviceinfo/DeviceInfoModule.kt) |
| 1px 边框与三边 borderWidth（2.1） | RN 在 Android 不做特殊取整：`borderWidth` 经 `PixelUtil.toPixelFromDIP`（`TypedValue.applyDimension`）直接转像素，不 ceil / round；但 RN 在 `PixelRatio.js` 里写明「一个取整误差就足以让 1 像素边框消失或变成两倍宽」，并给业务侧提供 `PixelRatio.roundToNearestPixel()` | 我们错在布局层（三边没写进 Yoga 节点），RN 的坑在绘制层的像素取整 | 两者互补：布局层四边都要写全，样式层按 `roundToNearestPixel` 取整。**npm 上并没有 `react-native-hairline` 这类包（registry 返回 Not Found）**，社区文章里的包名不要照抄。出处：[PixelUtil.kt](https://raw.githubusercontent.com/facebook/react-native/main/packages/react-native/ReactAndroid/src/main/java/com/facebook/react/uimanager/PixelUtil.kt)、[PixelRatio.js](https://raw.githubusercontent.com/facebook/react-native/main/packages/react-native/Libraries/Utilities/PixelRatio.js) |
| 图片 ResizeMode（2.1） | RN Android 侧可选值是 `contain/cover/stretch/center/repeat/none`（映射到 Fresco ScaleType），绘制层默认 `CENTER_CROP`，JS 层两端默认值都是 `'cover'` | 我们双端默认值不一致；Android 侧取值域也更窄 | 默认值直接对齐 `cover`；取值域差异写进属性协议（缺 fit_start / fit_end 属取值域问题，RN 也没有这两个值）。出处：[ImageResizeMode.kt](https://raw.githubusercontent.com/facebook/react-native/main/packages/react-native/ReactAndroid/src/main/java/com/facebook/react/views/image/ImageResizeMode.kt)、[Image.android.js](https://raw.githubusercontent.com/facebook/react-native/main/packages/react-native/Libraries/Image/Image.android.js) |
| 双端无障碍（2.4 第四条） | RN 的 `accessible` 在 Android 翻译成原生 `focusable`、iOS 翻译成 `isAccessibilityElement`；`accessibilityElementsHidden`（iOS）与 `importantForAccessibility="no-hide-descendants"`（Android）等价；`aria-hidden={true}` 在源码里就是同时写这两个 | 我们两端各写各的，语义分散在业务里 | 值得。把平台差异收进框架层翻译，业务侧只表达「要不要被辅助服务看见」。出处：[RN 无障碍](https://reactnative.dev/docs/accessibility)、[View.js](https://raw.githubusercontent.com/facebook/react-native/main/packages/react-native/Libraries/Components/View/View.js) |

曝光与可见性那一条不在这里展开，见《RN-IntersectionObserver-与-Recce-曝光方案对比》；布局引擎的选型见《Recce-Yoga-升级方案复盘》。

## 五、三条通则

- **差异未必是「一端对一端错」**。AlignSelf 是 Recce 解析反一次、iOS 又反一次，两次抵消后只有 Android 错 —— 只看两端结果会把根因判错。定位跨端差异要拿 RN 的行为当第三参照。
- **Android 的「隐藏」是一次真实的布局塌缩**。display:none 按引擎语义就是自身与整棵子树归零（4.1 ①），滚动位置、自适应高度、传给宿主的组件尺寸这些从尺寸派生的量都会被这个 0 污染。原始材料记「Android 会展开到全部子视图、iOS 只改自身」，按引擎语义 Android 才是标准行为，iOS 那一侧是否属实现偏差未核实（见第六章第 7 条）。凡「隐藏后再显示状态丢失」，先查这条链，不要先怀疑隐藏属性的实现差异。
- **属性协议要写清四件事**，这批问题里四件各出过一次：默认值（双端 ResizeMode 默认值不一致）、取值域（Android 侧 ResizeMode 只支持四个值，fit_start/fit_end 没有）、单位（1.32 以下 interactionClientRect 返回 px 而不是 dp）、参照系（同一次曝光，Android 相对屏幕、iOS 相对 scroll_view）。机型类差异的 hack 全是「显式声明」，修的时候要把「依赖某个机型默认值」换成结构性条件，否则换机型就复发。

## 六、待核实

| # | 事项 |
| --- | --- |
| 1 | 三篇标着【已解决】但正文三节全空的（EllipsizeMode 截断省略号、图片重载闪白、Image ResizeMode 三端不一致），本文按标题口径计入已落地，实际修复版本与根因都未核实 |
| 2 | 45 篇里没有一篇记录「哪个版本上线、灰度比例是多少、线上是否还有复现」，所以本文的「已解决」指文档状态，不等于线上状态 |
| 3 | 两篇只有外链单据的问题（image 单边 BorderWidth、on_touch 事件不一致），单据内容未展开，可能已有结论但文档没回写 |
| 4 | Border 那一支两处口径不一致：子文档写「跟随 recce 1.31 修复」，父文档对 1px 差写「建议业务线 hack」，1.31 是否覆盖这一处未核实 |
| 5 | 鸿蒙三篇（下划线间距、Dotted 圆点、圆角压缩）缺陷在鸿蒙侧，本文按「Android 是参照系」纳入 |
| 6 | 排查文档提到的 RN 上游修复（滚动位置保存、滚动动画插值器）未逐条核对 diff 与对应版本号；第四章已补上首批核对结果（4846f1b / be260b9 / 47903d0），其余未核 |
| 7 | 第四章的业界做法取自公开上游源码，与 Recce 自身实现的对应关系未逐处核实。例如 iOS 侧的 display:none 是否也按引擎语义做「子树归零」未确认；按 Yoga 官方语义应当一致，若不一致则属 Recce 的 iOS 实现偏差 |
| 8 | 1px 边框那一支的「小米机型」成因未核实：上游只给了「绘制层像素取整误差」这一个通用解释，没有按机型区分的官方说明，本文未把两者绑定 |
