"""Benchmark metadata shared by the public evaluator commands."""
import json
from pathlib import Path

DEFAULT_TECH_LEF = "lef/asap7_tech_1x_201209.lef"


def names(root):
    """Every benchmark directory that carries a benchmark.json: benchmarks/<name>,
    benchmarks/<design>/<condition> and its scan version benchmarks/<design>/<condition>/scan."""
    base = Path(root) / "benchmarks"
    found = (list(base.glob("*/benchmark.json")) + list(base.glob("*/*/benchmark.json"))
             + list(base.glob("*/*/scan/benchmark.json")))
    return sorted(p.parent.relative_to(base).as_posix() for p in found)


def environment(root, bench):
    """Technology LEF and hard-macro files from benchmark.json; paths joined by ':'."""
    cfg = json.loads((Path(bench) / "benchmark.json").read_text())
    platform = Path(root) / "platform/asap7"
    return dict(
        TECH_LEF=str(platform / cfg.get("tech_lef", DEFAULT_TECH_LEF)),
        ADDITIONAL_LEFS=":".join(str(Path(bench) / p) for p in cfg.get("macro_lefs", [])),
        ADDITIONAL_LIBS=":".join(str(Path(bench) / p) for p in cfg.get("macro_libs", [])))


def packed(bench):
    """Inputs still shipped only as .gz; they must be unpacked with gunzip -k first."""
    return [str(Path(bench) / (name + ".gz")) for name in ("input.def", "input.v")
            if not (Path(bench) / name).is_file() and (Path(bench) / (name + ".gz")).is_file()]
