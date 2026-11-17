"""Local file utilities; no network access or bundled research materials."""
import csv
import hashlib
import json
from pathlib import Path


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def read_manifest(path):
    with Path(path).open(newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    if not rows or any(not r.get('sample_id') for r in rows):raise ValueError('Nonempty sample_id is required')
    if len({r['sample_id'] for r in rows})!=len(rows):raise ValueError('sample_id must be unique')
    return rows


def write_csv(path,rows):
    with Path(path).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def write_json(path,value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False))
