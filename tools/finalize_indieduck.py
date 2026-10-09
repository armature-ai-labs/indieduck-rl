"""Resolve shared poses and serialize keyframes for native and browser consumers."""
import json,hashlib,sys
from pathlib import Path
import xml.etree.ElementTree as E
import mujoco
from mjlab_microduck.sim.indieduck import MODEL_DIR,set_pose
poses=json.loads((MODEL_DIR/'poses.json').read_text())
for scene in ['scene.xml','scene_skates.xml','robot.xml','robot_skates.xml']:
    model=mujoco.MjModel.from_xml_path(str(MODEL_DIR/scene));data=mujoco.MjData(model);tree=E.parse(MODEL_DIR/scene);root=tree.getroot()
    old=root.find('keyframe')
    if old is not None:root.remove(old)
    keys=E.SubElement(root,'keyframe')
    for p in poses['poses']:
        base=set_pose(model,data,p)
        if scene=='scene.xml':p['base_position_m']=base
        if scene=='scene_skates.xml':p['skates_base_position_m']=base
        E.SubElement(keys,'key',name=p['id'],qpos=' '.join(f'{v:.12g}' for v in data.qpos),ctrl=' '.join(f'{v:.12g}' for v in data.ctrl))
    E.indent(root);tree.write(MODEL_DIR/scene,encoding='unicode',xml_declaration=True)
(MODEL_DIR/'poses.json').write_text(json.dumps(poses,indent=2)+'\n')
files=sorted(p.relative_to(MODEL_DIR).as_posix() for p in MODEL_DIR.rglob('*') if p.suffix in ['.json','.xml','.stl'] and p.name!='files.json')
(MODEL_DIR/'files.json').write_text(json.dumps({'files':files,'default_scene':'scene.xml','skates_scene':'scene_skates.xml'},indent=2)+'\n')
print('keyframes and ground placement resolved')
