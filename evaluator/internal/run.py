#!/usr/bin/env python3
"""Run the selected public benchmark using standalone OpenROAD."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from legality import finalize

ROOT = Path(__file__).resolve().parents[2]


def executable(variable, default):
    value = os.environ.get(variable, default)
    resolved = shutil.which(value)
    if not resolved:
        raise ValueError(f"Cannot find {default}. Set {variable} or add it to PATH.")
    return str(Path(resolved).resolve())


def check_openroad_version(binary, env):
    versions = json.loads((ROOT / "evaluator/config/tool_versions.json").read_text())
    expected = versions.get("openroad_commit")
    if not expected:
        raise ValueError("Missing pinned OpenROAD revision in tool_versions.json")
    reported = subprocess.check_output([binary, "-version"], env=env, text=True,
                                       stderr=subprocess.STDOUT, timeout=30).strip()
    revision = re.search(r"(?:^|-)g([0-9a-f]{7,40})(?:\b|$)", reported)
    if not revision or not expected.startswith(revision.group(1)) or "dirty" in reported.lower():
        raise ValueError(f"Expected clean OpenROAD {expected[:12]}, got {reported!r}. "
                         "Set OPENROAD_EXE to the pinned upstream build; see tool_versions.json.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", choices=["aes", "jpeg"])
    parser.add_argument("output", type=Path, help="New output directory; never overwritten")
    parser.add_argument("--def", dest="input_def", type=Path)
    parser.add_argument("--verilog", type=Path)
    args = parser.parse_args()
    if bool(args.input_def) != bool(args.verilog):
        parser.error("Supply both --def and --verilog, or neither to evaluate R0.")
    bench = ROOT / "benchmarks" / args.benchmark
    cfg = json.loads((bench / "benchmark.json").read_text())
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error(f"Refusing to overwrite: {output}")
    def_file = (args.input_def or bench / "input.def").expanduser().resolve()
    verilog = (args.verilog or bench / "input.v").expanduser().resolve()
    for path in [def_file, verilog]:
        if not path.is_file():
            parser.error(f"Missing input: {path}")
    env = os.environ.copy()
    # All physical/timing settings come from this package, not inherited overrides.
    for key in ["SPEF_PREFIX", "INSPECT_DB"]:
        env.pop(key, None)
    env.update(
        BENCHMARK=args.benchmark, DESIGN_NAME=cfg["top_module"],
        INPUT_DEF=str(def_file), INPUT_VERILOG=str(verilog),
        BASELINE_DEF=str(bench / "input.def"), BASELINE_VERILOG=str(bench / "input.v"),
        SCENARIO_DIR=str(bench / "sdc"), SDC_FILE=str(bench / "sdc/TC.sdc"),
        MCMM_CONFIG=str(bench / "mcmm.tcl"), PLATFORM_DIR=str(ROOT / "platform/asap7"),
        OUTPUT_DIR=str(output), RUN_RESIZER="0", REPAIR_KIND="off",
        CORNERS="TC BC WC", LIBRARY_CORNERS="TC BC WC", NUM_CORES="8",
        SIGNAL_LAYERS="M2-M7", CLOCK_LAYERS="M4-M7", ROUTE_ADJUSTMENT="0.25",
        ROUTE_ITERATIONS="30", ROUTE_SEED="42", RSZ_MAX_ITERATIONS="500",
        RSZ_TNS_PERCENT="100", RSZ_SETUP_SEQUENCE="vt_swap sizeup swap buffer",
        PHASE="full", VERIFY_FORMAL="1", PYTHONDONTWRITEBYTECODE="1",
        OPENROAD_EXE=executable("OPENROAD_EXE", "openroad"),
        KEPLER_FORMAL_EXE=executable("KEPLER_FORMAL_EXE", "kepler-formal"),
    )
    # Internal scripts invoke python3; keep the same interpreter throughout.
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    subprocess.run([sys.executable, str(ROOT / "evaluator/internal/verify_package.py")],
                   env=env, check=True)
    check_openroad_version(env["OPENROAD_EXE"], env)
    started = time.monotonic()
    subprocess.run(["bash", str(ROOT / "evaluator/internal/core_run.sh")], env=env, check=True)
    with (output / "spef_validation.json").open("x") as stream:
        subprocess.run([sys.executable, str(ROOT / "evaluator/internal/check_spef.py"),
                        *[str(output / f"parasitics_{c}.spef") for c in cfg["corners"]]],
                       env=env, stdout=stream, check=True)
    subprocess.run([sys.executable, str(ROOT / "evaluator/internal/metrics.py"), str(output)],
                   env=env, check=True)
    (output / "evaluation_runtime.json").write_text(json.dumps({
        "evaluation_wall_seconds": time.monotonic() - started,
        "includes": "input checks, formal proofs, OpenROAD, SPEF checks, metric extraction",
        "contestant_tool_runtime_seconds": None,
    }, indent=2) + "\n")
    finalize(output)
    (output / "EVALUATION_COMPLETE").write_text(
        "Design legality, timing, routing and metric extraction passed; see legality.json.\n"
        "Use run_submission.py for measured tool-runtime validation. Scoring is a separate step.\n")
    print(f"Completed: {output / 'summary.csv'}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
