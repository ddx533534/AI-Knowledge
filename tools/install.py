#!/usr/bin/env python3
"""Install the user's authorized cross-project rule and skills, preserving other settings."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tomllib

from knowledge import ROOT, dump, write

BEGIN = "<!-- TECHNICAL-KNOWLEDGE-CAPTURE:BEGIN -->"
END = "<!-- TECHNICAL-KNOWLEDGE-CAPTURE:END -->"


def config_text(text, vault):
    original = tomllib.loads(text)
    target = copy.deepcopy(original)
    sandbox = target.setdefault("sandbox_workspace_write", {})
    roots = sandbox.setdefault("writable_roots", [])
    if not isinstance(roots, list) or any(not isinstance(p, str) for p in roots):
        raise ValueError("现有 writable_roots 格式异常，未修改")
    if any(os.path.normcase(str(Path(p).resolve())) == os.path.normcase(str(vault.resolve())) for p in roots):
        return text
    roots.append(str(vault))
    value = json.dumps(roots, ensure_ascii=False)
    section = re.search(r"^\[sandbox_workspace_write\][ \t]*(?:#.*)?$", text, re.M)
    if section:
        tail = text[section.end():]
        next_table = re.search(r"^\[", tail, re.M)
        end = section.end() + (next_table.start() if next_table else len(tail))
        body = text[section.end():end]
        assignment = re.search(r"^writable_roots\s*=\s*\[(?:[^\]\"']|\"(?:\\.|[^\"])*\"|'[^']*')*\][ \t]*(?:#.*)?$", body, re.M)
        if "writable_roots" in original.get("sandbox_workspace_write", {}) and not assignment:
            raise ValueError("现有 writable_roots 不是支持的数组写法，保留配置并停止")
        if assignment:
            body = body[:assignment.start()] + "writable_roots = " + value + body[assignment.end():]
        else:
            body = "\nwritable_roots = " + value + "\n" + body
        updated = text[:section.end()] + body + text[end:]
    else:
        if "sandbox_workspace_write" in original:
            raise ValueError("现有沙箱配置使用内联或点号写法，保留配置并停止")
        updated = text.rstrip() + "\n\n[sandbox_workspace_write]\nwritable_roots = " + value + "\n"
    if tomllib.loads(updated) != target:
        raise ValueError("配置对象对比不一致，未修改")
    return updated


def rule_text(original, block):
    if original.count(BEGIN) != original.count(END) or original.count(BEGIN) > 1:
        raise ValueError("全局归档区域标记不一致，未修改")
    if BEGIN in original:
        first, last = original.index(BEGIN), original.index(END) + len(END)
        if original.index(BEGIN) > original.index(END):
            raise ValueError("全局归档区域标记顺序异常")
        return original[:first] + block.strip() + original[last:]
    return original + ("\n\n" if original and not original.endswith("\n\n") else "") + block.strip() + "\n"


def install(vault, user_home, codex_home, check=False):
    vault, user_home, codex_home = vault.resolve(), user_home.resolve(), codex_home.resolve()
    distribution = vault / "99-System/Distribution"
    if not distribution.is_dir():
        raise ValueError("分发源不存在")
    user_skill = user_home / ".agents/skills/technical-knowledge-capture"
    replacements = {"__VAULT_ROOT__": vault.as_posix(), "__SKILL_PATH__": user_skill.as_posix()}
    plan = {}
    for name, destination in (("technical-knowledge-capture", user_skill),
                              ("knowledge-graph-builder", vault / ".agents/skills/knowledge-graph-builder")):
        for source in (distribution / name).rglob("*"):
            if source.is_file():
                content = source.read_text(encoding="utf-8")
                for old, new in replacements.items():
                    content = content.replace(old, new)
                if "__VAULT_ROOT__" in content or "__SKILL_PATH__" in content:
                    raise ValueError("部署路径替换失败")
                plan[destination / source.relative_to(distribution / name)] = content
    override = codex_home / "AGENTS.override.md"
    rule_path = override if override.is_file() and override.read_text(encoding="utf-8-sig").strip() else codex_home / "AGENTS.md"
    original_rule = rule_path.read_text(encoding="utf-8-sig") if rule_path.exists() else ""
    block = (distribution / "global-AGENTS.md").read_text(encoding="utf-8")
    for old, new in replacements.items():
        block = block.replace(old, new)
    plan[rule_path] = rule_text(original_rule, block)
    config_path = codex_home / "config.toml"
    original_config = config_path.read_text(encoding="utf-8-sig") if config_path.exists() else ""
    plan[config_path] = config_text(original_config, vault)
    changed = {p: c for p, c in plan.items() if not p.exists() or p.read_bytes() != c.encode("utf-8")}
    result = {"vault": str(vault), "global_rule": str(rule_path), "user_skill": str(user_skill),
              "changed": [str(p) for p in changed], "check_only": check}
    if check or not changed:
        return result
    # Verify destinations before backups and writes. Never follow a symlink into an unrelated place.
    for path in changed:
        expected = vault if path.is_relative_to(vault) else user_home if path.is_relative_to(user_home) else codex_home
        if not path.resolve().is_relative_to(expected) or path.is_symlink():
            raise ValueError(f"安装目标越界/链接异常：{path}")
    backup = codex_home / "backups/technical-knowledge" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup.mkdir(parents=True, exist_ok=False)
    restore = []
    for index, path in enumerate(changed):
        if path.exists():
            saved = backup / f"{index}-{path.name}"
            shutil.copy2(path, saved)
            restore.append({"target": str(path), "backup": str(saved)})
        else:
            restore.append({"target": str(path), "backup": None})
    write(backup / "restore-manifest.json", dump(restore))
    for path, content in changed.items():
        write(path, content)
    # Do not export global config or its contents to the repository.
    result["backup"] = str(backup)
    write(vault / "99-System/Maintenance/install-state.json", dump(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, default=ROOT)
    parser.add_argument("--user-home", type=Path, default=Path.home())
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        print(dump(install(args.vault, args.user_home, args.codex_home, args.check)), end="")
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(dump({"error": str(exc)}), file=sys.stderr, end="")
        return 1


if __name__ == "__main__":
    sys.exit(main())
