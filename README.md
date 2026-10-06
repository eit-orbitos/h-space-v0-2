# H_SPACE V0.2 — preregistered sweep

**STATUS:** INTERNAL_MATHEMATICAL_MODEL · NOT_PHYSICS · NOT_FROZEN_LAW
**ZENODO / FREEZE / PUBLICATION:** DOI_RESERVED · PUBLICATION_PENDING_GATES

Reserved Zenodo DOI: 10.5281/zenodo.23179226.
The DOI becomes registered when the archival record is published.

Part of the NOVA Q / EIT framework (EITNetworks LLC, Toni Mladenovski, ORCID 0009-0009-8343-662X).

## What this is

A small discrete toy model: units on a graph with limited capacity per node, in two
forms (E mobile, M immobile), with E↔M transitions and capacity-limited moves.
This repository holds one preregistered test of one question:

> Does a local occupancy snapshot predict the empirical destination-full fraction
> within ±10% relative error, across occupancy, size and topology?

The full rules are in `H_SPACE_V0_2_PREREG_PROTOCOL.md`. The protocol was written and
hashed before any grid cell was run.

## What this is not

- Not a physical law and not evidence about physical temperature, pressure or gravity.
- Not a novel result in statistical mechanics: rejection driven by destination
  saturation and update-rule dependence are known in exclusion-type lattice models.
- A PASS would not establish a constitutive law, MEMORY, or absence of missing variables.

## Files

| File | Role |
|---|---|
| `H_SPACE_V0_2_PREREG_PROTOCOL.md` | frozen protocol |
| `h_space_v0_2_sweep.py` | frozen primary implementation |
| `SHA256SUMS` | hashes of the two frozen files |
| `verify_hashes.py` | checks frozen bytes |
| `canonicalize_report.py` | rewrites the report in canonical bytes for hashing |
| `.github/workflows/replay.yml` | Linux / Windows / macOS replay |

## Run

    python verify_hashes.py
    python h_space_v0_2_sweep.py > report_raw.json
    python canonicalize_report.py report_raw.json report.json

Python 3.13. `random` output can differ between Python versions.

## Evidence roles

- **GitHub CI = cross-platform reproducibility.** Same code on three OS must give the
  same canonical report hash. This does not validate the code: a bug replays identically.
- **Independent validation = a second implementation** written only from the protocol
  text, without access to `h_space_v0_2_sweep.py`. Success criterion: the same
  cell-level PASS / FAIL / INCONCLUSIVE decisions under the frozen rules.

## Governance

- OVERALL PASS requires all 105 primary cells PASS.
- Low-exposure cells are INCONCLUSIVE, not FAIL.
- NO POST-HOC RESCUE RULE: any alternative low-Phi metric is a V0.2.1 candidate and
  needs a new version, new SHA-256 and new preregistration before execution.

## Citation

If you use this in research, please cite it. See `CITATION.cff` (GitHub shows a
"Cite this repository" button). A DOI will be added after archival release.
