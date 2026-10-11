#!/usr/bin/env python3
"""Archive research artifacts and maintain an evidence-backed local knowledge graph.

Only Python's standard library is required. Knowledge semantics are supplied by
Codex; this program copies, validates, preserves manual text and derives views.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
KINDS = {"research", "exploration", "analysis"}
TYPES = {"concept", "protocol", "framework", "model", "runtime", "tool", "architecture", "comparison"}
RELATIONS = {
    "depends_on": "依赖", "implements": "实现", "extends": "扩展",
    "alternative_to": "可替代", "integrates_with": "集成", "component_of": "组成部分",
    "uses": "使用", "related_to": "相关",
}
BEGIN, END = "<!-- AI:BEGIN -->", "<!-- AI:END -->"


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="microseconds")


def normalized(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def slug(value):
    result = re.sub(r"[^\w\-]+", "-", value, flags=re.UNICODE).strip("-_")[:60]
    return result or "document"


def contained(root, path):
    return path.resolve().is_relative_to(root.resolve())


def local(root, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise ValueError("必须使用库内相对路径")
    path = root / relative
    if not contained(root, path):
        raise ValueError("路径越出知识库")
    return path


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, content):
    """Replace one generated file atomically; keep mtime when content is identical."""
    if path.is_symlink():
        raise ValueError(f"不写入符号链接：{path}")
    payload = content.encode("utf-8") if isinstance(content, str) else content
    if path.exists() and path.read_bytes() == payload:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".knowledge-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
        os.replace(temp, path)
    finally:
        if Path(temp).exists():
            Path(temp).unlink()
    return True


@contextmanager
def lock(root):
    path = root / ".knowledge.lock"
    if path.is_symlink():
        raise ValueError("锁文件不能是符号链接")
    try:
        handle = path.open("x", encoding="utf-8")
    except FileExistsError:
        raise ValueError("知识库正在写入；稍后重试。若上次进程中断，确认无写入进程后手动移除 .knowledge.lock")
    with handle:
        handle.write(dump({"pid": os.getpid(), "started_at": now()}))
    try:
        yield
    finally:
        path.unlink()


def git_value(project, *args):
    try:
        result = subprocess.run(["git", "-C", str(project), *args], capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def manifests(root):
    records = {}
    for path in sorted((root / "05-Research").rglob("manifest.json")):
        if not contained(root, path):
            raise ValueError("归档清单越界")
        record = read_json(path)
        doc_id = record.get("id")
        if not isinstance(doc_id, str) or not re.fullmatch(r"[a-f0-9]{64}", doc_id):
            raise ValueError(f"无效文档 ID：{path}")
        if doc_id in records:
            raise ValueError(f"重复文档 ID：{doc_id}")
        record["_manifest"] = path.relative_to(root).as_posix()
        records[doc_id] = record
    return records


def capture(root, source, project, title, kind):
    source, project = source.resolve(), project.resolve()
    if not source.is_file() or not project.is_dir() or not contained(project, source):
        raise ValueError("来源必须是指定项目中的真实文件")
    if kind not in KINDS:
        raise ValueError("无效文档类别")
    if any((parent / "manifest.json").exists() and contained(root / "05-Research", parent)
           for parent in source.parents):
        raise ValueError("不能将归档副本再次归档")
    data = source.read_bytes()
    content_hash = digest(data)
    key = digest((os.path.normcase(str(project)) + "\n" + os.path.normcase(str(source))).encode("utf-8"))
    doc_id = digest((key + content_hash).encode("ascii"))
    records = manifests(root)
    if doc_id in records:
        archived = local(root, records[doc_id]["artifact"])
        if digest(archived.read_bytes()) != content_hash:
            raise ValueError("已有副本被改动；停止归档，先检查副本")
        return {"id": doc_id, "changed": False, "artifact": records[doc_id]["artifact"]}
    project_key = digest(os.path.normcase(str(project)).encode("utf-8"))[:12]
    directory = root / "05-Research" / f"{slug(project.name)}-{project_key}" / f"{slug(source.stem)}--{doc_id[:12]}"
    artifact = (directory / ("原文-" + slug(source.stem) + source.suffix.lower())).relative_to(root).as_posix()
    note = (directory / "归档说明.md").relative_to(root).as_posix()
    previous = [r for r in records.values() if r["source_key"] == key]
    previous.sort(key=lambda r: (r["captured_at"], r["id"]))
    record = {
        "schema_version": 2, "id": doc_id, "title": title or source.stem, "kind": kind,
        "source_key": key, "source_project": str(project), "source_path": str(source),
        "source_relative_path": source.relative_to(project).as_posix(),
        "source_commit": git_value(project, "rev-parse", "HEAD"),
        "source_worktree_dirty": None, "captured_at": now(), "sha256": content_hash,
        "size": len(data), "artifact": artifact, "note": note,
        "previous_version": previous[-1]["id"] if previous else None,
    }
    status = git_value(project, "status", "--porcelain")
    if status is not None:
        record["source_worktree_dirty"] = bool(status)
    if not contained(root, directory) or directory.exists():
        raise ValueError("归档目录越界或已存在不完整副本")
    directory.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix=".capture-", dir=directory.parent))
    try:
        write(staged / Path(artifact).name, data)
        explanation = (
            f"# {record['title']}\n\n原文副本保持字节一致；本文仅记录归档来源，不表示事实已核实。\n\n"
            f"- 来源项目：`{project}`\n- 来源文档：`{source}`\n"
            f"- 来源提交：`{record['source_commit'] or '未知/非 Git 项目'}`\n"
            f"- 来源工作区有变更：`{record['source_worktree_dirty']}`\n"
            f"- 归档时间：{record['captured_at']}\n- SHA-256：`{content_hash}`\n"
            f"- 文档 ID：`{doc_id}`\n\n原文：[[{artifact}|打开原文副本]]\n"
        )
        write(staged / "归档说明.md", explanation)
        write(staged / "manifest.json", dump(record))
        os.rename(staged, directory)
    finally:
        if staged.exists():
            for file in staged.iterdir():
                file.unlink()
            staged.rmdir()
    return {"id": doc_id, "changed": True, "artifact": artifact}


def parse_note(path):
    text = path.read_text(encoding="utf-8-sig")
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.S)
    if not match:
        raise ValueError(f"知识节点缺少 JSON 格式 frontmatter：{path}")
    meta = json.loads(match[1])
    if not isinstance(meta, dict):
        raise ValueError("节点元数据必须是对象")
    return meta, match[2]


def nodes(root):
    result = {}
    for path in sorted((root / "01-Knowledge").glob("*.md")):
        if not contained(root, path):
            raise ValueError("知识节点越界")
        meta, body = parse_note(path)
        node_id = meta.get("id")
        if node_id in result:
            raise ValueError("重复节点 ID")
        result[node_id] = {"meta": meta, "body": body, "path": path.relative_to(root).as_posix()}
    return result


def evidence_errors(sources, docs):
    errors = []
    if not isinstance(sources, list) or not sources:
        return ["至少需要一条文档证据"]
    for evidence in sources:
        if not isinstance(evidence, dict):
            errors.append("证据必须是对象")
            continue
        if evidence.get("document_id") not in docs:
            errors.append("证据文档不存在")
        if not isinstance(evidence.get("locator"), str) or not evidence["locator"].strip():
            errors.append("证据缺少章节/行号/页码定位")
    return errors


def validate(root, docs=None, knowledge=None):
    docs = manifests(root) if docs is None else docs
    knowledge = nodes(root) if knowledge is None else knowledge
    errors, owners = [], {}
    for doc_id, record in docs.items():
        try:
            for field in ("source_project", "source_path", "source_relative_path", "source_key", "title", "kind", "captured_at"):
                if not isinstance(record.get(field), str) or not record[field]:
                    raise ValueError(f"清单缺少 {field}")
            if record["kind"] not in KINDS:
                raise ValueError("文档类别无效")
            directory = local(root, record["_manifest"]).parent
            artifact = local(root, record["artifact"])
            note = local(root, record["note"])
            if artifact.parent != directory or note.parent != directory or not note.is_file():
                raise ValueError("副本和说明必须在清单所在目录")
            data = artifact.read_bytes()
            if digest(data) != record.get("sha256") or len(data) != record.get("size"):
                raise ValueError("原文副本的校验值/大小不匹配")
            if digest((record["source_key"] + record["sha256"]).encode("ascii")) != doc_id:
                raise ValueError("文档 ID 与来源/内容不匹配")
            previous = record.get("previous_version")
            if previous is not None and (previous not in docs or docs[previous]["source_key"] != record["source_key"] or previous == doc_id):
                raise ValueError("前一版本不存在或来源不一致")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"文档 {doc_id}: {exc}")
    for node_id, note in knowledge.items():
        meta, body = note["meta"], note["body"]
        prefix = f"节点 {node_id}: "
        if not isinstance(node_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", node_id):
            errors.append(prefix + "ID 必须是小写字母/数字/连字符")
        if Path(note["path"]).stem != node_id:
            errors.append(prefix + "ID 与文件名不一致")
        names = [meta.get("title")]
        aliases = meta.get("aliases", [])
        if not isinstance(aliases, list):
            errors.append(prefix + "aliases 必须是列表")
        else:
            names.extend(aliases)
        for name in names:
            if not isinstance(name, str) or not name.strip() or any(c in name for c in "\n\r[]|"):
                errors.append(prefix + "名称必须非空且不包含换行或链接分隔符")
                continue
            key = normalized(name)
            if key in owners and owners[key] != node_id:
                errors.append(prefix + f"标题/别名冲突：{name}")
            owners[key] = node_id
        if meta.get("type") not in TYPES or meta.get("status") not in ("verified", "partial", "unverified"):
            errors.append(prefix + "类型/核实状态无效")
        for field in ("created", "updated"):
            try:
                datetime.fromisoformat(meta[field])
            except (KeyError, TypeError, ValueError):
                errors.append(prefix + f"{field} 时间无效")
        verified = meta.get("last_verified")
        if verified is not None:
            try:
                datetime.strptime(verified, "%Y-%m-%d")
            except (TypeError, ValueError):
                errors.append(prefix + "last_verified 必须为 YYYY-MM-DD 或 null")
        if meta.get("status") in ("verified", "partial") and not verified:
            errors.append(prefix + "已核实/部分核实节点需要真实核实日期")
        errors.extend(prefix + e for e in evidence_errors(meta.get("sources"), docs))
        if body.count(BEGIN) != 1 or body.count(END) != 1 or body.find(BEGIN) > body.find(END):
            errors.append(prefix + "AI 编辑标记缺失或不成对")
        for heading in ("结论", "关键发现", "证据与分析", "建议", "人工笔记"):
            if not re.search(r"^## " + heading + r"\s*$", body, re.M):
                errors.append(prefix + f"缺少章节 {heading}")
        relationships = meta.get("relationships")
        if not isinstance(relationships, list):
            errors.append(prefix + "relationships 必须是列表")
            continue
        seen = set()
        for edge in relationships:
            if not isinstance(edge, dict):
                errors.append(prefix + "关系必须是对象")
                continue
            target, kind = edge.get("target"), edge.get("type")
            if not isinstance(target, str) or target not in knowledge or target == node_id:
                errors.append(prefix + "关系目标必须是其他已有节点")
            if not isinstance(kind, str) or kind not in RELATIONS:
                errors.append(prefix + "关系类型无效")
            if not isinstance(edge.get("explanation"), str) or not edge["explanation"].strip():
                errors.append(prefix + "关系缺少解释")
            errors.extend(prefix + e for e in evidence_errors(edge.get("sources"), docs))
            if isinstance(edge.get("sources"), list) and any(s not in meta.get("sources", []) for s in edge["sources"]):
                errors.append(prefix + "关系证据须同时保留在节点 sources")
            if isinstance(target, str) and f"[[01-Knowledge/{target}|" not in body:
                errors.append(prefix + "关系目标缺少正文链接")
            if isinstance(target, str) and isinstance(kind, str):
                key = (target, kind)
                if key in seen:
                    errors.append(prefix + "重复关系")
                seen.add(key)
        for target in re.findall(r"\[\[([^\]\n]+)\]\]", body):
            relative = target.split("|", 1)[0].split("#", 1)[0]
            try:
                candidate = local(root, relative)
                if not candidate.is_file() and not local(root, relative + ".md").is_file():
                    errors.append(prefix + f"无效链接：{relative}")
            except ValueError:
                errors.append(prefix + f"越界链接：{relative}")
    return errors


def upsert(root, spec):
    if not isinstance(spec, dict):
        raise ValueError("节点说明必须是 JSON 对象")
    node_id = spec.get("id")
    if not isinstance(node_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", node_id):
        raise ValueError("无效节点 ID")
    for field in ("title", "summary", "analysis"):
        if not isinstance(spec.get(field), str) or not spec[field].strip():
            raise ValueError(f"缺少 {field}")
    for field in ("findings", "recommendations"):
        if not isinstance(spec.get(field), list) or any(not isinstance(s, str) for s in spec[field]):
            raise ValueError(f"{field} 必须为字符串列表")
    docs, knowledge = manifests(root), nodes(root)
    path = local(root, f"01-Knowledge/{node_id}.md")
    previous_meta, previous_body = parse_note(path) if path.exists() else ({}, f"# {spec['title']}\n\n{BEGIN}\n{END}\n\n## 人工笔记\n\n")
    if previous_body.count(BEGIN) != 1 or previous_body.count(END) != 1 or previous_body.find(BEGIN) > previous_body.find(END):
        raise ValueError("旧节点没有唯一 AI 编辑区域，停止覆盖")
    meta = dict(previous_meta)
    for key in ("id", "title", "type", "status", "last_verified", "sources", "relationships", "aliases", "tags"):
        meta[key] = spec.get(key, {"aliases": [], "tags": [], "relationships": [], "status": "unverified"}.get(key))
    meta["schema_version"] = 2
    meta["created"] = previous_meta.get("created", now())
    meta["updated"] = previous_meta.get("updated", meta["created"])
    lines = [BEGIN, "## 结论", "", spec["summary"], "", "## 关键发现", ""]
    lines.extend("- " + s for s in spec["findings"])
    lines.extend(["", "## 证据与分析", "", spec["analysis"], ""])
    for number, evidence in enumerate(meta.get("sources") or [], 1):
        if not isinstance(evidence, dict) or evidence.get("document_id") not in docs:
            raise ValueError("来源文档不存在")
        doc = docs[evidence["document_id"]]
        lines.append(f"- [S{number}] [[{doc['artifact']}|原文证据]]；定位：{evidence.get('locator', '')}")
    for edge in meta["relationships"]:
        if not isinstance(edge, dict):
            raise ValueError("关系必须为对象")
        target = edge.get("target")
        title = knowledge.get(target, {}).get("meta", {}).get("title", target)
        lines.append(f"- [[01-Knowledge/{target}|{title}]]：{RELATIONS.get(edge.get('type'), edge.get('type'))}；{edge.get('explanation', '')}")
    lines.extend(["", "## 建议", ""])
    lines.extend("- " + s for s in spec["recommendations"])
    lines.extend(["", END])
    start, end = previous_body.index(BEGIN), previous_body.index(END) + len(END)
    body = previous_body[:start] + "\n".join(lines) + previous_body[end:]
    knowledge[node_id] = {"meta": meta, "body": body, "path": f"01-Knowledge/{node_id}.md"}
    errors = validate(root, docs, knowledge)
    if errors:
        raise ValueError("\n".join(errors))
    content = "---\n" + dump(meta).rstrip() + "\n---\n" + body
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return {"id": node_id, "changed": False}
    meta["updated"] = now()
    content = "---\n" + dump(meta).rstrip() + "\n---\n" + body
    write(path, content)
    return {"id": node_id, "changed": True}


def build(root):
    docs, knowledge = manifests(root), nodes(root)
    errors = validate(root, docs, knowledge)
    if errors:
        raise ValueError("\n".join(errors))
    graph = {"schema_version": 2, "nodes": [], "edges": []}
    document_lines = ["# 文档索引", "", "从归档清单派生，包含历史版本。请勿直接维护。", ""]
    for doc_id, doc in sorted(docs.items()):
        graph["nodes"].append({"id": "doc:" + doc_id, "kind": "document", "title": doc["title"],
                               "path": doc["artifact"], "artifact": doc["artifact"], "note": doc["note"], "project": doc["source_project"],
                               "source_path": doc["source_path"], "sha256": doc["sha256"], "captured_at": doc["captured_at"]})
        document_lines.append(f"- [[{doc['artifact']}|{doc['title']}]] — [[{doc['note']}|归档说明]]；{doc['kind']}；{doc['captured_at']}；`{doc_id[:12]}`")
    node_lines = ["# 知识索引", "", "从知识节点派生，节点事实与证据保存在原笔记。", ""]
    edge_lines = ["# 关系索引", "", "技术关系必须有直接证据；文档来源边另行展示。", ""]
    for node_id, note in sorted(knowledge.items()):
        meta = note["meta"]
        graph["nodes"].append({"id": "node:" + node_id, "kind": "knowledge", "title": meta["title"],
                               "path": note["path"], "type": meta["type"], "status": meta["status"],
                               "tags": meta.get("tags", []), "sources": meta["sources"]})
        node_lines.append(f"- [[{note['path']}|{meta['title']}]] — {meta['type']}；{meta['status']}")
        for doc_id in sorted({s["document_id"] for s in meta["sources"]}):
            graph["edges"].append({"source": "node:" + node_id, "target": "doc:" + doc_id,
                                   "type": "evidence", "label": "来源", "explanation": "节点的文档证据", "sources": []})
        for edge in meta["relationships"]:
            graph["edges"].append({"source": "node:" + node_id, "target": "node:" + edge["target"],
                                   "type": edge["type"], "label": RELATIONS[edge["type"]],
                                   "explanation": edge["explanation"], "sources": edge["sources"]})
            edge_lines.append(f"- [[{note['path']}|{meta['title']}]] → **{RELATIONS[edge['type']]}** → [[01-Knowledge/{edge['target']}|{knowledge[edge['target']]['meta']['title']}]]：{edge['explanation']}")
    template = (root / "tools/graph-template.html").read_text(encoding="utf-8")
    graph_html = template.replace("__GRAPH_JSON__", dump(graph).replace("<", "\\u003c").replace("&", "\\u0026"))
    outputs = {"99-System/graph.json": dump(graph), "99-System/知识图谱.html": graph_html,
               "99-System/文档索引.md": "\n".join(document_lines) + "\n",
               "99-System/知识索引.md": "\n".join(node_lines) + "\n",
               "99-System/关系索引.md": "\n".join(edge_lines) + "\n"}
    changed = [rel for rel, content in outputs.items() if write(local(root, rel), content)]
    return {"documents": len(docs), "knowledge_nodes": len(knowledge),
            "technical_relations": sum(e["type"] != "evidence" for e in graph["edges"]), "changed": changed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    archive = commands.add_parser("capture")
    archive.add_argument("--source", type=Path, required=True)
    archive.add_argument("--project", type=Path, required=True)
    archive.add_argument("--title")
    archive.add_argument("--kind", choices=sorted(KINDS), default="research")
    node = commands.add_parser("node")
    node.add_argument("--spec", type=Path, required=True)
    commands.add_parser("validate")
    commands.add_parser("build")
    args = parser.parse_args()
    root = args.vault.resolve()
    try:
        if not root.is_dir() or not (root / "tools/graph-template.html").is_file():
            raise ValueError("不是已初始化的知识库")
        # All commands share the same lock so validation cannot observe half a write.
        with lock(root):
            if args.command == "capture":
                result = capture(root, args.source, args.project, args.title, args.kind)
            elif args.command == "node":
                result = upsert(root, read_json(args.spec))
            elif args.command == "build":
                result = build(root)
            else:
                errors = validate(root)
                result = {"errors": errors, "documents": len(manifests(root)), "knowledge_nodes": len(nodes(root))}
                print(dump(result), end="")
                return int(bool(errors))
        print(dump(result), end="")
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(dump({"error": str(exc)}), end="", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
