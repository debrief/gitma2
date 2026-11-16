"""Maintain the PR preview index on the gh-pages branch (spec 022).

    python3 scripts/site/preview_index.py --index <gh-pages>/pr/index.json --pr N \\
        --title T --state open|merged|closed [--head SHA] [--posts-from FILE] [--url URL]

``--posts-from`` is a list of changed paths (one a line, ``git diff --name-only``). Blog posts
among them (``site/blog/*.md`` or ``.mdx``, not templates) become links into the preview:
``YYYY-MM-DD-name.md`` → ``blog/YYYY/MM/DD/name`` unless the front matter sets a ``slug``. The
title is the front matter's ``title``, read from the file as it is in the checkout. An entry is
updated in place; a state-only update (``--state`` without ``--head``) keeps the build fields.
Standard library only: the workflow runs it with the runner's Python.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

POST = re.compile(r"^site/blog/(\d{4})-(\d{2})-(\d{2})-([^/]+)\.mdx?$")


def front_matter(text: str) -> dict[str, str]:
    """The simple ``key: value`` lines of a Markdown file's front matter."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    out: dict[str, str] = {}
    for line in text[3 : end if end > 0 else 0].splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip("'\"")
    return out


def post_link(path: str, root: Path) -> dict[str, str] | None:
    m = POST.match(path)
    if m is None or "/_" in path:
        return None
    y, mo, d, name = m.groups()
    f = root / path
    fm = front_matter(f.read_text(encoding="utf-8")) if f.exists() else {}
    slug = fm.get("slug", "").strip("/")
    url = f"blog/{slug}" if slug else f"blog/{y}/{mo}/{d}/{name}"
    return {"title": fm.get("title", name), "path": url, "date": f"{y}-{mo}-{d}"}


def update(
    index: dict[str, Any],
    pr: int,
    title: str,
    state: str,
    head: str | None,
    posts: list[dict[str, str]] | None,
    url: str | None,
    now: str,
) -> dict[str, Any]:
    entries = {e["number"]: e for e in index.get("previews", [])}
    e = entries.get(pr, {"number": pr})
    e["title"] = title or e.get("title", "")
    e["state"] = state
    e["state_at"] = now
    if url:
        e["url"] = url
    if head:
        e["head"] = head
        e["built_at"] = now
        e["path"] = f"pr/{pr}/"
        e["posts"] = posts or []
    entries[pr] = e
    index["previews"] = sorted(entries.values(), key=lambda x: -int(x["number"]))
    index["updated_at"] = now
    return index


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--index", required=True)
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--state", required=True, choices=("open", "merged", "closed"))
    ap.add_argument("--head")
    ap.add_argument("--posts-from")
    ap.add_argument("--url")
    ap.add_argument("--root", default=".", help="checkout the post files are read from")
    a = ap.parse_args(argv)
    p = Path(a.index)
    index = json.loads(p.read_text()) if p.exists() else {"previews": []}
    posts = None
    if a.posts_from:
        paths = Path(a.posts_from).read_text().split()
        posts = [x for x in (post_link(q, Path(a.root)) for q in sorted(set(paths))) if x]
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    index = update(index, a.pr, a.title, a.state, a.head, posts, a.url, now)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(index, indent=1) + "\n")
    print(json.dumps(next(e for e in index["previews"] if e["number"] == a.pr)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
