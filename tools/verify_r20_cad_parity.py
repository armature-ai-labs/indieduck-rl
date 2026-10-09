from pathlib import Path
import json,sys
import numpy as np,mujoco
sys.path.insert(0,str(Path.cwd()/'tools'))
from generate_indieduck import load_stl
from mjlab_microduck.sim.indieduck import MODEL_DIR,set_pose
assets=Path(sys.argv[1]);manifest=json.loads((assets/'manifest.json').read_text());model=mujoco.MjModel.from_xml_path(str(MODEL_DIR/'scene.xml'));data=mujoco.MjData(model)
set_pose(model,data,manifest['standing_pose'],ground=False)
rows=[]
for p in manifest['parts']:
 g=model.geom(p['name']+'_visual');mid=int(g.dataid[0]);start=model.mesh_vertadr[mid];count=model.mesh_vertnum[mid];v=model.mesh_vert[start:start+count];world=v@data.geom_xmat[g.id].reshape(3,3).T+data.geom_xpos[g.id];reference=load_stl(assets/p['mesh'])['v'].reshape(-1,3)/1000
 error=float(np.max(abs(np.array([world.min(0),world.max(0)])-np.array([reference.min(0),reference.max(0)]))))
 assert error<.00015,(p['name'],error)
 rows.append({'name':p['name'],'body':p['body'],'bounds_max_error_mm':error*1000})
report={'status':'PASS','parts':len(rows),'printed':sum(p['category']=='printed' for p in manifest['parts']),'pose':'published R20 natural stance with exact CAD root, not seated collision-proxy pose','max_bounds_error_mm':max(p['bounds_max_error_mm'] for p in rows),'tolerance_mm':.15,'details':rows}
Path('validation/r20-cad-standing-parity.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],report['parts'],report['max_bounds_error_mm'])
