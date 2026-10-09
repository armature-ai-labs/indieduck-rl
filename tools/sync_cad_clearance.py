"""Attach exact CAD pose-check results without implying trained behavior success."""
import argparse
import json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('report',type=Path);p.add_argument('--floor-report',type=Path);a=p.parse_args()
model=Path(__file__).resolve().parents[1]/'src/mjlab_microduck/robot/indieduck'
poses=json.loads((model/'poses.json').read_text());report=json.loads(a.report.read_text());results={r['pose']:r for r in report['poses']}
for pose in poses['poses']:
    row=results.get(pose['id'])
    if row:
        hits=row['hits_over_0p5mm3'];pose['cad_clearance']={'threshold_mm3':report['threshold_mm3'],'status':'interference found' if hits else 'sampled clearance pass','hits':hits}
        pose['status']='Illustrative pose; CAD interference found, mechanical revision required' if hits else 'Illustrative pose; sampled CAD clearance pass, motion and physical fit unverified'
    elif 'cad_clearance' not in pose:
        pose['cad_clearance']={'status':'pending exact CAD check','hits':None}
if a.floor_report:
    floor=json.loads(a.floor_report.read_text())
    for pose in poses['poses']:
        if pose['id'] in floor:
            pose['cad_floor_clearance']={**floor[pose['id']], 'scope':'Exact CAD study pose with walking feet; skate floor contacts checked separately in physics'}
            if floor[pose['id']]['below_floor_parts']:
                pose['status']+='; exact CAD also penetrates floor despite proxy seating'
    (model/'cad-ground-contact-study.json').write_text(json.dumps(floor,indent=2)+'\n')
(model/'poses.json').write_text(json.dumps(poses,indent=2)+'\n')
(model/'cad-pose-clearance.json').write_text(json.dumps(report,indent=2)+'\n')
print({p['id']:p['cad_clearance']['status'] for p in poses['poses']})
