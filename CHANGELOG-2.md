# Changelog / lineage

## V0.2 — 2026-10-05 — PREREGISTERED
- Protocol and primary implementation hashed before execution.
- Canonical schedule candidate: UNIT_RANDOM_SEQUENTIAL. Comparison arm: NODE_RANDOM_SEQUENTIAL.
- Separate quantities: T_EIT (E↔M activity), MOBILITY_EIT (move-attempt rate), P_EIT (rejections).
- `P_EIT = rho_EIT × MOBILITY_EIT × Phi_emp` recorded as a definitional identity, not a test.
- Low-Phi policy: KEEP_CURRENT (decision by Toni Mladenovski, 2026-10-05).

## V0.1 exploratory findings (not preregistered)
- R1: P_EIT is not determined by rho_EIT × T_EIT; in V0.1, T_EIT ≈ 2a and does not affect P_EIT.
- R2: at fixed global occupancy, topology changes P_EIT strongly (star ≈ 4.5× ring).
- R3: the measured-Phi product is an identity; a predictor must be independent of rejection counts.
- R4: snapshot residual depends on update schedule; schedule is a model primitive.
- Synchronous update did not remove the residual under one declared conflict rule (adds competition).
- Opportunity-time predictor classified as a consistency check, not a test.

## V0.1 — source
- `h_space_minimal_core_v0_1.py`, SHA-256 cd3ea0a1a9d64da2a2474861e61b6216723f68ce5f716fd5b5dea9a0af0c19c4 (as reported by the author; not included here).
