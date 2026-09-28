#!/usr/bin/env python3
"""Record inputs and validate dedicated evaluator outputs; never parse QoR from the console."""
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

out = Path(os.environ['OUTPUT_DIR'])
platform = Path(os.environ['PLATFORM_DIR'])
def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def canonical(path):
    text = Path(path).read_text()
    text = re.sub(r'//[^\n]*|/\*.*?\*/', '', text, flags=re.S)
    # Only compare OpenROAD's own canonical flat exports, not arbitrary RTL.
    return sorted(tuple(re.findall(r'\\\S+|[A-Za-z_$][\w$]*|\d+\x27[bsdhBSHD][\da-fA-FxXzZ_]+|\d+|[^\s]', s))
                  for s in text.split(';') if s.strip())

def formal(name, first, second):
    manifest = json.loads((platform / 'manifest.json').read_text())
    config = dict(format='verilog', input_paths=[str(Path(first).resolve()), str(Path(second).resolve())],
        liberty_files=[str(platform / p) for p in manifest['corners']['TC']['libraries']],
        log_file=str(out / (name + '.proof.log')))
    cfg = out / (name + '.yml')
    cfg.write_text(json.dumps(config, indent=2)+'\n')
    started = time.monotonic()
    with (out / (name + '.stdout.log')).open('w') as f:
        result = subprocess.run([os.environ['KEPLER_FORMAL_EXE'], '--config', str(cfg)],
            cwd=out, stdout=f, stderr=subprocess.STDOUT, timeout=1800)
    proof = Path(config['log_file']).read_text() if Path(config['log_file']).exists() else ''
    output = (out / (name + '.stdout.log')).read_text()
    if result.returncode or 'Found difference' in proof or 'Circuits are IDENTICAL' not in proof or 'No difference was found.' not in output:
        raise RuntimeError(f'{name} did not prove equivalence; inspect {out}')
    return {'passed': True, 'seconds': time.monotonic()-started}

if sys.argv[1] == 'config':
    keys = ['BENCHMARK','DESIGN_NAME','INPUT_DEF','INPUT_VERILOG','SDC_FILE','PLATFORM_DIR',
            'BASELINE_DEF','BASELINE_VERILOG','MCMM_CONFIG','RUN_RESIZER','CORNERS','LIBRARY_CORNERS','NUM_CORES','SIGNAL_LAYERS','CLOCK_LAYERS','ROUTE_ADJUSTMENT',
            'ROUTE_ITERATIONS','ROUTE_SEED','RSZ_MAX_ITERATIONS','RSZ_TNS_PERCENT','RSZ_SETUP_SEQUENCE','PHASE',
            'OPENROAD_EXE','KEPLER_FORMAL_EXE','VERIFY_FORMAL','SCENARIO_DIR','REPAIR_KIND']
    data = {k: os.environ[k] for k in keys}
    data['sha256'] = {k:digest(data[k]) for k in ['INPUT_DEF','INPUT_VERILOG','SDC_FILE','BASELINE_DEF','BASELINE_VERILOG','MCMM_CONFIG']}
    data['scenario'] = json.loads((Path(data['SCENARIO_DIR'])/'config.json').read_text())
    data['scenario_sdc_sha256'] = {c:digest(Path(data['SCENARIO_DIR'])/(c+'.sdc')) for c in ['BC','TC','WC']}
    data['platform_manifest_sha256'] = digest(platform/'manifest.json')
    data['openroad_sha256'] = digest(data['OPENROAD_EXE'])
    data['script_sha256'] = {p.name:digest(p) for p in Path(__file__).parent.glob('*') if p.suffix in ['.tcl','.sh','.py']}
    if os.environ.get('SPEF_PREFIX'):
        data['spef_sha256']={c:digest(os.environ['SPEF_PREFIX']+'_'+c+'.spef') for c in data['CORNERS'].split()}
    (out/'run_config.json').write_text(json.dumps(data,indent=2)+'\n')
elif sys.argv[1] == 'generation':
    root = Path(__file__).resolve().parent
    bench = Path(os.environ.get('BENCHMARK_DIR', root/'benchmarks'/os.environ['BENCHMARK']))
    result = formal('generation_equivalence', bench/'source_synth.v', bench/'input.v')
    (out/'generation_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: mapped netlist to post-CTS equivalence:',bench)
elif sys.argv[1] == 'input':
    if canonical(out/'verilog_source.v') != canonical(out/'loaded.v'):
        raise RuntimeError('DEF and Verilog canonical exports differ; inspect verilog_source.v and loaded.v')
    if os.environ['PHASE'] == 'full':
        if (out/'baseline_clock.txt').read_text() != (out/'clock_before.txt').read_text():
            raise RuntimeError('Submitted clock nets, clock cells, or clock sink placement differ from official R0')
        baseline={r['instance']:r for r in csv.DictReader((out/'baseline_placement.tsv').open(),delimiter='\t')}
        # placement_before.tsv is exported immediately before this audit.
        current={r['instance']:r for r in csv.DictReader((out/'placement_before.tsv').open(),delimiter='\t')}
        for name, row in baseline.items():
            if row['status'] in ['FIRM', 'LOCKED'] and current.get(name) != row:
                raise RuntimeError('Protected instance changed: '+name)
        proof=formal('submission_equivalence', os.environ['BASELINE_VERILOG'], out/'loaded.v')
        (out/'submission_validation.json').write_text(json.dumps(dict(
            r0_to_submission_equivalence=proof, clock_and_sink_integrity=True,
            protected_instance_integrity=True, complete_contest_legality=False),indent=2)+'\n')
    print('Input Verilog and DEF connectivity match exactly.')
elif sys.argv[1] == 'finish':
    if 'EVALUATION_OPENROAD_SUCCESS' not in (out/'evaluation.log').read_text():
        raise RuntimeError('OpenROAD did not complete')
    same = canonical(out/'verilog_source.v') == canonical(out/'loaded.v')
    audit = {'input_def_verilog_structurally_identical': same}
    if (out/'submission_validation.json').exists():
        audit['submission'] = json.loads((out/'submission_validation.json').read_text())
    if not same:
        raise RuntimeError('DEF and Verilog canonical exports differ; review verilog_source.v and loaded.v')
    if os.environ['PHASE'] == 'full' and os.environ['VERIFY_FORMAL'] == '1':
        audit['input_to_evaluated_equivalence'] = formal('equivalence', out/'loaded.v', out/'evaluated.v')
    timing = list(csv.DictReader((out/'timing.csv').open()))
    for row in timing:
        scene = row['corner']
        for key in list(row):
            if key.endswith('_ps'):
                row[key]=float(row[key])
            elif key.endswith('_endpoints'):
                row[key]=int(row[key])
        row['setup_wns_ps']=min(0.0,row['setup_worst_slack_ps'])
        row['hold_wns_ps']=min(0.0,row['hold_worst_slack_ps'])
        power = json.loads((out/(scene+'_power.json')).read_text())
        row['power'] = power
        erc = {}
        for kind in ['max_slew','max_capacitance','max_fanout']:
            report = (out/f'{scene}_{kind}.rpt').read_text()
            violations = []
            for line in report.splitlines():
                if '(VIOLATED)' in line:
                    match = re.search(r'([-+\d.eE]+)\s+\(VIOLATED\)',line)
                    if not match:
                        raise RuntimeError('Unrecognized dedicated ERC report line: '+line)
                    violations.append(float(match[1]))
            erc[kind] = {'count':len(violations), 'sum_violation':sum(-v for v in violations)}
        row['erc'] = erc
    before = {r['instance']:r for r in csv.DictReader((out/'placement_before.tsv').open(),delimiter='\t')}
    after_path=out/'placement_after.tsv'
    if after_path.exists() and os.environ['PHASE']=='full':
        after={r['instance']:r for r in csv.DictReader(after_path.open(),delimiter='\t')}
        common=before.keys() & after.keys()
        audit['instances_before']=len(before); audit['instances_after']=len(after)
        audit['new_instances']=len(after.keys()-before.keys())
        audit['removed_instances']=len(before.keys()-after.keys())
        audit['resized_instances']=sum(before[k]['master']!=after[k]['master'] for k in common)
        disps=[abs(int(before[k]['x_dbu'])-int(after[k]['x_dbu']))+abs(int(before[k]['y_dbu'])-int(after[k]['y_dbu'])) for k in common]
        audit['displacement_dbu']={'max':max(disps,default=0),'sum':sum(disps)}
    data = {'validation':audit,'scenarios':timing,
            'runtime':list(csv.DictReader((out/'runtime.csv').open())),
            'units':{'time':'ps','capacitance':'fF','power':'W','displacement':'database units'},
            'hold_coverage':'Experimental corner-dependent periods and uncertainty; inherited JPEG interface hold coverage remains incomplete.'}
    (out/'metrics.json').write_text(json.dumps(data,indent=2)+'\n')
    (out/'SUCCESS').write_text('OpenROAD completed; input consistency and requested formal checks passed.\n')
    print('PASS: evaluation and validation:',out)
else:
    raise SystemExit('Usage: audit.py config|finish')
