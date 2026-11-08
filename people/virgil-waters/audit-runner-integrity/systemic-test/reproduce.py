#!/usr/bin/env python3
"""Independent strict verdict layer + systematic mutation test of VMS CAS ZIP.

This reproducer downloads only the publisher's SHA-256-pinned ZIP, extracts
separate disposable copies and invokes its unmodified master runner in each.
The second copy adds ONE synthetic failed subcheck to EACH of F0001-F0031:
the normal mathematical checks still run, and each module reports the
synthetic failure in its own total. F0000 is left unchanged.

The strict overlay is a separate verifier that checks the 32 module
statuses, per-module counters, omitted modules and skipped cross-block
identities. It never edits the official code in place.

Requires Python >=3.9 and SymPy in the interpreter used to invoke this file.
Executing publisher source is not a sandbox. Run in a trusted disposable VM
if source-code execution policy requires isolation.
"""
from __future__ import annotations
import hashlib, io, json, os, pathlib, re, subprocess, sys, tempfile
import urllib.request, zipfile, datetime

OFFICIAL = "https://www.vms-institute.org/audit/vms-sympy-audit.zip"
SHA256 = "42ff1df323780157baa374996f7f69f3fddbdd9a8348d3fcb4edd90dca393737"
EXPECTED_MODULES = tuple(f"F{i:04d}" for i in range(32))
MARKER = "    total_steps = 0"
INJECTION = (
    "    total_steps = 0\n"
    "    total_steps += 1\n"
    "    fail_count += 1\n"
    "    print('  NEGATIVE CONTROL: synthetic failed check inserted by independent auditor')"
)
PATTERN = re.compile(
    r"F(\d{4}) AUDIT RESULT\s+Steps:\s*(\d+)\s*\|\s*Pass:\s*(\d+)\s*\|\s*Fail:\s*(\d+)"
    r"[\s\S]*?STATUS: \*\*\* (PASS|FAIL) \*\*\*"
)

def load_archive():
    request = urllib.request.Request(OFFICIAL, headers={"User-Agent": "Independent-VMS-CAS-Review/1.0"})
    content = urllib.request.urlopen(request, timeout=22).read()
    digest = hashlib.sha256(content).hexdigest()
    if digest != SHA256:
        raise RuntimeError(f"Author archive changed: expected {SHA256}, observed {digest}; aborting.")
    archive = zipfile.ZipFile(io.BytesIO(content))
    names = archive.namelist()
    if len(names) != 35 or any(not s.startswith("sympy/") or ".." in pathlib.PurePosixPath(s).parts for s in names):
        raise RuntimeError("Unexpected archive paths; aborting.")
    for block in EXPECTED_MODULES:
        p = f"sympy/f{block[1:]}/CAS_{block}_VERIFY.py"
        if p not in names:
            raise RuntimeError(f"Missing expected module {p}")
    return archive

def strict_verdict(stdout, master):
    matches = PATTERN.findall(stdout)
    recorded = {}
    if len(matches) != 31:
        return {"status": "FAIL", "reason": "Expected 31 check-counter summaries", "observed": len(matches)}
    for ident, count, passed, failed, status in matches:
        key = "F" + ident
        if key in recorded:
            return {"status": "FAIL", "reason": f"Duplicate module {key}"}
        d = {"checks": int(count), "passed": int(passed), "failed": int(failed), "internal_status": status}
        recorded[key] = d
    if sorted(recorded) != list(EXPECTED_MODULES[1:]):
        return {"status": "FAIL", "reason": "Incomplete or unexpected module list"}
    assert "✓ F0000 — 11/11 PASS" in stdout, "Geometric root assertion count missing"
    global_lines = [line.strip() for line in stdout.splitlines()
                    if re.search(r": (?:SKIP|PASS|FAIL)(?:\s|$)", line)
                    and ("c^2*eps0*mu0" in line or "hbar=h/" in line or "sigma formula" in line)]
    skip_count = sum(": SKIP" in line for line in global_lines)
    failed_global = sum(": FAIL" in line for line in global_lines)
    failed_sub = sum(x["failed"] for x in recorded.values())
    count_bad = [k for k,d in recorded.items() if d["passed"] + d["failed"] != d["checks"]]
    status_bad = [k for k,d in recorded.items() if (d["failed"] > 0) != (d["internal_status"] == "FAIL")]
    top_bad = master["blocks_failed"] != 0 or master["blocks_passed"] != 32
    incomplete_global = len(global_lines) != 3 or skip_count or not master.get("constants_registered")
    if failed_sub or count_bad or status_bad or top_bad or failed_global:
        verdict = "FAIL"
    elif incomplete_global:
        verdict = "INCOMPLETE"
    else:
        verdict = "PASS"
    return {
        "status": verdict,
        "internal_checks": sum(x["checks"] for x in recorded.values()),
        "internal_pass": sum(x["passed"] for x in recorded.values()),
        "internal_fail": failed_sub,
        "modules_raising_no_exception": len(recorded),
        "count_inconsistencies": count_bad,
        "status_inconsistencies": status_bad,
        "global_identity_lines": global_lines,
        "global_checks_skipped": skip_count,
        "global_checks_failed": failed_global,
        "registered_constants": master.get("constants_registered", []),
        "module_outcomes": recorded,
    }

def run_case(archive, label, mutate=False):
    with tempfile.TemporaryDirectory(prefix="vms-systemic-check-") as temp:
        root = pathlib.Path(temp)
        archive.extractall(root)
        work = root / "sympy"
        injections = []
        if mutate:
            for block in EXPECTED_MODULES[1:]:
                file = work / f"f{block[1:]}" / f"CAS_{block}_VERIFY.py"
                content = file.read_text(encoding="utf-8")
                if content.count(MARKER) != 1:
                    raise AssertionError(f"Unexpected counter in {block}")
                file.write_text(content.replace(MARKER, INJECTION, 1), encoding="utf-8")
                injections.append(block)
        env = os.environ.copy()
        env.update({"HOME": temp, "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
        completed = subprocess.run(
            [sys.executable, "run_master.py"], cwd=work, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=110, env=env
        )
        reportfile = work / "audit_report.json"
        if not reportfile.is_file():
            raise RuntimeError(f"Master report was not created in {label}: {completed.stderr[-400:]}")
        result = json.loads(reportfile.read_text())
        strict = strict_verdict(completed.stdout, result)
        return {
            "case": label, "mutation": "synthetic failed step added to each reporting module" if mutate else "none",
            "injected_modules": injections,
            "master_exit_code": completed.returncode,
            "master_blocks_passed": result["blocks_passed"],
            "master_blocks_failed": result["blocks_failed"],
            "master_global": result["global_consistency"],
            "master_result_for_each_block": result["results"],
            "strict_verdict": strict,
            "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
            "stderr_tail": completed.stderr[-400:],
            "master_summary": "\n".join(completed.stdout.splitlines()[-11:]),
        }

def main():
    import sympy
    archive = load_archive()
    baseline = run_case(archive, "original", False)
    mutant = run_case(archive, "all_31_modules_report_synthetic_failure", True)
    if baseline["strict_verdict"]["status"] != "INCOMPLETE":
        raise AssertionError("Unexpected baseline strict verdict")
    if baseline["strict_verdict"]["internal_fail"] != 0 or baseline["master_exit_code"] != 0:
        raise AssertionError("Original source reported a subcheck failure")
    if mutant["strict_verdict"]["status"] != "FAIL":
        raise AssertionError("Strict overlay failed to detect the synthetic errors")
    if mutant["strict_verdict"]["internal_fail"] != 31 or mutant["strict_verdict"]["internal_checks"] != baseline["strict_verdict"]["internal_checks"] + 31:
        raise AssertionError("Mutation did not add exactly one failed check per module")
    if mutant["master_exit_code"] != 0 or mutant["master_blocks_passed"] != 32:
        raise AssertionError("Original master did not reproduce its false-green verdict")
    result = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "original_zip": OFFICIAL, "original_zip_sha256": SHA256,
        "python_version": sys.version.split()[0], "sympy_version": sympy.__version__,
        "finding": "All 31 reporting modules can report one synthetic failed subcheck yet the unmodified master reports 32 passing modules.",
        "scope": "Fail-status propagation and skipped global checks; not proof that original calculations fail.",
        "baseline": baseline, "systemic_mutation": mutant,
        "conclusion_verified": True,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
