#!/usr/bin/env python3
"""Check frozen files against SHA256SUMS. Exit 1 on any mismatch."""
import hashlib, sys
bad = 0
for line in open("SHA256SUMS", encoding="ascii"):
    if not line.strip(): continue
    want, name = line.split()
    got = hashlib.sha256(open(name, "rb").read()).hexdigest()
    print(("OK   " if got == want else "FAIL ") + name)
    bad += got != want
sys.exit(1 if bad else 0)
