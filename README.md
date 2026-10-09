# AI-Knowledge

这个目录同时是 Obsidian Vault 和 Codex 项目。入口为 [[99-System/知识库首页|知识库首页]]。

在 Codex 中以本目录为工作目录。确认调研需求后，Codex 按 `AGENTS.md` 完成原任务，并使用项目内 `knowledge-graph-builder` Skill 整理知识。Markdown 保存事实、来源与关系；Obsidian 图谱显示笔记链接。

写入正文、章节、解释和摘要统一使用中文，遵守 [[99-System/调研与分析输出规范]]。默认结构为“结论 → 关键发现 → 证据与分析 → 建议”；详细资料放附录，官方技术名称、代码与机器字段保留原样。

## 开始使用

1. 在 Codex 中打开 `/Users/dudongxu/Desktop/codex/AI-Knowledge`。首次使用新规则时启动一个新聊天，以便加载项目 `AGENTS.md`。
2. 在 Obsidian 打开同一目录，进入 [[99-System/知识库首页|知识库首页]]。如 Obsidian 已打开此库但设置未刷新，重新打开库。
3. 提出调研任务，例如：“调研 Microsoft AutoGen 和 LangGraph 的架构差异，核实当前官方资料。”先确认 Codex 的需求复述；完成后按项目规则归档。
4. 查看 `05-Research` 原始调研、概念/框架笔记及变更摘要，在 Obsidian 侧栏打开图谱。再执行相同调研，检查是否复用旧节点。

若 Skill 未显示，可以明确调用 `$knowledge-graph-builder`；也可以要求读取 `.agents/skills/knowledge-graph-builder/SKILL.md` 执行工作流。未完成一次真实任务验收前，不把技能自动发现、自动归档或图谱渲染称为已验证。

## 目录

| 目录 | 用途 |
| --- | --- |
| `00-Inbox` | 未分类材料、新笔记入口 |
| `01-Concepts` | 概念、协议、机制 |
| `02-Frameworks` | 框架、模型、运行时、开发工具 |
| `03-Architecture` | 架构与技术体系 |
| `04-Comparisons` | 对比、适用条件与取舍 |
| `05-Research` | 调研报告与原始证据摘要 |
| `06-Learning-Gaps` | 资料缺口、待学习建议 |
| `99-System` | 规范、模板、索引、日志、验收 |

## 本地工具

脚本使用 Python 3 和 PyYAML。本次配置时已核实本机 Python 3.11 与 PyYAML 6.0.2 可用。其他环境缺依赖时，可在自己的 Python 环境中安装技能内 `scripts/requirements.txt`；脚本不自动安装依赖。

```bash
python3 .agents/skills/knowledge-graph-builder/scripts/vault_tool.py validate
python3 .agents/skills/knowledge-graph-builder/scripts/vault_tool.py index
```

`validate` 只读，检查链接、名称/别名冲突、必要字段、来源格式和关系结构。它不能判断外部来源是否真实支持一个结论。`index` 只重建两个派生索引，内容无变化时不写文件。索引不能作为独立知识源。

## 自动化范围

已配置当前项目内和跨项目的任务收尾规则。规则依赖 Codex 加载 `AGENTS.md` 并实际执行 Skill，不是后台服务，不保证任意会话都会自动触发。未安装文件监听器。

2026-10-09 已追加全局 `~/.codex/AGENTS.md` 归档规则，并安装用户级 `~/.agents/skills/ai-knowledge-capture`。其他本地项目完成已确认的实质 AI 技术调研后，使用该入口将知识整理到本 Vault；在本 Vault 自身工作时使用项目 knowledge-graph-builder，避免一次任务归档两遍。用户明确不保存、项目规则禁止外部归档或没有实质新增知识时跳过。

全局 config.toml 已将本 Vault 加入 `sandbox_workspace_write.writable_roots`，保留原模式与审批策略。该设置适用于 workspace-write；桌面端受管理权限是否采用它，需在其他项目的新会话核实。规则不能绕过会话实际权限，受阻时会明确报告归档失败。

首次跨项目使用建议重启 Codex，并在其他项目开启新聊天。可要求其列出已加载的 AI-Knowledge 归档规则，或明确调用 `$ai-knowledge-capture`。其他项目 Skill 自动发现、实际自动归档和写入权限仍待真实任务验收；从其他工作目录运行绝对路径校验/索引工具已验证成功。

默认图谱过滤模板与系统文件，按目录给知识节点分组；还没有经过调研核实的知识节点时，图谱可能为空。关系类型保存在 Markdown 的 relationships 字段和解释正文中；原生图谱只显示链接，不给边添加类型标签。

现有 `欢迎.md` 和 `2026-10-09.md` 保留。原 Obsidian 设置见 `99-System/Backups/2026-10-09`，可按需恢复；恢复不会删除知识笔记。

规范见 [[99-System/知识规范]]、[[99-System/关系类型]]，验证状态见 [[99-System/验收记录]]。

官方参考：[Codex Skills](https://learn.chatgpt.com/docs/build-skills)、[AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)、[Obsidian Templates](https://obsidian.md/help/Plugins/Templates)、[Obsidian Graph view](https://obsidian.md/help/Plugins/Graph%2Bview)。
