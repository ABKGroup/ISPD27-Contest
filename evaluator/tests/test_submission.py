"""Exercise process failure, wall-time limits and successful tool execution."""
import os
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_submission import timed_command
import run_submission
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "internal"))
import run


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_command(self, code, timeout=5):
        timed_command([sys.executable, '-c', code], os.environ.copy(), self.root,
                      self.root / 'tool.log', timeout)

    def test_success(self):
        self.run_command("print('completed')")
        self.assertEqual((self.root / 'tool.log').read_text().strip(), 'completed')

    def test_failure(self):
        with self.assertRaisesRegex(RuntimeError, 'status 2'):
            self.run_command('raise SystemExit(2)')

    def test_timeout(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            self.run_command('import time; time.sleep(10)', timeout=0.1)

    def test_exhausted_budget(self):
        with self.assertRaises(TimeoutError):
            self.run_command('pass', timeout=0)

    def exercise_launcher(self, design, top, legacy_names=False):
        package = self.root / 'package with spaces'
        bench = package / 'benchmarks' / design
        bench.mkdir(parents=True)
        (bench / 'benchmark.json').write_text(json.dumps({'top_module': top}))
        reference = package / 'evaluator/reference_results' / design
        reference.mkdir(parents=True)
        (reference / 'runtimes.json').write_text(json.dumps({
            'reference_tool_s': 1, 'reference_flow_s': 2}))
        script = self.root / 'contestant tool.py'
        script.write_text('''import json, os, sys
from pathlib import Path
input_dir, platform_dir, output_dir, top_module = sys.argv[1:]
out = Path(output_dir)
assert list(out.iterdir()) == []
(out / 'arguments.json').write_text(json.dumps(sys.argv[1:]))
assert os.environ['OUTPUT_DEF'] == str(out / (Path(input_dir).name + '.def'))
assert os.environ['OUTPUT_VERILOG'] == str(out / (Path(input_dir).name + '.v'))
name = 'submission' if LEGACY else Path(input_dir).name
(out / (name + '.def')).write_text('test DEF')
(out / (name + '.v')).write_text('test Verilog')
'''.replace('LEGACY', repr(legacy_names)))
        out = self.root / 'output with spaces'
        evaluation_calls = []

        def execute(command, env, cwd, log, timeout):
            if command[1] == str(script):
                timed_command(command, env, cwd, log, timeout)
            else:
                evaluation_calls.append(command)
                (out / 'evaluation').mkdir()

        argv = ['run_submission.py', design, str(out), '--', sys.executable, str(script)]
        with patch.object(run_submission, 'ROOT', package), \
                patch.object(sys, 'argv', argv), \
                patch.object(run_submission.subprocess, 'run'), \
                patch.object(run_submission, 'timed_command', side_effect=execute), \
                patch.object(run_submission, 'finalize'):
            if legacy_names:
                with self.assertRaises(SystemExit):
                    run_submission.main()
                self.assertFalse(evaluation_calls)
                self.assertFalse((out / 'SUBMISSION_COMPLETE').exists())
                self.assertIn(f'{design}.def', (out / 'submission_failure.json').read_text())
                return
            run_submission.main()
        self.assertEqual(json.loads((out / 'tool/arguments.json').read_text()),
                         [str(bench), str(package / 'platform/asap7'), str(out / 'tool'), top])
        self.assertEqual(evaluation_calls[0][-4:],
                         ['--def', str(out / 'tool' / f'{design}.def'),
                          '--verilog', str(out / 'tool' / f'{design}.v')])
        self.assertTrue((out / 'SUBMISSION_COMPLETE').is_file())

    def test_aes_positional_interface(self):
        self.exercise_launcher('aes', 'aes_cipher_top')

    def test_jpeg_positional_interface(self):
        self.exercise_launcher('jpeg', 'jpeg_encoder')

    def test_legacy_output_names_rejected(self):
        self.exercise_launcher('aes', 'aes_cipher_top', legacy_names=True)

    def test_pinned_openroad_revision(self):
        (self.root / 'evaluator/config').mkdir(parents=True)
        expected = '8443f6ff398e3c4e06cb65a05a0abf22734ad345'
        (self.root / 'evaluator/config/tool_versions.json').write_text(json.dumps({'openroad_commit': expected}))
        with patch.object(run, 'ROOT', self.root):
            with patch.object(run.subprocess, 'check_output', return_value='26Q3-123-g8443f6ff39\n'):
                run.check_openroad_version('/test/openroad', {})
            for version in ('26Q3-123-g90e29809c3', '26Q3-123-g8443f6ff39-dirty', 'unknown'):
                with self.subTest(version=version), patch.object(run.subprocess, 'check_output', return_value=version):
                    with self.assertRaisesRegex(ValueError, 'Expected clean OpenROAD'):
                        run.check_openroad_version('/test/openroad', {})


if __name__ == '__main__':
    unittest.main()
