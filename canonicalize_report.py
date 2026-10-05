#!/usr/bin/env python3
"""Rewrite report.json in canonical bytes (UTF-8, LF, sorted keys, fixed separators)
and print its SHA-256. Does not alter any value. Not part of the frozen protocol logic."""
import hashlib, json, sys
src, dst = sys.argv[1], sys.argv[2]
data = json.loads(open(src, "rb").read().decode("utf-8-sig"))
out = (json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")
open(dst, "wb").write(out)
print(hashlib.sha256(out).hexdigest())
