#!/usr/bin/env python3
"""Report MCMM in a fresh OpenROAD process on the final DEF/Verilog and SPEFs."""
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path,data):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(path)


def refresh(folder):
    folder=folder.resolve()
    cfg=read(folder/'run_config.json')
    assert cfg['PHASE']=='full'
    final=folder/'final_timing'; original=folder/'inprocess_reports'
    inputs=['evaluated.def','evaluated.v']+[f'parasitics_{c}.spef' for c in cfg['CORNERS'].split()]
    fingerprint={p:sha(folder/p) for p in inputs}
    scenario_hashes={c:sha(Path(cfg['SCENARIO_DIR'])/(c+'.sdc')) for c in ['BC','TC','WC']}
    assert scenario_hashes==cfg['scenario_sdc_sha256']
    stamp=folder/'timing_refresh.json'
    if stamp.exists():
        record=read(stamp)
        assert record['input_sha256']==fingerprint
        assert record['refresh_script_sha256']==sha(Path(__file__))
        assert (folder/'SUCCESS').exists()
        return
    assert (folder/'SUCCESS').exists() or (original/'SUCCESS').exists()
    names=['timing.csv','metrics.json','runtime.csv','constraint_coverage.rpt','clocks.tsv','SUCCESS']
    for corner in cfg['CORNERS'].split():
        names += [p.name for p in folder.glob(corner+'_*') if p.is_file() and p.suffix in ['.rpt','.json']]
    original.mkdir(exist_ok=True)
    for name in names:
        if not (original/name).exists() and (folder/name).exists():shutil.copy2(folder/name,original/name)
    (folder/'SUCCESS').unlink(missing_ok=True)
    env=os.environ.copy()
    env.update({k:str(v) for k,v in cfg.items() if isinstance(v,str)})
    env.update(PHASE='timing',VERIFY_FORMAL='0',INPUT_DEF=str(folder/'evaluated.def'),
               INPUT_VERILOG=str(folder/'evaluated.v'),SPEF_PREFIX=str(folder/'parasitics'),OUTPUT_DIR=str(final))
    with (folder/'final_timing.log').open('w') as log:
        subprocess.run(['bash',str(ROOT/'core_run.sh')],env=env,cwd=ROOT.parent.parent,
                       stdout=log,stderr=subprocess.STDOUT,check=True)
    updated=read(final/'metrics.json')
    assert {s['corner'] for s in updated['scenarios']}==set(cfg['CORNERS'].split())
    metrics=read(original/'metrics.json')
    with (original/'runtime.csv').open() as f:
        runtime={r['stage']:float(r['seconds']) for r in csv.DictReader(f)}
    final_runtime={r['stage']:float(r['seconds']) for r in updated['runtime']}
    runtime['final_timing']=final_runtime['total_openroad']
    runtime['total_openroad']+=runtime['final_timing']
    metrics['scenarios']=updated['scenarios']
    metrics['runtime']=[{'stage':k,'seconds':str(v)} for k,v in sorted(runtime.items())]
    metrics['timing_source']='Fresh simultaneous MCMM reload in final_timing/; original reports in inprocess_reports/.'
    for name in names:
        if name not in ['metrics.json','runtime.csv','SUCCESS'] and (final/name).exists():
            shutil.copy2(final/name,folder/name)
    with (folder/'runtime.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=['stage','seconds']);writer.writeheader();writer.writerows(metrics['runtime'])
    write_json(folder/'metrics.json',metrics)
    record=dict(passed=True,input_sha256=fingerprint,refresh_script_sha256=sha(Path(__file__)),
                optimization_config_sha256=sha(folder/'run_config.json'),
                final_timing_config_sha256=sha(final/'run_config.json'),
                inprocess_runtime_s=runtime['total_openroad']-runtime['final_timing'],
                final_timing_runtime_s=runtime['final_timing'],total_openroad_runtime_s=runtime['total_openroad'])
    write_json(stamp,record)
    (folder/'SUCCESS').write_text('Physical evaluation/formal checks passed; final metrics use fresh MCMM SPEF reload.\n')
    print('PASS: fresh final MCMM reporting:',folder,flush=True)


if __name__=='__main__':
    refresh(Path(sys.argv[1]))
