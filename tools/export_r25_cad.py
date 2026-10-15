"""Export R25 display meshes (standing pose and zero pose) from the single R25 native file.

R25 parts are solids in assembled CAD coordinates with a MovingBody property naming their joint link.
Joint chain, standing pose and root registration are unchanged from R20 (servo and joint locations
were not moved), so the R20 contract, poses and published base position are reused and checked.
Run under FreeCAD with NumPy: INDIEDUCK_CAD=<indieduck-cad> INDIEDUCK_ASSETS=<out> FreeCAD -c tools/export_r25_cad.py
"""
import FreeCAD as A, Part, MeshPart, json, hashlib, csv, os, shutil
from pathlib import Path
import numpy as np

cad = Path(os.environ['INDIEDUCK_CAD']); out = Path(os.environ['INDIEDUCK_ASSETS']); zero = out / 'zero'
model = Path(__file__).resolve().parents[1] / 'src/mjlab_microduck/robot/indieduck'
for p in [out / 'meshes', zero / 'meshes']: p.mkdir(parents=True, exist_ok=True)
c = json.loads((model / 'contract.json').read_text())
poses = json.loads((model / 'poses.json').read_text()); stand = next(p for p in poses['poses'] if p['id'] == 'stand')
r20 = json.loads(Path(os.environ.get('INDIEDUCK_R20_MANIFEST', str(cad / 'assembly/manifest.json'))).read_text())
assert r20['revision'] == 'R20', 'expected the R20 display manifest as the registration reference'
stand['base_position_m'] = r20['standing_pose']['base_position_m']
a = A.openDocument(str(cad / 'editions/cyber/native/IndieDuck_Cyber_Assembly.FCStd')); a.recompute()
commit = os.environ.get('INDIEDUCK_CAD_COMMIT', 'unrecorded')
printed = {}
with open(cad / 'COMPONENTS.csv') as f:
    for r in csv.DictReader(f):
        if r['revision'] == 'R25': printed[r['assembly_link']] = r
r20parts = {p['id']: p for p in r20['parts']}
orig = {'trunk_base': np.array(c['root_origin_mm'])}; world = {'trunk_base': np.eye(4)}
world['trunk_base'][:3, 3] = np.array(stand['base_position_m']) * 1000
for j in c['joints']:
    o = np.array(j['origin_mm']); orig[j['body']] = o; v = np.array(j['axis'], float); ang = stand['joint_positions_rad'][j['name']]
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); r = np.eye(3) + np.sin(ang) * k + (1 - np.cos(ang)) * (k @ k)
    t = np.eye(4); t[:3, :3] = r; t[:3, 3] = o - orig[j['parent_body']]; world[j['body']] = world[j['parent_body']] @ t

def com(shape):
    s = shape.Solids; return sum((x.CenterOfMass * x.Volume for x in s), A.Vector()) / sum(x.Volume for x in s)

def rgb(o):
    v = getattr(o, 'DisplayColor', None)
    if isinstance(v, (tuple, list)) and len(v) >= 3: return [float(x) if max(v[:3]) <= 1 else x / 255 for x in v[:3]]
    if isinstance(v, int): return [((v >> n) & 255) / 255 for n in [24, 16, 8]]
    return [0.69, 0.69, 0.69]

rows = []; zeros = []; registration = []
for o in a.Objects:
    if not hasattr(o, 'MovingBody') or o.MovingBody in ('archive', ''): continue
    body = o.MovingBody; assert body in world, (o.Label, body)
    s = o.Shape.copy(); assert not s.isNull() and s.isValid(), o.Label
    oid = o.Label; rel = 'meshes/' + oid + '.stl'
    mesh = MeshPart.meshFromShape(Shape=s, LinearDeflection=.15, AngularDeflection=.35, Relative=False); mesh.write(str(out / rel))
    tozero = np.linalg.inv(world[body]); tozero[:3, 3] += orig[body]
    sz = s.transformGeometry(A.Matrix(*tozero.flatten().tolist()))
    MeshPart.meshFromShape(Shape=sz, LinearDeflection=.15, AngularDeflection=.35, Relative=False).write(str(zero / rel))
    p = printed.get(oid); bb = s.optimalBoundingBox(True, False); zbb = sz.optimalBoundingBox(True, False)
    if oid in r20parts:  # retained part: assembled bounds must match the R20 display export
        rb = np.array(r20parts[oid]['bounds_mm']); nb = np.array([[bb.XMin, bb.YMin, bb.ZMin], [bb.XMax, bb.YMax, bb.ZMax]])
        registration.append((oid, float(np.abs(rb - nb).max())))
    row = {'id': oid, 'name': oid[2:] if oid.startswith('A_') else oid, 'label': oid, 'mesh': rel, 'body': body, 'color': rgb(o),
           'category': 'printed' if p else 'purchased', 'material': p['material'] if p else 'Purchased hardware envelope, material estimate',
           'native_file': 'IndieDuck_Cyber_Assembly.FCStd', 'native_object': o.Name, 'native': 'editions/cyber/native/IndieDuck_Cyber_Assembly.FCStd',
           'step': p['step'] if p else None, 'stl': p['stl'] if p else None, 'reference': not bool(p), 'provisional': not bool(p),
           'volume_mm3': s.Volume, 'center_of_mass_mm': list(com(s)), 'bounds_mm': [[bb.XMin, bb.YMin, bb.ZMin], [bb.XMax, bb.YMax, bb.ZMax]],
           'facets': mesh.CountFacets, 'source_sha256': hashlib.sha256((out / rel).read_bytes()).hexdigest(), 'source_commit': commit}
    rows.append(row); z = dict(row); z['center_of_mass_mm'] = list(com(sz)); z['bounds_mm'] = [[zbb.XMin, zbb.YMin, zbb.ZMin], [zbb.XMax, zbb.YMax, zbb.ZMax]]; zeros.append(z)
    print('EXPORTED', oid, mesh.CountFacets, flush=True)
assert len(rows) == 141 and sum(p['category'] == 'printed' for p in rows) == 55, (len(rows), sum(p['category'] == 'printed' for p in rows))
worst = max(registration, key=lambda x: x[1])
moved = [r for r in registration if r[1] > 0.05]
print('REGISTRATION retained parts', len(registration), 'worst', worst, 'over 0.05 mm', moved, flush=True)
meta = {'revision': 'R25', 'cad_source_commit': commit, 'units': 'mm', 'coordinates': 'CAD world x forward, y left, z up; published standing pose (unchanged from R20)',
        'standing_pose': stand, 'registration_check': {'retained_parts': len(registration), 'max_bounds_difference_mm': worst[1], 'parts_over_0_05_mm': moved},
        'parts': rows, 'limitations': 'Visualization tessellation, not print meshes. Hardware envelopes and dimensions provisional; no physical assembly validation. See THIRD_PARTY_NOTICES.md.'}
(out / 'manifest.json').write_text(json.dumps(meta, indent=2) + '\n')
meta['coordinates'] = 'CAD zero world; derived by inverse explicit joint chain from standing assembly'; meta['parts'] = zeros
(zero / 'manifest.json').write_text(json.dumps(meta, indent=2) + '\n')
skates = Path(__file__).resolve().parents[1] / 'provenance/skates-r07'
shutil.copy2(skates / 'skate-manifest.json', zero / 'skate-manifest.json'); shutil.copytree(skates / 'mesh', zero / 'mesh', dirs_exist_ok=True)
print('DONE', len(rows), flush=True)
