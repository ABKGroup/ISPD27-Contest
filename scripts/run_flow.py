#!/usr/bin/env python3
"""Two-step entry points around ORFS generation and the validated evaluator."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / 'evaluation/difficulty_v2'
EVAL = EXP / 'scripts'
DEFAULTS = {
    'aes': dict(top='aes_cipher_top', util=50, period=620, density=.65, scenario='aes_p55_h55'),
    'jpeg': dict(top='jpeg_encoder', util=65, period=1100, density=.75, scenario='jpeg_p70_h35'),
}


def path(value):
    return Path(value).expanduser().resolve()


def require_file(value):
    p = path(value)
    if not p.is_file():
        raise ValueError(f'Missing file: {p}')
    return p


def save(p, data):
    with p.open('x') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')


def read(p):
    return json.loads(p.read_text())


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def run(command, logfile, env=None, cwd=None):
    print(f'Running; log: {logfile}', flush=True)
    with logfile.open('x') as log:
        result = subprocess.run([str(x) for x in command], env=env, cwd=cwd,
                                stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'Exit {result.returncode}; inspect {logfile}')


def setting(name, default=None):
    value = os.environ.get(name, default)
    if value is None or value == '':
        raise ValueError(f'Set {name} for this design.')
    return str(value)


def positive(name, default, upper=None):
    value = float(setting(name, default))
    if not value > 0 or (upper is not None and value > upper):
        raise ValueError(f'Invalid {name}: {value}')
    return value


def number(value):
    return f'{value:g}'


def common(args):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.design):
        raise ValueError('Design label must contain only letters, digits, underscore or hyphen.')
    default = DEFAULTS.get(args.design, {})
    top = setting('DESIGN_NAME', default.get('top'))
    cores = int(setting('NUM_CORES', 8))
    if cores < 1:
        raise ValueError('NUM_CORES must be positive.')
    work = path(args.run_dir or Path.cwd()/('mcmm_'+args.design))
    platform = path(os.environ.get('PLATFORM_DIR', ROOT/'platform/asap7'))
    require_file(platform/'manifest.json')
    return default, top, cores, work, platform


def generate(args):
    default, top, cores, work, platform = common(args)
    if args.scenarios:
        raise ValueError('Scenario arguments belong to step 2.')
    orfs = path(os.environ.get('ORFS', ROOT.parent/'OpenROAD-flow-scripts'))
    design_config = require_file(os.environ.get('DESIGN_CONFIG', orfs/f'flow/designs/asap7/{args.design}/config.mk'))
    source = require_file(os.environ.get('SOURCE_NETLIST', ROOT/f'generation/benchmarks/{args.design}/source_synth.v'))
    sdc = require_file(os.environ.get('GEN_SDC', ROOT/f'generation/benchmarks/{args.design}/constraint.sdc'))
    util = positive('UTIL', default.get('util'), 100)
    density = positive('PLACE_DENSITY', default.get('density'), 1)
    period = os.environ.get('CLOCK_PERIOD_PS', None if 'GEN_SDC' in os.environ else default.get('period'))
    sdc_text = sdc.read_text()
    if period is not None:
        period = float(period)
        if not period > 0:
            raise ValueError('CLOCK_PERIOD_PS must be positive.')
        sdc_text, count = re.subn(r'^set clk_period\s+\S+\s*$',
                                'set clk_period '+number(period), sdc_text, flags=re.M)
        if count != 1:
            raise ValueError('Period override requires exactly one "set clk_period VALUE" line in GEN_SDC.')
    else:
        match = re.search(r'^set clk_period\s+([0-9.eE+-]+)\s*$', sdc_text, re.M)
        if match:
            period = float(match[1])
    out = work/'generation'
    if out.exists():
        raise ValueError(f'Refusing to overwrite {out}; choose a fresh RUN_DIR.')
    # ORFS Makefiles do not support whitespace in WORK_HOME/input paths.
    for p in [work, source, sdc, design_config, orfs, ROOT]:
        if any(c.isspace() for c in str(p)):
            raise ValueError(f'ORFS requires a path without whitespace: {p}')
    out.mkdir(parents=True)
    bench = out/'benchmark'
    bench.mkdir()
    shutil.copy2(source, bench/'source_synth.v')
    (bench/'constraint.sdc').write_text(sdc_text)
    shutil.copy2(design_config, out/'design_config.snapshot.mk')
    variant = 'post_cts'
    result = out/f'results/asap7/{args.design}/{variant}'
    command = ['make', '-C', orfs/'flow', 'cts', f'FLOW_HOME={orfs}/flow',
               f'DESIGN_CONFIG={design_config}', f'DESIGN_NAME={top}',
               f'DESIGN_NICKNAME={args.design}', f'WORK_HOME={out}', f'FLOW_VARIANT={variant}',
               f'PLATFORM_DIR={orfs}/flow/platforms/asap7', f'SDC_FILE={bench}/constraint.sdc',
               f'CORE_UTILIZATION={number(util)}', f'PLACE_DENSITY={number(density)}',
               'CORNER=TC', 'ASAP7_USE_VT=RVT LVT SLVT', 'SYNTH_USE_SYN=0',
               f'SYNTH_NETLIST_FILES={bench}/source_synth.v', 'SKIP_CTS_REPAIR_TIMING=1',
               'CTS_SNAPSHOTS=1', f'POST_CTS_TCL={ROOT}/generation/export.tcl', f'NUM_CORES={cores}']
    config = dict(design=args.design, design_name=top, utilization_percent=util,
                  generation_period_ps=period, placement_density=density,
                  generation_corner='TC', source_netlist=str(source), source_sdc=str(sdc),
                  input_sha256={'source_synth.v':sha(source), 'constraint.sdc':sha(bench/'constraint.sdc')},
                  orfs=str(orfs), design_config=str(design_config), command=[str(x) for x in command],
                  created_utc=datetime.now(timezone.utc).isoformat())
    save(out/'generation_config.json', config)
    run(command, out/'generation.log')
    for original, target in [('post_cts.def','input.def'), ('post_cts.v','input.v'),
                             ('4_cts.odb','input.odb'), ('4_cts.sdc','orfs_generated.sdc')]:
        require_file(result/original)
        shutil.copy2(result/original, bench/target)
    for stage in ['2_floorplan.odb', '3_place.odb', '4_cts.odb']:
        require_file(result/stage)
    env = os.environ.copy()
    env.update(OUTPUT_DIR=str(bench), BENCHMARK=args.design, BENCHMARK_DIR=str(bench), PLATFORM_DIR=str(platform))
    run([sys.executable, EVAL/'audit.py', 'generation'], out/'generation_formal.log', env)
    save(bench/'sha256.json', {p.name:sha(p) for p in bench.iterdir() if p.suffix in ['.v','.def','.odb','.sdc']})
    save(out/'manifest.json', dict(config, input_def=str(bench/'input.def'), input_verilog=str(bench/'input.v'),
                                 input_odb=str(bench/'input.odb'), results_dir=str(result)))
    (out/'SUCCESS').write_text('ORFS floorplan, placement, CTS, legalization and generation formal checks passed.\n')
    print(f'Post-CTS ready: {bench}\nAll ORFS results/logs/reports/objects: {out}', flush=True)


def evaluate(args):
    default, top, cores, work, platform = common(args)
    mode = os.environ.get('RESIZER', 'both')
    if mode not in ['off','on','both']:
        raise ValueError('RESIZER must be off, on, or both.')
    kinds = ['off','both'] if mode == 'both' else ['off' if mode == 'off' else 'both']
    explicit = ['INPUT_DEF' in os.environ, 'INPUT_VERILOG' in os.environ]
    generated = work/'generation/manifest.json'
    generation = None
    if any(explicit):
        if not all(explicit):
            raise ValueError('Set INPUT_DEF and INPUT_VERILOG together.')
        input_def, input_v = require_file(os.environ['INPUT_DEF']), require_file(os.environ['INPUT_VERILOG'])
    elif generated.exists():
        require_file(work/'generation/SUCCESS')
        generation = read(generated)
        if generation['design'] != args.design or generation['design_name'] != top:
            raise ValueError('Step 1 design does not match step 2.')
        input_def, input_v = require_file(generation['input_def']), require_file(generation['input_verilog'])
    elif (work/'generation').exists():
        raise ValueError('Step 1 is incomplete; refusing to silently use a different benchmark.')
    else:
        bench = ROOT/f'generation/benchmarks/{args.design}'
        input_def, input_v = require_file(bench/'input.def'), require_file(bench/'input.v')
        if args.design in DEFAULTS:
            generation = dict(utilization_percent=default['util'], generation_period_ps=default['period'])
    tokens = args.scenarios or [os.environ.get('SCENARIO_DIR', default.get('scenario', ''))]
    if tokens == ['all']:
        tokens = [c['id'] for c in read(EXP/'trials.json') if c['design'] == args.design]
    scenarios = []
    for token in tokens:
        if not token:
            raise ValueError('Supply a scenario directory for this design.')
        scene = path(token) if Path(token).expanduser().is_dir() else EXP/'scenarios'/token
        for corner in ['BC','TC','WC']:
            require_file(scene/(corner+'.sdc'))
        cfg = read(scene/'config.json') if (scene/'config.json').exists() else {}
        if cfg.get('design', args.design) != args.design:
            raise ValueError(f'Scenario {scene} belongs to another design.')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', scene.name):
            raise ValueError(f'Use a simple directory name for the scenario: {scene}')
        scenarios.append((scene.resolve(), cfg))
    if not scenarios or len({s.name for s,c in scenarios}) != len(scenarios):
        raise ValueError('Scenario selection is empty or contains duplicate names.')
    out = work/'evaluation'
    if out.exists():
        raise ValueError(f'Refusing to overwrite {out}; choose a fresh RUN_DIR.')
    out.mkdir(parents=True)
    save(out/'request.json', dict(design=args.design, design_name=top, input_def=str(input_def),
         input_verilog=str(input_v), input_sha256={'def':sha(input_def),'verilog':sha(input_v)},
         resizer=mode, scenarios=[str(s) for s,c in scenarios], evaluator=str(EVAL),
         created_utc=datetime.now(timezone.utc).isoformat()))
    summary = []
    for scene, original_cfg in scenarios:
        trial = out/scene.name
        trial.mkdir()
        copied = trial/'scenario'
        shutil.copytree(scene, copied)
        cfg = dict(original_cfg)
        for key in ['source_case','baseline_dir','utilization_percent','generation_period_ps']:
            cfg.pop(key, None)
        if generation:
            for key in ['utilization_percent','generation_period_ps']:
                cfg[key] = generation.get(key)
        cfg.update(id=scene.name, design=args.design, scenario_dir=str(copied),
                   source_scenario_dir=str(scene), input_def=str(input_def), input_verilog=str(input_v),
                   platform_dir=str(platform))
        # These are descriptive fields only; the copied SDCs drive STA.
        periods = {}
        uncertainties = {'setup':{}, 'hold':{}}
        for corner in ['BC','TC','WC']:
            text = (copied/(corner+'.sdc')).read_text()
            match = re.search(r'^set clk_period\s+([0-9.eE+-]+)\s*$', text, re.M)
            if match:
                periods[corner] = float(match[1])
            for check in uncertainties:
                match = re.search(r'^set_clock_uncertainty -'+check+r'\s+([0-9.eE+-]+)\s+\[all_clocks\]\s*$', text, re.M)
                if match:
                    uncertainties[check][corner] = float(match[1])
        cfg.pop('periods_ps', None)
        if len(periods) == 3:
            cfg['periods_ps'] = periods
        for check, values in uncertainties.items():
            cfg.pop(check+'_uncertainty_ps', None)
            if len(values) == 3 and len(set(values.values())) == 1:
                cfg[check+'_uncertainty_ps'] = next(iter(values.values()))
        (copied/'config.json').write_text(json.dumps(cfg, indent=2)+'\n')
        for kind in kinds:
            folder = trial/kind
            env = os.environ.copy()
            env.pop('SPEF_PREFIX', None)
            env.update(BENCHMARK=args.design, DESIGN_NAME=top, INPUT_DEF=str(input_def), INPUT_VERILOG=str(input_v),
                       SCENARIO_DIR=str(copied), SDC_FILE=str(copied/'TC.sdc'), PLATFORM_DIR=str(platform),
                       OUTPUT_DIR=str(folder), RUN_RESIZER='0' if kind=='off' else '1', REPAIR_KIND=kind,
                       PHASE='full', VERIFY_FORMAL='1', NUM_CORES=str(cores), CORNERS='TC BC WC', LIBRARY_CORNERS='TC BC WC')
            run(['bash', EVAL/'eval.sh'], trial/(kind+'.log'), env, copied)
            if not (folder/'SUCCESS').is_file() or not read(folder/'timing_refresh.json')['passed']:
                raise RuntimeError(f'Final timing did not complete: {folder}')
            metrics = read(folder/'metrics.json')
            if not metrics['validation']['input_to_evaluated_equivalence']['passed']:
                raise RuntimeError(f'Equivalence did not pass: {folder}')
            run([sys.executable, EVAL/'check_spef.py', *[folder/f'parasitics_{c}.spef' for c in ['BC','TC','WC']]],
                folder/'spef_validation.json', env)
            with (folder/'clocks.tsv').open() as stream:
                clocks = list(csv.DictReader(stream, delimiter='\t'))
            for corner in ['BC','TC','WC']:
                selected = [c for c in clocks if c['corner']==corner]
                if not selected or any(c['propagated'] != ('0' if c['virtual']=='1' else '1') for c in selected):
                    raise RuntimeError(f'Clock propagation check failed: {folder}, {corner}')
                standard_scene = scene.parent == (EXP/'scenarios').resolve()
                if standard_scene and corner in periods and any(abs(float(c['period_ps'])-periods[corner]) > .001 for c in selected):
                    raise RuntimeError(f'Clock period check failed: {folder}, {corner}')
                row = next(s for s in metrics['scenarios'] if s['corner']==corner)
                summary.append(dict(design=args.design, scenario=scene.name, corner=corner, resizer=int(kind!='off'),
                    setup_wns_ns=row['setup_wns_ps']/1000, setup_tns_ns=row['setup_tns_ps']/1000,
                    hold_wns_ns=row['hold_wns_ps']/1000, hold_tns_ns=row['hold_tns_ps']/1000,
                    output_dir=str(folder)))
    order = {'BC':0,'TC':1,'WC':2}
    summary.sort(key=lambda r:(r['scenario'],order[r['corner']],r['resizer']))
    with (out/'timing_summary.csv').open('x') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    (out/'SUCCESS').write_text('All requested scenarios/branches passed physical evaluation, formal checks and fresh MCMM timing.\n')
    print(f'Post-GRT results: {out}\nTiming summary (ns): {out}/timing_summary.csv', flush=True)


def main():
    step = sys.argv[1]
    if step not in ['generate','evaluate']:
        raise SystemExit('Use 01_generate_post_cts.sh or 02_evaluate_post_grt.sh.')
    parser = argparse.ArgumentParser(prog='01_generate_post_cts.sh' if step=='generate' else '02_evaluate_post_grt.sh',
                                     description=__doc__)
    parser.add_argument('design', nargs='?', default='aes', help='aes, jpeg, or another ASAP7 design label')
    parser.add_argument('run_dir', nargs='?', help='Private workspace shared by steps 1 and 2; default ./mcmm_DESIGN')
    parser.add_argument('scenarios', nargs='*', help='Step 2: scenario IDs, directories, or all; default recommended scenario')
    args = parser.parse_args(sys.argv[2:])
    try:
        (generate if step=='generate' else evaluate)(args)
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        parser.exit(1, f'ERROR: {exc}\n')


if __name__ == '__main__':
    main()
