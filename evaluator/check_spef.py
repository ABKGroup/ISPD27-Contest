#!/usr/bin/env python3
"""Check exported wire capacitance against each SPEF *D_NET total."""
import json
from pathlib import Path
import sys

results=[]
for arg in sys.argv[1:]:
    path=Path(arg)
    count=0; mismatches=[]; total=0.; summed=0.; in_cap=False
    for line in path.open():
        fields=line.split()
        if not fields: continue
        if fields[0]=='*D_NET':
            name=fields[1]; declared=float(fields[2]); actual=0.; in_cap=False
        elif fields[0]=='*CAP': in_cap=True
        elif fields[0]=='*END':
            count+=1; total+=declared; summed+=actual
            if abs(declared-actual)>max(1e-5,abs(declared)*2e-5):
                mismatches.append({'net':name,'declared':declared,'sum':actual})
            in_cap=False
        elif fields[0].startswith('*'): in_cap=False
        elif in_cap:
            if len(fields)!=3:
                raise ValueError('This nominal-RC exporter should have only grounded caps: '+line)
            actual+=float(fields[2])
    results.append(dict(file=str(path),nets=count,declared_cap_ff=total,
        exported_cap_ff=summed,mismatches=len(mismatches),examples=mismatches[:5]))
print(json.dumps(results,indent=2))
if not results or any(r['nets']==0 or r['mismatches'] for r in results):
    raise SystemExit(1)
