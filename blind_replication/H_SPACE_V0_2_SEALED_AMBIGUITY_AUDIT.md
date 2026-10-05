# H_SPACE V0.2 — SEALED AMBIGUITY AUDIT (written by the primary implementer)

Written 2026-10-05, AFTER the primary run and CI replay, BEFORE any blind second implementation exists.
Author has seen primary source and primary results. Purpose: record, in advance, where the frozen
protocol text underdetermines the primary implementation, so a blind implementer's ambiguity reports
can later be compared against this list. NOT to be shown to the blind implementer.

Protocol SHA-256: d511d62804727e6153abdc4652d8bdda3c3926c2a9540efefd5de06f3d9f5052
Primary source SHA-256: 8b65e53442a0978f0ad8de397fe6ea174fb0f4cccb6a433173d3933c8ffc86c0

## A. Affects statistics (could change CI and therefore a boundary verdict)

A1. BOOTSTRAP STREAM SCOPE. Protocol: `random.Random(20261005)`. Not stated whether one stream runs
    across all cells or is re-seeded per cell. Primary: re-seeded per cell.
A2. BOOTSTRAP INDEX DRAW. Protocol: "paired percentile bootstrap over the 16 seed-level pairs".
    Draw method not stated. Primary: 16 calls of `randrange(16)` per resample.
A3. DEGENERATE RESAMPLE. Resample with mean Phi_emp = 0 — handling not stated. Primary: skipped,
    percentile indices computed on the remaining count.
A4. REJECTION GUARD SCOPE. "post-burn rejections < 50" — over all post-burn steps or only valid
    steps is not stated. Primary: all post-burn steps.

## B. Affects bit-level reproduction only (same distribution, different random stream)

B1. DESTINATION DRAW FOR DEGREE-1 NODES. Protocol: "choose destination uniformly from out-neighbours".
    Whether a random draw is consumed when there is exactly one neighbour is not stated.
    Primary: always calls `randrange(len(neighbours))`, which consumes random bits even for length 1.
    Affects DIRECTED_CYCLE (all nodes) and STAR (all leaves).
B2. DESTINATION DRAW METHOD. `randrange(k)` vs float-based index not stated. Primary: `randrange`.
B3. NEIGHBOUR LIST ORDER. Not stated. Primary: ascending node id.
B4. RNG ENGINE. Protocol names `random.Random` (CPython Mersenne Twister). An implementation in
    another language or with numpy cannot match seed-level numbers.
B5. PHASE-1 DRAW ORDER WITHIN A NODE is stated (E draws then M draws); order across nodes is stated
    (ascending). No ambiguity found, listed for completeness.

## C. Not an ambiguity but a disclosure

C1. Protocol section 14 states an expectation in advance (low-theta cells probably INCONCLUSIVE).
    It contains no results. A blind implementer will read this expectation.
C2. The protocol defines NO numerical tolerance for agreement between two implementations.

## Prediction recorded in advance

- A faithful blind implementation that does not happen to reproduce B1–B4 will NOT match primary
  seed-level numbers bit-for-bit.
- Cell verdicts should still agree except possibly in cells whose CI lies close to ±0.10.
- If the blind implementer reports none of A1–A4, the "report ambiguity, do not choose silently"
  rule was not effective.
