# Gate 1 decision record: amendment 1 (owner decision, 2026-11-01)

**What changes.** The validation rule's shuffled-label check. As registered
(`decision.json`, `validation_rule`), the shuffled-label control had to score "at naive level":
its validation median range error at least 0.8 × naive's. From this amendment it must be **no
better than batch least squares on the same rows**: the check fails (a leak) only when the
scenario-clustered 95% interval of its median range ratio to least squares lies wholly below 1.
Nothing else in the record changes: the criterion, the test seed, the carried rule, the other
two validation checks and the forecast stand.

**Why.** The control runs through the same physics layer as the carried model. With shuffled
labels its heads learn nothing useful, so its weights stay near uniform and its estimate stays
near batch least squares, whatever it learns. It cannot fall to naive level by construction
(constitution principle III: physics does the numerics), so the registered check would have
stopped the phase at validation for a reason unrelated to leakage. A leak through the learned
components would show as the control *beating* least squares, which the amended check tests.

**When, and what was known.** Decided by the owner on 2026-11-01, after training had started
(run 41319578497) and before the validation report was computed. What had been seen: the
per-epoch validation losses in the checkpoints (the normalised squared error of each model).
These showed the shuffled control at 3.29–3.39 against 3.27 for the physics models. No
validation-split metric at the gate rows, no ratio and no test-split result existed. Changing
a gate's criteria after a result exists is owner-only (AGENTS.md); this is that decision,
recorded before the report. Constitution principle IV's wording is amended in the same change.

**Applied by** `scripts/g1_validation.py` (check `shuffled-no-better-than-least-squares`).
