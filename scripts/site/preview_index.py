"""Maintain the PR preview index on the gh-pages branch (spec 022).

    python3 scripts/site/preview_index.py --index <gh-pages>/pr/index.json --pr N \\
        --title T --state open|merged|closed [--head SHA] [--posts-from FILE] [--url URL] \\
        [--comment FILE --site URL]

``--posts-from`` is a list of the PR's added or modified paths, one per line (removed files
excluded by the caller). Blog posts
among them (``site/blog/*.md`` or ``.mdx``, not templates) become links into the preview:
``YYYY-MM-DD-name.md`` → ``blog/YYYY/MM/DD/name`` unless the front matter sets a ``slug``. The
title is the front matter's ``title``, read from the file as it is in the checkout. An entry is
updated in place; a state-only update (``--state`` without ``--head``) keeps the build fields.
``--comment`` writes the PR comment that links the preview (issue 44): one comment per PR,
found by its first line (``MARKER``) and edited in place by the workflow. Standard library only: the workflow runs it with the runner's Python.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

MARKER = "<!-- site-preview -->"
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


def _md(s: str) -> str:
    """Text safe inside a Markdown link label: no brackets, markup or HTML."""
    return re.sub(r"[\\\[\]<>`*_|]", "", s).strip() or "post"


def comment_body(entry: dict[str, Any], site: str) -> str:
    """The preview comment for one index entry; ``site`` is the root URL with a trailing /."""
    site = site.rstrip("/") + "/"
    n = entry["number"]
    base = f"{site}pr/{n}/"
    lines = [MARKER, f"**Preview:** {base}", ""]
    posts = entry.get("posts") or []
    if posts:
        lines.append("Posts added or changed in this PR:")
        lines += [f"- [{_md(p['title'])}]({base}{p['path']})" for p in posts]
        lines.append("")
    head = str(entry.get("head", ""))[:7]
    lines.append(f"Built from `{head}` · all previews: {site}previews")
    lines += [
        "",
        "<sub>Rebuilt on every push to this PR and kept after it closes. "
        "GitHub Pages can take a minute or two to update.</sub>",
    ]
    return "\n".join(lines) + "\n"


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
    ap.add_argument("--comment", help="write the PR's preview comment to this file")
    ap.add_argument("--site", default="https://debrief.github.io/gitma2/")
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
    entry = next(e for e in index["previews"] if e["number"] == a.pr)
    if a.comment:
        Path(a.comment).write_text(comment_body(entry, a.site))
    print(json.dumps(entry))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
