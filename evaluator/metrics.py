#!/usr/bin/env python3
"""Write one row per scenario for the separate score.py scoring step."""
import csv
import importlib.util
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def rows(path, delimiter=","):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter=delimiter))


def summarize(folder):
    data = json.loads((folder / "metrics.json").read_text())
    cfg = json.loads((folder / "run_config.json").read_text())
    geometry = json.loads((folder / "geometry.json").read_text())
    spec = importlib.util.spec_from_file_location("displacement_movement", HERE / "displacement/netlist_equiv_check.py")
    movement = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = movement
    spec.loader.exec_module(movement)
    groups, _, _ = movement.load_equiv_cells(str(HERE / "displacement/asap7_equivalent_cell_list.csv"))
    dbu = geometry["dbu_per_um"]
    snapshots = []
    for name in ["baseline_placement.tsv", "placement_after.tsv"]:
        records = rows(folder / name, "\t")
        nodes = {r["instance"].replace("\\", ""): (r["master"], "Inst",
                 int(r["x_dbu"]) / dbu, int(r["y_dbu"]) / dbu) for r in records}
        if len(nodes) != len(records):
            raise ValueError("Instance names collide after ISPD26 name normalization")
        snapshots.append(nodes)
    average, matched, moved, maximum = movement.calculate_logic_cell_movement(*snapshots, groups)
    routing = rows(folder / "routing.csv")
    overflow = math.fsum(float(r["total_overflow"]) for r in routing)
    peak = max(float(r["max_overflow"]) for r in routing)
    runtime = {r["stage"]: float(r["seconds"]) for r in data["runtime"]}
    output = []
    for scene in sorted(data["scenarios"], key=lambda r: ["BC", "TC", "WC"].index(r["corner"])):
        row = dict(design=cfg["BENCHMARK"], scenario=cfg["scenario"]["id"],
                   corner=scene["corner"], resizer=int(cfg["RUN_RESIZER"]))
        for check in ["setup", "hold"]:
            row[f"{check}_wns_ns"] = min(0, float(scene[f"{check}_worst_slack_ps"])) / 1000
            row[f"{check}_tns_ns"] = float(scene[f"{check}_tns_ps"]) / 1000
            row[f"{check}_violating_endpoints"] = scene[f"{check}_violating_endpoints"]
        for report, column in [("max_slew", "slew_violation_sum_ps"),
                               ("max_capacitance", "cap_violation_sum_ff"),
                               ("max_fanout", "fanout_violation_sum")]:
            row[column] = scene["erc"][report]["sum_violation"]
            row[column + "_count"] = scene["erc"][report]["count"]
        power = scene["power"]["Total"]
        row.update(global_routing_overflow=overflow, max_global_routing_overflow=peak,
                   runtime_s=runtime["total_openroad"], average_displacement_um=average,
                   matched_logic_cells=matched, moved_logic_cells=moved,
                   max_displacement_um=maximum, dynamic_power_w=power["internal"] + power["switching"],
                   leakage_power_w=power["leakage"], area_um2=geometry["functional_cell_area_um2"])
        output.append(row)
    with (folder / "summary.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=output[0].keys())
        writer.writeheader()
        writer.writerows(output)


if __name__ == "__main__":
    summarize(Path(sys.argv[1]).resolve())
