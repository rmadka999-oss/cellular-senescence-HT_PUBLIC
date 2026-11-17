#!/usr/bin/env python3
"""Analyze separately supplied final masks paired with field scores."""
import argparse
from pathlib import Path
from common import read_manifest,write_csv,write_json
from nuclear import analyze


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True,help='Local CSV containing final-mask paths, spacing and field scores')
    p.add_argument('--data-dir',type=Path,required=True,help='Root directory for separately supplied final masks')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if not args.manifest.is_file() or not args.data_dir.is_dir():p.error('Required local materials are unavailable')
    if args.output.exists():p.error('Output directory already exists; choose a new path')
    rows=read_manifest(args.manifest);objects,fields,stats,summary=analyze(rows,args.data_dir)
    args.output.mkdir(parents=True)
    for name,data in [('nuclear_objects.csv',objects),('nuclear_FOVs.csv',fields),('correlations.csv',stats),('passage_summary.csv',summary)]:write_csv(args.output/name,data)
    write_json(args.output/'analysis.json',dict(n_FOV=len(fields),n_nuclei=len(objects),area_rule='all supplied positive labels; retain border-touching labels; average areas within each field',scores='local manifest input',association='two-sided Spearman; nominal P values',regression='OLS descriptive only'))
    print('Saved',len(fields),'fields and',len(objects),'nuclei')

if __name__=='__main__':main()
