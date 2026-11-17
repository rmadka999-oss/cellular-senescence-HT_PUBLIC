#!/usr/bin/env python3
"""Score supplied AIF examples and reproduce final-mask nuclear associations."""
from pathlib import Path
from urllib.request import urlopen
import argparse,csv,json,re,subprocess,time,zipfile
import numpy as np
import torch
from inference import sha256,load_scorer,score_paths
from nuclear import analyze
ROOT=Path(__file__).resolve().parent


def read_csv(path):
    with Path(path).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))


def write_csv(path,rows):
    with Path(path).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def get_repository():
    try:
        s=subprocess.check_output(['git','remote','get-url','origin'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
        m=re.search(r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$',s)
        return m.group(1) if m else None
    except (OSError,subprocess.CalledProcessError):return None


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--device',default='cpu')
    p.add_argument('--scope',choices=['all','montage','nuclear'],default='all')
    p.add_argument('--assets-dir',type=Path,default=next((d for d in [ROOT.parent/'02_RELEASE_UPLOAD',ROOT.parent/'release_assets'] if d.is_dir()),ROOT.parent/'release_assets'))
    p.add_argument('--workspace',type=Path,default=ROOT/'demo_workspace')
    p.add_argument('--output',type=Path)
    p.add_argument('--repository',help='Public OWNER/REPO if git origin is unavailable')
    p.add_argument('--tag',default='v2.0.0')
    p.add_argument('--threads',type=int,default=8)
    a=p.parse_args();start=time.time();torch.set_num_threads(a.threads)
    if a.device.startswith('cuda'):
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    a.assets_dir.mkdir(parents=True,exist_ok=True);a.workspace.mkdir(parents=True,exist_ok=True)
    for spec in json.loads((ROOT/'config/assets.json').read_text()):
        archive=a.assets_dir/spec['filename']
        if not archive.exists():
            repository=a.repository or get_repository()
            if not repository:raise ValueError('Provide local assets or --repository OWNER/REPO')
            url=f'https://github.com/{repository}/releases/download/{a.tag}/{archive.name}'
            print('Downloading',archive.name,flush=True);temp=archive.with_suffix('.part')
            with urlopen(url) as response,temp.open('wb') as f:
                for block in iter(lambda:response.read(1024*1024),b''):f.write(block)
            temp.replace(archive)
        if sha256(archive)!=spec['sha256']:raise ValueError('Archive checksum mismatch')
        with zipfile.ZipFile(archive) as z:
            for member in z.infolist():
                target=(a.workspace/member.filename).resolve();base=a.workspace.resolve()
                if target!=base and base not in target.parents:raise ValueError('Unsafe archive path')
            z.extractall(a.workspace)
    data=a.workspace/'examples';models=a.workspace/'models';datasets={}
    if a.scope in ['all','montage']:datasets['montage20']=read_csv(data/'montage20.csv')
    if a.scope in ['all','nuclear']:datasets['nuclear168']=read_csv(data/'nuclear168.csv')
    names=sorted({r['path'] for rows in datasets.values() for r in rows});indexes={s:i for i,s in enumerate(names)};scores={}
    for spec in json.loads((ROOT/'config/models.json').read_text()):
        model,weight,bias=load_scorer(models/spec['file'],spec['sha256'],a.device)
        scores[spec['id']]=score_paths([data/n for n in names],model,weight,bias,a.device)
        print('Scored',spec['id'],len(names),'examples',flush=True);del model
        if a.device.startswith('cuda'):torch.cuda.empty_cache()
    output=a.output or a.workspace/('results_'+time.strftime('%Y%m%d_%H%M%S'));output.mkdir(parents=True,exist_ok=False)
    report={};all_passed=True
    for cohort,rows in datasets.items():
        result=[]
        for row in rows:
            selected=row['models'].split(';');ix=indexes[row['path']]
            if any(s not in scores for s in selected):raise ValueError('Unknown example model ID')
            score=float(np.mean([scores[s][ix] for s in selected]));expected=float(row['expected_score'])
            result.append(dict(sample_id=row['sample_id'],passage=int(row['passage']),score=score,expected_score=expected,absolute_error=abs(score-expected),n_models=len(selected)))
        error=max(r['absolute_error'] for r in result);passed=error<=1e-4;all_passed=all_passed and passed
        report[cohort]=dict(n_examples=len(rows),max_absolute_score_error=error,passed=bool(passed))
        write_csv(output/(cohort+'_scores.csv'),result)
        if cohort=='nuclear168':
            inputs=[dict(row,score=r['score']) for row,r in zip(rows,result)];objects,fields,stats,summary=analyze(inputs,data)
            write_csv(output/'nuclear_objects.csv',objects);write_csv(output/'nuclear_FOVs.csv',fields);write_csv(output/'nuclear_correlations.csv',stats);write_csv(output/'nuclear_passage_summary.csv',summary)
            references={r['scope']:r for r in read_csv(data/'expected_correlations.csv')}
            corr=all(np.isclose(r['spearman_rho'],float(references[r['scope']]['spearman_rho']),rtol=0,atol=1e-12) and np.isclose(r['spearman_p'],float(references[r['scope']]['spearman_p']),rtol=1e-10,atol=0) for r in stats)
            area_ref={int(r['passage']):r for r in read_csv(data/'expected_passage_summary.csv')}
            area=all(r['n_FOV']==int(area_ref[r['passage']]['n_FOV']) and np.isclose(r['mean_area_um2'],float(area_ref[r['passage']]['mean_area_um2']),rtol=0,atol=1e-8) and np.isclose(r['sem_area_um2'],float(area_ref[r['passage']]['sem_area_um2']),rtol=0,atol=1e-8) for r in summary)
            passed=bool(corr and area and len(objects)==275 and len(fields)==168);all_passed=all_passed and passed
            report['nuclear_analysis']=dict(n_FOV=len(fields),n_nuclei=len(objects),correlations_and_P_values_match=bool(corr),passage_mean_SEM_match=bool(area),per_FOV_area_references_checked=True,passed=passed)
    report.update(passed=bool(all_passed),device=a.device,seconds=time.time()-start,torch_version=torch.__version__)
    (output/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));print('Output:',output)
    if not all_passed:raise SystemExit('Example verification failed')

if __name__=='__main__':main()
