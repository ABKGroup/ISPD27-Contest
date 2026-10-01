"""Policy tests: allowed data transforms, fixed geometry, and rejection paths."""
import copy
import csv
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from internal import legality as L


DEF = '''VERSION 5.8 ;
DESIGN example ;
UNITS DISTANCE MICRONS 1000 ;
DIEAREA ( 0 0 ) ( 1000 1000 ) ;
ROW r site 0 0 N DO 10 BY 1 STEP 10 0 ;
TRACKS X 10 DO 20 STEP 40 LAYER M2 ;
VIAS 1 ;
- v + RECT M1 ( -1 -1 ) ( 1 1 ) ;
END VIAS
COMPONENTS 0 ; END COMPONENTS
PINS 1 ;
- a + NET a + DIRECTION INPUT + PORT + LAYER M2 ( -1 -1 ) ( 1 1 ) + FIXED ( 0 10 ) N ;
END PINS
SPECIALNETS 1 ;
- VDD ( PIN VDD ) + USE POWER + ROUTED M1 10 ( 0 0 ) ( 1000 0 ) ;
END SPECIALNETS
BLOCKAGES 1 ;
- PLACEMENT RECT ( 0 0 ) ( 10 10 ) ;
END BLOCKAGES
NETS 0 ; END NETS
END DESIGN
'''


class PhysicalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.a = Path(self.temp.name) / 'a.def'
        self.b = Path(self.temp.name) / 'b.def'
        self.a.write_text(DEF)
        self.b.write_text(DEF)

    def test_whitespace_and_record_order(self):
        self.b.write_text(DEF.replace(' ;', '\n;').replace('VERSION 5.8 ;', 'VERSION 5.8 ;'))
        L.physical_check(self.a, self.b)

    def test_fixed_structure_mutations(self):
        edits = [
            ('( 1000 1000 )', '( 2000 1000 )', 'DIEAREA'),
            ('STEP 10 0', 'STEP 20 0', 'ROW'),
            ('STEP 40', 'STEP 80', 'TRACKS'),
            ('FIXED ( 0 10 )', 'FIXED ( 0 20 )', 'PINS'),
            ('LAYER M2 ( -1', 'LAYER M1 ( -1', 'PINS'),
            ('ROUTED M1 10', 'ROUTED M1 20', 'SPECIALNETS'),
            ('RECT M1 ( -1', 'RECT M1 ( -2', 'VIAS'),
            ('PLACEMENT RECT ( 0 0 )', 'PLACEMENT RECT ( 1 0 )', 'BLOCKAGES'),
            ('BLOCKAGES 1 ;\n- PLACEMENT RECT ( 0 0 ) ( 10 10 ) ;\nEND BLOCKAGES', '', 'BLOCKAGES'),
        ]
        for old, new, reason in edits:
            with self.subTest(reason=reason):
                self.b.write_text(DEF.replace(old, new))
                with self.assertRaisesRegex(L.Illegal, reason):
                    L.physical_check(self.a, self.b)

    def test_gcellgrid_only_ignored_after_routing(self):
        self.b.write_text(DEF.replace('END DESIGN', 'GCELLGRID X 0 DO 10 STEP 100 ;\nEND DESIGN'))
        with self.assertRaisesRegex(L.Illegal, 'GCELLGRID'):
            L.physical_check(self.a, self.b)
        L.physical_check(self.a, self.b, post_route=True)


def library():
    result = {}
    for master, func, inputs, buffer, inverter in [
        ('AND_X1', 'A*B', ['A','B'], 0, 0), ('AND_X2', 'A*B', ['A','B'], 0, 0),
        ('ASYM_X1', '!A*B', ['A','B'], 0, 0),
        ('BUF_X1', 'A', ['A'], 1, 0), ('INV_X1', '!A', ['A'], 0, 1)]:
        result[master] = {}
        for p in inputs + ['Y']:
            result[master][p] = dict(master=master,pin=p,direction='output' if p=='Y' else 'input',
                function=func if p=='Y' else '',tristate='',buffer=str(buffer),inverter=str(inverter))
    return result


class TransformTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.groups = self.root/'groups.csv'
        self.groups.write_text('AND_X1,AND_X2\nASYM_X1\nBUF_X1\nINV_X1\n')
        self.lib = library()
        self.old = {'g': ('AND_X1', {'A':'a','B':'b','Y':'o'})}
        self.new = copy.deepcopy(self.old)
        self.protected = set()

    def write(self, prefix, cells, protect=()):
        rows=[]; pins=[]
        for name,(master,connections) in cells.items():
            rows.append(dict(instance=name,master=master,x='0',y='0',orientation='R0',
                             status='FIRM' if name in protect else 'PLACED',macro='0',physical='0'))
            for pin,net in connections.items():
                pins.append(dict(instance=name,pin=pin,direction='OUTPUT' if pin=='Y' else 'INPUT',
                                 signal='SIGNAL',net=net,net_signal='SIGNAL'))
        for name,direction in [('a','INPUT'),('b','INPUT'),('o','OUTPUT')]:
            pins.append(dict(instance='',pin=name,direction=direction,signal='SIGNAL',net=name,net_signal='SIGNAL'))
        for suffix,data in [('cells',rows),('pins',pins)]:
            with Path(str(prefix)+'.'+suffix+'.tsv').open('w',newline='') as f:
                fields = ('instance','master','x','y','orientation','status','macro','physical') if suffix=='cells' else ('instance','pin','direction','signal','net','net_signal')
                writer=csv.DictWriter(f,fieldnames=fields,delimiter='\t');writer.writeheader();writer.writerows(data)

    def check(self):
        a,b=self.root/'a',self.root/'b'
        self.write(a,self.old,self.protected);self.write(b,self.new,self.protected)
        return L.transformations(a,b,self.lib,self.groups)

    def test_identity_and_sizing(self):
        self.check()
        self.new['g']=('AND_X2',self.new['g'][1])
        self.assertEqual(self.check()['changed_masters'],1)

    def test_baseline_and_net_renaming_are_not_optimization(self):
        self.check()  # write the two snapshots
        a, b = self.root/'a', self.root/'b'
        for prefix in (a, b):
            Path(str(prefix)+'.def').write_text(DEF)
        libpath = self.root/'library.tsv'
        rows = [row for ports in self.lib.values() for row in ports.values()]
        with libpath.open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t')
            w.writeheader(); w.writerows(rows)
        self.assertFalse(L.check(a,b,libpath,self.groups)['changed_from_baseline'])
        pins = Path(str(b)+'.pins.tsv')
        pins.write_text(pins.read_text().replace('\ta\tSIGNAL', '\trenamed\tSIGNAL'))
        self.assertFalse(L.check(a,b,libpath,self.groups)['changed_from_baseline'])
        cells = Path(str(b)+'.cells.tsv')
        cells.write_text(cells.read_text().replace('AND_X1','AND_X2'))
        self.assertTrue(L.check(a,b,libpath,self.groups)['changed_from_baseline'])

    def test_equivalent_pin_swap(self):
        self.new['g'][1].update(A='b',B='a')
        self.assertEqual(self.check()['pin_swapped_instances'],1)

    def test_nonequivalent_pin_swap_rejected(self):
        self.old['g']=('ASYM_X1',self.old['g'][1]);self.new=copy.deepcopy(self.old)
        self.new['g'][1].update(A='b',B='a')
        with self.assertRaisesRegex(L.Illegal,'Non-equivalent input-pin swap'):
            self.check()

    def test_buffer_insert_remove_and_inverter_pair(self):
        self.new['buf']=('BUF_X1',dict(A='a',Y='n'))
        self.new['g'][1]['A']='n'
        self.assertEqual(self.check()['inserted_data_repeaters'],1)
        self.old,self.new=copy.deepcopy(self.new),copy.deepcopy(self.old)
        self.assertEqual(self.check()['removed_data_repeaters'],1)
        self.old=copy.deepcopy(self.new)
        self.new.update(i1=('INV_X1',dict(A='a',Y='n1')),i2=('INV_X1',dict(A='n1',Y='n2')))
        self.new['g'][1]['A']='n2'
        self.check()

    def test_odd_inversion_rejected(self):
        self.new['inv']=('INV_X1',dict(A='a',Y='n'));self.new['g'][1]['A']='n'
        with self.assertRaisesRegex(L.Illegal,'polarity'):
            self.check()

    def test_insert_logic_and_remove_logic_rejected(self):
        self.new['extra']=('AND_X1',dict(A='a',B='b',Y='extra'))
        with self.assertRaisesRegex(L.Illegal,'Only data repeaters may be inserted'):
            self.check()
        self.new={}
        with self.assertRaisesRegex(L.Illegal,'Only data repeaters may be removed'):
            self.check()

    def test_protected_master(self):
        self.protected={'g'};self.new['g']=('AND_X2',self.new['g'][1])
        with self.assertRaisesRegex(L.Illegal,'Protected instance'):
            self.check()

    def test_protected_data_input_allows_buffering(self):
        self.protected={'g'}
        self.new['buf']=('BUF_X1',dict(A='a',Y='n'));self.new['g'][1]['A']='n'
        self.check()

    def test_cycle_and_multiple_drivers(self):
        self.new['buf']=('BUF_X1',dict(A='n',Y='n'));self.new['g'][1]['A']='n'
        with self.assertRaisesRegex(L.Illegal,'cycle'):
            self.check()
        self.new['buf']=('BUF_X1',dict(A='a',Y='o'))
        with self.assertRaisesRegex(L.Illegal,'Multiple drivers'):
            self.check()

    def test_expression_parser(self):
        self.assertTrue(L.boolean(L.expression("!(A+B)' ^ 1"),dict(A=False,B=False)))
        self.assertFalse(L.boolean(L.expression('A B'),dict(A=True,B=False)))
        with self.assertRaises(L.Illegal):
            L.expression('__import__("os")')


class CertificateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        names = ['summary.csv', 'metrics.json', 'evaluated.def', 'evaluated.v', 'run_config.json',
                 'structural_validation.json', 'final_structural_validation.json',
                 'submission_validation.json', 'evaluation_runtime.json', 'spef_validation.json',
                 'runtime_validation.json']
        for name in names:
            (self.folder / name).write_text('{}')
        self.record = dict(passed=True, design_legality_passed=True, runtime_measured=True,
            files_sha256={n:L.digest(self.folder / n) for n in names})
        self.save()

    def save(self):
        (self.folder / 'legality.json').write_text(json.dumps(self.record))

    def test_valid_and_changed_artifact(self):
        L.verify_certificate(self.folder / 'summary.csv')
        (self.folder / 'evaluated.def').write_text('changed')
        with self.assertRaisesRegex(L.Illegal, 'artifact changed'):
            L.verify_certificate(self.folder / 'summary.csv')

    def test_incomplete_certificate(self):
        del self.record['files_sha256']['metrics.json']; self.save()
        with self.assertRaisesRegex(L.Illegal, 'Incomplete'):
            L.verify_certificate(self.folder / 'summary.csv')

    def test_unmeasured_runtime(self):
        self.record['runtime_measured'] = False; self.save()
        with self.assertRaisesRegex(L.Illegal, 'measure tool runtime'):
            L.verify_certificate(self.folder / 'summary.csv')
        L.verify_certificate(self.folder / 'summary.csv', require_runtime=False)

    def test_failed_check(self):
        self.record['passed'] = False; self.save()
        with self.assertRaisesRegex(L.Illegal, 'not passed'):
            L.verify_certificate(self.folder / 'summary.csv')


class FinalizeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        reports = {
            'structural_validation.json': {'passed': True},
            'final_structural_validation.json': {'passed': True},
            'submission_validation.json': {
                'r0_to_submission_equivalence': {'passed': True},
                'clock_and_sink_integrity': True, 'protected_instance_integrity': True},
            'metrics.json': {'validation': {'input_def_verilog_structurally_identical': True,
                'input_to_evaluated_equivalence': {'passed': True}}},
            'spef_validation.json': [{'nets': 1, 'mismatches': 0}] * 3,
            'run_config.json': {'RUN_RESIZER': '0', 'PHASE': 'full', 'VERIFY_FORMAL': '1',
                'BENCHMARK': 'example', 'scenario': {'id': 'example'}},
            'evaluation_runtime.json': {'evaluation_wall_seconds': 1}}
        for name, content in reports.items():
            (self.folder / name).write_text(json.dumps(content))
        for name in ('summary.csv', 'evaluated.def', 'evaluated.v'):
            (self.folder / name).write_text('fixture')
        (self.folder / 'evaluation.log').write_text('EVALUATION_OPENROAD_SUCCESS')

    def test_complete_legality_after_all_checks_pass(self):
        report = L.finalize(self.folder)
        self.assertIs(report['complete_contest_legality'], True)
        self.assertIs(report['runtime_measured'], False)
        L.verify_certificate(self.folder / 'summary.csv', require_runtime=False)

    def test_failed_post_route_check_cannot_publish_success(self):
        (self.folder / 'final_structural_validation.json').write_text('{"passed": false}')
        with self.assertRaisesRegex(L.Illegal, 'Failed check'):
            L.finalize(self.folder)
        self.assertFalse((self.folder / 'legality.json').exists())


if __name__ == '__main__':
    unittest.main()
