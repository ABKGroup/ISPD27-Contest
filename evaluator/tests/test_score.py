"""Run with python3 -B -m unittest discover -s evaluator/tests -v."""
import copy
import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("contest_score", ROOT / "score.py")
score = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score)


class ScoreTests(unittest.TestCase):
    def setUp(self):
        # Fixed fixture weights keep hand-calculated expectations independent
        # of changes to the released contest scoring policy.
        self.config = {
            "status": "provisional",
            "weights": {
                "setup_tns": 0.5, "setup_wns": 0.5,
                "dynamic_power": 0.05, "leakage_power": 0.05,
                "hold_tns": 1.0, "hold_wns": 1.0,
                "slew": 0.1, "cap": 0.1, "fanout": 0.1,
                "tool_runtime": 0.05, "flow_runtime": 0.05,
                "displacement": 0.05,
                "max_overflow": 1.0, "total_overflow": 1.0,
            },
        }
        self.config["scenarios"] = {"BC": {"mode": "functional",
            "weight": 1, "hold_weight": 1, "hold_tns_tolerance_ns": 1, "hold_wns_tolerance_ns": 1}}
        self.config["epsilon"] = dict.fromkeys(score.EPSILONS, 1)
        self.config["overflow_thresholds"] = {"max": 1, "total": 5}
        row = dict.fromkeys(score.TIMING + score.NONNEGATIVE, 0.0)
        row.update(setup_tns_ns=-101, setup_wns_ns=-11, dynamic_power_w=10,
                   leakage_power_w=2, slew_violation_sum_ps=9,
                   cap_violation_sum_ff=9, fanout_violation_sum=9,
                   average_displacement_um=2)
        self.base = {"BC": row}
        self.candidate = copy.deepcopy(self.base)
        self.reference = copy.deepcopy(self.base)
        self.times = dict(tool_s=200, flow_s=400, reference_tool_s=200, reference_flow_s=400)

    def result(self):
        return score.calculate(self.base, self.candidate, self.reference, self.config, self.times)

    def test_identical_within_tolerances_scores_zero(self):
        self.assertEqual(self.result()["score"], 0)

    def test_hand_calculated_all_components(self):
        self.candidate["BC"].update(
            setup_tns_ns=-51, setup_wns_ns=-6, hold_tns_ns=-3, hold_wns_ns=-2,
            dynamic_power_w=8, leakage_power_w=1, slew_violation_sum_ps=19,
            cap_violation_sum_ff=4, average_displacement_um=1,
            max_global_routing_overflow=3, global_routing_overflow=9)
        self.times["tool_s"] = 100
        result = self.result()
        expected = dict(ppa=0.535, hold_penalty=1.5, erc_penalty=0.05,
                        runtime_penalty=-0.025, displacement_penalty=-1 / 60,
                        overflow_penalty=5 / 3)
        for key, value in expected.items():
            self.assertAlmostEqual(result["components"][key], value)
        self.assertAlmostEqual(result["score"], -2.64)

    def test_scenario_weights_and_physical_penalty_counted_once(self):
        for data in (self.base, self.candidate, self.reference):
            data["TC"] = copy.deepcopy(data["BC"])
            data["WC"] = copy.deepcopy(data["BC"])
        self.config["scenarios"] = {c: dict(mode="functional", weight=w, hold_weight=w, hold_tns_tolerance_ns=1,
            hold_wns_tolerance_ns=1) for c, w in (("BC", .2), ("TC", .3), ("WC", .5))}
        self.candidate["WC"]["setup_tns_ns"] = -51
        for row in self.candidate.values():
            row["average_displacement_um"] = 5
        result = self.result()
        self.assertAlmostEqual(result["components"]["ppa"], .125)
        self.assertAlmostEqual(result["components"]["displacement_penalty"], .05)
        self.assertAlmostEqual(result["score"], .075)

    def test_hold_threshold_boundary(self):
        self.candidate["BC"].update(hold_tns_ns=-1, hold_wns_ns=-1)
        self.assertEqual(self.result()["components"]["hold_penalty"], 0)

    def test_zero_threshold_overflow_uses_one_resource_unit(self):
        self.config['overflow_thresholds'] = {'max': 0, 'total': 0}
        self.config['epsilon']['overflow'] = 1e-6
        self.assertEqual(self.result()['components']['overflow_penalty'], 0)
        self.candidate['BC'].update(max_global_routing_overflow=1, global_routing_overflow=1)
        self.assertEqual(self.result()['components']['overflow_penalty'], 2)
        self.candidate['BC']['global_routing_overflow'] = 5
        self.assertEqual(self.result()['components']['overflow_penalty'], 6)

    def test_overflow_threshold_boundary_and_positive_threshold(self):
        self.config['overflow_thresholds'] = {'max': 2, 'total': 10}
        self.config['epsilon']['overflow'] = 1e-6
        self.candidate['BC'].update(max_global_routing_overflow=2, global_routing_overflow=10)
        self.assertEqual(self.result()['components']['overflow_penalty'], 0)
        self.candidate['BC'].update(max_global_routing_overflow=4, global_routing_overflow=15)
        self.assertAlmostEqual(self.result()['components']['overflow_penalty'],
                               2 / 2.000001 + 5 / 10.000001)

    def test_equal_weights_required_for_both_timing_types(self):
        for key in ("setup_tns", "hold_tns"):
            with self.subTest(key=key):
                original = self.config["weights"][key]
                self.config["weights"][key] = original + 1
                with self.assertRaisesRegex(ValueError, "weights must be equal"):
                    self.result()
                self.config["weights"][key] = original

    def test_missing_scenario_rejected(self):
        self.candidate.clear()
        with self.assertRaisesRegex(ValueError, "identical scenario sets"):
            self.result()

    def test_zero_baseline_power_rejected(self):
        self.base["BC"]["dynamic_power_w"] = 0
        with self.assertRaisesRegex(ValueError, "denominator"):
            self.result()

    def test_literal_setup_denominator_cancellation_rejected(self):
        self.base["BC"]["setup_tns_ns"] = -1
        with self.assertRaisesRegex(ValueError, "denominator"):
            self.result()

    def test_runtime_limit_and_inclusion(self):
        # The limit is on tool runtime; total-flow runtime has no limit.
        self.assertEqual(score.TOOL_LIMIT_SECONDS, 7 * 3600)
        self.times.update(tool_s=score.TOOL_LIMIT_SECONDS, flow_s=40000)
        self.result()
        self.times["tool_s"] = score.TOOL_LIMIT_SECONDS + 1
        with self.assertRaisesRegex(ValueError, "runtime limit"):
            self.result()
        self.times.update(tool_s=200, flow_s=1)
        with self.assertRaisesRegex(ValueError, "include tool"):
            self.result()

    def scan_fixture(self, weight=0, hold_weight=0.5):
        """A scan testcase with one functional scene BC and one scan test scene BC_test."""
        self.config["scan_scenarios"] = {
            "BC": {"mode": "functional", "weight": 1 - weight, "hold_weight": 1 - hold_weight,
                   "hold_tns_tolerance_ns": 1, "hold_wns_tolerance_ns": 1},
            "BC_test": {"mode": "scan test", "weight": weight, "hold_weight": hold_weight,
                        "hold_tns_tolerance_ns": 1, "hold_wns_tolerance_ns": 1}}
        for data in (self.base, self.candidate, self.reference):
            data["BC_test"] = copy.deepcopy(data["BC"])

    def test_scan_hold_penalty_uses_hold_weights_of_all_scenarios(self):
        self.scan_fixture()
        self.assertEqual(self.result()["score"], 0)
        # BC: (3-1)/2 + (2-1)/2 = 1.5; BC_test: (5-1)/2 + 0 = 2; hold weights 0.5 each.
        self.candidate["BC"].update(hold_tns_ns=-3, hold_wns_ns=-2)
        self.candidate["BC_test"].update(hold_tns_ns=-5, hold_wns_ns=-1)
        result = self.result()
        self.assertAlmostEqual(result["components"]["hold_penalty"], 1.75)
        self.assertAlmostEqual(result["score"], -1.75)
        self.assertEqual(set(result["scenarios"]), {"BC", "BC_test"})
        self.assertEqual(result["scenarios"]["BC_test"]["mode"], "scan test")

    def test_scan_test_scene_with_zero_weight_scores_hold_only(self):
        self.scan_fixture(weight=0)
        self.candidate["BC_test"].update(
            setup_tns_ns=-500, setup_wns_ns=-50, dynamic_power_w=99, leakage_power_w=99,
            slew_violation_sum_ps=99, cap_violation_sum_ff=99, fanout_violation_sum=99)
        self.assertEqual(self.result()["score"], 0)

    def test_scan_test_scene_setup_and_erc_use_its_weight_but_power_is_functional_only(self):
        self.scan_fixture(weight=0.5)
        # Setup TNS: (-51 + 101) / |-101 + 1| = 0.5, weight 0.5 -> 0.25; scenario weight 0.5 -> 0.125.
        # Slew: (19 - 9) / (9 + 1) = 1, weight 0.1 -> 0.1; scenario weight 0.5 -> 0.05.
        # Dynamic power 10 -> 5 would add 0.05 * 0.5 * 0.5 if power were scored in scan test mode.
        self.candidate["BC_test"].update(setup_tns_ns=-51, slew_violation_sum_ps=19, dynamic_power_w=5)
        result = self.result()
        self.assertAlmostEqual(result["components"]["ppa"], 0.125)
        self.assertAlmostEqual(result["components"]["erc_penalty"], 0.05)
        self.assertAlmostEqual(result["score"], 0.075)
        self.assertEqual(result["scenarios"]["BC_test"]["weighted_terms"]["dynamic_power"], 0)
        self.candidate["BC"]["dynamic_power_w"] = 5
        self.assertAlmostEqual(self.result()["components"]["ppa"], 0.125 + 0.5 * 0.05 * 0.5)

    def test_config_with_scan_scenarios_scores_functional_testcase(self):
        self.config["scan_scenarios"] = {
            "BC": {"mode": "functional", "weight": 1, "hold_weight": 1,
                   "hold_tns_tolerance_ns": 1, "hold_wns_tolerance_ns": 1},
            "BC_test": {"mode": "scan test", "weight": 0, "hold_weight": 0,
                        "hold_tns_tolerance_ns": 1, "hold_wns_tolerance_ns": 1}}
        self.assertEqual(self.result()["score"], 0)
        self.assertEqual(set(self.result()["scenarios"]), {"BC"})

    def test_scan_scene_sets_must_match(self):
        self.scan_fixture()
        del self.candidate["BC_test"]
        with self.assertRaisesRegex(ValueError, "identical scenario sets"):
            self.result()
        self.candidate["BC_test"] = copy.deepcopy(self.candidate["BC"])
        del self.config["scan_scenarios"]
        with self.assertRaisesRegex(ValueError, "identical scenario sets"):
            self.result()

    def test_scenario_block_validation(self):
        self.config["scenarios"]["BC"]["mode"] = "shift"
        with self.assertRaisesRegex(ValueError, "mode must be"):
            self.result()
        self.config["scenarios"]["BC"]["mode"] = "scan test"
        with self.assertRaisesRegex(ValueError, "functional scenario"):
            self.result()
        self.config["scenarios"]["BC"]["mode"] = "functional"
        for key in ("weight", "hold_weight"):
            with self.subTest(key=key):
                self.config["scenarios"]["BC"][key] = 0.5
                with self.assertRaisesRegex(ValueError, f"{key} must sum to one"):
                    self.result()
                self.config["scenarios"]["BC"][key] = 1

    def test_nonfinite_config_and_unknown_fields(self):
        self.config["epsilon"]["time_ns"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            self.result()
        self.config["epsilon"]["time_ns"] = 1
        self.config["typo"] = 1
        with self.assertRaisesRegex(ValueError, "expected keys"):
            self.result()

    def write_csv(self, path, data, design="aes"):
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=("design", "scenario", "corner") + score.TIMING + score.NONNEGATIVE)
            writer.writeheader()
            for corner, row in data.items():
                writer.writerow(dict(row, design=design, scenario="aes_test", corner=corner))

    def test_cli_number_json_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            args = [sys.executable, "-B", str(ROOT / "score.py"), "--allow-unverified"]
            for key, data in (("baseline", self.base), ("candidate", self.candidate), ("reference", self.reference)):
                path = folder / (key + ".csv")
                self.write_csv(path, data)
                args += ["--" + key, str(path)]
            for key, data in (("config", self.config), ("runtimes", self.times)):
                path = folder / (key + ".json")
                path.write_text(json.dumps(data))
                args += ["--" + key, str(path)]
            output = folder / "score.json"
            args += ["--output", str(output)]
            result = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "0")
            report = json.loads(output.read_text())
            self.assertEqual(report["design"], "aes")
            self.assertEqual(report["status"], "provisional")
            self.assertEqual(report["eligibility"], "unverified_dummy")
            before = output.read_bytes()
            rerun = subprocess.run(args, capture_output=True, text=True)
            self.assertNotEqual(rerun.returncode, 0)
            self.assertEqual(rerun.stdout, "")
            self.assertEqual(output.read_bytes(), before)
            self.write_csv(folder / "candidate.csv", self.candidate, design="jpeg")
            mismatch = subprocess.run(args[:-2], capture_output=True, text=True)
            self.assertNotEqual(mismatch.returncode, 0)
            self.assertIn("IDs must match", mismatch.stderr)

    def test_csv_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "summary.csv"
            for value in (float("nan"), float("inf"), 1):
                with self.subTest(value=value):
                    self.candidate["BC"]["setup_tns_ns"] = value
                    self.write_csv(path, self.candidate)
                    with self.assertRaises(ValueError):
                        score.read_summary(path)
            self.write_csv(path, self.base)
            path.write_text(path.read_text() + path.read_text().splitlines()[-1] + "\n")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                score.read_summary(path)

    def test_inconsistent_physical_metric_rejected(self):
        for data in (self.base, self.candidate, self.reference):
            data["TC"] = copy.deepcopy(data["BC"])
        self.config["scenarios"]["BC"].update(weight=.5, hold_weight=.5)
        self.config["scenarios"]["TC"] = copy.deepcopy(self.config["scenarios"]["BC"])
        self.candidate["TC"]["average_displacement_um"] = 42
        with self.assertRaisesRegex(ValueError, "identical across corners"):
            self.result()


class PackagedConfigTests(unittest.TestCase):
    def test_released_scoring_config_is_valid(self):
        config = json.loads((ROOT / "config/scoring_config.json").read_text())
        score.validate_config(config)
        self.assertEqual(set(config["scenarios"]), {"BC", "TC", "WC"})
        self.assertEqual(set(config["scan_scenarios"]), {"BC", "TC", "WC", "BC_test", "TC_test", "WC_test"})
        for scene, values in config["scan_scenarios"].items():
            self.assertEqual(values["mode"], "scan test" if scene.endswith("_test") else "functional")


if __name__ == "__main__":
    unittest.main()
