"""Areas and score associations from supplied final integer nuclear labels."""
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
from inference import sha256


def analyze(rows,data_dir):
    objects=[];fields=[]
    for row in rows:
        path=Path(data_dir)/row['mask_path']
        if sha256(path)!=row['mask_sha256']:raise ValueError('Mask checksum mismatch')
        with np.load(path,allow_pickle=False) as archive:
            if archive.files!=['mask']:raise ValueError('Expected final label array only')
            mask=np.asarray(archive['mask'])
        if mask.ndim!=2 or not np.issubdtype(mask.dtype,np.integer) or (mask<0).any():
            raise ValueError('Invalid final label array')
        ids,counts=np.unique(mask,return_counts=True);positive=ids>0;ids=ids[positive];counts=counts[positive]
        if len(ids)==0:raise ValueError('Empty mask')
        dx=float(row['pixel_size_x_um']);dy=float(row['pixel_size_y_um'])
        if min(dx,dy)<=0 or not np.isfinite([dx,dy]).all():raise ValueError('Invalid pixel spacing')
        areas=counts*dx*dy;border=set(np.r_[mask[0],mask[-1],mask[:,0],mask[:,-1]])-{0}
        for label,count,area in zip(ids,counts,areas):
            objects.append(dict(sample_id=row['sample_id'],passage=int(row['passage']),label=int(label),area_pixels=int(count),area_um2=float(area),touches_border=bool(label in border)))
        area=float(areas.mean());expected=float(row['expected_mean_area_um2'])
        if not np.isclose(area,expected,rtol=0,atol=1e-8):raise ValueError('Area reference mismatch')
        fields.append(dict(sample_id=row['sample_id'],passage=int(row['passage']),score=float(row['score']),n_nuclei=len(ids),mean_nucleus_area_um2=area))
    statistics=[];summary=[]
    for p in [None]+sorted({r['passage'] for r in fields}):
        group=[r for r in fields if p is None or r['passage']==p]
        x=np.array([r['score'] for r in group]);y=np.array([r['mean_nucleus_area_um2'] for r in group])
        rho,pvalue=spearmanr(x,y);slope,intercept=np.polyfit(x,y,1);sem=y.std(ddof=1)/np.sqrt(len(y))
        statistics.append(dict(scope='combined' if p is None else f'P{p}',n=len(group),spearman_rho=float(rho),spearman_p=float(pvalue),ols_slope=float(slope),ols_intercept=float(intercept),mean_area_um2=float(y.mean()),sem_area_um2=float(sem)))
        if p is not None:summary.append(dict(passage=p,n_FOV=len(group),n_nuclei=sum(r['n_nuclei'] for r in group),mean_area_um2=float(y.mean()),sem_area_um2=float(sem)))
    return objects,fields,statistics,summary
