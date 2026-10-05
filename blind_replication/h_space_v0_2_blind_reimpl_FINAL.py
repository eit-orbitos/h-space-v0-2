#!/usr/bin/env python3
"""
NOVA Q / EIT - H_SPACE V0.2
BLIND PROTOCOL-ONLY REIMPLEMENTATION (fresh, from the protocol text alone).

Primary arm : UNIT_RANDOM_SEQUENTIAL (required, run in full)
Comparison arm NODE_RANDOM_SEQUENTIAL is NOT run (optional per the blind request).

Usage:
  python3 h_space_v0_2_reimpl.py --smoke        # quick sanity mode (not evidence)
  python3 h_space_v0_2_reimpl.py --resume       # run/resume full primary grid
Output: checkpoint JSONL in results_cells_<tag>.jsonl, final JSON in result.json
"""

import argparse
import hashlib
import json
import os
import platform
import random
import sys
import time
from decimal import Decimal, ROUND_HALF_UP

# ------------------------- fixed model parameters (protocol section 1-7) ----
CAPACITY = 8
A_RATE = 0.10            # P(E->M) per E unit per step
B_RATE = 0.05            # P(M->E) per M unit per step
P_MOVE = 0.45            # MOBILITY_EIT
THETA_GRID = [0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
N_GRID = [12, 24, 48]
TOPOLOGIES = ["RING", "COMPLETE", "DIRECTED_CYCLE", "STAR", "RANDOM_GRAPH"]
SEED_LIST = list(range(101, 117))   # 101..116 inclusive
BURN_IN = 500
POST_BURN_HORIZON = 1500
TOTAL_STEPS = BURN_IN + POST_BURN_HORIZON
BOOTSTRAP_B = 10000
BOOTSTRAP_SEED = 20261005
TOLERANCE = 0.10
MIN_VALID_STEPS = 0.90 * POST_BURN_HORIZON   # 1350
MIN_REJECTIONS = 50
PRIMARY_SCHEDULE = "UNIT_RANDOM_SEQUENTIAL"

# ------------------------- ambiguity-declared knobs -------------------------
# AMBIGUITY A: mechanism of the "uniform" destination draw.
#   DECLARED_CHOICE: rng.randrange(len(out_neighbours))  (exactly uniform).
#   alternative: int(u * len)  (uses the u2 = rng.random() draw).
# AMBIGUITY C: R_hat opportunity set.
#   DECLARED_CHOICE: p_j = P_MOVE * fullfrac(src) summed over ALL roster
#   entries (since p_j already contains the p_move factor).
#   alternative: sum fullfrac(src) over ATTEMPTS only (u < P_MOVE).
# AMBIGUITY D: RING / COMPLETE / STAR treated as UNDIRECTED (out-neighbours =
# all neighbours); DIRECTED_CYCLE is directed. Alternative: all directed.

def build_topology(topology, n, graph_rng_seed=None):
    """Return list of out-neighbour lists."""
    adj = [[] for _ in range(n)]
    if topology == "RING":
        for i in range(n):
            adj[i] = [(i - 1) % n, (i + 1) % n]
    elif topology == "COMPLETE":
        for i in range(n):
            adj[i] = [j for j in range(n) if j != i]
    elif topology == "DIRECTED_CYCLE":
        for i in range(n):
            adj[i] = [(i + 1) % n]
    elif topology == "STAR":   # hub = node 0, undirected
        for i in range(1, n):
            adj[i] = [0]
        adj[0] = list(range(1, n))
    elif topology == "RANDOM_GRAPH":
        p = 4.0 / (n - 1)
        seed = 900000 + n
        while True:
            grng = random.Random(seed)
            for i in range(n):
                for j in range(i + 1, n):
                    if grng.random() < p:
                        adj[i].append(j)
                        adj[j].append(i)
            seen = {0}
            stack = [0]
            while stack:
                u = stack.pop()
                for v in adj[u]:
                    if v not in seen:
                        seen.add(v)
                        stack.append(v)
            if len(seen) == n and all(len(a) > 0 for a in adj):
                return adj, seed
            seed += 1
        # unreachable
    else:
        raise ValueError(topology)
    if topology == "RANDOM_GRAPH":
        return adj, seed
    return adj, None


def q_total_round(theta, n):
    """INTEGER_Q_RULE: round_half_up in decimal arithmetic."""
    q = (Decimal(str(theta)) * Decimal(n) * Decimal(8)).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP)
    return int(q)


def run_seed(seed, n, adj, q, schedule, dest_mode="randrange", rhat_mode="all_entries"):
    """One dynamics run. Returns per-seed metrics dict."""
    rng = random.Random(seed)
    rr = rng.random
    # initial state: floor(q/n) per node, +1 for i < q % n, all E
    e = [q // n + (1 if i < q % n else 0) for i in range(n)]
    m = [0] * n
    total = [e[i] + m[i] for i in range(n)]   # total occupancy per node

    valid_steps = 0
    sum_phi_emp = 0.0
    sum_phi_snap = 0.0
    rejections = 0
    attempts = 0
    r_hat_sum = 0.0

    ecount_range = range(n)
    for step in range(TOTAL_STEPS):
        # PHASE 1 - nodes ascending; draws counted on pre-step values
        for i in ecount_range:
            ep = e[i]
            mp = m[i]
            conv = 0
            for _ in range(ep):
                if rr() < A_RATE:
                    conv += 1
            if conv:
                e[i] = ep - conv
                m[i] = mp + conv
            conv = 0
            for _ in range(mp):
                if rr() < B_RATE:
                    conv += 1
            if conv:
                m[i] -= conv
                e[i] += conv
        # recompute totals changed in phase 1
        for i in ecount_range:
            total[i] = e[i] + m[i]

        # MOVE_PHASE_START: snapshot
        sum_e = sum(e)
        # Phi_snapshot = sum_i E_i * fullfrac(out-neighbours of i) / sum_i E_i
        num = 0.0
        if sum_e > 0:
            for i in ecount_range:
                ei = e[i]
                if ei:
                    outs = adj[i]
                    full = 0
                    for v in outs:
                        if total[v] >= CAPACITY:
                            full += 1
                    num += ei * (full / len(outs))

        # PHASE 2 - roster fixed at MOVE_PHASE_START
        roster = []
        for i in ecount_range:
            if e[i]:
                roster.extend([i] * e[i])
        if schedule == "UNIT_RANDOM_SEQUENTIAL":
            rng.shuffle(roster)
        else:  # NODE_RANDOM_SEQUENTIAL
            nodes = [i for i in ecount_range if e[i]]
            rng.shuffle(nodes)
            roster = []
            for i in nodes:
                roster.extend([i] * e[i])

        acc = 0
        rej = 0
        post = step >= BURN_IN
        for src in roster:
            if post and rhat_mode == "all_entries":
                outs = adj[src]
                full = 0
                for v in outs:
                    if total[v] >= CAPACITY:
                        full += 1
                r_hat_sum += P_MOVE * (full / len(outs))
            u = rr()
            if u >= P_MOVE:
                continue
            if post and rhat_mode == "attempts_only":
                outs = adj[src]
                full = 0
                for v in outs:
                    if total[v] >= CAPACITY:
                        full += 1
                r_hat_sum += (full / len(outs))
            outs = adj[src]
            k = len(outs)
            if dest_mode == "randrange":
                dst = outs[rng.randrange(k)]
            else:  # int draw
                dst = outs[min(int(rr() * k), k - 1)]
            if total[dst] >= CAPACITY:
                rej += 1
            else:
                acc += 1
                e[src] -= 1
                e[dst] += 1
                total[src] -= 1
                total[dst] += 1

        if post:
            att = acc + rej
            if att > 0 and sum(e) > 0:
                valid_steps += 1
                sum_phi_emp += rej / att
                sum_phi_snap += num / sum_e
                rejections += rej
                attempts += att

    if valid_steps > 0:
        phi_emp_seed = sum_phi_emp / valid_steps
        phi_snap_seed = sum_phi_snap / valid_steps
    else:
        phi_emp_seed = None
        phi_snap_seed = None
    r_hat_rel = (r_hat_sum - rejections) / rejections if rejections > 0 else None
    return {
        "seed": seed,
        "phi_emp_seed": phi_emp_seed,
        "phi_snapshot_seed": phi_snap_seed,
        "valid_steps": valid_steps,
        "post_burn_rejections": rejections,
        "post_burn_attempts": attempts,
        "r_hat_sum": r_hat_sum,
        "r_hat_rel_seed": r_hat_rel,
    }


def cell_statistics(seed_results):
    """Aggregate + guards + bootstrap CI + verdict for one primary cell."""
    phis_emp = [r["phi_emp_seed"] for r in seed_results]
    phis_snap = [r["phi_snapshot_seed"] for r in seed_results]
    mean_emp = sum(phis_emp) / len(phis_emp)
    mean_snap = sum(phis_snap) / len(phis_snap)

    guards = []
    for r in seed_results:
        if r["valid_steps"] < MIN_VALID_STEPS:
            guards.append("LOW_VALID_STEPS(seed=%d)" % r["seed"])
            break
    for r in seed_results:
        if r["post_burn_rejections"] < MIN_REJECTIONS:
            guards.append("LOW_REJECTION_COUNT(seed=%d)" % r["seed"])
            break
    if mean_emp == 0:
        guards.append("MEAN_PHI_EMP_ZERO")

    if mean_emp != 0:
        e = (mean_snap - mean_emp) / mean_emp
        brng = random.Random(BOOTSTRAP_SEED)
        n_seeds = len(seed_results)
        boots = []
        for _ in range(BOOTSTRAP_B):
            se = 0.0
            ss = 0.0
            for _ in range(n_seeds):
                idx = brng.randrange(n_seeds)
                se += phis_emp[idx]
                ss += phis_snap[idx]
            se /= n_seeds
            ss /= n_seeds
            boots.append((ss - se) / se)
        boots.sort()
        ci_low = boots[int(0.025 * BOOTSTRAP_B)]      # floor(0.025*B) = 250
        ci_high = boots[9750 - 1]                     # ceil(0.975*B) - 1 = 9749
    else:
        e = None
        ci_low = None
        ci_high = None

    if guards:
        verdict = "INCONCLUSIVE"
    elif ci_low is None:
        verdict = "INCONCLUSIVE"
    elif ci_low >= -TOLERANCE and ci_high <= TOLERANCE:
        verdict = "PASS"
    elif ci_low > TOLERANCE or ci_high < -TOLERANCE:
        verdict = "FAIL"
    else:
        verdict = "INCONCLUSIVE"

    r_tot = sum(r["post_burn_rejections"] for r in seed_results)
    rh_tot = sum(r["r_hat_sum"] for r in seed_results)
    consistency_rel = (rh_tot - r_tot) / r_tot if r_tot > 0 else None

    return {
        "mean_phi_emp": mean_emp,
        "mean_phi_snapshot": mean_snap,
        "relative_prediction_error": e,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "guards_triggered": guards,
        "verdict": verdict,
        "consistency_check_rel": consistency_rel,
    }


def cell_id(topology, n, theta, schedule):
    return "%s|N=%d|theta=%s|%s" % (topology, n, theta, schedule)


def all_cells():
    cells = []
    for topology in TOPOLOGIES:
        for n in N_GRID:
            for theta in THETA_GRID:
                cells.append((topology, n, theta))
    return cells


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--alt-a", action="store_true",
                        help="alternative interpretation A (int(u*k) destination)")
    parser.add_argument("--alt-c", action="store_true",
                        help="alternative interpretation C (attempts-only R_hat)")
    args = parser.parse_args()

    t0 = time.time()
    if args.smoke:
        # smoke mode mirrors the protocol's own smoke settings (off-grid)
        n, theta = 12, 0.75
        adj, gs = build_topology("RANDOM_GRAPH", n)
        q = q_total_round(theta, n)
        print("smoke: N=12 theta=0.75 q=%d graph_seed=%s edges=%d"
              % (q, gs, sum(len(a) for a in adj) // 2))
        res = [run_seed(s, n, adj, q, PRIMARY_SCHEDULE) for s in (1, 2, 3)]
        for r in res:
            print(r)
        return

    tag = "primary"
    kw = {}
    if args.alt_a:
        tag = "altA"
        kw["dest_mode"] = "int_draw"
    elif args.alt_c:
        tag = "altC"
        kw["rhat_mode"] = "attempts_only"
    ckpt = "results_cells_%s.jsonl" % tag
    final = "result_%s.json" % tag

    cells = all_cells()
    done = {}
    if os.path.exists(ckpt):
        with open(ckpt) as f:
            for line in f:
                obj = json.loads(line)
                done[obj["cell_id"]] = obj

    for (topology, n, theta) in cells:
        cid = cell_id(topology, n, theta, PRIMARY_SCHEDULE)
        if cid in done:
            continue
        adj, gs = build_topology(topology, n)
        q = q_total_round(theta, n)
        theta_realized = q / (n * 8)
        seed_results = [run_seed(s, n, adj, q, PRIMARY_SCHEDULE, **kw)
                        for s in SEED_LIST]
        stats = cell_statistics(seed_results)
        cell_obj = {
            "cell_id": cid,
            "topology": topology,
            "n_nodes": n,
            "theta_target": theta,
            "schedule": PRIMARY_SCHEDULE,
            "q_total": q,
            "total_capacity": n * 8,
            "theta_realized": theta_realized,
            "graph_seed": gs,
            "seeds": seed_results,
        }
        cell_obj.update(stats)
        if args.alt_a:
            cell_obj["ambiguity_id"] = "A"
            cell_obj["interpretation"] = "destination = out_neighbours[min(int(u2*k), k-1)]"
        if args.alt_c:
            cell_obj["ambiguity_id"] = "C"
            cell_obj["interpretation"] = "R_hat summed over attempts only, p_j = fullfrac (no p_move factor)"
        done[cid] = cell_obj
        with open(ckpt, "a") as f:
            f.write(json.dumps(cell_obj) + "\n")
        print("DONE %s e=%s verdict=%s (%.1fs elapsed)"
              % (cid, stats["relative_prediction_error"], stats["verdict"],
                 time.time() - t0), flush=True)

    if len(done) == len(cells):
        out = build_report(done, cells, tag, time.time() - t0, kw)
        with open(final, "w") as f:
            json.dump(out, f, indent=1)
        print("REPORT WRITTEN %s (%.1fs)" % (final, time.time() - t0), flush=True)
    else:
        print("PARTIAL: %d/%d cells done; rerun with --resume" % (len(done), len(cells)),
              flush=True)


def build_report(done, cells, tag, wall, kw):
    ordered = [done[cell_id(t, n, th, PRIMARY_SCHEDULE)]
               for (t, n, th) in cells]
    verdicts = [c["verdict"] for c in ordered]
    level7 = {
        "primary_arm_schedule": PRIMARY_SCHEDULE,
        "pass_count": verdicts.count("PASS"),
        "fail_count": verdicts.count("FAIL"),
        "inconclusive_count": verdicts.count("INCONCLUSIVE"),
        "ambiguity_blocked_count": verdicts.count("BLOCKED_BY_PROTOCOL_AMBIGUITY"),
        "overall_protocol_status": None,
    }
    if level7["pass_count"] == len(ordered):
        level7["overall_protocol_status"] = "OVERALL_PASS"
    elif level7["fail_count"] > 0:
        level7["overall_protocol_status"] = "OVERALL_FAIL"
    else:
        level7["overall_protocol_status"] = "OVERALL_INCONCLUSIVE"

    protocol_path = "/home/user/uploads/H_SPACE_V0_2_PREREG_PROTOCOL-2.md"
    with open(protocol_path, "rb") as f:
        phash = hashlib.sha256(f.read()).hexdigest()

    report = {
        "level1_protocol": {
            "protocol_filename": "H_SPACE_V0_2_PREREG_PROTOCOL-2.md",
            "protocol_sha256": phash,
            "protocol_hash_match": phash == "d511d62804727e6153abdc4652d8bdda3c3926c2a9540efefd5de06f3d9f5052",
        },
        "level2_coverage": {
            "expected_cell_count": 105,
            "constructed_cell_count": len(ordered),
            "missing_cells": [],
            "duplicate_cells": [],
        },
        "cells": ordered,
        "level7_global": level7,
        "environment": {
            "language": "Python",
            "language_version": platform.python_version(),
            "os": platform.platform(),
            "random_generator": "random.Random (Mersenne Twister, Python stdlib)",
            "wall_time_seconds": wall,
            "result_status": "COMPLETE" if len(ordered) == 105 else "PARTIAL",
        },
    }
    return report


if __name__ == "__main__":
    main()
