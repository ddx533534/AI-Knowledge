---
{
  "id": "makers-blob-assessment-storage",
  "title": "Makers Blob测评存储与最佳努力扣次",
  "type": "architecture",
  "status": "partial",
  "last_verified": "2026-10-11",
  "sources": [
    {
      "document_id": "b8f58a8d9d319b771b81f7654b80549dbcac660994a0c7b27c8ee31ed01aebbb",
      "locator": "第1—3节：接受的Blob并发边界、SDK条件写限制和数据组织；第4—6节：固定算法、配置与实测范围"
    }
  ],
  "relationships": [
    {
      "target": "makers-postgresql-quiz-deployment",
      "type": "alternative_to",
      "explanation": "用户接受并发额度偏差后，Node云函数与Blob替换原Makers/PostgreSQL方案，省去数据库配置和迁移；不保留原事务保证。",
      "sources": [
        {
          "document_id": "b8f58a8d9d319b771b81f7654b80549dbcac660994a0c7b27c8ee31ed01aebbb",
          "locator": "第1—3节：接受的Blob并发边界、SDK条件写限制和数据组织；第4—6节：固定算法、配置与实测范围"
        }
      ]
    },
    {
      "target": "deterministic-narrative-result-generation",
      "type": "uses",
      "explanation": "Blob后端使用移植的Node固定评分/查表算法，580组答案逐项对照Python，覆盖96变体；存储与随机会话不参与文学身份生成。",
      "sources": [
        {
          "document_id": "b8f58a8d9d319b771b81f7654b80549dbcac660994a0c7b27c8ee31ed01aebbb",
          "locator": "第1—3节：接受的Blob并发边界、SDK条件写限制和数据组织；第4—6节：固定算法、配置与实测范围"
        }
      ]
    }
  ],
  "aliases": [
    "Blob替代测评数据库"
  ],
  "tags": [
    "Makers",
    "Blob",
    "对象存储",
    "并发边界",
    "测评"
  ],
  "schema_version": 2,
  "created": "2026-10-11T17:56:50.157432+08:00",
  "updated": "2026-10-11T17:56:50.250559+08:00"
}
---
# Makers Blob测评存储与最佳努力扣次

<!-- AI:BEGIN -->
## 结论

在明确接受并发读改写偏差的前提下，以Makers Node.js云函数和Blob存放码、会话、草稿、结果及批次，只需要三个服务端配置变量。串行次数、幂等重试与结果隐私已本地验证，云端Blob授权与运行尚未验收。

## 关键发现

- SDK0.0.18将onlyIfNew标为不受底层支持，不可据此构造锁；强一致读也不等于原子读改写。
- 报告和轮次记录先提交到同一码对象，再发布独立结果快照；普通重试复用相同ID，避免再次计次。
- 独立分享撤销标记和已发布结果快照降低陈旧码对象覆盖的影响，但仍无跨对象事务。
- 批次固定HMAC派生码并加密导出清单，部分初始化失败可继续，不重置已有码。
- 13项Blob测试、580组跨语言报告对比与手机端流程通过；实际Makers Blob、多运营商、冷启动及备份恢复待验证。

## 证据与分析

实施文档第2节包含官方SDK发布包检查，第3节具体写入顺序，第6节限定验证范围。Blob替代仅适用于用户接受并发偏差的产品，不把文件模拟或SDK强一致读当成线上事务保证；保存响应丢失时须用原轮次重试。

- [S1] [[05-Research/website-7b89a34872b0/Makers-Blob替代数据库实施记录--b8f58a8d9d31/原文-Makers-Blob替代数据库实施记录.md|原文证据]]；定位：第1—3节：接受的Blob并发边界、SDK条件写限制和数据组织；第4—6节：固定算法、配置与实测范围
- [[01-Knowledge/makers-postgresql-quiz-deployment|Makers与PostgreSQL的趣味测评部署边界]]：可替代；用户接受并发额度偏差后，Node云函数与Blob替换原Makers/PostgreSQL方案，省去数据库配置和迁移；不保留原事务保证。
- [[01-Knowledge/deterministic-narrative-result-generation|冻结内容库的确定性生成与跨语言一致性]]：使用；Blob后端使用移植的Node固定评分/查表算法，580组答案逐项对照Python，覆盖96变体；存储与随机会话不参与文学身份生成。

## 建议

- 服务端仅配置APP_SECRET、ADMIN_KEY与正式PUBLIC_ORIGIN，不使用VITE变量暴露秘密。
- 正式上线前验证Blob真实读写、域名HTTPS、管理批次和完整结果分享。
- 严格额度、付费权益或高并发场景应改用有条件写入/事务的存储；不能沿用本方案声称严格3次。

<!-- AI:END -->

## 人工笔记

