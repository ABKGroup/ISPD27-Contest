"""Benchmark names, packed inputs and benchmark.json paths."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from internal.benchmark import DEFAULT_TECH_LEF, environment, names, packed


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def bench(self, name, config=None):
        folder = self.root / "benchmarks" / name
        folder.mkdir(parents=True)
        (folder / "benchmark.json").write_text(json.dumps(config or {}))
        return folder

    def test_names_cover_condition_and_scan_directories(self):
        self.bench("jpeg/util_65")
        self.bench("jpeg/util_65/scan")
        self.bench("chip/util_65/scan")
        # A directory without benchmark.json is not a benchmark, such as the parent of a scan-only testcase.
        (self.root / "benchmarks/chip/util_65/macros").mkdir()
        self.assertEqual(names(self.root), ["chip/util_65/scan", "jpeg/util_65", "jpeg/util_65/scan"])

    def test_packed_inputs(self):
        folder = self.bench("nyuzi/util_55")
        self.assertEqual(packed(folder), [])
        for name in ("input.def.gz", "input.v.gz"):
            (folder / name).write_text("")
        self.assertEqual(packed(folder), [str(folder / "input.def.gz"), str(folder / "input.v.gz")])
        (folder / "input.def").write_text("")
        self.assertEqual(packed(folder), [str(folder / "input.v.gz")])

    def test_environment_paths(self):
        folder = self.bench("chip/util_65/scan", {
            "macro_lefs": ["../macros/lef/a.lef", "../macros/lef/b.lef"], "macro_libs": ["../macros/lib/a.lib"]})
        env = environment(self.root, folder)
        self.assertEqual(env["TECH_LEF"], str(self.root / "platform/asap7" / DEFAULT_TECH_LEF))
        self.assertEqual(env["ADDITIONAL_LEFS"],
                         f"{folder}/../macros/lef/a.lef:{folder}/../macros/lef/b.lef")
        self.assertEqual(env["ADDITIONAL_LIBS"], f"{folder}/../macros/lib/a.lib")
        self.assertEqual(environment(self.root, self.bench("aes/util_50"))["ADDITIONAL_LEFS"], "")


if __name__ == "__main__":
    unittest.main()
