"""Verify the seeded failures and materialise them as branches.

    python tools/seeds.py verify [ID ...]   check each seed against its manifest entry
    python tools/seeds.py branch [ID ...]   create seed/ID branches from main

`verify` is what makes the manifest ground truth rather than a claim. For each
seed it checks out main into a scratch directory, applies inject.patch, and
runs the steps of .github/workflows/ci.yml in a fresh virtualenv:

* the injected tree must fail at the named step, with the named signature and
  the named failing tests;
* with fix.patch applied it must pass;
* a flaky seed is run under many PYTHONHASHSEED values instead, and must fail
  some of them and pass some, and pass all of them once fixed.

The workflow is read rather than duplicated so that a seed which edits the
workflow (s04) changes what gets run.

`branch` writes inject.patch onto a branch from main and deletes seeds/ in the
same commit, so the failing checkout has no fix.patch in its working tree. The
fix is still in main's history; an agent that runs `git show main:seeds/...`
can find it, so the harness must not give it that ref.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import venv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"

#: Each CI step is "- name: X" then "run: CMD" on the next line. Steps that only
#: `uses:` an action have no command here and are covered by the venv.
_STEP = re.compile(r"- name: (?P<name>.+)\n\s+run: (?P<cmd>.+)")
_TEST_ID = re.compile(r"^(?:ERROR|FAIL): (?P<id>.+?) \((?P<full>[^)]+)\)$", re.MULTILINE)


@dataclass
class CiRun:
    failed_step: str | None
    output: str

    @property
    def passed(self) -> bool:
        return self.failed_step is None


def git(*args: str, cwd: Path = ROOT, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=text, check=True)


def checkout_tree(ref: str, dest: Path) -> None:
    """Export `ref` into dest without a .git directory, so `git apply` sees a plain tree."""
    tar = git("archive", "--format=tar", ref, text=False).stdout
    with tarfile.open(fileobj=io.BytesIO(tar)) as t:
        t.extractall(dest, filter="data")


def apply_patch(tree: Path, patch: Path) -> None:
    subprocess.run(
        ["git", "apply", "--whitespace=nowarn", str(patch)], cwd=tree, capture_output=True,
        text=True, check=True,
    )


def workflow_steps(tree: Path) -> list[tuple[str, str]]:
    text = (tree / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    return [(m["name"], m["cmd"]) for m in _STEP.finditer(text)]


def make_venv(where: Path) -> dict[str, str]:
    venv.create(where, with_pip=True)
    bindir = where / ("Scripts" if os.name == "nt" else "bin")
    env = dict(os.environ)
    env["PATH"] = f"{bindir}{os.pathsep}{env['PATH']}"
    env["VIRTUAL_ENV"] = str(where)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    return env


def run_ci(tree: Path, env: dict[str, str], *, skip_install: bool = False) -> CiRun:
    """Run the workflow's commands in order, stopping at the first failure."""
    log: list[str] = []
    for name, cmd in workflow_steps(tree):
        if skip_install and "pip install" in cmd:
            continue
        proc = subprocess.run(
            cmd, cwd=tree, env=env, shell=True, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        log.append(f"=== {name}: {cmd}\n{proc.stdout}{proc.stderr}")
        if proc.returncode != 0:
            return CiRun(name, "\n".join(log))
    return CiRun(None, "\n".join(log))


def failing_test_ids(output: str) -> set[str]:
    return {m["full"] for m in _TEST_ID.finditer(output)}


def load(ids: list[str]) -> list[dict]:
    seeds = json.loads((SEEDS / "manifest.json").read_text(encoding="utf-8"))["seeds"]
    if not ids:
        return seeds
    unknown = set(ids) - {s["id"] for s in seeds}
    if unknown:
        sys.exit(f"unknown seed: {', '.join(sorted(unknown))}")
    return [s for s in seeds if s["id"] in ids]


def expected_ids(seed: dict) -> set[str]:
    """Manifest test ids, which are the dotted path unittest prints in parentheses.

    A missing dependency fails as a whole module, printed as
    unittest.loader._FailedTest.<module>.
    """
    return {
        f"unittest.loader._FailedTest.{t}" if t.count(".") == 1 else t
        for t in seed["failing_tests"]
    }


def check_injected(seed: dict, run: CiRun) -> list[str]:
    problems = []
    if run.passed:
        return ["injected tree passed"]
    if run.failed_step != seed["failing_step"]:
        problems.append(f"failed at {run.failed_step!r}, expected {seed['failing_step']!r}")
    if seed["signature"] not in run.output:
        problems.append(f"signature not found: {seed['signature']}")
    got, want = failing_test_ids(run.output), expected_ids(seed)
    if got != want:
        problems.append(f"failing tests differ: missing {sorted(want - got)}, extra {sorted(got - want)}")
    return problems


def verify_seed(seed: dict, baseline_ref: str, flake_runs: int) -> list[str]:
    sid = seed["id"]
    inject, fix = SEEDS / sid / "inject.patch", SEEDS / sid / "fix.patch"
    problems: list[str] = []
    with tempfile.TemporaryDirectory(prefix=f"seed-{sid}-") as tmp:
        tmp = Path(tmp)
        tree = tmp / "tree"
        tree.mkdir()
        checkout_tree(baseline_ref, tree)
        apply_patch(tree, inject)

        if seed.get("flaky"):
            env = make_venv(tmp / "venv-inject")
            results = []
            for seed_value in range(flake_runs):
                env["PYTHONHASHSEED"] = str(seed_value)
                results.append(run_ci(tree, env, skip_install=seed_value > 0))
            failed = [r for r in results if not r.passed]
            rate = len(failed) / flake_runs
            lo, hi = seed["expected_failure_rate"]
            print(f"    {len(failed)}/{flake_runs} runs failed ({rate:.0%})")
            if not failed:
                problems.append("flaky seed never failed")
            elif not lo <= rate <= hi:
                problems.append(f"failure rate {rate:.0%} outside {lo:.0%}-{hi:.0%}")
            else:
                problems += check_injected(seed, failed[0])
            apply_patch(tree, fix)
            env = make_venv(tmp / "venv-fix")
            for seed_value in range(flake_runs):
                env["PYTHONHASHSEED"] = str(seed_value)
                if not run_ci(tree, env, skip_install=seed_value > 0).passed:
                    problems.append(f"fixed tree failed under PYTHONHASHSEED={seed_value}")
                    break
            return problems

        problems += check_injected(seed, run_ci(tree, make_venv(tmp / "venv-inject")))
        apply_patch(tree, fix)
        fixed = run_ci(tree, make_venv(tmp / "venv-fix"))
        if not fixed.passed:
            problems.append(f"fixed tree failed at {fixed.failed_step!r}:\n{fixed.output[-800:]}")
    return problems


def cmd_verify(args: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory(prefix="seed-baseline-") as tmp:
        tmp = Path(tmp)
        (tmp / "tree").mkdir()
        checkout_tree(args.ref, tmp / "tree")
        base = run_ci(tmp / "tree", make_venv(tmp / "venv"))
    if not base.passed:
        print(f"baseline {args.ref} is not green (step {base.failed_step!r}):\n{base.output}")
        return 1
    print(f"baseline {args.ref}: green")

    bad = 0
    for seed in load(args.ids):
        print(f"  {seed['id']} ({seed['category']})")
        problems = verify_seed(seed, args.ref, args.flake_runs)
        for p in problems:
            print(f"    FAIL {p}")
        print("    ok" if not problems else "")
        bad += bool(problems)
    print(f"{bad} of {len(load(args.ids))} seeds failed verification")
    return 1 if bad else 0


def cmd_branch(args: argparse.Namespace) -> int:
    if git("status", "--porcelain").stdout.strip():
        sys.exit("working tree is dirty; commit or stash first")
    start = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    try:
        for seed in load(args.ids):
            branch = f"seed/{seed['id']}"
            git("switch", "-q", "-c", branch, args.ref)
            git("apply", "--whitespace=nowarn", str(SEEDS / seed["id"] / "inject.patch"))
            git("rm", "-rq", "seeds")
            git("add", "-A")
            git("commit", "-q", "-m", seed["commit_message"])
            print(f"created {branch}")
            git("switch", "-q", args.ref)
    finally:
        git("switch", "-q", start)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name, fn in (("verify", cmd_verify), ("branch", cmd_branch)):
        p = sub.add_parser(name)
        p.add_argument("ids", nargs="*")
        p.add_argument("--ref", default="main")
        if name == "verify":
            p.add_argument("--flake-runs", type=int, default=12)
        p.set_defaults(fn=fn)
    args = parser.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
