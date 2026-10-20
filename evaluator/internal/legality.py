#!/usr/bin/env python3
"""Validate fixed physical data and allowed transforms from OpenROAD snapshots.

Data repeaters may be inserted, removed, resized or replaced. Other original
instances retain their names. Clock cells/sinks, macros and physical-only cells
are protected. Formal equivalence and OpenROAD placement checking remain required.
"""
import argparse
from collections import Counter, defaultdict
import csv
import fnmatch
from functools import lru_cache
import hashlib
import itertools
import json
import math
from pathlib import Path
import re


class Illegal(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise Illegal(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def table(path):
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


SECTIONS = set("COMPONENTS PINS NETS SPECIALNETS VIAS NONDEFAULTRULES REGIONS GROUPS BLOCKAGES FILLS SLOTS SCANCHAINS PINPROPERTIES STYLES PROPERTYDEFINITIONS IOTIMINGS TIMINGDISABLES PARTITIONS CONSTRAINTS ASSERTIONS".split())
TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|\\\S+|[();+]|[^\s();+]+')


def def_records(path):
    """Read canonical DEF records; compare all nonmutable sections, fail closed."""
    text = Path(path).read_text()
    tokens = TOKEN.findall(re.sub(r"(?m)^\s*#.*$", "", text))
    result = defaultdict(list)
    i = 0
    while i < len(tokens):
        key = tokens[i]
        if key == "END":
            require(tokens[i:] == ["END", "DESIGN"], "Invalid canonical DEF trailer")
            break
        i += 1
        if key in SECTIONS:
            require(key not in result, f"Repeated DEF section: {key}")
            count = None
            if key != "PROPERTYDEFINITIONS":
                count = int(tokens[i]); i += 1
                require(tokens[i] == ";", f"Malformed {key} header"); i += 1
            result[key] = []
            while tokens[i:i+2] != ["END", key]:
                end = tokens.index(";", i)
                result[key].append(tuple(tokens[i:end])); i = end + 1
            i += 2
            if count is not None:
                require(count == len(result[key]), f"Wrong {key} record count")
        else:
            end = tokens.index(";", i)
            result[key].append(tuple(tokens[i:end])); i = end + 1
    return result


def immutable_def(path, post_route=False):
    data = def_records(path)
    data.pop("COMPONENTS", None)
    if post_route:
        data.pop("GCELLGRID", None)  # global_route builds its own GCell grid
    nets = data.pop("NETS", [])
    attributes = []
    for record in nets:
        # Regular signal-net names/connectivity are permitted to change. Routing
        # and NDR attributes are not allowed to smuggle in altered resources.
        tail = list(record[record.index("+"):]) if "+" in record else []
        if tail[:3] in (["+", "USE", "SIGNAL"], ["+", "USE", "CLOCK"]):
            tail = tail[3:]
        if tail:
            attributes.append((record[1], *tail))
    data["NET_ROUTING_ATTRIBUTES"] = attributes
    # I/O geometry and attributes are fixed; signal NET names may change.
    pins = []
    for row in data.get("PINS", []):
        row = list(row)
        if "NET" in row:
            at = row.index("NET")
            require(row[at-1] == "+", "Malformed canonical pin record")
            del row[at-1:at+2]
        pins.append(tuple(row))
    data["PINS"] = pins
    # Special-net geometry/attributes are fixed; permitted data repeaters can
    # change PG instance connections, checked individually below.
    special = []
    for row in data.get("SPECIALNETS", []):
        at = row.index("+") if "+" in row else len(row)
        special.append(tuple(row[:2]) + tuple(row[at:]))
    data["SPECIALNETS"] = special
    return {key: Counter(rows) for key, rows in data.items() if rows}


def physical_check(before, after, post_route=False):
    left, right = immutable_def(before, post_route), immutable_def(after, post_route)
    changed = sorted(k for k in left.keys() | right.keys() if left.get(k) != right.get(k))
    require(not changed, "Fixed DEF data changed: " + ", ".join(changed))
    return sorted(left)


def component_attributes(path):
    result = {}
    for record in def_records(path).get("COMPONENTS", []):
        attrs = list(record[3:]); kept = []
        while attrs:
            require(attrs[0] == "+", "Malformed component attributes")
            end = attrs.index("+", 1) if "+" in attrs[1:] else len(attrs)
            chunk, attrs = attrs[:end], attrs[end:]
            if chunk[1] not in ("PLACED", "FIXED", "COVER", "UNPLACED", "SOURCE"):
                kept.append(tuple(chunk))
        result[record[1]] = sorted(kept)
    return result


@lru_cache(maxsize=None)
def expression(text):
    """Parse Liberty Boolean functions without eval or executing user text."""
    parts = re.findall(r"[A-Za-z_][A-Za-z_0-9]*|[01!~'()*&+|^]", text)
    require("".join(parts) == re.sub(r"\s", "", text), f"Unsupported Liberty function: {text}")
    pos = 0

    def atom():
        nonlocal pos
        require(pos < len(parts), "Incomplete Liberty function")
        token = parts[pos]; pos += 1
        if token in ("!", "~"):
            node = ("not", atom())
        elif token == "(":
            node = either()
            require(pos < len(parts) and parts[pos] == ")", "Unbalanced Liberty function")
            pos += 1
        else:
            require(re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*|[01]", token), "Invalid Liberty atom")
            node = ("var", token)
        while pos < len(parts) and parts[pos] == "'":
            pos += 1; node = ("not", node)
        return node

    def both():
        nonlocal pos
        node = atom()
        while pos < len(parts) and parts[pos] not in (")", "+", "|", "^", "'"):
            if parts[pos] in ("*", "&"):
                pos += 1
            node = ("and", node, atom())
        return node

    def xor():
        nonlocal pos
        node = both()
        while pos < len(parts) and parts[pos] == "^":
            pos += 1; node = ("xor", node, both())
        return node

    def either():
        nonlocal pos
        node = xor()
        while pos < len(parts) and parts[pos] in ("+", "|"):
            pos += 1; node = ("or", node, xor())
        return node

    node = either()
    require(pos == len(parts), "Trailing Liberty function tokens")
    return node


def boolean(node, values):
    op = node[0]
    if op == "var":
        return node[1] == "1" if node[1] in ("0", "1") else values[node[1]]
    a = boolean(node[1], values)
    if op == "not":
        return not a
    b = boolean(node[2], values)
    return {"and": a and b, "or": a or b, "xor": a != b}[op]


def read_library(path):
    cells = defaultdict(dict)
    for row in table(path):
        master, pin = row["master"], row["pin"]
        require(pin not in cells[master] or cells[master][pin] == row,
                f"Liberty views disagree on function/classification: {master}/{pin}")
        cells[master][pin] = row
    return dict(cells)


def io(library, master):
    ports = library.get(master, {})
    inputs = sorted(p for p, v in ports.items() if v["direction"] == "input")
    outputs = sorted(p for p, v in ports.items() if v["direction"] == "output")
    return inputs, outputs


def repeater(library, master):
    ports = library.get(master, {})
    if not ports:
        return None
    row = next(iter(ports.values()))
    if row["buffer"] == "1":
        return 0
    if row["inverter"] == "1":
        return 1
    return None


@lru_cache(maxsize=None)
def symmetric(functions, inputs, permutation):
    require(len(inputs) <= 12, "Unsupported gate with more than 12 inputs")
    exprs = [expression(f) for f in functions]
    for bits in itertools.product((False, True), repeat=len(inputs)):
        original = dict(zip(inputs, bits))
        swapped = {p: original[q] for p, q in zip(inputs, permutation)}
        if any(boolean(f, original) != boolean(f, swapped) for f in exprs):
            return False
    return True


class Design:
    def __init__(self, prefix, library):
        prefix = str(prefix)
        rows = table(prefix + ".cells.tsv")
        self.cells = {row["instance"]: row for row in rows}
        require(len(rows) == len(self.cells), "Duplicate instance names")
        self.pins = defaultdict(dict)
        self.drivers = defaultdict(list)
        self.protected = set()
        self.library = library
        for row in table(prefix + ".pins.tsv"):
            inst, pin = row["instance"], row["pin"]
            require(pin not in self.pins[inst], f"Duplicate pin: {inst}/{pin}")
            self.pins[inst][pin] = row
            if inst and (row["net_signal"] == "CLOCK" or row["signal"] == "CLOCK"):
                self.protected.add(inst)
            if row["signal"] not in ("POWER", "GROUND") and row["net"]:
                driver = row["direction"] == ("INPUT" if not inst else "OUTPUT")
                require(row["direction"] != "INOUT", f"Unsupported signal inout: {inst}/{pin}")
                if driver:
                    self.drivers[row["net"]].append((inst, pin))
        for name, row in self.cells.items():
            if row["macro"] == "1" or row["physical"] == "1" or row["status"] in ("FIRM", "LOCKED", "COVER"):
                self.protected.add(name)
        for net, drivers in self.drivers.items():
            require(len(drivers) == 1, f"Multiple drivers on {net}: {drivers[:3]}")
        self.cache = {}

    def source(self, row):
        net = row["net"]
        if not net:
            return ("unconnected", "", 0)
        return self.resolve(net, set())

    def resolve(self, net, visiting):
        if net in self.cache:
            return self.cache[net]
        require(net not in visiting, f"Repeater cycle on net {net}")
        visiting.add(net)
        drivers = self.drivers.get(net, [])
        if not drivers:
            result = ("undriven", net, 0)
        else:
            inst, pin = drivers[0]
            parity = repeater(self.library, self.cells[inst]["master"]) if inst else None
            if parity is None or inst in self.protected:
                result = (inst, pin, 0)
            else:
                ins, outs = io(self.library, self.cells[inst]["master"])
                require(len(ins) == len(outs) == 1, f"Malformed repeater {inst}")
                upstream = self.pins[inst][ins[0]]["net"]
                require(upstream, f"Unconnected repeater input {inst}")
                a, b, inv = self.resolve(upstream, visiting)
                result = (a, b, inv ^ parity)
        visiting.remove(net)
        self.cache[net] = result
        return result


def transformations(before, after, library, group_file):
    groups = {}
    for index, line in enumerate(Path(group_file).read_text().splitlines()):
        for master in line.split(","):
            if master.strip():
                groups[master.strip()] = index
    old, new = Design(before, library), Design(after, library)
    removed = old.cells.keys() - new.cells.keys()
    added = new.cells.keys() - old.cells.keys()
    # Keep baseline protection even if a candidate changes a pin/net's type.
    new.protected |= old.protected
    for name in old.protected:
        a, b = old.cells[name], new.cells.get(name)
        require(b is not None and all(a[k] == b[k] for k in a if k != "status"),
                f"Protected instance changed or removed: {name}")
        require(a["status"] == b["status"] or
                (a["status"] == "PLACED" and b["status"] == "FIRM" and
                 any(p["net_signal"] == "CLOCK" for p in old.pins[name].values())),
                f"Protected instance status changed: {name}")
        require(set(new.pins[name]) == set(old.pins[name]), f"Protected pin interface changed: {name}")
        for pin, row in old.pins[name].items():
            other = new.pins[name][pin]
            if (old.cells[name]["physical"] == "1"
                    or row["signal"] in ("POWER", "GROUND", "CLOCK") or row["net_signal"] == "CLOCK"):
                require(row == other, f"Protected instance connectivity changed: {name}/{pin}")
            elif row["direction"] == "INPUT":
                require(old.source(row) == new.source(other), f"Protected data input changed: {name}/{pin}")
    blocked = ("*x1p*_ASAP7*", "*xp*_ASAP7*", "SDF*", "ICG*")
    for name, row in new.cells.items():
        previous = old.cells.get(name)
        master = row["master"]
        if previous is None or previous["master"] != master:
            require(master in library and master in groups, f"Unapproved master: {name} -> {master}")
            require(not any(fnmatch.fnmatchcase(master, p) for p in blocked), f"Prohibited master: {name} -> {master}")
        if name not in old.protected:
            require(row["status"] == "PLACED", f"Movable cell must be PLACED: {name}")
    for name in removed:
        require(name not in old.protected and repeater(library, old.cells[name]["master"]) is not None,
                f"Only data repeaters may be removed: {name}")
    for name in added:
        require(repeater(library, new.cells[name]["master"]) is not None,
                f"Only data repeaters may be inserted: {name}")
    swapped = resized = 0
    for name in old.cells.keys() & new.cells.keys():
        a, b = old.cells[name]["master"], new.cells[name]["master"]
        resized += a != b
        if repeater(library, a) is not None and name not in old.protected:
            require(repeater(library, b) is not None, f"Data repeater replaced by logic: {name}")
            continue
        require(a == b or (a in groups and groups[a] == groups.get(b)), f"Non-equivalent cell substitution: {name}: {a} -> {b}")
        require(set(old.pins[name]) == set(new.pins[name]), f"Pin interface changed: {name}")
        for pin, row in old.pins[name].items():
            if row["signal"] in ("POWER", "GROUND"):
                require(row == new.pins[name][pin], f"Power connectivity changed: {name}/{pin}")
        if name in old.protected:
            continue
        ins, outs = io(library, a)
        require(io(library, b) == (ins, outs), f"Liberty pin interface changed: {name}")
        av = {p: old.source(old.pins[name][p]) for p in ins}
        bv = {p: new.source(new.pins[name][p]) for p in ins}
        functions = tuple(library[a][p]["function"] for p in outs)
        require(all(functions), f"Unsupported non-combinational unprotected cell: {name}")
        require(all(not library[a][p]["tristate"] and not library[b][p]["tristate"] for p in outs), f"Unsupported tristate cell: {name}")
        require(functions == tuple(library[b][p]["function"] for p in outs), f"Liberty functions differ: {name}")
        if av != bv:
            require(Counter(av.values()) == Counter(bv.values()), f"Logic connectivity or polarity changed: {name}")
            choices = [[q for q in ins if av[q] == bv[p]] for p in ins]
            valid = any(len(set(perm)) == len(ins) and symmetric(functions, tuple(ins), perm)
                        for perm in itertools.product(*choices))
            require(valid, f"Non-equivalent input-pin swap: {name}")
            swapped += 1
    require(set(old.pins[""]) == set(new.pins[""]), "Top-level pin interface changed")
    for pin, row in old.pins[""].items():
        other = new.pins[""][pin]
        require((row["direction"], row["signal"]) == (other["direction"], other["signal"]), f"I/O type changed: {pin}")
        if row["signal"] in ("POWER", "GROUND"):
            require(row == other, f"Power port connectivity changed: {pin}")
        elif row["direction"] == "OUTPUT":
            require(old.source(row) == new.source(other), f"Output connection/polarity changed: {pin}")
    # Existing PG connections are fixed; new repeaters can use implicit PG pins.
    power_nets = {kind: {p["net"] for ps in old.pins.values() for p in ps.values()
                        if p["signal"] == kind and p["net"]} for kind in ("POWER", "GROUND")}
    for name in new.cells:
        if repeater(library, new.cells[name]["master"]) is not None and name not in old.protected:
            ins, outs = io(library, new.cells[name]["master"])
            for pin in ins + outs:
                require(new.pins[name][pin]["net"], f"Unconnected repeater pin: {name}/{pin}")
            new.resolve(new.pins[name][outs[0]]["net"], set())
            for pin, row in new.pins[name].items():
                if row["signal"] in ("POWER", "GROUND"):
                    # PG pins may be unconnected when the supplied flow leaves
                    # logic PG implicit. Explicit connections must target a
                    # baseline power net of the same type.
                    allowed = power_nets[row["signal"]]
                    require(not row["net"] or row["net"] in allowed, f"Invalid repeater power connection: {name}/{pin}")
                    if name in old.cells and pin in old.pins[name]:
                        require(row == old.pins[name][pin], f"Repeater power connection changed: {name}/{pin}")
    return {"removed_data_repeaters": len(removed), "inserted_data_repeaters": len(added),
            "changed_masters": resized, "pin_swapped_instances": swapped,
            "protected_instances": len(old.protected)}


def check(before, after, library_path, group_file, post_route=False):
    sections = physical_check(str(before) + ".def", str(after) + ".def", post_route)
    attrs_a, attrs_b = component_attributes(str(before) + ".def"), component_attributes(str(after) + ".def")
    for name, attrs in attrs_b.items():
        require(attrs == attrs_a.get(name, []), f"Component region/halo/properties changed: {name}")
    counts = transformations(before, after, read_library(library_path), group_file)
    def implementation(prefix):
        cells = {r["instance"]: tuple(r[k] for k in ("master", "x", "y", "orientation"))
                 for r in table(str(prefix) + ".cells.tsv")}
        nets = defaultdict(list)
        for row in table(str(prefix) + ".pins.tsv"):
            if row["net"]:
                nets[row["net"]].append((row["instance"], row["pin"]))
        # Net renaming and PLACED-to-FIXED status alone are not optimization.
        return cells, sorted(tuple(sorted(pins)) for pins in nets.values())
    return {"passed": True, "fixed_def_sections": sections, "transformations": counts,
            "changed_from_baseline": implementation(before) != implementation(after)}


def finalize(folder):
    """Publish a hash-bound validation record only after every evaluator stage."""
    folder = Path(folder)
    read = lambda name: json.loads((folder / name).read_text())
    for name in ("structural_validation.json", "final_structural_validation.json"):
        require(read(name).get("passed") is True, f"Failed check: {name}")
    submission = read("submission_validation.json")
    require(submission.get("r0_to_submission_equivalence", {}).get("passed") is True,
            "Baseline-to-submission formal proof did not pass")
    for key in ("clock_and_sink_integrity", "protected_instance_integrity"):
        require(submission.get(key) is True, f"Failed check: {key}")
    metrics = read("metrics.json")
    require(metrics["validation"].get("input_def_verilog_structurally_identical") is True,
            "DEF/Verilog consistency failed")
    require(metrics["validation"].get("input_to_evaluated_equivalence", {}).get("passed") is True,
            "Post-evaluation formal proof did not pass")
    require("EVALUATION_OPENROAD_SUCCESS" in (folder / "evaluation.log").read_text(),
            "OpenROAD did not complete placement/routing checks")
    spefs = read("spef_validation.json")
    require(len(spefs) == 3 and all(s["nets"] > 0 and s["mismatches"] == 0 for s in spefs),
            "SPEF validation failed")
    cfg = read("run_config.json")
    require(cfg["RUN_RESIZER"] == "0" and cfg["PHASE"] == "full" and cfg["VERIFY_FORMAL"] == "1",
            "Submission validation requires the public full evaluator")
    measured = (folder / "runtime_validation.json").exists()
    if measured:
        runtime = read("runtime_validation.json")
        require(read("structural_validation.json").get("changed_from_baseline") is True,
                "Unchanged baseline is valid for calibration, but not a contestant solution")
        require(runtime.get("passed") is True and math.isfinite(runtime["tool_s"])
                and math.isfinite(runtime["flow_s"]) and 0 <= runtime["tool_s"] <= 18000
                and runtime["tool_s"] <= runtime["flow_s"] <= 18000,
                "Measured tool/flow runtime failed")
        require(runtime["input_sha256"] == {k: cfg["sha256"][k] for k in ("INPUT_DEF", "INPUT_VERILOG")},
                "Runtime record does not belong to evaluated submission")
    names = ["summary.csv", "metrics.json", "evaluated.def", "evaluated.v", "run_config.json",
             "structural_validation.json", "final_structural_validation.json",
             "submission_validation.json", "evaluation_runtime.json", "spef_validation.json"]
    if measured:
        names.append("runtime_validation.json")
    report = {"passed": True, "design_legality_passed": True,
              "complete_contest_legality": True, "runtime_measured": measured,
              "automated_checks_passed": True,
              "design": cfg["BENCHMARK"], "configuration": cfg["scenario"]["id"],
              "files_sha256": {name: digest(folder / name) for name in names},
              "checks": ["fixed_floorplan_io_pdn_blockages_tracks", "protected_macros_and_cells",
                         "allowed_masters_and_transforms", "clock_tree_and_sink_integrity",
                         "placement_legality", "def_verilog_consistency", "formal_equivalence",
                         "post_routing_integrity", "spef_integrity"],
              "note": "Design legality is checked against the packaged contest policy. Tool provenance/originality and final ranking are organizer responsibilities."}
    (folder / "legality.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def verify_certificate(candidate, require_runtime=True):
    candidate = Path(candidate)
    folder = candidate.parent
    record = json.loads((folder / "legality.json").read_text())
    require(record.get("passed") is True and record.get("design_legality_passed") is True,
            "Candidate has not passed design legality")
    require(record["files_sha256"].get("summary.csv") == digest(candidate), "Scoring CSV changed since validation")
    if require_runtime:
        require(record.get("runtime_measured") is True, "Run run_submission.py to measure tool runtime, or explicitly request an unverified dummy score")
    required = {"summary.csv", "metrics.json", "evaluated.def", "evaluated.v", "run_config.json",
                "structural_validation.json", "final_structural_validation.json",
                "submission_validation.json", "evaluation_runtime.json", "spef_validation.json"}
    if require_runtime:
        required.add("runtime_validation.json")
    require(required <= record["files_sha256"].keys(), "Incomplete validation record")
    for name, expected in record["files_sha256"].items():
        require(Path(name).name == name and digest(folder / name) == expected,
                f"Validated evaluation artifact changed: {name}")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--post-route", action="store_true")
    args = parser.parse_args()
    try:
        report = check(args.baseline, args.candidate, str(args.baseline) + ".library.tsv",
                       Path(__file__).resolve().parents[1] / "third_party/displacement" / "asap7_equivalent_cell_list.csv", args.post_route)
    except (ValueError, KeyError, IndexError, RecursionError, OSError) as error:
        report = {"passed": False, "reason": str(error)}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    require(report["passed"], report.get("reason", "Legality failed"))


if __name__ == "__main__":
    main()
