#!/usr/bin/env python3
"""Reproduce the VMS Institute SymPy audit failure-propagation experiment.

Requires: Python 3 and SymPy installed in this interpreter.
Fetches the institute's public ZIP, verifies its pinned SHA-256 and runs three
fresh temporary copies. It does not edit the downloaded source in place.
It invokes the publisher's own code: run only in an environment you control.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

URL = "https://www.vms-institute.org/audit/vms-sympy-audit.zip"
SHA256 = "42ff1df323780157baa374996f7f69f3fddbdd9a8348d3fcb4edd90dca393737"
TIMEOUT_S = 100

def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "VMS-Audit-Independent-Reproducer/1.0"})
    source = urllib.request.urlopen(req, timeout=20).read()
    checksum = hashlib.sha256(source).hexdigest()
    if checksum != SHA256:
        raise ValueError(f"Official ZIP changed: expected {SHA256}, received {checksum}. Stop and inspect.")
    archive = zipfile.ZipFile(io.BytesIO(source))
    entries = archive.namelist()
    if len(entries) != 35 or any(
        not name.startswith("sympy/") or PurePosixPath(name).is_absolute()
        or ".." in PurePosixPath(name).parts for name in entries
    ):
        raise ValueError("Unexpected ZIP structure; refusing extraction")
    return archive

def case(archive, label):
    with tempfile.TemporaryDirectory(prefix="vms-audit-reproduction-") as temporary:
        root = Path(temporary)
        archive.extractall(root)
        wd = root / "sympy"
        target = wd / "f0001" / "CAS_F0001_VERIFY.py"
        source = target.read_text(encoding="utf-8")
        if label == "false_expected_value":
            old = "step1_target = m * xdot_sym"
            if source.count(old) != 1:
                raise ValueError("F0001 has changed; do not mutate")
            target.write_text(source.replace(old, old + " + 1", 1), encoding="utf-8")
        elif label == "raised_exception":
            old = "def run():\n"
            if source.count(old) != 1:
                raise ValueError("F0001 has changed; do not mutate")
            target.write_text(
                source.replace(old, old + '    raise AssertionError("CONTROLLED_TEST")\n', 1),
                encoding="utf-8",
            )
        elif label != "original":
            raise ValueError("Unknown case")

        env = os.environ.copy()
        env["HOME"] = str(root)
        env["PYTHONNOUSERSITE"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        run = subprocess.run(
            [sys.executable, "run_master.py"], cwd=wd, capture_output=True,
            text=True, errors="replace", timeout=TIMEOUT_S, env=env,
        )
        report = json.loads((wd / "audit_report.json").read_text(encoding="utf-8"))
        pattern = r"F0001 AUDIT RESULT.*?Steps:\s*(\d+)\s*\|\s*Pass:\s*(\d+)\s*\|\s*Fail:\s*(\d+).*?STATUS: \*\*\* (PASS|FAIL) \*\*\*"
        match = re.search(pattern, run.stdout, re.S)
        sub = (
            {"checks": int(match.group(1)), "pass": int(match.group(2)),
             "fail": int(match.group(3)), "verdict": match.group(4)}
            if match else None
        )
        return {
            "case": label, "exit_code": run.returncode, "f0001_internal": sub,
            "master_blocks_pass": report["blocks_passed"],
            "master_blocks_fail": report["blocks_failed"],
            "global_status": report["global_consistency"],
            "registered_constants": report["constants_registered"],
            "summary_stdout_sha256": hashlib.sha256(run.stdout.encode()).hexdigest(),
        }

def main():
    import sympy
    archive = fetch()
    result = {
        "source_zip_sha256": SHA256,
        "python": sys.version.split()[0], "sympy": sympy.__version__,
        "cases": [case(archive, name) for name in ("original", "false_expected_value", "raised_exception")],
    }
    a, b, c = result["cases"]
    result["reproduced"] = bool(
        a["exit_code"] == 0 and a["master_blocks_pass"] == 32
        and b["exit_code"] == 0 and b["f0001_internal"]["fail"] >= 1
        and b["master_blocks_pass"] == 32
        and c["exit_code"] == 1 and c["master_blocks_fail"] == 1
    )
    print(json.dumps(result, indent=2))
    return 0 if result["reproduced"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
