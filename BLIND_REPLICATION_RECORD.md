# H_SPACE V0.2 — BLIND REPLICATION RECORD

STATUS: INTERNAL_MATHEMATICAL_MODEL · NOT_PHYSICS · ZENODO / FREEZE / PUBLICATION = HOLD
Record written 2026-10-05 by the primary implementer (Claude), who has seen all artifacts.

## 1. Summary status

    PROTOCOL_FREEZE                          = COMPLETE
    PRIMARY_IMPLEMENTATION                   = COMPLETE
    CROSS_PLATFORM_CI                        = PASS (Linux / Windows / macOS, identical canonical report)
    BLIND_PROTOCOL_ONLY_IMPLEMENTATION       = COMPLETE (source delivered)
    MISTRAL_SELF_EXECUTION                   = UNVERIFIED_DUE_TO_INTERRUPTED_SESSION
    SEALED_BLIND_SOURCE_REPLAY               = PASS
    BLIND_SOURCE -> DELIVERED_JSON MATCH     = 105 / 105 cells bit-identical
    PRIMARY vs BLIND VERDICT AGREEMENT       = 105 / 105
    PRIMARY vs BLIND NUMERICAL AGREEMENT     = 4 topologies to ~1e-16; RING differs
    OVERALL V0.2 RESULT                      = NOT_PASS_INCONCLUSIVE (101 PASS / 0 FAIL / 4 INCONCLUSIVE)
    PHYSICAL_VALIDATION                      = NO

## 2. Artifacts and hashes (SHA-256)

| Artifact | SHA-256 |
|---|---|
| H_SPACE_V0_2_PREREG_PROTOCOL.md | d511d62804727e6153abdc4652d8bdda3c3926c2a9540efefd5de06f3d9f5052 |
| h_space_v0_2_sweep.py (primary source) | 8b65e53442a0978f0ad8de397fe6ea174fb0f4cccb6a433173d3933c8ffc86c0 |
| primary canonical report, Python 3.13.16 (local) | a4a85be7a03a0b6bbd15935a282b24e609f15c6da0d169fae5fec726e818e5ab |
| primary canonical report, Python 3.13.15 (GitHub CI run #1, all three OS) | 7fea63676bc1757f99abf6ac260107ce2b7593f55088ddf0adfb2ff7cb8eea56 |
| H_SPACE_V0_2_BLIND_REQUEST.txt | 5a04d3a98c5b493dfe617fa38c46c847761024b293a852d975e03b8df66479ba |
| H_SPACE_V0_2_SEALED_AMBIGUITY_AUDIT.md | bf3285b07f1bdfb9c1bb95be533cd348323a6d42395e9b3c01bb7aae1a1857eb |
| h_space_v0_2_blind_reimpl_FINAL.py (blind source) | 44e56469a0eae21e8fd06778b8a58bc6f8d6842f64ebb67b03bad16229b12dc6 |
| h_space_v0_2_blind_result_FINAL.json (blind result) | 7257bd98ef0cb2936752244268c8e34b0bcb67ab189292e4ee78df941cd11082 |
| DELIVERY_MANIFEST.txt (from the blind implementer) | c10cef2b38ddaf43773d595ea38bb854fdec9b647c3c1ccfff4aea081f9230ea |

The two CI/local primary hashes differ only in the recorded Python version string; changing
"3.13.16" to "3.13.15" in the local report reproduces the CI hash exactly.
The CI hash was read from a screenshot of run #1; run #2 passed the identity check but its hash
value was not read.

## 3. Blind test conditions

- Implementer: Mistral, official chat.mistral.ai ("Work mode"), new account, no prior use
  for this project (user-reported). Model version not recorded.
- Inputs given: the protocol file and the blind request file, plus one sentence pointing to them.
  Nothing else.
- BLINDNESS_MODEL = HONOR_BASED. The primary repository is public; the request forbade access.
  FULL_CRYPTOGRAPHIC_BLINDNESS = NO.
- OUTCOME_BLIND = YES (no primary result values supplied).
  HYPOTHESIS_BLIND = NO (protocol section 14 states an expectation about low-theta cells).
- The blind request was written by the primary implementer, who had seen primary results.
  It was reviewed for leakage by three other AI reviewers before dispatch.
- Dispatch: 2026-10-05 12:10 EDT. Delivery files visible: 14:12 EDT.
  Sealed by hash on receipt: 2026-10-05 18:17 UTC, before any comparison with primary results.
  The source was received and sealed first; the result JSON was received about 13 minutes later
  and matched the hash already stated in the implementer's manifest.

## 4. Execution observation

The Mistral session experienced repeated connection interruptions (at least 7 attempts observed
through screenshots; the user reports about 10). The implementer worked first in JavaScript with a
ported Mersenne Twister, later in Python; it rebuilt its engine at least once mid-run and persisted
partial results between attempts.

A clean, uninterrupted full-grid completion by Mistral was NOT independently observed.

    MISTRAL_SELF_EXECUTION_STATUS = UNVERIFIED_COMPLETE

The delivered JSON reports result_status = COMPLETE (Python 3.12.13, wall time 410 s). That
self-report is not treated as independently verified.

    NO CLAIM: the results were fabricated.
    NO CLAIM: the results were completed in the background.
    STATUS  : how and when the original session computed each cell is UNKNOWN.

## 5. Sealed implementation replay

The delivered FINAL blind source was executed by the primary implementer after delivery
(Python 3.13.16, 229 s, command `--resume`, protocol file placed at the path the source expects).

    105 / 105 cells reproduced bit-for-bit against the delivered Mistral JSON
    (fixtures, all seed-level metrics, means, relative error, CI bounds, verdicts).

This establishes SOURCE -> RESULT REPRODUCIBILITY. The delivered numerical results are reproducible
by executing the sealed FINAL source, and the delivered JSON matches that replay bit-for-bit across
all 105 cells.

The original Mistral session execution path remains unknown.

## 6. Primary vs blind comparison

| Level | Result |
|---|---|
| 1 Protocol bytes | match |
| 2 Cell coverage | 105 / 105, no missing, no duplicates |
| 3 Fixtures (Q_TOTAL, theta_realized, graph seed) | 105 / 105 |
| 4 Seed-level metrics | bit-exact in 37 cells; COMPLETE, DIRECTED_CYCLE, STAR, RANDOM_GRAPH agree to <= 4.4e-16; RING differs (max 0.029) |
| 5 Confidence intervals | same pattern: four topologies to <= 6.5e-16; RING differs (max 0.047) |
| 6 Cell verdicts | 105 / 105 |
| 7 Overall status | identical: OVERALL_INCONCLUSIVE, 101 / 0 / 4, same four cells |

No numerical tolerance for inter-implementation agreement was defined in advance, so levels 4-5
are reported as observed and not graded. NUMERICAL_AGREEMENT_VERDICT = UNRESOLVED_BY_DESIGN.

Cause of the RING difference: neighbour list order. Primary uses ascending node id; the blind
source uses (i-1, i+1), which reverses the order at two nodes and therefore the destination chosen
by the same random draw. Statistically equivalent, numerically different.
Sub-1e-15 differences elsewhere come from floating-point summation order.

The four INCONCLUSIVE cells (both implementations):
RING N=12 theta=0.40 (low rejections), COMPLETE N=12 theta=0.40 (low rejections),
DIRECTED_CYCLE N=12 theta=0.40 and N=24 theta=0.40 (CI crosses +0.10).

## 7. Sealed ambiguity audit vs blind ambiguity report

| Sealed item (primary implementer, before blind run) | Reported by blind implementer (final JSON) |
|---|---|
| A1 bootstrap stream scope | YES (its B) |
| A2 bootstrap index draw method | NO in final JSON (present in an earlier draft source) |
| A3 degenerate resample | NO |
| A4 rejection guard scope | YES (its E) |
| B1 draw consumed for degree-1 nodes | NO |
| B2 destination draw method | YES (its A) |
| B3 neighbour list order | NO — chosen silently; the only ambiguity that changed numbers |
| B4 RNG engine | not reported as ambiguity; implementer reproduced CPython's generator |

Found by the blind implementer and missing from the sealed audit:
R_hat opportunity set (its C); directedness of RING / COMPLETE / STAR (its D).
An earlier draft source additionally listed: meaning of "pre-step values", definition of
destination "total", exact-zero reading of the mean guard.

The "report ambiguity, do not choose silently" rule was partially effective: 3 of 7 sealed items
reported; at least B1 and B3 were resolved silently.

Sealed prediction check: "seed-level numbers will not match bit-for-bit" — wrong for four
topologies (agreement to rounding), right for RING. "Verdicts agree except possibly near ±0.10" —
held; the fragile cell DIRECTED_CYCLE N=48 theta=0.40 (CI upper 0.098) stayed PASS.

## 8. Known weaknesses

- Honor-based blindness. The blind source coincides with the primary on several unstated choices
  (per-cell bootstrap re-seed, randrange for destinations including degree-1 nodes). The protocol
  names the Python functions, so this is explicable, but source non-exposure cannot be proven.
- One implementer, one run. No second blind implementer.
- Latent bug in the blind source: on a random-graph redraw the adjacency lists are not cleared.
  No effect here (all three graphs succeed on the first seed).
- The implementer's alternative-interpretation script (alt_runs.py) references engine functions not
  present in the delivered FINAL source; its alternative results were not replayed or verified.
- The comparison arm (NODE_RANDOM_SEQUENTIAL) was not run by the blind implementer.
- Two primary/blind files and all comparisons were handled by the primary implementer.

## 9. What may be claimed

- A second implementation, written from the protocol text by a model of a different family,
  yields the same 105 cell verdicts and the same overall status.
- The protocol is NOT precise enough for bit-identical numbers; neighbour order at minimum must be
  specified.
- V0.2 did not pass its preregistered criterion. The replication shows that this outcome is
  reproducible, not that the model passed.
- No post-hoc rescue rule was applied. Any fix to the protocol is a V0.2.1 candidate requiring a
  new version, new hash and new preregistration.
- Nothing here is a physical result.
  
