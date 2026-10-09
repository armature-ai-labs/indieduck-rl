import FreeCAD as A,Part,MeshPart,json,zipfile,hashlib,xml.etree.ElementTree as E
from pathlib import Path
import numpy as np
import os
cad=Path(os.environ['INDIEDUCK_CAD']);out=Path(os.environ['INDIEDUCK_ASSETS']);zero=out/'zero';model=Path(__file__).resolve().parents[1]/'src/mjlab_microduck/robot/indieduck'
for p in [out/'meshes',zero/'meshes']:p.mkdir(parents=True,exist_ok=True)
c=json.loads((model/'contract.json').read_text());mapping=json.loads((model/'part-bodies.json').read_text());poses=json.loads((model/'poses.json').read_text());stand=next(p for p in poses['poses'] if p['id']=='stand')
docs={r:A.openDocument(str(cad/'native/robot'/('IndieDuck_R20_'+r+'.FCStd'))) for r in ['Structure','Interfaces','HeadBand','Assembly']};a=docs['Assembly'];a.recompute()
# CAD registration comes from the native trunk link, not collision-proxy grounding.
stand['base_position_m']=[x/1000 for x in a.A_Trunk.Placement.multVec(A.Vector(*c['root_origin_mm']))]
assert abs(a.A_Trunk.Placement.Rotation.Angle)<1e-10, 'Review changed CAD root rotation before export'
xml=E.fromstring(zipfile.ZipFile(a.FileName).read('GuiDocument.xml'))
printed={p['assembly_link']:p for p in json.loads((cad/'validation/exports.json').read_text())['parts']}
orig={'trunk_base':np.array(c['root_origin_mm'])};world={'trunk_base':np.eye(4)};world['trunk_base'][:3,3]=np.array(stand['base_position_m'])*1000
for j in c['joints']:
 o=np.array(j['origin_mm']);orig[j['body']]=o;v=np.array(j['axis'],float);ang=stand['joint_positions_rad'][j['name']];k=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]]);r=np.eye(3)+np.sin(ang)*k+(1-np.cos(ang))*(k@k);t=np.eye(4);t[:3,:3]=r;t[:3,3]=o-orig[j['parent_body']];world[j['body']]=world[j['parent_body']]@t
def com(shape):
 solids=shape.Solids
 return sum((x.CenterOfMass*x.Volume for x in solids),A.Vector())/sum(x.Volume for x in solids)
rows=[];zeros=[]
for o in a.Objects:
 if o.TypeId!='App::Link' or not o.Visibility:continue
 name=o.Name[2:];body=mapping[name];s=o.Shape.copy();assert not s.isNull() and s.isValid(),name
 color=xml.find(f'.//ViewProvider[@name="{o.Name}"]/Properties/Property[@name="ShapeMaterial"]/PropertyMaterial');v=int(color.get('diffuseColor')) if color is not None else 0xb0b0b0ff;rgb=[((v>>n)&255)/255 for n in [24,16,8]]
 # Presentation meshes are deliberately coarser than manufacturing exports.
 mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.15,AngularDeflection=.35,Relative=False);rel='meshes/'+o.Name+'.stl';mesh.write(str(out/rel))
 inverse=np.linalg.inv(world[body]);tozero=inverse.copy();tozero[:3,3]+=orig[body];matrix=A.Matrix(*tozero.flatten().tolist());sz=s.transformGeometry(matrix)
 m0=MeshPart.meshFromShape(Shape=sz,LinearDeflection=.15,AngularDeflection=.35,Relative=False);m0.write(str(zero/rel))
 target=o.LinkedObject;p=printed.get(o.Name);bb=s.optimalBoundingBox(True,False);zbb=sz.optimalBoundingBox(True,False)
 row={'id':o.Name,'name':name,'label':o.Label,'mesh':rel,'body':body,'color':rgb,'category':'printed' if p else 'purchased','material':p['material'] if p else 'Purchased hardware envelope, material estimate','native_file':Path(target.Document.FileName).name,'native_object':target.Name,'native':'native/robot/'+Path(target.Document.FileName).name,'step':p['step'] if p else None,'stl':p['stl'] if p else None,'reference':not bool(p),'provisional':not bool(p),'volume_mm3':s.Volume,'center_of_mass_mm':list(com(s)),'bounds_mm':[[bb.XMin,bb.YMin,bb.ZMin],[bb.XMax,bb.YMax,bb.ZMax]],'facets':mesh.CountFacets,'source_sha256':hashlib.sha256((out/rel).read_bytes()).hexdigest(),'source_commit':c['cad_source_commit']}
 rows.append(row);z=dict(row);z['center_of_mass_mm']=list(com(sz));z['bounds_mm']=[[zbb.XMin,zbb.YMin,zbb.ZMin],[zbb.XMax,zbb.YMax,zbb.ZMax]];zeros.append(z)
 print('EXPORTED',name,mesh.CountFacets,flush=True)
assert len(rows)==124 and sum(p['category']=='printed' for p in rows)==41
metadata={'revision':'R20','cad_source_commit':c['cad_source_commit'],'units':'mm','coordinates':'CAD world x forward, y left, z up; complete published natural standing pose','standing_pose':stand,'parts':rows,'limitations':'Visualization tessellation, not print meshes. Hardware envelopes and dimensions provisional; no physical assembly validation. See THIRD_PARTY_NOTICES.md.'}
(out/'manifest.json').write_text(json.dumps(metadata,indent=2)+'\n');metadata['coordinates']='CAD zero world; derived by inverse explicit joint chain from standing assembly';metadata['parts']=zeros;(zero/'manifest.json').write_text(json.dumps(metadata,indent=2)+'\n')
import shutil
skates=Path(__file__).resolve().parents[1]/'provenance/skates-r07'
shutil.copy2(skates/'skate-manifest.json',zero/'skate-manifest.json')
shutil.copytree(skates/'mesh',zero/'mesh',dirs_exist_ok=True)
print('DONE',len(rows),flush=True)
