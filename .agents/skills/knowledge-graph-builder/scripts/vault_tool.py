#!/usr/bin/env python3
"""Validate vault Markdown and rebuild derived indexes without invoking a model."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    sys.exit("缺少 PyYAML；请在你的 Python 环境中安装 scripts/requirements.txt 后重试。")


def normalized(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def within(root, path):
    return path.resolve().is_relative_to(root.resolve())


def plain_body(text):
    """Skip fenced examples, inline code and HTML comments when resolving links."""
    lines, fence, length = [], None, 0
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if match:
            marker = match[1]
            if fence is None:
                fence, length = marker[0], len(marker)
            elif marker[0] == fence and len(marker) >= length and not match[2].strip():
                fence = None
            lines.append("")
        elif fence is None:
            lines.append(line)
        else:
            lines.append("")
    body = re.sub(r"<!--.*?-->", "", "\n".join(lines), flags=re.S)
    return re.sub(r"(`+).*?\1", "", body)


class Vault:
    def __init__(self, root):
        self.root = root.resolve()
        self.config = json.loads((self.root / "99-System/vault-config.json").read_text())
        self.notes, self.nodes, self.edges = {}, {}, []
        self.errors, self.warnings = [], []
        self.names = defaultdict(set)
        excluded = self.config["excluded_folders"]
        for path in sorted(self.root.rglob("*.md")):
            rel = path.relative_to(self.root).as_posix()
            if any(rel == entry or rel.startswith(entry + "/") for entry in excluded):
                continue
            if not within(self.root, path):
                self.error(rel, "笔记指向 Vault 外部，未读取")
                continue
            text = path.read_text(encoding="utf-8")
            meta, body = {}, text
            if text.startswith("---\n"):
                match = re.match(r"\A---\n(.*?)\n---(?:\n|$)(.*)\Z", text, flags=re.S)
                if not match:
                    self.error(rel, "frontmatter 缺少结束分隔符")
                else:
                    body = match[2]
                    try:
                        loaded = yaml.safe_load(match[1])
                        if loaded is None:
                            loaded = {}
                        if not isinstance(loaded, dict):
                            raise ValueError("必须是 YAML 对象")
                        meta = loaded
                    except (yaml.YAMLError, ValueError) as exc:
                        self.error(rel, f"frontmatter 无效：{exc}")
            self.notes[rel] = {"path": path, "meta": meta, "body": body, "text": text}
            if any(rel.startswith(folder + "/") for folder in self.config["knowledge_folders"]):
                self.nodes[rel] = self.notes[rel]
            self.names[normalized(path.stem)].add(rel)
            if isinstance(meta.get("title"), str):
                self.names[normalized(meta["title"])].add(rel)
            if isinstance(meta.get("aliases", []), list):
                for alias in meta.get("aliases", []):
                    if isinstance(alias, str):
                        self.names[normalized(alias)].add(rel)

    def error(self, rel, message):
        self.errors.append(f"{rel}: {message}")

    def warning(self, rel, message):
        self.warnings.append(f"{rel}: {message}")

    def resolve(self, source, target):
        target = target.strip().replace("\\|", "|").split("|", 1)[0].split("#", 1)[0].strip()
        if not target:
            return {source}
        if "://" in target or target.startswith("/"):
            return set()
        base = self.root / Path(source).parent
        for candidate in (base / target, self.root / target):
            paths = [candidate]
            if candidate.suffix != ".md":
                paths.append(Path(str(candidate) + ".md"))
            for path in paths:
                if within(self.root, path) and path.is_file():
                    return {path.resolve().relative_to(self.root).as_posix()}
        if "/" not in target:
            return set(self.names.get(normalized(target.removesuffix(".md")), set()))
        return set()

    def valid_source(self, value):
        if not isinstance(value, str) or not value.strip():
            return False
        if value.startswith("vault:"):
            rel = value[6:]
            path = self.root / rel
            return bool(rel) and not Path(rel).is_absolute() and within(self.root, path) and path.is_file()
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    @staticmethod
    def valid_date(value):
        if isinstance(value, date):
            return type(value) is date
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return False
        try:
            date.fromisoformat(value)
            return True
        except ValueError:
            return False

    def validate(self):
        links = {}
        for rel, note in self.notes.items():
            destinations = set()
            for target in re.findall(r"(?<!\\)\[\[([^\]\n]+)\]\]", plain_body(note["body"])):
                resolved = self.resolve(rel, target)
                if len(resolved) != 1:
                    message = f"{'链接歧义' if resolved else '无效链接'}：{target}"
                    if rel in self.config.get("legacy_notes", []):
                        self.warning(rel, f"既有人工笔记，{message}")
                    else:
                        self.error(rel, message)
                destinations.update(resolved)
            links[rel] = destinations
            begin, end = note["body"].count("<!-- AI:BEGIN -->"), note["body"].count("<!-- AI:END -->")
            if begin != end or begin > 1 or (begin and note["body"].index("<!-- AI:BEGIN -->") > note["body"].index("<!-- AI:END -->")):
                self.error(rel, "AI 编辑区域标记不成对或重复")

        owners = defaultdict(set)
        required = ("title", "type", "aliases", "status", "created", "updated", "last_verified", "sources", "relationships")
        sections = ("一句话定义", "解决的问题", "核心机制", "重要关系", "取舍与局限", "来源与证据", "待核实", "人工笔记")
        for rel, note in self.nodes.items():
            meta = note["meta"]
            for key in required:
                if key not in meta:
                    self.error(rel, f"缺少字段 {key}")
            title = meta.get("title")
            if not isinstance(title, str) or not title.strip():
                self.error(rel, "title 必须为非空字符串")
            else:
                owners[normalized(title)].add(rel)
                if title != note["path"].stem:
                    self.error(rel, "title 与文件名不一致")
            owners[normalized(note["path"].stem)].add(rel)
            aliases = meta.get("aliases")
            if not isinstance(aliases, list) or any(not isinstance(a, str) or not a.strip() for a in aliases):
                self.error(rel, "aliases 必须为非空字符串组成的列表，可以为空列表")
            else:
                if len({normalized(a) for a in aliases}) != len(aliases):
                    self.error(rel, "aliases 内存在重复名称")
                for alias in aliases:
                    owners[normalized(alias)].add(rel)
            if meta.get("type") not in self.config["knowledge_types"]:
                self.error(rel, "type 不在允许的知识节点类型中")
            if meta.get("status") not in ("verified", "partial", "unverified"):
                self.error(rel, "status 必须为 verified / partial / unverified")
            for key in ("created", "updated"):
                if not self.valid_date(meta.get(key)):
                    self.error(rel, f"{key} 必须为 YYYY-MM-DD")
            verified = meta.get("last_verified")
            if verified is not None and not self.valid_date(verified):
                self.error(rel, "last_verified 必须为日期或 null")
            if meta.get("status") in ("verified", "partial") and not self.valid_date(verified):
                self.error(rel, "已核实/部分核实节点必须记录真实核实日期")
            sources = meta.get("sources")
            if not isinstance(sources, list) or any(not self.valid_source(s) for s in sources):
                self.error(rel, "sources 必须为有效 HTTP(S) 地址或可访问 vault: 路径的列表")
                sources = []
            if not sources:
                if meta.get("status") == "unverified":
                    self.warning(rel, "未核实节点没有来源；不得当成可靠事实")
                else:
                    self.error(rel, "已核实/部分核实节点缺少来源")
            headings = set(re.findall(r"^##\s+(.+?)\s*$", plain_body(note["body"]), flags=re.M))
            for section in sections:
                if section not in headings:
                    self.error(rel, f"缺少章节：{section}")
            relationships = meta.get("relationships")
            if not isinstance(relationships, list):
                self.error(rel, "relationships 必须为对象列表")
                continue
            seen = set()
            for edge in relationships:
                if not isinstance(edge, dict):
                    self.error(rel, "关系必须为对象")
                    continue
                target, kind = edge.get("target"), edge.get("type")
                explanation, evidence = edge.get("explanation"), edge.get("sources")
                valid = True
                if not isinstance(target, str) or target not in self.nodes or target == rel:
                    self.error(rel, f"关系目标必须是存在的其他知识节点路径：{target}")
                    valid = False
                if kind not in self.config["relationship_types"]:
                    self.error(rel, f"无效关系类型：{kind}")
                    valid = False
                if not isinstance(explanation, str) or not explanation.strip():
                    self.error(rel, "关系缺少解释")
                    valid = False
                if not isinstance(evidence, list) or not evidence or any(not self.valid_source(s) for s in evidence):
                    self.error(rel, "关系缺少有效的直接证据来源")
                    valid = False
                elif any(s not in sources for s in evidence):
                    self.error(rel, "关系证据需同时保留在节点 sources")
                    valid = False
                if isinstance(target, str) and target not in links[rel]:
                    self.error(rel, f"关系目标未在正文中用 wikilink 表达：{target}")
                    valid = False
                if isinstance(target, str) and isinstance(kind, str):
                    key = (target, kind)
                    if key in seen:
                        self.error(rel, f"重复关系：{kind} → {target}")
                        valid = False
                    seen.add(key)
                if valid:
                    self.edges.append((rel, target, kind, explanation, evidence))
        for name, paths in sorted(owners.items()):
            if len(paths) > 1:
                self.error("名称索引", f"重复标题/别名候选 {name}：{', '.join(sorted(paths))}")

    def render_indexes(self):
        notes = ["# 知识索引", "", "由 Markdown 派生；请修改原笔记后重建，不在此维护独立事实。", ""]
        if not self.nodes:
            notes.extend(["尚无经过整理的技术节点。真实调研完成后由 Skill 创建。", ""])
        for folder in self.config["knowledge_folders"]:
            members = [(r, n) for r, n in self.nodes.items() if r.startswith(folder + "/")]
            if not members:
                continue
            notes.extend([f"## {folder}", ""])
            for rel, node in members:
                meta = node["meta"]
                target = rel.removesuffix(".md")
                notes.append(f"- [[{target}|{meta['title']}]] — {meta['type']}；{meta['status']}；核实日期：{meta.get('last_verified') or '未知'}")
            notes.append("")
        edges = ["# 关系索引", "", "由笔记 relationships 派生；图谱边由原笔记正文中的链接生成。", ""]
        if not self.edges:
            edges.extend(["暂无已核实并记录的技术关系。", ""])
        for source, target, kind, explanation, evidence in sorted(self.edges):
            source_name = self.nodes[source]["meta"]["title"]
            target_name = self.nodes[target]["meta"]["title"]
            edges.append(f"- [[{source.removesuffix('.md')}|{source_name}]] → **{kind}** → [[{target.removesuffix('.md')}|{target_name}]]")
            edges.append("  " + explanation.replace("\n", " "))
            edges.append("  证据：" + "；".join(evidence))
            edges.append("")
        return {self.config["indexes"]["notes"]: "\n".join(notes), self.config["indexes"]["relationships"]: "\n".join(edges)}

    def write_indexes(self):
        outputs = self.render_indexes()
        for rel in outputs:
            if not within(self.root, self.root / rel) or not rel.startswith("99-System/"):
                raise ValueError(f"索引写入路径越界：{rel}")
        changed = []
        for rel, content in outputs.items():
            path = self.root / rel
            if path.exists() and path.read_text(encoding="utf-8") == content:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_name(path.name + ".tmp")
            if temp.exists():
                raise ValueError(f"发现既有临时文件，保留原文件并停止：{temp}")
            with temp.open("x", encoding="utf-8") as handle:
                handle.write(content)
            temp.replace(path)
            changed.append(rel)
        return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "index"))
    parser.add_argument("--vault", type=Path, default=Path(__file__).resolve().parents[4])
    args = parser.parse_args()
    try:
        vault = Vault(args.vault)
        vault.validate()
        for warning in vault.warnings:
            print("WARN " + warning)
        for error in vault.errors:
            print("ERROR " + error)
        print(f"检查 {len(vault.notes)} 篇笔记，{len(vault.nodes)} 个知识节点，{len(vault.edges)} 条关系；错误 {len(vault.errors)}，警告 {len(vault.warnings)}。")
        if vault.errors:
            return 1
        if args.command == "index":
            changed = vault.write_indexes()
            print("已更新：" + "、".join(changed) if changed else "索引无变化，未写入文件。")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
