"""Behavioral tests use isolated synthetic fixtures; they never enter the real graph."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import knowledge as k
import install as installer


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "vault"
        (self.root / "tools").mkdir(parents=True)
        shutil.copyfile(k.ROOT / "tools/graph-template.html", self.root / "tools/graph-template.html")
        self.project = self.base / "source-project"
        self.project.mkdir()
        self.source = self.project / "研究.md"
        self.source.write_bytes("# Synthetic fixture\r\n此内容仅用于测试。\r\n".encode("utf-8"))

    def archive(self, source=None, project=None, **kwargs):
        return k.capture(self.root, source or self.source, project or self.project, None, "research", **kwargs)

    def spec(self, node_id="test-concept", title="测试概念", document=None):
        document = document or self.archive()["id"]
        return {"id": node_id, "title": title, "aliases": [], "type": "concept", "status": "unverified",
                "last_verified": None, "sources": [{"document_id": document, "locator": "Synthetic fixture 第 2 行"}],
                "relationships": [], "summary": "测试用概念，不是真实知识。", "findings": ["仅验证行为。"],
                "analysis": "来源明确标为测试。", "recommendations": ["不得进入真实图谱。"]}

    def test_byte_exact_copy_and_repeated_archive_keeps_mtime(self):
        before = (self.source.read_bytes(), self.source.stat().st_mtime_ns)
        first = self.archive()
        artifact = self.root / first["artifact"]
        mtime = artifact.stat().st_mtime_ns
        second = self.archive()
        self.assertFalse(second["changed"])
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(artifact.read_bytes(), before[0])
        self.assertEqual(artifact.stat().st_mtime_ns, mtime)
        self.assertEqual(before, (self.source.read_bytes(), self.source.stat().st_mtime_ns))

    def test_archive_path_has_readable_name_and_short_version(self):
        archived = self.archive()
        path = Path(archived['artifact'])
        self.assertEqual(path.parent.name, '研究--' + archived['id'][:12])
        self.assertEqual(path.name, '原文-研究.md')
        self.assertEqual(k.manifests(self.root)[archived['id']]['id'], archived['id'])

    def test_new_version_keeps_previous_original(self):
        first = self.archive()
        self.source.write_text("新的 synthetic fixture", encoding="utf-8")
        second = self.archive()
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(k.manifests(self.root)[second["id"]]["previous_version"], first["id"])
        self.assertTrue((self.root / first["artifact"]).exists())
        self.assertEqual(k.validate(self.root), [])

    def test_document_graph_and_evidence_open_byte_exact_original(self):
        archived = self.archive()
        k.upsert(self.root, self.spec(document=archived['id']))
        k.build(self.root)
        graph = k.read_json(self.root / '99-System/graph.json')
        doc = next(n for n in graph['nodes'] if n['kind'] == 'document')
        self.assertEqual(doc['path'], archived['artifact'])
        self.assertEqual((self.root / doc['path']).read_bytes(), self.source.read_bytes())
        self.assertNotEqual(doc['path'], doc['note'])
        index = (self.root / '99-System/文档索引.md').read_text(encoding='utf-8')
        self.assertIn('[[' + archived['artifact'] + '|', index)
        note = (self.root / '01-Knowledge/test-concept.md').read_text(encoding='utf-8')
        self.assertIn('[[' + archived['artifact'] + '|原文证据]]', note)

    def test_same_name_in_distinct_projects_does_not_collide(self):
        first = self.archive()
        project = self.base / "second-project"
        project.mkdir()
        source = project / self.source.name
        source.write_bytes(self.source.read_bytes())
        second = self.archive(source, project)
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(len(k.manifests(self.root)), 2)

    def test_rapid_changes_keep_the_latest_version_in_chain(self):
        first = self.archive()
        self.source.write_text("synthetic second version", encoding="utf-8")
        second = self.archive()
        self.source.write_text("synthetic third version", encoding="utf-8")
        third = self.archive()
        records = k.manifests(self.root)
        self.assertEqual(records[third["id"]]["previous_version"], second["id"])
        self.assertEqual(records[second["id"]]["previous_version"], first["id"])

    def test_binary_copy_is_not_decoded(self):
        source = self.project / "fixture.pdf"
        source.write_bytes(b"%PDF-1.4\x00\xff\r\nsynthetic")
        result = self.archive(source)
        self.assertEqual((self.root / result["artifact"]).read_bytes(), source.read_bytes())

    def test_duplicate_archive_rejects_tampered_copy(self):
        first = self.archive()
        (self.root / first["artifact"]).write_text("changed", encoding="utf-8")
        self.assertTrue(k.validate(self.root))
        with self.assertRaises(ValueError):
            self.archive()

    def test_source_outside_project_is_rejected(self):
        outside = self.base / "outside.md"
        outside.write_text("synthetic", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.archive(outside)

    def test_archive_cannot_archive_itself(self):
        first = self.archive()
        with self.assertRaises(ValueError):
            self.archive(self.root / first["artifact"], self.root)

    def test_manual_body_and_custom_fields_survive_update(self):
        spec = self.spec()
        k.upsert(self.root, spec)
        path = self.root / "01-Knowledge/test-concept.md"
        meta, body = k.parse_note(path)
        meta["my_manual_field"] = {"value": "保留"}
        body += "用户的人工笔记不得丢失。\n"
        k.write(path, "---\n" + k.dump(meta).rstrip() + "\n---\n" + body)
        spec["summary"] = "更新解释。"
        k.upsert(self.root, spec)
        updated, updated_body = k.parse_note(path)
        self.assertEqual(updated["my_manual_field"], meta["my_manual_field"])
        self.assertTrue(updated_body.endswith("用户的人工笔记不得丢失。\n"))

    def test_node_and_build_repeat_without_rewriting(self):
        spec = self.spec()
        k.upsert(self.root, spec)
        k.build(self.root)
        files = list((self.root / "99-System").glob("*")) + list((self.root / "01-Knowledge").glob("*"))
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in files}
        self.assertFalse(k.upsert(self.root, spec)["changed"])
        self.assertEqual(k.build(self.root)["changed"], [])
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in files})

    def test_relation_exports_type_and_evidence(self):
        target = self.spec("target", "目标概念")
        k.upsert(self.root, target)
        source = self.spec("source", "源概念")
        source["relationships"] = [{"target": "target", "type": "uses", "explanation": "测试使用关系。", "sources": source["sources"]}]
        k.upsert(self.root, source)
        result = k.build(self.root)
        self.assertEqual(result["technical_relations"], 1)
        graph = k.read_json(self.root / "99-System/graph.json")
        edge = next(e for e in graph["edges"] if e["type"] == "uses")
        self.assertEqual(edge["sources"], source["sources"])

    def test_invalid_relation_does_not_create_node(self):
        spec = self.spec()
        spec["relationships"] = [{"target": "missing", "type": "uses", "explanation": "无效目标。", "sources": spec["sources"]}]
        with self.assertRaises(ValueError):
            k.upsert(self.root, spec)
        self.assertFalse((self.root / "01-Knowledge/test-concept.md").exists())

    def test_missing_relation_evidence_is_rejected(self):
        k.upsert(self.root, self.spec("target", "目标"))
        spec = self.spec()
        spec["relationships"] = [{"target": "target", "type": "uses", "explanation": "缺证据。", "sources": []}]
        with self.assertRaises(ValueError):
            k.upsert(self.root, spec)

    def test_normalized_alias_conflict_is_rejected(self):
        first = self.spec("first", "First")
        first["aliases"] = ["ＡＢＣ"]
        k.upsert(self.root, first)
        second = self.spec("second", "Second")
        second["aliases"] = ["abc"]
        with self.assertRaises(ValueError):
            k.upsert(self.root, second)

    def test_manifest_cannot_point_outside_vault(self):
        doc_id = self.archive()["id"]
        records = k.manifests(self.root)
        path = self.root / records[doc_id]["_manifest"]
        record = k.read_json(path)
        record["artifact"] = "../source-project/研究.md"
        k.write(path, k.dump(record))
        self.assertTrue(k.validate(self.root))
        with self.assertRaises(ValueError):
            k.build(self.root)

    def test_read_only_validation_preserves_source_and_derived_files(self):
        k.upsert(self.root, self.spec())
        k.build(self.root)
        files = [p for p in self.base.rglob("*") if p.is_file()]
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in files}
        self.assertEqual(k.validate(self.root), [])
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in files})

    def test_cli_refuses_mutation_during_existing_lock(self):
        with k.lock(self.root):
            result = subprocess.run([sys.executable, str(k.ROOT / "tools/knowledge.py"), "--vault", str(self.root), "capture", "--source", str(self.source), "--project", str(self.project)], capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse((self.root / "05-Research").exists())
        self.assertFalse((self.root / ".knowledge.lock").exists())

    def test_graph_data_escapes_script_end_in_document_title(self):
        k.capture(self.root, self.source, self.project, "</script><script>alert(1)</script>", "research")
        k.build(self.root)
        output = (self.root / "99-System/知识图谱.html").read_text(encoding="utf-8")
        self.assertNotIn("</script><script>alert(1)</script>", output)
        self.assertIn("\\u003c/script>", output)

    def test_config_preserves_unrelated_settings_and_existing_roots(self):
        original = 'model = "keep-model"\napproval_policy = "on-request"\n[sandbox_workspace_write]\nwritable_roots = ["other-path"]\nnetwork_access = false\n[other]\nsetting = 9\n'
        updated = installer.config_text(original, self.root)
        expected = copy.deepcopy(installer.tomllib.loads(original))
        expected["sandbox_workspace_write"]["writable_roots"].append(str(self.root))
        self.assertEqual(installer.tomllib.loads(updated), expected)
        self.assertEqual(installer.config_text(updated, self.root), updated)

    def test_install_backups_preserves_global_text_and_is_idempotent(self):
        shutil.copytree(k.ROOT / "99-System/Distribution", self.root / "99-System/Distribution")
        home = self.base / "user"
        codex = home / ".codex"
        codex.mkdir(parents=True)
        (codex / "AGENTS.md").write_text("用户原有规则。\n", encoding="utf-8")
        (codex / "config.toml").write_text('model = "keep-model"\n', encoding="utf-8")
        result = installer.install(self.root, home, codex)
        self.assertTrue(result["changed"])
        self.assertTrue((codex / "AGENTS.md").read_text(encoding="utf-8").startswith("用户原有规则。\n"))
        restore = k.read_json(Path(result["backup"]) / "restore-manifest.json")
        self.assertTrue(any(item["target"].endswith("config.toml") and item["backup"] for item in restore))
        self.assertEqual(installer.install(self.root, home, codex)["changed"], [])
        self.assertNotIn("__VAULT_ROOT__", (home / ".agents/skills/technical-knowledge-capture/SKILL.md").read_text(encoding="utf-8"))

    def test_install_uses_active_global_override(self):
        shutil.copytree(k.ROOT / "99-System/Distribution", self.root / "99-System/Distribution")
        home = self.base / "user"
        codex = home / ".codex"
        codex.mkdir(parents=True)
        (codex / "AGENTS.override.md").write_text("覆盖规则。\n", encoding="utf-8")
        result = installer.install(self.root, home, codex)
        self.assertEqual(result["global_rule"], str(codex / "AGENTS.override.md"))
        self.assertFalse((codex / "AGENTS.md").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
