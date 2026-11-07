#!/usr/bin/env python3
"""Measure a contestant command, validate its outputs, and enforce the tool runtime limit."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from internal.benchmark import environment, names, packed
from internal.legality import TOOL_LIMIT_SECONDS, digest, finalize

ROOT = Path(__file__).resolve().parents[1]
# Tool runtime limit. Evaluation time is recorded in the total-flow runtime but is not limited.
LIMIT_SECONDS = TOOL_LIMIT_SECONDS


def timed_command(command, env, cwd, log, timeout):
    if timeout is not None and timeout <= 0:
        raise TimeoutError(f"Tool runtime limit of {LIMIT_SECONDS // 3600} hours exceeded")
    with Path(log).open("x") as stream:
        process = subprocess.Popen(command, env=env, cwd=cwd, stdout=stream,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            result = process.wait(timeout=timeout)
        except BaseException:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise
        # A tool may leave workers alive after its main process exits.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if result:
        raise RuntimeError(f"Command exited with status {result}; see {log}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("design", choices=names(ROOT))
    parser.add_argument("output", type=Path, help="New run directory")
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="-- run.sh; appends input_dir platform_dir output_dir top_module")
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("Supply a tool command after --")
    if packed(ROOT / "benchmarks" / args.design):
        parser.error("Unpack the benchmark first: gunzip -k " + " ".join(packed(ROOT / "benchmarks" / args.design)))
    out = args.output.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=False)
    tool = out / "tool"
    tool.mkdir()
    bench = ROOT / "benchmarks" / args.design
    # A <design>/<condition> name gives one flat file name in tool/.
    stem = args.design.replace("/", "_")
    output_def, output_v = tool / f"{stem}.def", tool / f"{stem}.v"
    env = os.environ.copy()
    env.update(INPUT_DEF=str(bench / "input.def"), INPUT_VERILOG=str(bench / "input.v"),
               OUTPUT_DEF=str(output_def), OUTPUT_VERILOG=str(output_v),
               BENCHMARK_DIR=str(bench), MCMM_CONFIG=str(bench / "mcmm.tcl"),
               PLATFORM_DIR=str(ROOT / "platform/asap7"), PYTHONDONTWRITEBYTECODE="1",
               **environment(ROOT, bench))
    start = time.monotonic()
    try:
        top_module = json.loads((bench / "benchmark.json").read_text())["top_module"]
        tool_command = command + [str(bench), str(ROOT / "platform/asap7"),
                                  str(tool), top_module]
        tool_start = time.monotonic()
        # Keep invocation cwd so relative commands/arguments resolve as supplied.
        timed_command(tool_command, env, Path.cwd(), out / "tool.log", LIMIT_SECONDS)
        tool_s = time.monotonic() - tool_start
        if not output_def.is_file() or not output_v.is_file():
            raise ValueError(f"Tool must write {output_def} and {output_v}")
        evaluation = out / "evaluation"
        timed_command([sys.executable, str(ROOT / "evaluator/internal/run.py"), args.design,
                       str(evaluation), "--def", str(output_def), "--verilog", str(output_v)],
                      env, ROOT, out / "evaluation.log", None)
        flow_s = time.monotonic() - start
        if tool_s > LIMIT_SECONDS:
            raise TimeoutError(f"Tool runtime limit of {LIMIT_SECONDS // 3600} hours exceeded")
        runtime = {"passed": True, "tool_s": tool_s, "flow_s": flow_s,
                   "limit_seconds": LIMIT_SECONDS,
                   "input_sha256": {"INPUT_DEF": digest(output_def), "INPUT_VERILOG": digest(output_v)}}
        (evaluation / "runtime_validation.json").write_text(json.dumps(runtime, indent=2) + "\n")
        # Bind the measured time to this evaluated design and summary.
        finalize(evaluation)
        reference_file = ROOT / "evaluator/reference_results" / args.design / "runtimes.json"
        if reference_file.is_file():
            reference = json.loads(reference_file.read_text())
            reference.update(tool_s=tool_s, flow_s=flow_s)
            (evaluation / "runtimes.json").write_text(json.dumps(reference, indent=2) + "\n")
            (out / "SUBMISSION_COMPLETE").write_text("Design legality and measured runtime passed.\n")
        else:
            # The submission is valid; only the score needs the packaged reference results.
            (out / "SUBMISSION_COMPLETE").write_text(
                "Design legality and measured runtime passed.\n"
                "No reference results are packaged for this benchmark, so score.py cannot be run.\n")
            print("No reference results are packaged for this benchmark; score.py cannot be run.")
        print(f"Validated submission: {evaluation}")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        (out / "submission_failure.json").write_text(json.dumps({"passed": False, "reason": str(error)}, indent=2) + "\n")
        parser.exit(1, f"Submission rejected: {error}\n")


if __name__ == "__main__":
    main()
