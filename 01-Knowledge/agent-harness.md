---
{
  "id": "agent-harness",
  "title": "Agent Harness：底层运行机制与业务工作流",
  "aliases": ["Harness", "Agent Harness", "业务 Harness", "研发业务 Harness", "Agent 执行机制"],
  "tags": ["AI", "Agent", "Harness", "工作流"],
  "created": "2026-10-15",
  "last_verified": "2026-10-15"
}
---
# Agent Harness：底层运行机制与业务工作流

整理日期：2026-10-15。

**Harness 是把大模型、工具、上下文和执行规则组织起来，让 Agent 能实际完成任务的执行系统。** 在底层运行机制之上，还可以针对研发等具体任务增加流程控制，把这一层称为「业务 Harness」。后者是本文与用户确认的架构描述，不作为统一的行业术语分类。

## 1. 用最直接的话理解

模型负责判断下一步，工具提供读取文件、执行命令等能力，Harness 负责接住模型的调用、执行工具、回填结果并继续运行。只列出模型和工具，还需要宿主程序把它们接成实际执行过程。[S1]

一个修 bug 的简化循环：

```text
模型判断需要看文件
  → Harness 调用读取工具
  → 工具返回文件内容
  → Harness 把结果交回模型
  → 模型分析后提出修改或测试调用
  → Harness 继续执行并反馈，直到结束或等待外部输入
```

这段循环可以由很少的代码实现；上下文管理、权限、执行记录和恢复能力则让它能承载更复杂的工作。OpenAI 对 Harness 的描述既包含这类执行能力，也有将指令、工具、路由、输出要求与验证检查纳入讨论的用法。因此，Harness 的范围需要结合具体系统说明。[S1][S2]

## 2. 底层 Harness 与业务 Harness

| 层次 | 解决的问题 | 本次讨论中的对应 |
| --- | --- | --- |
| 底层 Harness | 模型怎样调用工具、取得反馈、维持会话并在配置的权限范围内运行 | Codex 的通用 Agent 执行能力 |
| 业务 Harness | 一个业务任务按哪些步骤完成、谁负责、何时审批、失败后回到哪里 | dsh-workflow 中的研发流程控制 |

这种划分依据职责：官方文档描述了由应用掌管业务上下文、规则和工具，由 Codex 提供 Agent 循环及沙箱执行的组合方式。[S1] 将本项目上层称为「研发业务 Harness」，是结合源码作出的架构归纳。

**每个能调用工具并持续工作的 Agent 都需要某种执行机制，但不要求每个 Agent 各有一套独立 Harness。** 多个 Agent 可以由同一套底层系统承载，并各自维护会话。共用运行机制与共用对话上下文是两件事。本项目通过主 Agent 维护声明角色到实际 Agent 实例的映射，并按角色复用子 Agent。[S3]

## 3. 与 dsh-workflow 的具体对应

| 组成 | 职责 | 本地依据 |
| --- | --- | --- |
| 各个子 Skill | 说明需求澄清、设计、编码、审查、测试等步骤怎么做 | 顶层 `SKILL.md` 对子 Skill 的加载约定 |
| 流程模板与运行时 `.workflow.json` | 声明任务、依赖、执行角色、回退条件，并保存进度与历史 | `workflow_template.json`；`saveWorkflow` |
| `engine/loop.js` | 选择任务、组装输入、发出执行指令、记录结果、判定回退与终止 | `findNextTask`、`gatherInput`、`executeHandler`、`checkLoops` |
| 主 Agent | 调用单步引擎，创建或复用子 Agent，传递材料与产出路径，并与用户交互 | 顶层 `SKILL.md` 的执行约定 |
| planner / coder / verifier | 分别执行规划、编码及审查、测试及判定工作 | 模板中的 `executor` 声明 |
| artifacts 与任务 history | 保存产出及每次尝试，供后续步骤使用和回溯 | `processOutput`、任务历史记录逻辑 |

以上对应由模板、入口说明和源码共同支持。[S3][S4][S5]

默认流程为：

```text
需求澄清 → 技术设计 → 测试用例设计 → 编码前审批
  → 编码 → 代码审查 → 跑测试 → 判定

判定 passed=false → 回到编码，默认最多回退 3 次
编码审批被拒绝 → 回到技术设计，默认最多回退 2 次
```

流程由主 Agent 反复调用单步引擎推进。引擎遇到 Skill 或 MCP 任务时发出相应指令，实际的 Agent 创建和工具调用由宿主中的主 Agent 衔接；`loop.js` 本身没有完成这些运行时操作。[S3][S4][S5]

由此可以区分两种循环：coder 读取代码、修改、观察报错，是当前步骤内部的执行过程；从设计转向编码、验证失败后退回编码，是外层业务流程。

**Workflow 描述任务怎样组织；业务 Harness 包含让这套流程实际运行的引擎、调度、规则与记录机制。** 仅有一份步骤清单，还不足以构成这套执行能力。

## 4. 程序强制与文档约束要分清

| 规则 | 当前证据支持的判断 | 依据 |
| --- | --- | --- |
| 验证不通过后回退、达到上限后终止 | 已有引擎逻辑处理 | `checkLoops`、`postTaskSettlement` |
| 编码前进入审批等待 | 正常入口会发出 `NEED_APPROVAL`；后续最小复现确认结果回填入口可绕过审批，因此尚未形成完整门禁 | `step` 的审批与结果回填逻辑 |
| 批准一定来自真实的人 | 入口与规则要求主 Agent 取得用户同意；这段代码读取 `--approve`，并没有独立验证批准者身份 | `step`；`rules.json` 的 R001 |
| 主 Agent 不读仓库、不判断子 Agent 产出质量 | 当前规则标为文档约束，需要执行者遵守 | `rules.json` 的 R002、R005 |

这些边界来自代码与规则文件。[S5][S6] 引擎能控制通过它推进的流程；不能据此推断所有绕过流程的动作都已被权限系统禁止，也不能保证模型的判断、代码或测试结果一定正确。

## 5. 可直接复用的项目表述

> 在 Codex 的 Agent 运行机制之上，构建一套面向研发流程的业务 Harness，管理多 Agent 分工、阶段推进、人工审批、验证回退和过程记录。

这里的「人工审批」是流程设计要求，具体强制程度见上一节。

## 6. 从工程审查补充的可靠性原则

**确定性流程与模型决策可以共存：模型选择恢复方案，程序核验执行条件并管理状态。** 程序可以检查目标、身份、版本、审批和预算；模型对根因的判断仍需要后续验证。

| 可复用原则 | 本次直接证据 |
| --- | --- |
| 结果必须绑定到已派发的任务和尝试，并明确处理重复或过期反馈 | 现有反馈按当前任务接收；重复结果可被下一任务接受。见 `step` 的结果回填分支 [S5] |
| 执行完成、验收通过与流程动作要分别表达，缺少判定字段不能默认成功 | 默认模板缺少输出 schema；漏填 `passed` 不命中严格比较的失败回环。见 [S4][S5] |
| 纠错同时需要回退路径和失败材料；反馈应引用具体产物版本 | code 的依赖不包含测试失败报告，`gatherInput` 不自动补恢复材料。见 [S4][S5] |
| 模型恢复请求与固定规则需要明确优先级，未解决失败不能因恢复请求被拒而自动放行 | 固定 loops 优先；`checkRequestBacktrack` 的非法或耗尽分支会继续推进。见 [S5] |

这些是由源码与最小复现归纳的设计原则，不代表修复已经实现。完整工程案例、复现条件和待确认项见[《dsh-workflow 流程控制与重试机制复盘》](/Users/dudongxu/Desktop/codex/AI-Knowledge/02-Work-Practice/dsh-workflow-流程控制与重试机制复盘.md)。

## 7. 核实范围与待核实事项

- 本次核实方式：阅读官方资料与 dsh-workflow 源码，并补充临时流程和模拟输出的协议级最小复现；没有运行完整真实需求的多 Agent 开发与验证闭环。
- 本地来源项目：`/Users/dudongxu/Desktop/dsh-workflow`；核实时工作区无未提交改动，HEAD 为 `96588aef23a70c3137577b67780319af27f74ece`。这些实现结论限定于该快照。
- 来源发布日期与本次核实日期分别记录，见下方来源；没有将本次对话当作实现已通过运行验证的证据。
- 待核实：目标宿主是否完整兑现子 Agent 会话复用、审批来源验证与工具权限隔离，需要结合宿主实现和实际运行记录另行检查。

## 8. 来源与定位

| 来源 | 发布日期或版本 | 直接支撑的内容 |
| --- | --- | --- |
| [S1 OpenAI：Codex as a platform: build on the open agent harness][S1] | 2026-08-19；2026-10-15 核实 | Agent 执行循环、业务流程及应用与 Codex 的职责划分 |
| [S2 OpenAI：Build an Agent Improvement Loop with Traces, Evals, and Codex][S2] | 2026-05-12；2026-10-15 核实 | 引言对 Harness 范围的说明，包含指令、工具、路由、输出要求和验证检查 |
| [S3 dsh-workflow：工作流入口说明][S3] | 上述本地提交；2026-10-15 核实 | 「How to use」；「Two kinds of id」；「Sub-agent lifecycle」 |
| [S4 dsh-workflow：默认流程模板][S4] | 上述本地提交；2026-10-15 核实 | `phases`、`tasks`、`executor`、`requires_approval`、`loops` |
| [S5 dsh-workflow：单步流程引擎][S5] | 上述本地提交；2026-10-15 核实 | `executeHandler`、`checkLoops`、`postTaskSettlement`、`step` |
| [S6 dsh-workflow：规则声明][S6] | 上述本地提交；2026-10-15 核实 | R001、R002、R005 及各自的 `enforced_by` |

本地源码链接仅供本机复查；站点读者需要取得对应仓库与提交才能复核。本文没有为尚未建立的其他知识节点添加推测关系。

[S1]: https://developers.openai.com/blog/codex-as-a-platform
[S2]: https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop
[S3]: /Users/dudongxu/Desktop/dsh-workflow/verification-workflow-v1/SKILL.md
[S4]: /Users/dudongxu/Desktop/dsh-workflow/verification-workflow-v1/templates/workflow_template.json
[S5]: /Users/dudongxu/Desktop/dsh-workflow/verification-workflow-v1/engine/loop.js
[S6]: /Users/dudongxu/Desktop/dsh-workflow/verification-workflow-v1/rules.json
