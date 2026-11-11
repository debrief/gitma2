"""Time-late TMA (spec 013): the whole track over a period of bearings.

A period is a random portion of a 5-second engagement. A time-late solution is the target's
state at every row of the period; it is scored at every row against the truth and against a
Cramér–Rao bound for that row given all the period's bearings. Nothing here is trained.
"""
