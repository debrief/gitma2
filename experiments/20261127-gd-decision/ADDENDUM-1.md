# Addendum 1 (2026-11-28, after the test; a correction, no reading changed)

The decision record's limits say "the fine-tuned models met far ranges in a fifth of their
training stream". That is wrong: `configs/regress/held-course-ranges.json` draws initial ranges
of 2 to 20 km, as MAN2 does, and no training stream drew 20 to 30 km. Found by the panel
(`experiments/20261128-gd/review.md`, finding 7). The registered readings and lines are
unaffected; the README is left as registered.
