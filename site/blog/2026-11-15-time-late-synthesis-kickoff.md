---
title: "Kickoff: one last diagnostic, and the time-late track written up as a whole"
date: 2026-11-15T14:00
tags: [kickoff, spec-019]
---

The owner has chosen option B after spec 018: write up the time-late track (specs 013 to
018) as a whole, with the classical control standing, after one diagnostic on periods
already used. Spec: `specs/019-time-late-synthesis/`. Nothing is trained, no GPU is used
and no new seed is generated.

<!-- truncate -->

## Where we are

[Spec 018](/blog/2026/11/15/adaptive-prior) was decided by its panel in one round. A
control that chooses among 30 manoeuvre priors by one period's evidence gains nothing on
busier targets; the standing control stays. The search told the targets' own statistics is
about 1.15 better over three seeds, in a minority of periods. One thing was left
confounded: the family's members refitted shared candidates while the true prior had its
own search, and the family differed from the truth in parts never varied.

## Where this task moves to

SRD §1 and §5; a line in §9 records the decision (proposed; the owner merges).

1. **A ladder of priors.** From the broadened prior to the true one, taking on the busier
   targets' own statistics a part at a time (legs, turn sizes, turn rates, speed changes,
   kinds of manoeuvre), each with a search of its own; and each part alone. On 150 shifted
   periods of seed 347, already used: development work, not a result.
2. **Search against refit.** The family member nearest the truth, given its own search,
   against spec 018's refit of the same periods.
3. **The account.** One post covering specs 013 to 018: the standing system, each result
   as its panel left it, what was withdrawn, the forecasts that were wrong, what was never
   tested, and what the work adds to the project's founding question.
4. Independent reviewers check the account against the records; slides; PR.

The time-late track ends here unless the diagnostic shows something the owner wants
pursued.

Risks: the parts of a prior may interact, so that no rung "carries" the gain (both the
ladder and the single parts are run for that reason); 150 used periods separate only
large effects; a synthesis invites tidy conclusions the panels did not allow.

## How progress will be shown

- The ladder: each rung against the standing control, with the share of its gain in the
  ten best periods.
- Search of its own against refit for the nearest member.
- The track's gains in one chart: old system, search, control, by kind of target and
  bearing error, from the committed test records of specs 013 to 018.
- Track plots of example periods chosen by a rule, good and bad.
- All from committed experiment folders by scripts named in the slides post.

**Update, 2026-11-15 (evening).** Done. The diagnostic ran on 130 used periods: a search
of its own did no better than a refit, and the true prior's gain builds along the ladder,
legs first, with nothing separated. Three reviewers checked the account against the
records and corrected it. [The account](/blog/2026/11/15/time-late-synthesis) and
[the slides](/blog/2026/11/15/time-late-synthesis-slides).
