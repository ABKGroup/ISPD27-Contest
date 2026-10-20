#!/usr/bin/env python3
"""
Netlist Equivalence Checker

Validates post-optimization netlists against pre-optimization netlists.
Checks: instance presence, buffer/inverter paths, physical/macro/IO locations.
"""

import argparse
import csv
import os
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, Set, Tuple, List

# Default paths and seeds
DEFAULT_EQUIV_CELLS = (
    "./asap7_equivalent_cell_list.csv"
)
BUFFER_SEED = "BUFx2_ASAP7_75t_L"
INVERTER_SEED = "INVx1_ASAP7_75t_L"


@dataclass(frozen=True)
class PinNode:
    """Represents a pin in the netlist graph."""
    pin_name: str
    inst_id: int
    inst_name: str
    is_driver: bool


def parse_args():
    parser = argparse.ArgumentParser(
        description="Check equivalence between pre-opt and post-opt netlists"
    )
    parser.add_argument(
        "--pre_opt", required=True,
        help="Path to pre-optimization directory"
    )
    parser.add_argument(
        "--post_opt", required=True,
        help="Path to post-optimization directory"
    )
    parser.add_argument(
        "--equiv_cells", default=DEFAULT_EQUIV_CELLS,
        help="Path to equivalent cells CSV"
    )
    return parser.parse_args()


def load_nodes(node_file: str) -> Dict[str, Tuple[str, str, float, float]]:
    """Load node.csv into dict: {name: (master, type, x, y)}"""
    nodes = {}
    with open(node_file, "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 5:
                nodes[row[0]] = (
                    row[1], row[2], float(row[3]), float(row[4])
                )
    return nodes


def load_nets(net_file: str):
    """Load nets.csv into dict: {net_name: (driver_pin, [sink_pins])}"""
    nets = {}
    with open(net_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 2:
                continue
            net_name = parts[0]
            pins = []
            for p in parts[1:]:
                p = p.strip()
                if not p:
                    continue
                if " " in p:
                    inst, pin = p.rsplit(" ", 1)
                    pins.append((inst, pin))
                else:
                    pins.append((p, ""))
            if pins:
                nets[net_name] = (pins[0], pins[1:])
    return nets


def load_equiv_cells(equiv_file: str):
    """Load equivalent_cells.csv.

    Returns (equiv_groups, buffer_masters, inverter_masters).
    """
    equiv_groups = {}
    buffer_masters = set()
    inverter_masters = set()

    with open(equiv_file, "r") as f:
        for group_id, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            cells = [c.strip() for c in line.split(",") if c.strip()]
            for cell in cells:
                equiv_groups[cell] = group_id
            if BUFFER_SEED in cells:
                buffer_masters = set(cells)
            if INVERTER_SEED in cells:
                inverter_masters = set(cells)

    return equiv_groups, buffer_masters, inverter_masters


def build_graph(post_nets, post_nodes, pre_nodes,
                buffer_masters, inverter_masters):
    """Build pin-level graph.

    Returns (inst_registry, inst_is_matched, buffer_ids, inverter_ids,
             net_edges, internal_edges).
    """
    inst_registry = {}
    id_to_inst = {}
    inst_is_matched = {}
    buffer_ids = set()
    inverter_ids = set()
    inst_driver_pins = defaultdict(set)
    inst_sink_pins = defaultdict(set)
    net_edges = defaultdict(list)
    next_id = 0

    # Register instances from nodes
    for inst_name, (master, _, _, _) in post_nodes.items():
        inst_registry[inst_name] = next_id
        id_to_inst[next_id] = inst_name
        inst_is_matched[next_id] = inst_name in pre_nodes
        if master in buffer_masters:
            buffer_ids.add(next_id)
        elif master in inverter_masters:
            inverter_ids.add(next_id)
        next_id += 1

    # Process nets
    for _, (driver, sinks) in post_nets.items():
        driver_inst, driver_pin = driver

        # Register driver if needed (for IOs)
        if driver_inst not in inst_registry:
            inst_registry[driver_inst] = next_id
            id_to_inst[next_id] = driver_inst
            inst_is_matched[next_id] = driver_inst in pre_nodes
            next_id += 1

        driver_id = inst_registry[driver_inst]
        inst_driver_pins[driver_id].add(driver_pin)
        driver_node = PinNode(driver_pin, driver_id, driver_inst, True)

        for sink_inst, sink_pin in sinks:
            if sink_inst not in inst_registry:
                inst_registry[sink_inst] = next_id
                id_to_inst[next_id] = sink_inst
                inst_is_matched[next_id] = sink_inst in pre_nodes
                next_id += 1

            sink_id = inst_registry[sink_inst]
            inst_sink_pins[sink_id].add(sink_pin)
            sink_node = PinNode(sink_pin, sink_id, sink_inst, False)
            net_edges[driver_node].append(sink_node)

    # Build internal edges for unmatched buffers/inverters
    internal_edges = defaultdict(list)
    for inst_id in buffer_ids | inverter_ids:
        if inst_is_matched[inst_id]:
            continue
        inst_name = id_to_inst[inst_id]
        for sink_pin in inst_sink_pins[inst_id]:
            sink_node = PinNode(sink_pin, inst_id, inst_name, False)
            for driver_pin in inst_driver_pins[inst_id]:
                drv_node = PinNode(driver_pin, inst_id, inst_name, True)
                internal_edges[sink_node].append(drv_node)

    return (inst_registry, inst_is_matched, buffer_ids, inverter_ids,
            net_edges, internal_edges)


def check_instance_presence(pre_nodes, post_nodes, equiv_groups,
                            buffer_masters, inverter_masters):
    """Check 1: Instance presence with equivalent cell mapping."""
    violations = []

    # Check pre_opt instances exist in post_opt with valid masters
    for name, (master, node_type, _, _) in pre_nodes.items():
        if node_type == "IO":
            continue
        if name not in post_nodes:
            violations.append(f"Missing instance: {name} (master: {master})")
            continue
        post_master = post_nodes[name][0]
        if master != post_master:
            pre_grp = equiv_groups.get(master)
            post_grp = equiv_groups.get(post_master)
            if pre_grp is None or post_grp is None or pre_grp != post_grp:
                violations.append(
                    f"Invalid cell substitution: {name} "
                    f"({master} -> {post_master})"
                )

    # Check newly added instances are buffers/inverters
    pre_insts = {n for n, (_, t, _, _) in pre_nodes.items() if t != "IO"}
    for name, (master, node_type, _, _) in post_nodes.items():
        if node_type == "IO" or name in pre_insts:
            continue
        if master not in buffer_masters and master not in inverter_masters:
            violations.append(
                f"Invalid newly added instance: {name} (master: {master})"
            )

    return len(violations) == 0, violations


def bfs_from_driver(driver_inst, driver_pin, inst_registry, inst_is_matched,
                    buffer_ids, inverter_ids, net_edges, internal_edges):
    """BFS from driver to find all reachable sinks.

    Returns (valid_sinks, invalid_sinks).
    """
    start_id = inst_registry.get(driver_inst)
    if start_id is None:
        return set(), set()

    start_node = PinNode(driver_pin, start_id, driver_inst, True)
    visited = set()
    valid_sinks = set()
    invalid_sinks = set()

    queue = deque([(start_node, 0)])

    while queue:
        node, inv_count = queue.popleft()
        state = (node, inv_count % 2)
        if state in visited:
            continue
        visited.add(state)

        if node.is_driver:
            for sink_node in net_edges.get(node, []):
                is_matched = inst_is_matched.get(sink_node.inst_id, False)
                is_unmatched_buf = (not is_matched and
                                    sink_node.inst_id in buffer_ids)
                is_unmatched_inv = (not is_matched and
                                    sink_node.inst_id in inverter_ids)

                if is_unmatched_buf:
                    if (sink_node, inv_count % 2) not in visited:
                        queue.append((sink_node, inv_count))
                elif is_unmatched_inv:
                    if (sink_node, (inv_count + 1) % 2) not in visited:
                        queue.append((sink_node, inv_count + 1))
                else:
                    sink_key = (sink_node.inst_name, sink_node.pin_name)
                    if inv_count % 2 == 0:
                        valid_sinks.add(sink_key)
                    elif sink_key not in valid_sinks:
                        invalid_sinks.add(sink_key)
        else:
            for driver_node in internal_edges.get(node, []):
                if (driver_node, inv_count % 2) not in visited:
                    queue.append((driver_node, inv_count))

    return valid_sinks, invalid_sinks


def check_buffer_inverter_paths(pre_nets, post_nets, inst_registry,
                                inst_is_matched, buffer_ids, inverter_ids,
                                net_edges, internal_edges):
    """Check 2: Verify valid paths for all pre_opt driver-sink pairs."""
    violations = []

    # Build direct edge lookup for fast matching
    print("  Phase 1: Building direct edge lookup...")
    t0 = time.time()
    direct_edges = set()
    for _, (driver, sinks) in post_nets.items():
        for sink in sinks:
            direct_edges.add((driver[0], driver[1], sink[0], sink[1]))
    print(f"    Built {len(direct_edges)} edges in {time.time() - t0:.2f}s")

    # Check pre_opt pairs
    print("  Phase 2: Checking pairs...")
    t0 = time.time()
    total, direct_matches = 0, 0
    needs_bfs = defaultdict(list)

    for net_name, (driver, sinks) in pre_nets.items():
        d_inst, d_pin = driver
        for s_inst, s_pin in sinks:
            if driver[1] == "_IO_" and s_pin == "_IO_":
                continue
            total += 1
            if (d_inst, d_pin, s_inst, s_pin) in direct_edges:
                direct_matches += 1
            else:
                needs_bfs[(d_inst, d_pin)].append((net_name, s_inst, s_pin))

    pct = 100 * direct_matches / total if total > 0 else 0
    print(f"    Total: {total}, Direct: {direct_matches} ({pct:.1f}%), "
          f"BFS needed: {total - direct_matches}")
    print(f"    Phase 2 time: {time.time() - t0:.2f}s")

    # BFS for buffered connections
    if needs_bfs:
        print("  Phase 3: BFS for buffered connections...")
        t0 = time.time()
        for i, ((d_inst, d_pin), sinks_to_check) in enumerate(
                needs_bfs.items()):
            if (i + 1) % 1000 == 0:
                print(f"    Progress: {i + 1}/{len(needs_bfs)}")

            valid, invalid = bfs_from_driver(
                d_inst, d_pin, inst_registry, inst_is_matched,
                buffer_ids, inverter_ids, net_edges, internal_edges
            )

            for net_name, s_inst, s_pin in sinks_to_check:
                key = (s_inst, s_pin)
                if key in valid:
                    continue
                if key in invalid:
                    violations.append(
                        f"Net {net_name}: {d_inst}.{d_pin} -> "
                        f"{s_inst}.{s_pin} (odd inverters)"
                    )
                else:
                    violations.append(
                        f"Net {net_name}: No path {d_inst}.{d_pin} -> "
                        f"{s_inst}.{s_pin}"
                    )

        print(f"    Phase 3 time: {time.time() - t0:.2f}s")

    return len(violations) == 0, violations


def check_locations(pre_nodes, post_nodes, node_type, equiv_groups=None):
    """Check that nodes of given type haven't moved.

    For Inst type, only check if not in equiv_groups.
    """
    violations = []

    for name, (master, ntype, pre_x, pre_y) in pre_nodes.items():
        if ntype != node_type:
            continue

        # For Inst type, skip if master is in equiv_groups
        if node_type == "Inst" and equiv_groups and master in equiv_groups:
            continue

        if name not in post_nodes:
            violations.append(f"Missing {node_type}: {name}")
            continue

        _, _, post_x, post_y = post_nodes[name]
        if abs(pre_x - post_x) > 1e-6 or abs(pre_y - post_y) > 1e-6:
            violations.append(
                f"{node_type} moved: {name} "
                f"({pre_x},{pre_y}) -> ({post_x},{post_y})"
            )

    return len(violations) == 0, violations


def calculate_logic_cell_movement(pre_nodes, post_nodes, equiv_groups):
    """Calculate average movement for matched logic cells.

    Logic cells are:
    - Type "Inst" (excludes Macros and IOs by type)
    - Master in equiv_groups (excludes fixed/physical cells)
    Only considers cells that exist in both pre and post netlists.

    Returns: (avg_movement, count, moved_count, max_movement)
    """
    total_movement = 0.0
    count = 0
    moved_count = 0
    max_movement = 0.0

    for name, (master, node_type, pre_x, pre_y) in pre_nodes.items():
        # Skip Macros and IOs by type
        if node_type != "Inst":
            continue

        # Skip fixed/physical cells (only include moveable logic cells)
        if master not in equiv_groups:
            continue

        # Only consider matched cells (exist in both netlists)
        if name not in post_nodes:
            continue

        _, _, post_x, post_y = post_nodes[name]
        movement = abs(post_x - pre_x) + abs(post_y - pre_y)

        total_movement += movement
        count += 1
        if movement > 1e-6:
            moved_count += 1
        if movement > max_movement:
            max_movement = movement

    avg_movement = total_movement / count if count > 0 else 0.0
    return avg_movement, count, moved_count, max_movement


def print_result(name, passed, violations, max_show=10):
    print(f"\n=== {name} ===")
    print(f"{'PASS' if passed else 'FAIL'}: {len(violations)} violations")
    for v in violations[:max_show]:
        print(f"  - {v}")
    if len(violations) > max_show:
        print(f"  ... and {len(violations) - max_show} more")


def main():
    t_start = time.time()
    args = parse_args()

    # File paths
    files = {
        'pre_node': os.path.join(args.pre_opt, "node.csv"),
        'pre_net': os.path.join(args.pre_opt, "nets.csv"),
        'post_node': os.path.join(args.post_opt, "node.csv"),
        'post_net': os.path.join(args.post_opt, "nets.csv"),
        'equiv': args.equiv_cells
    }
    for f in files.values():
        if not os.path.exists(f):
            print(f"Error: File not found: {f}")
            sys.exit(1)

    # Load data
    print("Loading data...")
    t0 = time.time()
    pre_nodes = load_nodes(files['pre_node'])
    post_nodes = load_nodes(files['post_node'])
    pre_nets = load_nets(files['pre_net'])
    post_nets = load_nets(files['post_net'])
    equiv_groups, buf_masters, inv_masters = load_equiv_cells(files['equiv'])
    print(f"  Load time: {time.time() - t0:.2f}s")
    print(f"  Pre: {len(pre_nodes)} nodes, {len(pre_nets)} nets | "
          f"Post: {len(post_nodes)} nodes, {len(post_nets)} nets")

    results = []

    # Check 1: Instance presence
    print("\nCheck 1: Instance Presence...")
    t0 = time.time()
    passed, violations = check_instance_presence(
        pre_nodes, post_nodes, equiv_groups, buf_masters, inv_masters
    )
    results.append(("Check 1: Instance Presence", passed, violations))
    print_result("Check 1: Instance Presence", passed, violations)
    print(f"  Time: {time.time() - t0:.2f}s")

    # Build graph
    print("\nBuilding graph...")
    t0 = time.time()
    graph_data = build_graph(
        post_nets, post_nodes, pre_nodes, buf_masters, inv_masters
    )
    inst_reg, inst_matched, buf_ids, inv_ids, net_edges, int_edges = graph_data
    print(f"  Graph time: {time.time() - t0:.2f}s")

    # Check 2: Buffer/inverter paths
    print("\nCheck 2: Buffer/Inverter Paths...")
    t0 = time.time()
    passed, violations = check_buffer_inverter_paths(
        pre_nets, post_nets, inst_reg, inst_matched,
        buf_ids, inv_ids, net_edges, int_edges
    )
    results.append(("Check 2: Buffer/Inverter Paths", passed, violations))
    print_result("Check 2: Buffer/Inverter Paths", passed, violations)
    print(f"  Time: {time.time() - t0:.2f}s")

    # Check 3: Physical cell locations
    print("\nCheck 3: Physical Cell Locations...")
    t0 = time.time()
    passed, violations = check_locations(
        pre_nodes, post_nodes, "Inst", equiv_groups
    )
    results.append(("Check 3: Physical Cells", passed, violations))
    print_result("Check 3: Physical Cells", passed, violations)
    print(f"  Time: {time.time() - t0:.2f}s")

    # Logic cell movement statistics
    print("\n=== Logic Cell Movement Statistics ===")
    avg_move, total_cells, moved_cells, max_move = calculate_logic_cell_movement(
        pre_nodes, post_nodes, equiv_groups
    )
    print(f"  Matched logic cells: {total_cells}")
    print(f"  Number of cells that moved: {moved_cells}")
    print(f"  Average movement: {avg_move:.2f} units")
    print(f"  Max movement: {max_move:.2f} units")

    # Check 4: Macro locations
    print("\nCheck 4: Macro Locations...")
    t0 = time.time()
    passed, violations = check_locations(pre_nodes, post_nodes, "Macro")
    results.append(("Check 4: Macros", passed, violations))
    print_result("Check 4: Macros", passed, violations)
    print(f"  Time: {time.time() - t0:.2f}s")

    # Check 5: IO locations
    print("\nCheck 5: I/O Locations...")
    t0 = time.time()
    passed, violations = check_locations(pre_nodes, post_nodes, "IO")
    results.append(("Check 5: I/O", passed, violations))
    print_result("Check 5: I/O", passed, violations)
    print(f"  Time: {time.time() - t0:.2f}s")

    # Summary
    print("\n" + "=" * 50)
    passed_count = sum(1 for _, p, _ in results if p)
    print(f"SUMMARY: {passed_count}/{len(results)} checks passed")
    print(f"TOTAL TIME: {time.time() - t_start:.2f}s")
    result_str = "EQUIVALENT" if passed_count == len(results) else "NOT EQUIV"
    print(f"RESULT: {result_str}")

    return 0 if passed_count == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
