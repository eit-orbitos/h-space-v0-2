# NOVA Q / EIT — H_SPACE V0.2 PREREGISTERED SWEEP PROTOCOL

STATUS: PREREGISTERED_BEFORE_EXECUTION · INTERNAL_DISCRETE_MODEL · NOT_PHYSICS · NOT_FROZEN_LAW
Date written: 2026-10-05. The sweep has NOT been run.
Implementation: `h_space_v0_2_sweep.py`
SHA-256: `8b65e53442a0978f0ad8de397fe6ea174fb0f4cccb6a433173d3933c8ffc86c0`

## 0. Question under test

Does the snapshot predictor Phi_snapshot predict the empirical destination-full
fraction Phi_emp within ±10% relative error, across occupancy theta, size N and
topology, under UNIT_RANDOM_SEQUENTIAL scheduling?

`P_EIT = rho_EIT × MOBILITY_EIT × Phi_emp` is a DEFINITIONAL IDENTITY and is not tested.

## 1. Fixed model parameters

| Item | Value |
|---|---|
| CAPACITY per node | 8 (uniform) |
| a = P(E→M) per E unit per step | 0.10 |
| b = P(M→E) per M unit per step | 0.05 |
| MOBILITY_EIT = p_move | 0.45 |
| Destination rule | uniform over out-neighbours of the source node |

## 2. Grid (105 primary cells)

- THETA_GRID: 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95
- N_GRID: 12, 24, 48
- TOPOLOGY_SET: RING, COMPLETE, DIRECTED_CYCLE, STAR (hub = node 0), RANDOM_GRAPH
- Primary arm: UNIT_RANDOM_SEQUENTIAL (7 × 3 × 5 = 105 cells)
- Comparison arm: NODE_RANDOM_SEQUENTIAL (same 105 cells; reported, never used for the overall verdict or to tune anything)

## 3. INTEGER_Q_RULE

`Q_TOTAL = round_half_up(theta × N × 8)`, computed in decimal arithmetic
(Python `Decimal.quantize(..., ROUND_HALF_UP)`), never binary-float or banker's rounding.
Both theta_target and theta_realized = Q_TOTAL / (N × 8) are recorded per cell.

| N | Q_TOTAL for theta = 0.40 … 0.95 |
|---|---|
| 12 | 38, 48, 58, 67, 77, 86, 91 |
| 24 | 77, 96, 115, 134, 154, 173, 182 |
| 48 | 154, 192, 230, 269, 307, 346, 365 |

## 4. Initial state

All Q_TOTAL units start in E form. Node i receives floor(Q/N) units, plus one extra
if i < Q mod N. M = 0 everywhere.

## 5. RANDOM_GRAPH rule

Undirected Erdős–Rényi G(N, p) with p = 4 / (N − 1); no self-loops, no multi-edges.
Graph seed = 900000 + N, from a `random.Random` stream separate from dynamics.
Pairs (i, j), i < j, are visited in lexicographic order; edge iff draw < p.
If the graph is disconnected or has an isolated node, graph seed += 1 and redraw.
Resulting graphs (already determined by this rule): N=12 → seed 900012, 26 edges;
N=24 → seed 900024, 48 edges; N=48 → seed 900048, 112 edges.
One graph per N, shared by all theta, seeds and schedules.

## 6. Step order and schedule rule

Each macro-step n:

1. PHASE 1 — nodes in ascending id; at each node, one draw per E unit (convert if < a),
   then one draw per M unit (convert if < b), both counted on pre-step values.
2. MOVE_PHASE_START — state after phase 1. Phi_snapshot is measured here.
3. PHASE 2 — opportunity roster fixed at MOVE_PHASE_START: one entry per E unit,
   labelled by its source node. Units arriving during the step get no extra opportunity.
   - UNIT_RANDOM_SEQUENTIAL: roster built in ascending node order, then shuffled (`rng.shuffle`).
   - NODE_RANDOM_SEQUENTIAL: node order shuffled, then all entries of each node consecutively.
   For each entry: draw u; if u ≥ p_move, no attempt. Otherwise choose destination
   uniformly from out-neighbours; if destination total ≥ CAPACITY → REJECTED,
   else move one E unit → ACCEPTED. State updates immediately.

RANDOM_STREAM_RULE: one `random.Random(seed)` per run drives phase 1, shuffles,
attempt draws and destination draws, in the order above.

## 7. Seeds, burn-in, horizon

- SEED_LIST (dynamics): 101, 102, …, 116 (16 independent runs per cell)
- BURN_IN: 500 steps, discarded
- POST_BURN_HORIZON: 1500 steps
- Bootstrap seed: 20261005

## 8. Metrics

Per step t (post-burn), with A_t = accepted + rejected, R_t = rejected:

- Phi_emp,t = R_t / A_t
- Phi_snapshot,t = Σ_i E_i × (fraction of out-neighbours of i that are full) / Σ_i E_i, at MOVE_PHASE_START

ZERO_ATTEMPT_GUARD: a step is valid only if A_t > 0 and Σ E_i > 0. Invalid steps are
excluded from both means.

Per seed: Phi_emp_seed and Phi_snapshot_seed = plain means over that seed's valid steps.

PRIMARY_METRIC (per cell), RELATIVE_PREDICTION_ERROR:

    e = [ mean_seed(Phi_snapshot_seed) − mean_seed(Phi_emp_seed) ] / mean_seed(Phi_emp_seed)

Positive e = predictor overestimates rejection.

## 9. CI_PROCEDURE (locked)

Paired percentile bootstrap over the 16 seed-level pairs, B = 10000 resamples,
`random.Random(20261005)`. Each resample recomputes e as a ratio of means.
Interval = [sorted[floor(0.025·B)], sorted[ceil(0.975·B) − 1]].
Time steps within a trajectory are never treated as independent.

Known limitation, declared in advance: with 16 seeds the percentile bootstrap
tends to be slightly too narrow.

## 10. MINIMUM_EXPOSURE guards

A cell is INCONCLUSIVE regardless of its interval if, for any seed:

- valid steps < 0.90 × 1500, or
- post-burn rejections < 50, or
- mean Phi_emp over seeds = 0.

## 11. Verdict logic

Per cell, tolerance band [−0.10, +0.10]:

- PASS: no guard triggered AND CI lies entirely inside the band
- FAIL: no guard triggered AND CI lies entirely outside the band on one side
- INCONCLUSIVE: guard triggered, or CI crosses a band boundary

Overall (primary arm only):

- OVERALL PASS only if all 105 cells are PASS
- OVERALL FAIL if at least one cell is FAIL
- otherwise OVERALL INCONCLUSIVE

The tolerance, grid, seeds and guards are not to be changed after the run.

## 12. Consistency check (not a test)

R_hat = Σ_j p_j with p_j = p_move × (fraction of full out-neighbours of the source
immediately before opportunity j). Reported per cell as (R_hat − R) / R.
E[R − R_hat] = 0 by construction, so this is an instrumentation check only.
A small value does NOT exclude a hidden additional term. No decision rule is attached.

## 13. Manifest fields (emitted as JSON)

artifact, mode, python version, all constants, and per cell: topology, n_nodes,
schedule, theta_target, theta_realized, q_total, graph_seed, e, ci95, verdict,
guards, mean_phi_emp, mean_phi_snapshot, consistency_check_rel, and per seed:
seed, valid_steps, rejections, attempts, r_hat, phi_emp_seed, phi_snapshot_seed.

Replay: `python3 h_space_v0_2_sweep.py > report.json` (Python 3.13.16 used here;
`random` output can differ across Python versions, so record the version).

## 14. Disclosures

- The script was smoke-tested only in `--smoke` mode: theta = 0.75 (off-grid), N = 12,
  seeds 1–3, burn 100, horizon 300. Its output was seen. It is not evidence.
- theta = 0.75, N = 12 was explored earlier and motivated the ±10% tolerance.
  No grid cell has been run.
- EXPECTED IN ADVANCE: low-theta cells (0.40, likely 0.50) have Phi_emp near zero and
  will probably trigger LOW_REJECTION_COUNT → INCONCLUSIVE. Under rule 11 this makes
  OVERALL PASS unlikely for reasons unrelated to predictor quality.

## 15. Claim boundary

A PASS would mean only: in this toy model, at these parameters, a one-step local
occupancy snapshot predicts rejection frequency within 10%. It would not establish
a constitutive law, MEMORY, absence of missing variables, or anything physical.
