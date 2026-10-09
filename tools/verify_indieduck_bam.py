"""Bounded CPU BAM m1 execution evidence; no hardware calibration or learned control."""
import hashlib,json,platform,statistics,sys,time
from pathlib import Path
import mujoco
import numpy as np
from mjlab_microduck.sim.bam_native import NativeBamStudy,D8_DELAY_S,VENDOR_PARAMS
from mjlab_microduck.sim.indieduck import MODEL_DIR,contract

params_path=VENDOR_PARAMS/'m1.json';params=json.loads(params_path.read_text())
characterization_path=VENDOR_PARAMS/'characterization.json'
characterization=json.loads(characterization_path.read_text())
report={'model_id':contract()['model_id'],'contract_sha256':hashlib.sha256((MODEL_DIR/'contract.json').read_bytes()).hexdigest(),'mujoco_version':mujoco.__version__,'machine':platform.platform(),'python':sys.version,'motor':'HD-1910-C001','fit':'m1','source':{'repository':'https://github.com/JoyandAI/microduck_rl','commit':'22916b9d82f250caa563ed9a56976eb33243fb91','params_path':'vendor/bam/bam/params/hd1910/m1.json','params_sha256':hashlib.sha256(params_path.read_bytes()).hexdigest(),'characterization_sha256':hashlib.sha256(characterization_path.read_bytes()).hexdigest(),'supply_voltage_V':characterization['supply_voltage_V'],'parameters':params,'provenance':'Upstream measured/fitted identification; not remeasured on IndieDuck'},'configuration':{'selected_decision':'D8, decisions-2026-10-06.md','volts':5.0,'firmware_kp':32.0,'selected_delay_s':D8_DELAY_S,'pinned_file_delay_s':params['command_delay'],'delay_discrepancy':'D8 delay overrides only the standalone diagnostic baseline; pinned source file is unchanged. Pinned-file delay is a comparison, not a new hardware decision.','q_offset_applied':False,'q_offset_reason':'Upstream bench rig alignment nuisance; does not replace R20 joint zero or hardware encoder calibration.','voltage_sag':'None; regulated 5.0 V diagnostic, not battery simulation','model_change':'Same canonical CAD/body/contact/sensor model; in-memory torque actuators, BAM armature and friction replace estimated XML position actuators.'},'parameter_basis':{'kt':'upstream no-load speed measurement','R':'upstream datasheet equivalent, not IndieDuck measured','error_gain':'upstream duty/error regression','armature':'upstream fitted','friction_base':'upstream fitted','friction_viscous':'upstream fitted','kp':'upstream register readback,32','kd':'upstream register readback,40; effective derivative gain/scaling unverified','command_delay':'m1 fitted file value, selected D8 override recorded separately','max_current':'upstream provisional limiter assumption, actual mode-4 limiting uncertain','max_velocity_and_acceleration':'retained source values, rate limiting disabled as in upstream HD1910 default'},'acceptance_boundary':'Finite execution and equation/delay/reset tests. No trained balance, hardware validation or mjlab GPU task integration.','performance_contract':{'workload':'one complete R20 duck with ball/floor, 15 BAM motors; walking feet and passive inline skates','step_s':.005,'cold_samples':5,'steady_samples':5,'warmup_steps':200,'measured_steps':1000,'target_steps_per_s':200,'scope':'Mac CPU only; not Radxa or GPU throughput'},'models':{}}
for scene in ['scene.xml','scene_skates.xml']:
    cold=[]
    for _ in range(5):
        start=time.perf_counter();study=NativeBamStudy(scene);cold.append(time.perf_counter()-start)
    results={}
    for label,delay in [('D8_selected',D8_DELAY_S),('pinned_file_comparison',params['command_delay'])]:
        study=NativeBamStudy(scene,delay_s=delay);rows=[]
        for i in range(study.model.nkey):
            name=study.model.key(i).name;study.reset(name);worst=0.;max_torque=0.
            for _ in range(200):
                study.step();assert np.isfinite(study.data.qpos).all() and np.isfinite(study.data.qvel).all()
                worst=max(worst,float(np.max(abs(study.data.qvel))));max_torque=max(max_torque,float(np.max(abs(study.data.ctrl))))
            warnings=[int(w.number) for w in study.data.warning];assert not sum(warnings)
            rows.append({'pose':name,'finite':True,'warnings':warnings,'end_contacts':int(study.data.ncon),'max_velocity_rad_s':worst,'max_motor_torque_Nm':max_torque})
        results[label]={'delay_s':delay,'poses':rows}
    study=NativeBamStudy(scene);samples=[]
    for _ in range(5):
        study.reset()
        for _ in range(200):study.step()
        start=time.perf_counter()
        for _ in range(1000):study.step()
        samples.append(time.perf_counter()-start)
    rates=[1000/t for t in samples]
    report['models'][scene]={'diagnostics':results,'cold_load_s':cold,'steady_elapsed_s':samples,'steps_per_s':{'median':statistics.median(rates),'min':min(rates),'max':max(rates),'stddev':statistics.stdev(rates)}}
Path('validation/r20-bam-native.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({s:{'pose_checks':sum(len(d['poses']) for d in v['diagnostics'].values()),'steps_per_s':v['steps_per_s']} for s,v in report['models'].items()},indent=2))
