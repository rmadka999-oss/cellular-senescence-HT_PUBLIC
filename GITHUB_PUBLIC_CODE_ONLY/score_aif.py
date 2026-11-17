#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Scope: this file only; see ../LICENSE and README.md.
"""Score separately supplied model-ready AIF arrays with local fixed artifacts."""
import argparse,json,time
from pathlib import Path
import numpy as np
import torch
from common import read_manifest,write_csv,write_json
from inference import load_scorer,score_paths


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True,help='Local CSV describing authorized inputs')
    p.add_argument('--data-dir',type=Path,required=True,help='Root of the separately supplied AIF files')
    p.add_argument('--model-manifest',type=Path,required=True,help='Local JSON list of model IDs, filenames and SHA256 hashes')
    p.add_argument('--models-dir',type=Path,required=True,help='Local fixed inference artifacts')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--device',default='cpu')
    p.add_argument('--threads',type=int,default=8)
    args=p.parse_args();start=time.time()
    for path in [args.manifest,args.data_dir,args.model_manifest,args.models_dir]:
        if not path.exists():p.error('Required local material not found: '+str(path))
    if args.output.exists():p.error('Output directory already exists; choose a new path')
    rows=read_manifest(args.manifest);specs=json.loads(args.model_manifest.read_text())
    if not specs or len({s['id'] for s in specs})!=len(specs):raise ValueError('Unique model IDs required')
    for row in rows:
        if not row.get('models') or not row.get('path'):raise ValueError('Manifest needs path and models')
    needed=set(s for row in rows for s in row['models'].split(';'))
    if not needed<={s['id'] for s in specs}:raise ValueError('Unknown requested model ID')
    torch.set_num_threads(args.threads)
    if args.device.startswith('cuda'):
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    predictions={};per_model=[]
    for spec in specs:
        if spec['id'] not in needed:continue
        model,w,b=load_scorer(args.models_dir/spec['file'],spec['sha256'],args.device)
        predictions[spec['id']]=score_paths([args.data_dir/r['path'] for r in rows],model,w,b,args.device)
        for i,row in enumerate(rows):
            if spec['id'] in row['models'].split(';'):per_model.append(dict(sample_id=row['sample_id'],model_id=spec['id'],score=float(predictions[spec['id']][i])))
        print('Scored',spec['id'],len(rows),'inputs',flush=True);del model
        if args.device.startswith('cuda'):torch.cuda.empty_cache()
    results=[];scored=[];errors=[]
    for i,row in enumerate(rows):
        selected=row['models'].split(';');score=float(np.mean([predictions[s][i] for s in selected]))
        expected=row.get('expected_score','');error=abs(score-float(expected)) if expected else ''
        if error!='':errors.append(error)
        results.append(dict(sample_id=row['sample_id'],passage=row.get('passage',''),score=score,n_models=len(selected),expected_score=expected,absolute_error=error))
        scored.append(dict(row,score=score))
    args.output.mkdir(parents=True)
    write_csv(args.output/'scores.csv',results);write_csv(args.output/'scores_per_model.csv',per_model);write_csv(args.output/'scored_manifest.csv',scored)
    passed=all(e<=1e-4 for e in errors)
    report=dict(n_inputs=len(rows),n_model_artifacts=len(predictions),reference_scores_checked=len(errors),max_absolute_score_error=max(errors) if errors else None,passed=bool(passed),device=args.device,seconds=time.time()-start)
    write_json(args.output/'verification.json',report);print(json.dumps(report,indent=2))
    if not passed:raise SystemExit('Reference score comparison exceeded tolerance')

if __name__=='__main__':main()
