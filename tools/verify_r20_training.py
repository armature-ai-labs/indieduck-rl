import json, time
from pathlib import Path
import torch
from mjlab_microduck.tasks.indieduck_velocity_env_cfg import make_indieduck_velocity_env_cfg,get_r20_spec,POLICY_JOINTS
from mjlab.envs import ManagerBasedRlEnv
cfg=make_indieduck_velocity_env_cfg();cfg.scene.num_envs=1
print('spec',get_r20_spec().compile().nu,'actions',cfg.actions['joint_pos'].actuator_names,flush=True)
t=time.monotonic();env=ManagerBasedRlEnv(cfg,device='cpu');print('ENV_READY',env.action_manager.total_action_dim,flush=True)
obs,_=env.reset();
from mjlab.rl.exporter_utils import get_base_metadata
metadata=get_base_metadata(env,run_path='untrained-r20-smoke')
assert metadata['joint_names']==list(POLICY_JOINTS)
height=float(env.scene['robot'].data.root_link_pos_w[0,2]-env.scene.env_origins[0,2])
assert .142 <= height <= .149,height
print('OBS',[(k,tuple(v.shape)) for k,v in obs.items()],flush=True)
assert env.action_manager.total_action_dim==14 and obs['actor'].shape==(1,61)
for _ in range(2):
 out=env.step(torch.zeros((1,14)));assert torch.isfinite(out[0]['actor']).all()
print('TWO_STEPS_PASS',time.monotonic()-t,flush=True)
Path('validation/r20-training-smoke.json').write_text(json.dumps({'status':'PASS','device':'cpu','environments':1,'action_size':14,'actor_observation_size':61,'steps':2,'elapsed_s':time.monotonic()-t,'scope':'configuration, reset and two environment steps only; no learned policy or GPU validation'},indent=2)+'\n');env.close()
