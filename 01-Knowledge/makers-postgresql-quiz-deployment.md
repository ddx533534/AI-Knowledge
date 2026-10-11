---
{
  "id": "makers-postgresql-quiz-deployment",
  "title": "Makers与PostgreSQL的趣味测评部署边界",
  "type": "architecture",
  "status": "partial",
  "last_verified": "2026-10-11",
  "sources": [
    {
      "document_id": "22bbe9b15acb13a5a04d8ddb9deb40ee15e4a773c4f132edfc39a4d0416cc6da",
      "locator": "第1—2节：官方免费套餐、域名与数据库连接边界；第3—5节：函数适配、验证与待验收项"
    },
    {
      "document_id": "b8f58a8d9d319b771b81f7654b80549dbcac660994a0c7b27c8ee31ed01aebbb",
      "locator": "第1—3节：接受的Blob并发边界、SDK条件写限制和数据组织；第4—6节：固定算法、配置与实测范围"
    }
  ],
  "relationships": [
    {
      "target": "transactional-access-code-quota",
      "type": "uses",
      "explanation": "Makers函数复用同一FastAPI后端，以PostgreSQL事务预留和扣次；本地实现已测试，云端联调待验证。",
      "sources": [
        {
          "document_id": "22bbe9b15acb13a5a04d8ddb9deb40ee15e4a773c4f132edfc39a4d0416cc6da",
          "locator": "第1—2节：官方免费套餐、域名与数据库连接边界；第3—5节：函数适配、验证与待验收项"
        }
      ]
    },
    {
      "target": "deterministic-narrative-result-generation",
      "type": "uses",
      "explanation": "构建仅打包固定Python评分引擎、题库及结果库，随机会话或分享链接不参与文学身份生成。",
      "sources": [
        {
          "document_id": "22bbe9b15acb13a5a04d8ddb9deb40ee15e4a773c4f132edfc39a4d0416cc6da",
          "locator": "第1—2节：官方免费套餐、域名与数据库连接边界；第3—5节：函数适配、验证与待验收项"
        }
      ]
    },
    {
      "target": "hong-kong-assessment-stack",
      "type": "alternative_to",
      "explanation": "在免费试运行且实际数据库网络可达的条件下，Makers函数可替代租用香港应用服务器；自有域名及生产验收仍必需。",
      "sources": [
        {
          "document_id": "22bbe9b15acb13a5a04d8ddb9deb40ee15e4a773c4f132edfc39a4d0416cc6da",
          "locator": "第1—2节：官方免费套餐、域名与数据库连接边界；第3—5节：函数适配、验证与待验收项"
        }
      ]
    }
  ],
  "aliases": [
    "Makers免费测评网站",
    "EdgeOne与CloudBase测评部署"
  ],
  "tags": [
    "Makers",
    "CloudBase",
    "Supabase",
    "PostgreSQL",
    "大陆访问"
  ],
  "schema_version": 2,
  "created": "2026-10-11T15:09:45.444727+08:00",
  "updated": "2026-10-11T17:56:50.421364+08:00"
}
---
# Makers与PostgreSQL的趣味测评部署边界

<!-- AI:BEGIN -->
## 结论

历史Makers/FastAPI与PostgreSQL方案依赖事务型额度账本和数据库连接；本地实现已验证，云端连接未验收。2026-10-11用户接受并发偏差后，当前项目已改用Node/Blob，该节点保留数据库架构的条件与历史证据。

## 关键发现

- Makers可用ASGI模式，平台去除/api前缀，本项目以本地测试适配恢复。
- 官方域名规则明确大陆预览3小时，境外加速区域绑定自有域名可不做ICP备案。
- CloudBase有PG协议与免费环境额度/续期条件，实际Makers区域到数据库的网络仍需验证。
- 生产后端不接受SQLite，浏览器不接触数据库密钥或码账本。
- 现行项目已替换为Node/Blob，无需DATABASE_URL或数据库迁移；原事务保证不适用于Blob版。

## 证据与分析

首版实施记录支持Makers/Python/PG的设计和本地测试边界；新Blob实施记录第1、5、6节明确替换原因、三变量配置和未上线实测事项。既有关系仍描述历史数据库架构，不把旧PG并发测试当作现行Blob严格额度保证。

- [S1] [[05-Research/website-7b89a34872b0/免费部署调研与实施记录--22bbe9b15acb/原文-免费部署调研与实施记录.md|原文证据]]；定位：第1—2节：官方免费套餐、域名与数据库连接边界；第3—5节：函数适配、验证与待验收项
- [S2] [[05-Research/website-7b89a34872b0/Makers-Blob替代数据库实施记录--b8f58a8d9d31/原文-Makers-Blob替代数据库实施记录.md|原文证据]]；定位：第1—3节：接受的Blob并发边界、SDK条件写限制和数据组织；第4—6节：固定算法、配置与实测范围
- [[01-Knowledge/transactional-access-code-quota|有限次访问码的事务扣次与幂等设计]]：使用；Makers函数复用同一FastAPI后端，以PostgreSQL事务预留和扣次；本地实现已测试，云端联调待验证。
- [[01-Knowledge/deterministic-narrative-result-generation|冻结内容库的确定性生成与跨语言一致性]]：使用；构建仅打包固定Python评分引擎、题库及结果库，随机会话或分享链接不参与文学身份生成。
- [[01-Knowledge/hong-kong-assessment-stack|香港部署的中文测评网站架构]]：可替代；在免费试运行且实际数据库网络可达的条件下，Makers函数可替代租用香港应用服务器；自有域名及生产验收仍必需。

## 建议

- 先选数据库环境并验证连接/TLS/权限，再部署Makers。
- 把正式PUBLIC_ORIGIN设置为自有域名，不能用3小时预览域名发行长期分享链接。
- 免费续期、备份恢复、冷启动和额度耗尽行为纳入上线验收。
- 区分历史数据库方案与当前Blob部署；恢复严格额度时才重启数据库架构与云端联调。

<!-- AI:END -->

## 人工笔记

