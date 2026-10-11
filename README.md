# 技术知识库

在 Codex 任意本地项目中创建技术调研、探索或分析文档后，保留原文，并自动复制一份到本库；再提取知识节点和有直接证据的关系。覆盖所有技术主题。

日常阅读从 [首页](首页.md) 进入。目录分工如下：

| 目录 | 用途 |
| --- | --- |
| `01-Knowledge` | 提炼后的技术知识 |
| `05-Research` | 与来源版本字节一致的完整原文 |
| `06-Learning-Gaps` | 待补证据与验证问题 |
| `00-Inbox` | 临时节点说明，处理完成后清空 |
| `99-System` | 索引、图谱与规范；维护记录集中在 `Maintenance`，备份在 `Backups` |
| `tools`、`.agents`、`.obsidian` | 工具、技能与编辑器配置 |

## 使用方式

本机知识库路径：`E:\AI-Knowledge`。完成安装后，在其他项目新建聊天，照常要求调研、架构探索、技术对比或故障分析并生成文档。Codex 的全局规则会要求在任务收尾调用 `$technical-knowledge-capture`。

原文副本保存在 `05-Research`，知识笔记保存在 `01-Knowledge`。在 Obsidian 打开本目录，从 [[首页]] 浏览；在浏览器打开 `99-System/知识图谱.html`，可搜索、拖动节点、查看带类型的关系与证据来源。

如果只在聊天中回答、没有创建文档，不额外生成文档。用户明确不保存时跳过。重复归档不新增副本；文档内容变化时保留新版本。原文副本含原始链接，跨项目相对链接/附件不会自动修复或打包；结构化知识节点使用本库证据链接。

## 本地工具

核心工具仅依赖 Python 3.10+ 标准库，无需 PyYAML；安装脚本和测试需要 Python 3.11+。Windows 入口会寻找可用 Python，包括当前 Codex 附带的运行时。

```powershell
& E:\AI-Knowledge\tools\knowledge.ps1 capture --source E:\OtherProject\docs\research.md --project E:\OtherProject --kind research
& E:\AI-Knowledge\tools\knowledge.ps1 node --spec E:\AI-Knowledge\00-Inbox\node.json
& E:\AI-Knowledge\tools\knowledge.ps1 validate
& E:\AI-Knowledge\tools\knowledge.ps1 build
```

`capture` 复制指定文件，不会自动扫描项目或上传数据；支持 Markdown、文本、PDF、Word 等文件的字节复制，语义提取由 Codex 使用相应读取工具完成。`node` 接收已阅读证据后的知识说明，维护 AI 区域并保留人工区域。`validate` 检查副本完整性、字段、证据定位、名称冲突、链接与关系；不证明技术事实正确。`build` 校验后生成索引、JSON 和无外部依赖的 HTML 图谱，内容无变化时不重写文件。

## 安装与迁移

本机安装脚本：`tools/install.ps1`。它安装用户级技能、追加全局归档规则，并将本库加入 `sandbox_workspace_write.writable_roots`；保留现有配置及权限模式。改动前在用户 Codex 目录内备份全局文件，备份不进入此 Git 仓库。

全局入口源文件位于 `99-System/Distribution`；项目内整理技能位于 `.agents/skills/knowledge-graph-builder`。迁移机器后重新执行安装，路径按本仓库实际位置生成。

机制依赖 Codex 加载全局规则并执行技能，权限仍受当前会话约束。它不是后台监听器，不能保证任意旧聊天都执行。安装后重启 Codex，在另一个项目的新聊天验证规则加载、技能调用和实际写入。验收状态见 [[99-System/Maintenance/验收记录]]。

官方依据：[全局 AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)、[用户级 Skills](https://learn.chatgpt.com/docs/build-skills)、[额外可写目录](https://learn.chatgpt.com/docs/config-file/config-reference)。

旧库完整备份：`99-System/Backups/2026-10-10-before-rebuild.zip`。Git 历史保留；未自动推送远程。

## 技术内容准入（2026-10-11 用户明确要求）

归档前必须阅读正文并判断研究对象，不能凭“调研”“总结”“分析”、research/analysis 标记、项目名称或出现代码就收录。

- 仅收录以软件、算法、系统、协议、工程技术或其他技术机制为主要对象，且包含可复查技术证据的调研、探索、架构、技术对比和故障调查文档。
- 非技术性的调研、总结、分析不归档、不提取节点、不进入图谱。明确排除趣味/人格测评的题库与结果文案、叙事身份设计、心理测量与用户访谈方案，以及营销、运营、商业策划和一般内容创作。
- 测评等业务项目中的数据库事务、并发、存储、部署、权限和算法实现研究可收录；业务题材本身不是技术知识。
- 混合文档以主要研究对象判断；非技术文档夹带少量计分规则、脚本或测试记录仍排除。已有独立技术研究文档时仅收录该文档，不为归档另造材料。
- capture 只是复制工具，不负责语义准入；执行者必须先完成上述判断。用户明确要求清理的误收录材料应移出活跃归档、节点及派生视图，并清除悬空引用。
