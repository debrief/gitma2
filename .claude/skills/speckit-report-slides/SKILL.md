---
name: "speckit-report-slides"
description: "Build the slides post for the current task before its PR: a reveal.js deck with an illustrated overview and a demonstration of progress (charts, track plots), embedded in a blog post."
argument-hint: "Optional: spec folder or gate id; defaults to the current feature branch's spec"
compatibility: "Requires .specify/, site/blog/, site/static/slides/ and tma2-plot"
metadata:
  author: "gitma2"
  source: "AGENTS.md, Reporting"
user-invocable: true
disable-model-invocation: false
---

## User Input

```text
$ARGUMENTS
```

## Outline

1. Find the task (as `/speckit-report-kickoff`) and its kickoff post; the kickoff's "How progress
   will be shown" section is the figure list to deliver. For a gate, also read its write-up: the
   slides post is the write-up's illustrated companion and links to it, it does not retell it.
2. Make the figures, each by a committed command, into `site/static/img/<date-slug>/`:
   - Data: a seeded demo split (`tma2-generate`, name seed, count and ranges) or a committed
     experiment's predictions. Never hand-edit a figure.
   - Track plots: `tma2-plot track --truth ... --predictions ... --labels ... --scenario i --at
     t1,t2 --out site/static/img/<date-slug>/track-i.svg`. Choose scenarios that show the point
     (a near one for legibility, one where the estimator struggles). Always include the
     estimators the constitution requires on the same rows where they exist: naive or one leg,
     batch least squares, the tuned IMM, the oracle, and the task's own estimator.
   - Error curves: `tma2-plot errors ...`. Metric charts from a scoring run: a script under
     `scripts/research/`, named in the post with its commit.
   - Keep the `.json` sidecars next to the SVGs; keep each figure under about 200 KB.
3. Copy `site/static/slides/_template/` to `site/static/slides/<date-slug>/` and fill the deck:
   overview (illustrated, one idea per slide), demonstration (the figures), not achieved, next.
   Reference figures as `../../img/<date-slug>/<file>.svg`.
4. Copy `site/blog/_templates/slides.md` to `site/blog/YYYY-MM-DD-<slug>-slides.md`; fill it, set
   `<Slides slug="<date-slug>" />`, list the exact commands under "Reproducing the figures".
5. Build the site (`cd site && npm ci && npm run build`) and open the deck once with Playwright
   (headless Chromium is installed) to check that each figure loads and no slide is empty.
6. Commit the post, the deck and the figures on the task's branch *before* opening the PR, and
   name the post in the PR description.

## Done When

- [ ] Figures exist with sidecars and were made by commands recorded in the post.
- [ ] The deck has the four parts and every image loads.
- [ ] The post embeds the deck and builds.
- [ ] Committed on the task branch before the PR is opened.
