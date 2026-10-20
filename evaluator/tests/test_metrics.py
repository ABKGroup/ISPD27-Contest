"""Regression for ERC reports produced by the pinned OpenSTA revision."""
from pathlib import Path
import sys
import csv
import json
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from internal.metrics import parse_erc_violations, movable_displacement

class ErcTests(unittest.TestCase):
    def test_real_jpeg_blank_fanout_slack(self):
        line = 'qnr.divider.spipe[13]$_DFFE_PP_/QN       10     11        (VIOLATED)'
        self.assertEqual(parse_erc_violations(line, 'max_fanout'),
                         {'count': 1, 'sum_violation': 1.0})

    def test_mixed_fanout_rows(self):
        report = 'ena 10 4589 -4579 (VIOLATED)\nreg/QN 10 11 (VIOLATED)'
        self.assertEqual(parse_erc_violations(report, 'max_fanout'),
                         {'count': 2, 'sum_violation': 4580.0})

    def test_slew_and_capacitance(self):
        for kind in ('max_slew', 'max_capacitance'):
            self.assertEqual(parse_erc_violations('pin/A 1.5 2.75 -1.25 (VIOLATED)', kind),
                             {'count': 1, 'sum_violation': 1.25})
            self.assertEqual(parse_erc_violations('No violations', kind),
                             {'count': 0, 'sum_violation': 0})

    def test_ambiguous_or_positive_slack_rejected(self):
        for kind, line in [('max_slew', 'pin 10 11 (VIOLATED)'),
                           ('max_fanout', 'pin 10 12 (VIOLATED)'),
                           ('max_fanout', 'pin 10 11 11 (VIOLATED)')]:
            with self.subTest(kind=kind, line=line), self.assertRaises(ValueError):
                parse_erc_violations(line, kind)

class DisplacementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.master = 'BUFx2_ASAP7_75t_R'
        self.cells = [dict(instance=name, master=self.master, x='0', y='0',
                           orientation='R0', status=status, macro=macro, physical=physical)
                      for name,status,macro,physical in [
                          ('move','PLACED','0','0'), ('still','PLACED','0','0'),
                          ('removed','PLACED','0','0'), ('clock','PLACED','0','0'),
                          ('sink','PLACED','0','0'), ('fixed','FIRM','0','0'),
                          ('locked','LOCKED','0','0'), ('cover','COVER','0','0'),
                          ('macro','PLACED','1','0'), ('tap','PLACED','0','1')]]
        pins = [dict(instance='clock', pin='Y', direction='OUTPUT', signal='SIGNAL',
                     net='clknet', net_signal='CLOCK'),
                dict(instance='sink', pin='A', direction='INPUT', signal='CLOCK',
                     net='clknet', net_signal='CLOCK')]
        self.write('baseline_structure.cells.tsv',self.cells)
        self.write('baseline_structure.pins.tsv',pins)
        self.write('baseline_structure.library.tsv',[dict(master=self.master,pin='A')])
        self.before = [dict(instance=c['instance'],master=self.master,x_dbu='0',y_dbu='0',
                            orientation='R0',status=c['status']) for c in self.cells]
        self.after = [dict(c, x_dbu='3000', y_dbu='4000') for c in self.before
                      if c['instance'] != 'removed']
        next(c for c in self.after if c['instance']=='still').update(x_dbu='0',y_dbu='0')
        self.after.append(dict(self.after[0],instance='inserted',x_dbu='999999'))
        self.write('baseline_placement.tsv',self.before)
        self.write('placement_after.tsv',self.after)
        (self.root/'geometry.json').write_text(json.dumps({'dbu_per_um':1000}))

    def write(self,name,records):
        with (self.root/name).open('w') as f:
            writer=csv.DictWriter(f,fieldnames=list(records[0]),delimiter='\t')
            writer.writeheader();writer.writerows(records)

    def test_only_surviving_original_movable_cells(self):
        # Protected zero-motion cells must not dilute the denominator. Their
        # fixture positions deliberately move to prove they are excluded.
        self.assertEqual(movable_displacement(self.root),(3.5,2,1,7.0))

    def test_baseline_eligibility_cannot_be_changed_by_candidate_status(self):
        next(c for c in self.after if c['instance']=='move')['status']='FIRM'
        self.write('placement_after.tsv',self.after)
        self.assertEqual(movable_displacement(self.root),(3.5,2,1,7.0))

    def test_no_surviving_movable_cells(self):
        self.after=[c for c in self.after if c['instance'] not in ('move','still')]
        self.write('placement_after.tsv',self.after)
        self.assertEqual(movable_displacement(self.root),(0.0,0,0,0.0))

if __name__ == '__main__':
    unittest.main()
