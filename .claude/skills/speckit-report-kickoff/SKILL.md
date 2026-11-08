---
name: "speckit-report-kickoff"
description: "Write the kickoff blog post for the current task (spec or gate run): where we are, where this task moves to, how progress will be shown."
argument-hint: "Optional: spec folder or gate id; defaults to the current feature branch's spec"
compatibility: "Requires .specify/ and site/blog/"
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

1. Find the task: the spec under `specs/` for the current branch (or the argument), or the gate
   id given. Read its `spec.md` (and `plan.md` if present), the last gate's write-up under
   `site/blog/`, and the project status in `AGENTS.md`.
2. Copy `site/blog/_templates/kickoff.md` to `site/blog/YYYY-MM-DD-<slug>-kickoff.md` with today's
   date and a slug from the task name. Fill every section; delete the template comments. Keep it
   under a page. The title starts with `Kickoff:`. Tags: `kickoff` and `spec-NNN` or `gate-x`.
3. "Where we are" states the last gate's verdict with a link to its post, what is carried and what
   is open. "Where this task moves to" names the SRD section(s), the criteria or acceptance, the
   plan in three to six steps, the risks and the stop condition. "How progress will be shown"
   names the figures the slides post will carry and the data they come from (seed, split or
   committed experiment).
4. Check the post builds: `cd site && npm run build` (or at least that the front matter parses and
   no `{...}` appears in prose: MDX treats it as an expression).
5. Report the file path. Do not open a PR for the post alone; it travels with the task's PR.

## Done When

- [ ] The kickoff post exists under `site/blog/` with the three sections filled.
- [ ] It links the last gate's write-up and the spec folder.
- [ ] It builds.
