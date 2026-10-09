"""Native finite-physics, contract, sensor and benchmark evidence for one R20 duck."""
import argparse, hashlib, json, platform, statistics, sys, time
from pathlib import Path
import mujoco
import numpy as np
from mjlab_microduck.sim.indieduck import MODEL_DIR,contract,set_pose

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('validation/r20-native.json'));args=p.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
c=contract();poses=json.loads((MODEL_DIR/'poses.json').read_text())['poses']
report={'model_id':c['model_id'],'cad_manifest_sha256':c['cad_manifest_sha256'],'mujoco_version':mujoco.__version__,'machine':platform.platform(),'processor':platform.processor(),'python':sys.version,'performance_contract':{'workload':'one R20 duck, floor, 40 mm ball; walking feet and four passive wheels; 5 x 1000 steps after 200 warmup steps','step_s':.005,'target':'at least real time 200 physics steps/s on this Mac; finite state, no CPU-specific optimization','limitations':'desktop CPU study, not Radxa performance; this report uses approximate XML PD; separate m1 BAM report; no learned balancing'},'models':{},'fixtures':{}}
for filename in ['scene.xml','scene_skates.xml']:
    cold=[]
    for _ in range(5):
        t=time.perf_counter();model=mujoco.MjModel.from_xml_path(str(MODEL_DIR/filename));cold.append(time.perf_counter()-t)
    data=mujoco.MjData(model)
    assert np.all(model.body_mass[1:]>0)
    assert np.all(model.body_inertia[1:]>0)
    names=[mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_ACTUATOR,i) for i in range(model.nu)]
    assert names==c['physical_joint_names']
    assert model.nu==15
    assert len(c['policy_action_joints'])==14 and c['mouth_index']==9 and c['policy_observation_size']==61
    pose_results=[];fixtures=[]
    for pose in poses:
        key=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_KEY,pose['id']);mujoco.mj_resetDataKeyframe(model,data,key);mujoco.mj_forward(model,data)
        fixtures.append({'id':pose['id'],'qpos':data.qpos.tolist(),'ctrl':data.ctrl.tolist(),'body_positions':{model.body(i).name:data.xpos[i].tolist() for i in range(model.nbody)},'body_quaternions':{model.body(i).name:data.xquat[i].tolist() for i in range(model.nbody)},'contacts':int(data.ncon)})
        worst=0.;initial_contacts=int(data.ncon)
        for _ in range(200):
            mujoco.mj_step(model,data)
            assert np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()
            worst=max(worst,float(np.max(abs(data.qvel))))
        warnings=[int(w.number) for w in data.warning]
        assert sum(warnings)==0,(filename,pose['id'],warnings)
        pose_results.append({'pose':pose['id'],'initial_contacts':initial_contacts,'end_contacts':int(data.ncon),'max_abs_velocity':worst,'finite':True,'warnings':warnings,'status':'one second finite integration, not successful behavior or stable balance'})
    samples=[]
    for _ in range(5):
        mujoco.mj_resetDataKeyframe(model,data,model.key('stand').id)
        mujoco.mj_step(model,data,nstep=200);t=time.perf_counter();mujoco.mj_step(model,data,nstep=1000);samples.append(time.perf_counter()-t)
    key=model.key('stand').id;mujoco.mj_resetDataKeyframe(model,data,key);mujoco.mj_forward(model,data)
    sensor_report={}
    for name in ['body_imu_gyro','body_imu_accel','body_imu_quat','head_imu_gyro','head_imu_accel','head_imu_quat']:
        value=data.sensor(name).data;assert np.isfinite(value).all();sensor_report[name]=value.tolist()
    rays=[float(data.sensor(f'tof_{r}_{col}').data[0]) for r in range(8) for col in range(8)]
    assert len(rays)==64 and np.isfinite(rays).all()
    rates=[1000/t for t in samples]
    report['models'][filename]={'mass_kg':float(model.body_mass.sum()),'bodies':model.nbody,'joints':model.njnt,'actuators':model.nu,'sensors':model.nsensor,'poses':pose_results,'imu_samples':sensor_report,'tof_ranges_m':rays,'cold_load_s':cold,'steady_elapsed_s':samples,'steps_per_s':{'median':statistics.median(rates),'min':min(rates),'max':max(rates),'stddev':statistics.stdev(rates)},'real_time_factor_median':statistics.median(rates)*.005,'decision':'promote local study numerical execution, hold hardware fidelity'}
    report['fixtures'][filename]=fixtures
args.output.write_text(json.dumps(report,indent=2)+'\n')
(MODEL_DIR/'native-fixtures.json').write_text(json.dumps({'mujoco_version':mujoco.__version__,'cad_manifest_sha256':c['cad_manifest_sha256'],'fixtures':report['fixtures']},indent=2)+'\n')
print(json.dumps({k:{'mass_kg':v['mass_kg'],'steps_per_s':v['steps_per_s'],'poses':len(v['poses'])} for k,v in report['models'].items()},indent=2))
