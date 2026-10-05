#!/usr/bin/env python3
"""
NOVA Q / EIT — H_SPACE V0.2 PREREGISTERED SWEEP
STATUS: PREREGISTERED_PROTOCOL_IMPLEMENTATION / INTERNAL_DISCRETE_MODEL / NOT_PHYSICS
All constants below are frozen by H_SPACE_V0_2_PREREG_PROTOCOL.md. Do not edit after hashing.
Usage:  python3 h_space_v0_2_sweep.py            (full preregistered sweep -> JSON on stdout)
        python3 h_space_v0_2_sweep.py --smoke    (OFF-GRID instrumentation check only)
"""
from __future__ import annotations
import json, math, random, sys, platform
from decimal import Decimal, ROUND_HALF_UP
from multiprocessing import Pool

# ---------------- FROZEN CONSTANTS ----------------
CAPACITY = 8
P_EIT_TO_MATTER = 0.10      # a
P_TIE_TO_EIT = 0.05         # b
P_MOVE = 0.45               # MOBILITY_EIT
THETA_GRID = ["0.40", "0.50", "0.60", "0.70", "0.80", "0.90", "0.95"]
N_GRID = [12, 24, 48]
TOPOLOGIES = ["RING", "COMPLETE", "DIRECTED_CYCLE", "STAR", "RANDOM_GRAPH"]
SCHEDULES = ["UNIT_RANDOM_SEQUENTIAL", "NODE_RANDOM_SEQUENTIAL"]   # primary, comparison
PRIMARY_SCHEDULE = "UNIT_RANDOM_SEQUENTIAL"
SEEDS = list(range(101, 117))        # 16 independent dynamics seeds
BURN_IN = 500
HORIZON = 1500                       # evaluated steps after burn-in
TOL = 0.10
BOOT_B = 10000
BOOT_SEED = 20261005
MIN_VALID_STEP_FRACTION = 0.90       # per seed
MIN_REJECTIONS_PER_SEED = 50         # per seed, post-burn
RG_MEAN_DEGREE = 4
RG_SEED_BASE = 900000                # graph seed = RG_SEED_BASE + N (+1 per redraw)

# ---------------- CONSTRUCTION ----------------
def q_total_for(theta: str, n: int) -> int:
    return int((Decimal(theta) * n * CAPACITY).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def connected(adj):
    seen = {0}; stack = [0]
    while stack:
        for j in adj[stack.pop()]:
            if j not in seen: seen.add(j); stack.append(j)
    return len(seen) == len(adj)

def build_graph(topology: str, n: int):
    """Returns (out-neighbour dict, graph_seed_used or None)."""
    if topology == "RING":
        return {i: sorted({(i - 1) % n, (i + 1) % n}) for i in range(n)}, None
    if topology == "COMPLETE":
        return {i: [j for j in range(n) if j != i] for i in range(n)}, None
    if topology == "DIRECTED_CYCLE":
        return {i: [(i + 1) % n] for i in range(n)}, None
    if topology == "STAR":
        d = {0: list(range(1, n))}
        d.update({i: [0] for i in range(1, n)})
        return d, None
    if topology == "RANDOM_GRAPH":   # undirected Erdos-Renyi G(n,p), no self-loops, no multi-edges
        p = RG_MEAN_DEGREE / (n - 1)
        gs = RG_SEED_BASE + n
        while True:
            r = random.Random(gs)
            d = {i: set() for i in range(n)}
            for i in range(n):
                for j in range(i + 1, n):
                    if r.random() < p:
                        d[i].add(j); d[j].add(i)
            adj = {i: sorted(v) for i, v in d.items()}
            if all(adj[i] for i in adj) and connected(adj):
                return adj, gs
            gs += 1
    raise ValueError(topology)

# ---------------- DYNAMICS ----------------
def run_seed(args):
    topology, n, theta, schedule, seed, burn, horizon = args
    adj, _ = build_graph(topology, n)
    q = q_total_for(theta, n)
    # INITIAL STATE: all units in E form, round-robin over nodes 0..n-1
    E = [q // n + (1 if i < q % n else 0) for i in range(n)]
    M = [0] * n
    assert all(E[i] <= CAPACITY for i in range(n))
    rng = random.Random(seed)
    nodes = list(range(n))
    sum_emp = sum_snap = 0.0
    valid = 0; R_tot = A_tot = 0; Rhat_tot = 0.0
    for step in range(1, burn + horizon + 1):
        # PHASE 1: E<->M, nodes in ascending order, E draws then M draws (as V0.1)
        for i in nodes:
            ce = sum(1 for _ in range(E[i]) if rng.random() < P_EIT_TO_MATTER)
            cm = sum(1 for _ in range(M[i]) if rng.random() < P_TIE_TO_EIT)
            E[i] += cm - ce; M[i] += ce - cm
        # MOVE_PHASE_START
        full = [E[i] + M[i] >= CAPACITY for i in nodes]
        e_tot = sum(E)
        snap = (sum(E[i] * sum(full[j] for j in adj[i]) / len(adj[i]) for i in nodes) / e_tot) if e_tot else None
        # PHASE 2: opportunity roster fixed at MOVE_PHASE_START (one entry per E unit)
        if schedule == "UNIT_RANDOM_SEQUENTIAL":
            roster = [i for i in nodes for _ in range(E[i])]
            rng.shuffle(roster)
        elif schedule == "NODE_RANDOM_SEQUENTIAL":
            order = nodes[:]; rng.shuffle(order)
            roster = [i for i in order for _ in range(E[i])]
        else:
            raise ValueError(schedule)
        acc = rej = 0; rhat = 0.0
        for i in roster:
            nb = adj[i]
            rhat += P_MOVE * sum(E[j] + M[j] >= CAPACITY for j in nb) / len(nb)
            if rng.random() >= P_MOVE:
                continue
            j = nb[rng.randrange(len(nb))]
            if E[j] + M[j] >= CAPACITY:
                rej += 1
            else:
                E[i] -= 1; E[j] += 1; acc += 1
        assert sum(E) + sum(M) == q, "Q_TOTAL_CONSERVATION_FAILURE"
        assert all(0 <= E[i] and 0 <= M[i] and E[i] + M[i] <= CAPACITY for i in nodes), "CAPACITY_FAILURE"
        if step > burn:
            R_tot += rej; A_tot += acc + rej; Rhat_tot += rhat
            if snap is not None and acc + rej > 0:      # ZERO_ATTEMPT_GUARD
                sum_emp += rej / (acc + rej); sum_snap += snap; valid += 1
    return {"seed": seed, "valid_steps": valid, "rejections": R_tot, "attempts": A_tot,
            "r_hat": Rhat_tot,
            "phi_emp_seed": sum_emp / valid if valid else None,
            "phi_snapshot_seed": sum_snap / valid if valid else None}

# ---------------- CELL STATISTICS ----------------
def classify(seed_rows, horizon):
    guards = []
    for r in seed_rows:
        if r["valid_steps"] < MIN_VALID_STEP_FRACTION * horizon: guards.append("LOW_VALID_STEPS")
        if r["rejections"] < MIN_REJECTIONS_PER_SEED: guards.append("LOW_REJECTION_COUNT")
    emp = [r["phi_emp_seed"] for r in seed_rows]; snp = [r["phi_snapshot_seed"] for r in seed_rows]
    if any(x is None for x in emp) or sum(emp) == 0:
        return {"e": None, "ci95": None, "verdict": "INCONCLUSIVE", "guards": sorted(set(guards + ["ZERO_DENOMINATOR"]))}
    s = len(emp); me = sum(emp) / s; ms = sum(snp) / s
    e = (ms - me) / me
    br = random.Random(BOOT_SEED); boots = []
    for _ in range(BOOT_B):
        idx = [br.randrange(s) for _ in range(s)]          # paired resampling of seeds
        be = sum(emp[k] for k in idx) / s; bs = sum(snp[k] for k in idx) / s
        if be > 0: boots.append((bs - be) / be)
    boots.sort()
    lo = boots[int(math.floor(0.025 * len(boots)))]; hi = boots[int(math.ceil(0.975 * len(boots))) - 1]
    if guards: verdict = "INCONCLUSIVE"
    elif lo >= -TOL and hi <= TOL: verdict = "PASS"
    elif hi < -TOL or lo > TOL: verdict = "FAIL"
    else: verdict = "INCONCLUSIVE"
    R = sum(r["rejections"] for r in seed_rows); Rh = sum(r["r_hat"] for r in seed_rows)
    return {"e": e, "ci95": [lo, hi], "verdict": verdict, "guards": sorted(set(guards)),
            "mean_phi_emp": me, "mean_phi_snapshot": ms,
            "consistency_check_rel": (Rh - R) / R if R else None}

def main():
    smoke = "--smoke" in sys.argv
    if smoke:   # OFF-GRID: theta 0.75 is not in THETA_GRID
        cells = [(t, 12, "0.75", s) for t in TOPOLOGIES for s in SCHEDULES]; seeds = [1, 2, 3]; burn, hor = 100, 300
    else:
        cells = [(t, n, th, s) for s in SCHEDULES for t in TOPOLOGIES for n in N_GRID for th in THETA_GRID]
        seeds = SEEDS; burn, hor = BURN_IN, HORIZON
    jobs = [(t, n, th, s, sd, burn, hor) for (t, n, th, s) in cells for sd in seeds]
    with Pool() as pool:
        res = pool.map(run_seed, jobs, chunksize=4)
    out = []; k = len(seeds)
    for ci, (t, n, th, s) in enumerate(cells):
        rows = res[ci * k:(ci + 1) * k]
        q = q_total_for(th, n); _, gs = build_graph(t, n)
        c = classify(rows, hor)
        c.update({"topology": t, "n_nodes": n, "schedule": s, "theta_target": th, "q_total": q,
                  "theta_realized": q / (n * CAPACITY), "graph_seed": gs, "seed_rows": rows})
        out.append(c)
    prim = [c for c in out if c["schedule"] == PRIMARY_SCHEDULE]
    counts = {v: sum(c["verdict"] == v for c in prim) for v in ("PASS", "FAIL", "INCONCLUSIVE")}
    overall = "PASS" if counts["PASS"] == len(prim) else ("FAIL" if counts["FAIL"] else "INCONCLUSIVE")
    print(json.dumps({
        "artifact": "H_SPACE_V0_2_PREREGISTERED_SWEEP", "mode": "SMOKE_OFF_GRID" if smoke else "PREREGISTERED",
        "claim_boundary": ["INTERNAL_DISCRETE_MODEL", "NOT_PHYSICS"],
        "python": platform.python_version(),
        "constants": {"CAPACITY": CAPACITY, "a": P_EIT_TO_MATTER, "b": P_TIE_TO_EIT, "p_move": P_MOVE,
                      "seeds": seeds, "burn_in": burn, "horizon": hor, "tol": TOL, "boot_B": BOOT_B,
                      "boot_seed": BOOT_SEED, "min_rejections_per_seed": MIN_REJECTIONS_PER_SEED,
                      "min_valid_step_fraction": MIN_VALID_STEP_FRACTION,
                      "rg_mean_degree": RG_MEAN_DEGREE, "rg_seed_base": RG_SEED_BASE},
        "primary_schedule": PRIMARY_SCHEDULE, "primary_counts": counts, "overall_primary_verdict": overall,
        "cells": out}, indent=1))

if __name__ == "__main__":
    main()
