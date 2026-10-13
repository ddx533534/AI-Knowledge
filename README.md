# 技术知识库

在 Codex 任意本地项目中创建技术调研、探索或分析文档后，保留原文，并自动复制一份到本库；再提取知识节点和有直接证据的关系。覆盖所有技术主题。

日常阅读从 [首页](首页.md) 进入。目录分工如下：

| 目录 | 用途 |
| --- | --- |
| `01-Knowledge` | 提炼后的技术知识，一个主题一个节点 |
| `03-Work-Practice` | 工作中真实遇到并解决的问题的实践记录 |
| `05-Research` | 与来源版本字节一致的归档文档，一份文档一个文件，外加一份 `manifest.json` 来源清单 |
| `06-Learning-Gaps` | 待补证据与验证问题，合并在一份记录里 |
| `00-Inbox` | 临时工作区，处理完成后清空 |
| `99-System` | 一份生成的 `索引.md`、图谱与规范；维护记录集中在 `Maintenance`，备份在 `Backups` |
| `tools`、`.agents`、`.obsidian` | 工具、技能与编辑器配置 |

## 使用方式

本机知识库路径：`/Users/dudongxu/Desktop/codex/AI-Knowledge`（2026-10-12 由 Windows 机器的 `E:\AI-Knowledge` 迁入，目录结构与内容不变）。完成安装后，在其他项目新建聊天，照常要求调研、架构探索、技术对比或故障分析并生成文档。Codex 的全局规则会要求在任务收尾调用归档技能。

归档文档保存在 `05-Research`，知识节点保存在 `01-Knowledge`。在 Obsidian 打开本目录，从 [[首页]] 浏览；在浏览器打开 `99-System/知识图谱.html`，可搜索、拖动节点、查看带类型的关系与证据来源。

如果只在聊天中回答、没有创建文档，不额外生成文档。用户明确不保存时跳过。同一内容重复归档不新增文件；内容变化时保留新版本，最新版本占用可读文件名，旧版本改挂内容 ID。归档文档保留文档原有的链接，跨项目相对链接与附件不会自动修复或打包；知识节点直接用库内路径指向归档文档。

## 本地工具

核心工具仅依赖 Python 3.10+ 标准库，无需 PyYAML；安装脚本和测试需要 Python 3.11+。`tools/*.ps1` 是 Windows 入口，会寻找可用 Python（含当前 Codex 附带的运行时）；macOS/Linux 直接调用 `tools/knowledge.py`。

```bash
python3 tools/knowledge.py capture --source /path/to/OtherProject/docs/research.md --project /path/to/OtherProject --kind research
python3 tools/knowledge.py node --spec /Users/dudongxu/Desktop/codex/AI-Knowledge/00-Inbox/node.json
python3 tools/knowledge.py validate
python3 tools/knowledge.py build
```

`capture` 复制指定文件，不会自动扫描项目或上传数据；支持 Markdown、文本、PDF、Word 等文件的字节复制，语义提取由 Codex 使用相应读取工具完成。归档文件直接落在 `05-Research/` 下，文件名沿用文档名，来源信息写进 `05-Research/manifest.json`。`node` 接收已阅读证据后的知识说明，维护 AI 区域并保留人工区域。`validate` 检查归档文件完整性、字段、证据定位、名称冲突、链接与关系；不证明技术事实正确。`build` 校验后生成一份 `99-System/索引.md`、`graph.json` 和无外部依赖的 HTML 图谱，内容无变化时不重写文件。

## 安装与迁移

本机安装脚本：`tools/install.py`（Windows 入口为 `tools/install.ps1`，macOS/Linux 用 `python3 tools/install.py`）。它安装用户级技能、追加全局归档规则，并将本库加入 `sandbox_workspace_write.writable_roots`；保留现有配置及权限模式。改动前在用户 Codex 目录内备份全局文件，备份不进入此 Git 仓库。`python3 tools/install.py --check` 只读比对分发源与已部署内容，可用来确认是否需要重新安装。

全局入口源文件位于 `99-System/Distribution`；项目内整理技能位于 `.agents/skills/knowledge-graph-builder`。迁移机器后重新执行安装，路径按本仓库实际位置生成。当前机器与分发源的差异见 `99-System/Maintenance/install-state.json`。

机制依赖 Codex 加载全局规则并执行技能，权限仍受当前会话约束。它不是后台监听器，不能保证任意旧聊天都执行。安装后重启 Codex，在另一个项目的新聊天验证规则加载、技能调用和实际写入。验收状态见 [[99-System/Maintenance/验收记录]]。

官方依据：[全局 AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)、[用户级 Skills](https://learn.chatgpt.com/docs/build-skills)、[额外可写目录](https://learn.chatgpt.com/docs/config-file/config-reference)。

旧库完整备份：`99-System/Backups/2026-10-10-before-rebuild.zip`（保留在 Git 中）。其余备份只留在磁盘，不进入版本库——Git 历史本身已提供版本控制。Git 历史保留；未自动推送远程。

## 技术内容准入（2026-10-11 用户明确要求）

归档前必须阅读正文并判断研究对象，不能凭“调研”“总结”“分析”、research/analysis 标记、项目名称或出现代码就收录。

- 仅收录以软件、算法、系统、协议、工程技术或其他技术机制为主要对象，且包含可复查技术证据的调研、探索、架构、技术对比和故障调查文档。
- 非技术性的调研、总结、分析不归档、不提取节点、不进入图谱。明确排除题库与结果文案、叙事身份设计、心理测量与用户访谈方案、营销、运营、商业策划与一般内容创作。
- 混合文档以主要研究对象判断；非技术文档夹带少量计分规则、脚本或测试记录仍排除。已有独立技术研究文档时仅收录该文档，不为归档另造材料。
- capture 只是复制工具，不负责语义准入；执行者必须先完成上述判断。用户明确要求清理的误收录材料应移出活跃归档、节点及派生视图，并清除悬空引用。
