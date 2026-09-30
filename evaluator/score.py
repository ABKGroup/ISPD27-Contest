#!/usr/bin/env python3
"""Compute one design's numerical score using contest PDF Section 3.3.1."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from internal.legality import verify_certificate


WEIGHTS = (
    "setup_tns", "setup_wns", "dynamic_power", "leakage_power",
    "hold_tns", "hold_wns", "slew", "cap", "fanout", "tool_runtime",
    "flow_runtime", "displacement", "max_overflow", "total_overflow",
)
EPSILONS = ("time_ns", "slew_ps", "cap_ff", "fanout", "displacement_um", "overflow")
TIMING = ("setup_tns_ns", "setup_wns_ns", "hold_tns_ns", "hold_wns_ns")
NONNEGATIVE = (
    "dynamic_power_w", "leakage_power_w", "slew_violation_sum_ps",
    "cap_violation_sum_ff", "fanout_violation_sum", "average_displacement_um",
    "max_global_routing_overflow", "global_routing_overflow",
)


def number(value, label, minimum=None, positive=False):
    if isinstance(value, bool):
        raise ValueError(f"{label}: expected a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label}: provide a finite number (not null)") from None
    if not math.isfinite(result):
        raise ValueError(f"{label}: must be finite")
    if positive and result <= 0:
        raise ValueError(f"{label}: must be positive")
    if minimum is not None and result < minimum:
        raise ValueError(f"{label}: must be >= {minimum}")
    return result


def exact_keys(data, keys, label):
    if not isinstance(data, dict) or set(data) != set(keys):
        raise ValueError(f"{label}: expected keys {', '.join(keys)}")


def validate_config(config):
    exact_keys(config, ("status", "weights", "scenarios", "epsilon", "overflow_thresholds"), "config")
    if config["status"] not in ("provisional", "official"):
        raise ValueError("config.status must be provisional or official")
    exact_keys(config["weights"], WEIGHTS, "weights")
    for key in WEIGHTS:
        config["weights"][key] = number(config["weights"][key], f"weights.{key}", minimum=0)
    weights = config["weights"]
    for prefix in ("setup", "hold"):
        if weights[prefix + "_tns"] != weights[prefix + "_wns"]:
            raise ValueError(f"{prefix} TNS and WNS weights must be equal")
    if weights["setup_tns"] <= 0:
        raise ValueError("Setup timing weights must be positive")
    exact_keys(config["epsilon"], EPSILONS, "epsilon")
    for key in EPSILONS:
        config["epsilon"][key] = number(config["epsilon"][key], f"epsilon.{key}", positive=True)
    exact_keys(config["overflow_thresholds"], ("max", "total"), "overflow_thresholds")
    for key in ("max", "total"):
        config["overflow_thresholds"][key] = number(
            config["overflow_thresholds"][key], f"overflow_thresholds.{key}", minimum=0)
    scenes = config["scenarios"]
    if not isinstance(scenes, dict) or not scenes:
        raise ValueError("scenarios must be a nonempty object keyed by summary.csv corner")
    for scene, values in scenes.items():
        exact_keys(values, ("weight", "hold_tns_tolerance_ns", "hold_wns_tolerance_ns"), scene)
        for key in values:
            values[key] = number(values[key], f"scenarios.{scene}.{key}", minimum=0)
        if values["weight"] == 0:
            raise ValueError(f"{scene}: scenario weight must be positive")
    if not math.isclose(math.fsum(v["weight"] for v in scenes.values()), 1.0,
                        rel_tol=0, abs_tol=1e-12):
        raise ValueError("Scenario weights must sum to one")
    return config


def read_summary(path):
    with path.open(newline="") as stream:
        records = list(csv.DictReader(stream))
    if not records:
        raise ValueError(f"{path}: empty summary")
    scenes = {}
    identities = set()
    for row in records:
        identities.add((row["design"], row["scenario"]))
        corner = row["corner"]
        if not corner or corner in scenes:
            raise ValueError(f"{path}: duplicate or empty corner; supply one configuration only")
        values = {}
        for key in TIMING + NONNEGATIVE:
            values[key] = number(row[key], f"{path}:{corner}:{key}")
            if key in TIMING and values[key] > 0:
                raise ValueError(f"{key} must be signed negative slack or zero, in ns")
            if key in NONNEGATIVE and values[key] < 0:
                raise ValueError(f"{key} must be nonnegative")
        if values["max_global_routing_overflow"] > values["global_routing_overflow"]:
            raise ValueError(f"{path}: maximum overflow exceeds total overflow")
        scenes[corner] = values
    if len(identities) != 1 or any(not x for x in next(iter(identities))):
        raise ValueError(f"{path}: expected one design and one configuration")
    return next(iter(identities)), scenes


def shared(scenes, key):
    values = [row[key] for row in scenes.values()]
    if any(v != values[0] for v in values[1:]):
        raise ValueError(f"{key} must be identical across corners of one physical design")
    return values[0]


def ratio(numerator, denominator, label):
    if denominator <= 0:
        raise ValueError(f"{label}: normalization denominator must be positive")
    return number(numerator / denominator, label)


def calculate(baseline, candidate, reference, config, runtimes):
    """Inputs are per-corner dictionaries; reference is the Resizer result."""
    validate_config(config)
    expected = set(config["scenarios"])
    if any(set(data) != expected for data in (baseline, candidate, reference)):
        raise ValueError("Baseline, candidate, reference, and config must have identical scenario sets")
    exact_keys(runtimes, ("tool_s", "flow_s", "reference_tool_s", "reference_flow_s"), "runtimes")
    times = {key: number(value, key, minimum=0, positive=key.startswith("reference_"))
             for key, value in runtimes.items()}
    for prefix in ("", "reference_"):
        if times[prefix + "flow_s"] < times[prefix + "tool_s"]:
            raise ValueError("Flow runtime must include tool runtime")
    if times["tool_s"] > 18000 or times["flow_s"] > 18000:
        raise ValueError("Candidate exceeds the five-hour tool or flow runtime limit; no numerical score")
    weights, eps = config["weights"], config["epsilon"]
    details = {}
    for scene, settings in config["scenarios"].items():
        base, cand = baseline[scene], candidate[scene]
        terms = {}
        for metric in ("tns", "wns"):
            key = "setup_" + metric
            col = key + "_ns"
            # Literal denominator printed in Section 3.3.1: |baseline + epsilon|.
            terms[key] = weights[key] * ratio(cand[col] - base[col],
                abs(base[col] + eps["time_ns"]), key)
            hold_key = "hold_" + metric
            tolerance = settings[hold_key + "_tolerance_ns"]
            magnitude = max(0.0, -cand[hold_key + "_ns"])
            terms[hold_key] = weights[hold_key] * max(0.0, magnitude - tolerance) / (
                tolerance + eps["time_ns"])
        for key in ("dynamic_power", "leakage_power"):
            col = key + "_w"
            # The PDF includes no epsilon in power normalization.
            terms[key] = (weights[key] * ratio(base[col] - cand[col], base[col], key)
                          if weights[key] else 0.0)
        for key, col, unit in (("slew", "slew_violation_sum_ps", "slew_ps"),
                              ("cap", "cap_violation_sum_ff", "cap_ff"),
                              ("fanout", "fanout_violation_sum", "fanout")):
            terms[key] = weights[key] * (cand[col] - base[col]) / (base[col] + eps[unit])
        details[scene] = {"weight": settings["weight"], "weighted_terms": terms}

    def aggregate(keys):
        return math.fsum(d["weight"] * math.fsum(d["weighted_terms"][k] for k in keys)
                         for d in details.values())

    components = {
        "ppa": aggregate(("setup_tns", "setup_wns", "dynamic_power", "leakage_power")),
        "hold_penalty": aggregate(("hold_tns", "hold_wns")),
        "erc_penalty": aggregate(("slew", "cap", "fanout")),
        "runtime_penalty": math.fsum(
            weights[key + "_runtime"] * (times[key + "_s"] - times["reference_" + key + "_s"])
            / times["reference_" + key + "_s"] for key in ("tool", "flow")),
    }
    # Physical-design metrics occur in each CSV row but are charged only once.
    for data in (baseline, candidate, reference):
        for key in ("average_displacement_um", "max_global_routing_overflow", "global_routing_overflow"):
            shared(data, key)
    reference_displacement = shared(reference, "average_displacement_um")
    components["displacement_penalty"] = weights["displacement"] * (
        shared(candidate, "average_displacement_um") - reference_displacement
    ) / (reference_displacement + eps["displacement_um"])
    # Overflow is counted in routing-resource units. Use at least one unit
    # for normalization, even when the permitted overflow threshold is zero.
    components["overflow_penalty"] = math.fsum(
        weights[key + "_overflow"] * max(0.0, shared(candidate, col) - config["overflow_thresholds"][key])
        / max(1.0, config["overflow_thresholds"][key] + eps["overflow"])
        for key, col in (("max", "max_global_routing_overflow"), ("total", "global_routing_overflow")))
    for key, value in components.items():
        number(value, key)
    result = number(components["ppa"] - math.fsum(v for k, v in components.items() if k != "ppa"), "score")
    return {"score": result, "higher_is_better": True, "status": config["status"], "components": components,
            "scenarios": details, "config": config, "runtimes": times,
            "eligibility": "not_certified",
            "note": "Numerical Section 3.3.1 score only; mandatory legality checks and ranking remain separate."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag, help_text in (
        ("baseline", "Unoptimized R0 summary.csv"),
        ("candidate", "Candidate summary.csv, one design/configuration"),
        ("reference", "OpenROAD Resizer reference summary.csv"),
        ("runtimes", "Measured candidate and Resizer tool/total-flow runtimes JSON"),
    ):
        parser.add_argument("--" + flag, type=Path, required=True, help=help_text)
    parser.add_argument("--config", type=Path, default=Path(__file__).parent / "config/scoring_config.json",
                        help="Scoring policy JSON (default: supplied PROVISIONAL scoring_config.json)")
    parser.add_argument("--output", type=Path, help="Optional NEW JSON file containing score and breakdown")
    parser.add_argument("--allow-unverified", action="store_true",
                        help="Explicitly compute a dummy score without eligibility/runtime certification")
    args = parser.parse_args()
    try:
        inputs = {name: getattr(args, name) for name in ("baseline", "candidate", "reference", "config", "runtimes")}
        if not args.allow_unverified:
            certificate = verify_certificate(args.candidate)
            official = Path(__file__).with_name("reference_results") / certificate["design"]
            for key, filename in (("baseline", "baseline.csv"), ("reference", "resizer.csv")):
                if inputs[key].read_bytes() != (official / filename).read_bytes():
                    raise ValueError(f"Use the packaged {key} metrics for this benchmark")
            measured = json.loads((args.candidate.parent / "runtime_validation.json").read_text())
            requested = json.loads(args.runtimes.read_text())
            reference_times = json.loads((official / "runtimes.json").read_text())
            for key in ("reference_tool_s", "reference_flow_s"):
                if requested[key] != reference_times[key]:
                    raise ValueError(f"{key} differs from the packaged reference runtime")
            for key in ("tool_s", "flow_s"):
                if requested[key] != measured[key]:
                    raise ValueError(f"{key} differs from the measured runtime")
        summaries = [read_summary(inputs[key]) for key in ("baseline", "candidate", "reference")]
        if len({identity for identity, _ in summaries}) != 1:
            raise ValueError("Baseline, candidate, and reference design/configuration IDs must match")
        report = calculate(*(scenes for _, scenes in summaries),
                           json.loads(args.config.read_text()), json.loads(args.runtimes.read_text()))
        report.update(design=summaries[0][0][0], configuration=summaries[0][0][1],
                      inputs={name: {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                              for name, path in inputs.items()})
        report["eligibility"] = "unverified_dummy" if args.allow_unverified else "design_and_runtime_checks_passed"
        if args.output:
            with args.output.open("x") as stream:
                json.dump(report, stream, indent=2, allow_nan=False)
                stream.write("\n")
        print(format(report["score"], ".17g"))
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        parser.exit(2, f"Scoring error: {error}\n")


if __name__ == "__main__":
    main()
