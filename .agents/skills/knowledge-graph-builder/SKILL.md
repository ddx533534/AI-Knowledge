---
name: knowledge-graph-builder
description: Maintain this technical knowledge vault by archiving original research documents, extracting reusable evidence-backed knowledge, and rebuilding typed relationships and graph views. Use after substantive technical document creation in this vault or for explicit graph maintenance.
---

# 本库知识图谱整理

库根目录为本技能向上三级的目录。适用于所有技术主题；原文副本与知识节点分开维护。具体字段和命令见库根 `99-System/知识规范.md`、`99-System/Templates/知识节点说明.json` 和 `README.md`。

完成原任务后，使用 `tools/knowledge.ps1 capture --source <绝对文档路径> --project <来源项目根目录> --kind research`，复制实际创建的调研/探索/分析文档。已有归档副本不重复 capture；本库工具、规范、备份和派生图谱不归档。

阅读副本，检索旧节点 title、aliases、正文，提取可复用技术知识。使用 capture 返回的文档 ID 与具体章节/行号/页码作为 sources。在 `00-Inbox` 准备 JSON，通过 `node --spec` 创建/更新节点；保留旧来源、人工字段和 AI 区域外正文。不同版本冲突明确记录，不猜测补全。

关系需要已有目标节点、直接证据、中文解释和适用条件。先创建目标，再加关系。未知关系只记待核实，不进入图谱。有关的资料缺口保存在复用的 `06-Learning-Gaps` 中，不推断用户知识水平。

无可复用新增知识时跳过 node，仍执行 `validate` 与 `build`，更新文档视图、三个索引、JSON 与交互 HTML 图谱。提取失败时保留副本并报告失败。有实际变更时追加变更日志；无变化不刷新日期或日志。工具结构检查不能替代证据核实。简短报告副本、节点、关系和失败；知识整理只写本库，不改来源项目、全局配置或外部服务。

## 技术内容准入（2026-10-11 用户明确要求）

归档前必须阅读正文并判断研究对象，不能凭“调研”“总结”“分析”、research/analysis 标记、项目名称或出现代码就收录。

- 仅收录以软件、算法、系统、协议、工程技术或其他技术机制为主要对象，且包含可复查技术证据的调研、探索、架构、技术对比和故障调查文档。
- 非技术性的调研、总结、分析不归档、不提取节点、不进入图谱。明确排除趣味/人格测评的题库与结果文案、叙事身份设计、心理测量与用户访谈方案，以及营销、运营、商业策划和一般内容创作。
- 测评等业务项目中的数据库事务、并发、存储、部署、权限和算法实现研究可收录；业务题材本身不是技术知识。
- 混合文档以主要研究对象判断；非技术文档夹带少量计分规则、脚本或测试记录仍排除。已有独立技术研究文档时仅收录该文档，不为归档另造材料。
- capture 只是复制工具，不负责语义准入；执行者必须先完成上述判断。用户明确要求清理的误收录材料应移出活跃归档、节点及派生视图，并清除悬空引用。
