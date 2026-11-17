"""Spec 022: the PR preview index."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

spec = importlib.util.spec_from_file_location(
    "preview_index", Path(__file__).resolve().parents[2] / "scripts/site/preview_index.py"
)
assert spec and spec.loader
pi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pi)


def test_post_links(tmp_path: Path) -> None:
    blog = tmp_path / "site/blog"
    blog.mkdir(parents=True)
    (blog / "2026-11-15-time-late-synthesis.md").write_text('---\ntitle: "The account"\n---\nx')
    (blog / "2026-11-16-x.md").write_text("---\ntitle: X\nslug: special/one\n---\n")
    got = pi.post_link("site/blog/2026-11-15-time-late-synthesis.md", tmp_path)
    assert got == {
        "title": "The account",
        "path": "blog/2026/11/15/time-late-synthesis",
        "date": "2026-11-15",
    }
    assert pi.post_link("site/blog/2026-11-16-x.md", tmp_path)["path"] == "blog/special/one"
    assert pi.post_link("site/blog/_templates/kickoff.md", tmp_path) is None
    assert pi.post_link("site/docs/index.md", tmp_path) is None


def test_update_keeps_build_on_state_change(tmp_path: Path) -> None:
    index: dict[str, Any] = {"previews": []}
    posts = [{"title": "T", "path": "blog/2026/11/16/a", "date": "2026-11-16"}]
    pi.update(index, 39, "Spec 022", "open", "abc", posts, "u", "t1")
    pi.update(index, 38, "Older", "open", "def", [], None, "t1")
    pi.update(index, 39, "", "merged", None, None, None, "t2")
    e = index["previews"][0]
    assert [x["number"] for x in index["previews"]] == [39, 38]
    assert e["state"] == "merged" and e["head"] == "abc" and e["posts"] == posts
    assert e["title"] == "Spec 022" and e["built_at"] == "t1" and e["state_at"] == "t2"


def test_cli_writes_index(tmp_path: Path) -> None:
    (tmp_path / "changed").write_text("site/blog/2026-11-16-a.md\nsrc/x.py\n")
    (tmp_path / "site/blog").mkdir(parents=True)
    (tmp_path / "site/blog/2026-11-16-a.md").write_text("---\ntitle: A post\n---\n")
    idx = tmp_path / "gh/pr/index.json"
    pi.main(
        ["--index", str(idx), "--pr", "7", "--title", "T", "--state", "open", "--head", "h",
         "--posts-from", str(tmp_path / "changed"), "--root", str(tmp_path)]
    )  # fmt: skip
    data = json.loads(idx.read_text())
    assert data["previews"][0]["posts"][0]["title"] == "A post"
