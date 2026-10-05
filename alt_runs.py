#!/usr/bin/env python3
"""Alternative-interpretation runs for the ambiguity report."""
import json, importlib.util, time, math, random
spec = importlib.util.spec_from_file_location("m", "h_space_v0_2_blind_reimpl.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def ring_directed(n):
    return {i: ((i + 1) % n,) for i in range(n)}
def star_hub_out(n):   # only hub can send
    return {0: tuple(range(1, n)), **{i: () for i in range(1, n)}}
def star_leaves_in(n): # only leaves can send to hub
    return {**{0: ()}, **{i: (0,) for i in range(1, n)}}

def cell_from_adj(adj, topo, n, theta):
    q = m.q_total(theta, n)
    out_deg = {i: len(adj[i]) for i in range(n)}
    # nodes with zero out-degree can never be a destination source; fraction 0/0 guard
    inn = m.in_neighbours(adj, n)
    seed_rows, tot_rhat, tot_r = [], 0.0, 0
    for sd in m.SEED_LIST:
        steps = m.run(sd, n, adj, out_deg, inn, q)
        valid = [s for s in steps if s[0] > 0 and s[2] is not None]
        v = len(valid)
        phi_emp = sum(s[1] / s[0] for s in valid) / v if v else None
        phi_snap = sum(s[2] for s in valid) / v if v else None
        r_sum = sum(s[1] for s in valid); rhat_sum = sum(s[3] for s in valid)
        tot_rhat += rhat_sum; tot_r += r_sum
        seed_rows.append({"seed": sd, "phi_emp_seed": phi_emp, "phi_snapshot_seed": phi_snap,
                          "valid_steps": v, "post_burn_rejections": r_sum,
                          "post_burn_attempts": sum(s[0] for s in valid),
                          "r_hat": (rhat_sum - r_sum) / r_sum if r_sum > 0 else None})
    return q, seed_rows, ((tot_rhat - tot_r) / tot_r if tot_r > 0 else None)

def mean_or_none(vals):
    vals=[v for v in vals if v is not None]
    return sum(vals)/len(vals) if vals else None

def verdict_for(seed_rows):
    guards = []
    for r in seed_rows:
        if r["valid_steps"] < 0.90 * m.HORIZON and "LOW_VALID_STEPS" not in guards:
            guards.append("LOW_VALID_STEPS")
        if r["post_burn_rejections"] < 50 and "LOW_REJECTION_COUNT" not in guards:
            guards.append("LOW_REJECTION_COUNT")
    defined = [r for r in seed_rows if r["phi_emp_seed"] is not None]
    mean_emp = mean_or_none([r["phi_emp_seed"] for r in seed_rows])
    mean_snap = mean_or_none([r["phi_snapshot_seed"] for r in seed_rows])
    if (mean_emp == 0 or mean_emp is None) and "ZERO_MEAN_PHI_EMP" not in guards:
        guards.append("ZERO_MEAN_PHI_EMP")
    e_val = (mean_snap - mean_emp) / mean_emp if mean_emp not in (None, 0) else None
    lo = hi = None
    if defined and mean_emp not in (None, 0):
        pairs = [(r["phi_snapshot_seed"], r["phi_emp_seed"]) for r in defined]
        lo, hi = m.bootstrap_ci(pairs)
    if guards: verdict = "INCONCLUSIVE"
    elif lo >= m.TOL_LO and hi <= m.TOL_HI: verdict = "PASS"
    elif lo > m.TOL_HI or hi < m.TOL_LO: verdict = "FAIL"
    else: verdict = "INCONCLUSIVE"
    return {"mean_phi_emp": mean_emp, "mean_phi_snapshot": mean_snap,
            "relative_prediction_error": e_val, "ci_low": lo, "ci_high": hi,
            "guards_triggered": guards, "verdict": verdict}

alts = {"RING_directed": ("RING", ring_directed),
        "STAR_hub_out_only": ("STAR", star_hub_out),
        "STAR_leaves_in_only": ("STAR", star_leaves_in)}
out = []
for label, (topo, mk) in alts.items():
    t0 = time.time()
    for n in m.N_GRID:
        adj = mk(n)
        for theta in m.THETA_GRID:
            q, rows, consist = cell_from_adj(adj, topo, n, theta)
            res = verdict_for(rows)
            out.append({"ambiguity_id": "A1" if label.startswith("RING") else "A2",
                        "interpretation": label,
                        "cell_id": f"{topo}|N={n}|theta={theta}|UNIT_RANDOM_SEQUENTIAL",
                        "topology": topo, "n_nodes": n, "theta_target": theta,
                        "schedule": "UNIT_RANDOM_SEQUENTIAL", "q_total": q,
                        "total_capacity": n * 8, "theta_realized": q / (n * 8),
                        "graph_seed": None,
                        "seeds": rows, "consistency_check_rel": consist, **res})
    print(label, "done", round(time.time() - t0, 1), "s", file=__import__("sys").stderr)
json.dump(out, open("alt_results.json", "w"), indent=1, allow_nan=False)
v = {}
for r in out:
    v[r["interpretation"]] = v.get(r["interpretation"], {"P":0,"F":0,"I":0})
    k = "P" if r["verdict"]=="PASS" else "F" if r["verdict"]=="FAIL" else "I"
    v[r["interpretation"]][k]+=1
print(v)
