# Feature Specification: Publish the site, a time-late page, and persistent PR previews

**Feature Branch**: `022-site-publishing` (developed on `claude/keen-wozniak-77td7j`)

**Created**: 2026-11-16

**Status**: Draft

**Input**: Owner, 2026-11-16: "A + B + PR Preview instances. These will link to persistent
copies of the blog-post of feature being delivered in that PR. The link will remain valid after
the PR has completed. There will be a clickable index of PRs in the site." The options were:
- **A**: publish the whole site to GitHub Pages on each merge;
- **B**: a time-late page showing the standing system's tracks beside the truth and the old
  system.

**SRD traceability**: §1 (the browser viewer; the site and its process, as gitma). AGENTS.md
Reporting: the blog posts are the project's progress reports. Publishing on this repository's own
site is within the agent's remit. Publishing elsewhere is not.

## Background

The site (welcome page, glossary, data dictionary, blog, slide decks, viewer) is built in CI
only to check that it compiles. The `gh-pages` branch holds the initial commit's README, so
`https://debrief.github.io/gitma2/` shows that README and every other path returns 404. The
owner's current focus is time-late TMA (specs 013 to 019), whose performance exists only in
Markdown files and SVG figures in the repository.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the site online (Priority: P1)

After a merge to `main`, the owner opens `https://debrief.github.io/gitma2/` and finds the
current site: the blog with every write-up and slide deck, the viewer, and the time-late page.

**Independent Test**: After a merge, fetch the root, a blog post and `/viewer`, and expect
HTTP 200 for each, with the post's title in the page.

**Acceptance Scenarios**:

1. **Given** a merge to `main`, **When** the deploy finishes, **Then** the published root
   serves that commit's site, and the footer or page source names the commit.
2. **Given** published PR previews, **When** `main` deploys, **Then** every preview is still
   there.

---

### User Story 2 - See time-late performance (Priority: P1)

The owner opens `/timelate` and sees, on simulated periods from spec 016's test record (seed
341, used):
- for each of three kinds of period (Annex B targets, 2% wild bearings, a shifted manoeuvre
  prior), the whole track of the truth, the standing classical control, C″ (the old system read
  as a track), the true-history reference and the learned model's arc read-out;
- a timeline of true manoeuvres against each system's declared ones;
- each system's median range error over the period;
- the headline figures of the time-late account, with a link to it.

**Independent Test**: Open `/timelate` headless, select each split and a period, and check that
the tracks, the timeline and the error table are drawn from the committed record's values.

**Acceptance Scenarios**:

1. **Given** the page, **When** a period is chosen, **Then** its tracks, its manoeuvre
   timeline and its per-system median range errors are shown. The errors agree with the record
   (`tracks.npz`), recomputed the way the scorer does.
2. **Given** the page, **Then** it says plainly:
   - what the systems are;
   - which seed and record the periods come from;
   - that these 20 periods a split are the first stored, not chosen;
   - that the figures of record are in the account.

---

### User Story 3 - A persistent preview of each PR's report (Priority: P1)

Every pull request from this repository builds the site at its head and publishes it at
`/pr/<number>/`. That copy stays after the PR is merged or closed. The site's `/previews` page
lists every PR with a preview:
- its number, title and state (open, merged or closed);
- a link to the preview;
- links to the blog posts the PR adds or changes, opened in that preview.

**Independent Test**: Open a PR that adds a blog post. Wait for the preview workflow. Open
`/previews`, follow the PR's post link, and expect the post. Merge the PR and check that the link
still works and that the state reads "merged".

**Acceptance Scenarios**:

1. **Given** a PR is opened or updated, **Then** its preview is rebuilt at its head commit, and
   the index records that commit.
2. **Given** a PR is merged or closed, **Then** its preview stays, and its state in the index
   changes.
3. **Given** a PR from a fork, **Then** no preview is built and no index entry is made.
4. **Given** the build, **Then** it runs the PR's code without write access, and the publishing
   job runs no npm code (review finding 5).

### Edge Cases

- Two deploys at once (a merge and a PR update): they must not overwrite each other.
  Deploys are serialised.
- A PR that adds no blog post still gets a preview, listed with no post links.
- Size: GitHub Pages limits a published site to 1 GB, and every preview's files count, even if
  git stores identical files once. Previews leave out the 15 MB browser runtime and load the
  root's, so each costs about 12 MB. That allows roughly 80 previews before pruning is needed,
  and pruning is the owner's decision.
- Pages must serve from the `gh-pages` branch. If the repository's Pages setting is otherwise,
  the owner changes it. Nothing here can.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A workflow MUST build the site on every push to `main` and publish it at the root
  of `gh-pages`, leaving `pr/` untouched. A `.nojekyll` file MUST be present.
- **FR-002**: The same workflow MUST, for every same-repository PR opened, reopened or
  synchronised:
  - build the site with base URL `/gitma2/pr/<number>/`;
  - publish it at `pr/<number>/`;
  - update `pr/index.json` with the PR's number, title, state, head commit, update time and the
    blog posts it adds or changes.

  On a closed PR it MUST update only the state, recording merged or closed.
- **FR-003**: Concurrent deploys MUST NOT lose each other's changes. Each deploy re-applies its
  change to the branch's latest state until its push succeeds, regenerating the index rather
  than merging it. A preview whose commit is no longer the PR's head is not published.
  (Amended after review: a concurrency group cannot serialise runs, because GitHub cancels
  queued runs in the same group.)
- **FR-004**: The site MUST have a `/previews` page that reads the root's `pr/index.json` and
  lists the previews, newest first, with clickable links. On a preview build it MUST still read
  the root index.
- **FR-005**: The time-late page (`/timelate`) MUST be built from committed records by a script
  (`scripts/research/timelate_viewer_data.py`). The data MUST carry a manifest with source
  digests. The page MUST NOT compute any estimate itself.
- **FR-006**: The navbar MUST link the time-late page and the previews index.
- **FR-007**: A manual trigger MUST be able to build a preview for an earlier PR at a given
  commit, to backfill PRs merged before this feature.

## Success Criteria *(mandatory)*

- **SC-001**: After a merge, the published root, a blog post, `/viewer`, `/timelate` and
  `/previews` all return 200.
- **SC-002**: A PR's preview and its post links work while it is open and after it is merged.
- **SC-003**: The time-late page's per-period median range errors equal the record's values
  recomputed in Python, to 1e-6 relative.

## Assumptions

- GitHub Pages is set to serve the `gh-pages` branch: its root serves the README there today.
- Previews are kept indefinitely, as the owner asked. If the branch grows too large, pruning is
  the owner's decision, since deleting published copies is owner-only.
- The time-late periods come from spec 016's test record, the only record with tracks for three
  splits. Spec 017's and spec 018's records hold the shifted split only.
- No PR comments are posted: the index and the workflow's job summary carry the links, and
  comments would notify people.
