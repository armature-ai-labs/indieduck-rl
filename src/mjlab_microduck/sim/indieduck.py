"""IndieDuck R20 model operations shared by native checks and pose export."""
from pathlib import Path
import json
import numpy as np
import mujoco

MODEL_DIR = Path(__file__).resolve().parents[1] / 'robot/indieduck'

def contract():
    return json.loads((MODEL_DIR/'contract.json').read_text())

def joint_addresses(model):
    return {j['name']:int(model.joint(j['name']).qposadr[0]) for j in contract()['joints']}

def set_pose(model, data, pose, ground=True):
    c=contract();mujoco.mj_resetData(model,data)
    root=int(model.joint('trunk_base_freejoint').qposadr[0]);data.qpos[root:root+3]=pose['base_position_m'];data.qpos[root+3:root+7]=pose['base_quaternion_wxyz']
    for name,adr in joint_addresses(model).items():
        data.qpos[adr]=pose['joint_positions_rad'][name]
        data.ctrl[model.actuator(name).id]=pose['joint_positions_rad'][name]
    mujoco.mj_forward(model,data)
    if ground:
        lowest=1e6
        for i in range(model.ngeom):
            if model.geom_group[i]!=3 and 'wheel' not in (mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,i) or ''):continue
            rotation=data.geom_xmat[i].reshape(3,3);typ=model.geom_type[i];size=model.geom_size[i]
            if typ==mujoco.mjtGeom.mjGEOM_BOX:extent=np.abs(rotation[2])@size
            elif typ==mujoco.mjtGeom.mjGEOM_CYLINDER:extent=size[0]*np.sqrt(1-rotation[2,2]**2)+size[1]*abs(rotation[2,2])
            else:extent=max(size)
            lowest=min(lowest,data.geom_xpos[i,2]-extent)
        data.qpos[root+2]+=.0003-lowest
        mujoco.mj_forward(model,data)
    return data.qpos[root:root+3].tolist()
