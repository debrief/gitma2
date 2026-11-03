# Specification Quality Checklist: Steady-leg segmentation and Gate S

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-11-03
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Readers are the owner and the review panel. Domain terms are defined in the spec's
  Definitions table or in the site glossary.
- Method names stay where they carry a requirement that a careful colleague could not otherwise
  check:
  - **The two-stage search (FR-022) and the semi-Markov likelihood (FR-042)** define what C must
    do and how L can learn. Leaving them out would let L repeat Gate D's failure, a hard decoder
    with no gradient.
  - **ONNX (FR-045)** is the constitution's portability rule.

  No language, library or file layout is specified.
- Values left to the decision record (S1 and S3 limits, the margin, k, the physics-layer mode,
  the gap normalisation) are deliberately not fixed here. The constitution requires them to be
  fixed before training, not before specification.
- Every owner decision from the review is recorded in the spec:
  - C, S, L_min and T_min;
  - offline on each prefix only;
  - C alone is acceptable;
  - no paid compute.
