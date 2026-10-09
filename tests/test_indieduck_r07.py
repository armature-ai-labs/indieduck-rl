import json, math, socket, threading
from pathlib import Path
import mujoco
import numpy as np
import pytest
from mjlab_microduck.sim.indieduck import MODEL_DIR,contract
from mjlab_microduck.sim.body_server import World,Body,Server,Handler,CONTRACT_SHA256

@pytest.fixture
def body():
    world=World(MODEL_DIR/'scene.xml');body=Body(world,0);world.bodies=[body];body.reset('stand');return body

def test_contract_and_cad_origins():
    c=contract();m=mujoco.MjModel.from_xml_path(str(MODEL_DIR/'scene.xml'));d=mujoco.MjData(m);mujoco.mj_forward(m,d)
    assert m.nu==15 and c['mouth_index']==9 and len(c['policy_action_joints'])==14
    assert c['policy_observation_size']==61 and c['servo_volts']==5
    for j in c['joints']:
        np.testing.assert_allclose(d.xanchor[m.joint(j['name']).id],np.array(j['origin_mm'])/1000,atol=1e-10)
    assert np.all(m.body_mass[1:]>0) and np.all(m.body_inertia[1:]>0)

def test_direct_drive_jaw_and_no_passive_linkage():
    c=contract();m=mujoco.MjModel.from_xml_path(str(MODEL_DIR/'scene.xml'))
    assert c['mouth_linkage']['type']=='direct_drive'
    assert c['joints'][9]['limits_rad']==pytest.approx([0,math.pi/6])
    assert c['joints'][9]['axis']==[0,1,0]
    assert mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,'passive_jaw')==-1
    assert m.neq==0

def test_targets_validated_without_partial_write(body):
    targets=list(body.sensors()['positions']);old=body.world.data.ctrl.copy()
    for bad in [targets[:-1],[float('nan')]+targets[1:],[10]+targets[1:]]:
        with pytest.raises(ValueError):body.set_targets(bad)
        np.testing.assert_array_equal(body.world.data.ctrl,old)

def test_torque_gain_and_reset(body):
    body.set_torque(True);body.set_gain(32);assert body.released
    old=body.world.epoch;body.reset('sit');assert body.world.epoch==old+1 and not body.torque_on
    assert np.all(body.world.model.actuator_gainprm[body.actuator_slice,0]==0)
    assert body.slow_sensors()['volts']==5
    sensors=body.sensors();assert len(sensors['head_imu']['quat'])==4 and len(sensors['imu']['gyro'])==3

def test_native_tof_shape(body):
    depth=body.depth();assert depth['rows']==depth['cols']==8
    assert len(depth['distance_mm'])==len(depth['status'])==64
    assert set(depth['status'])<={5,255}
    assert all(mm>10 for mm,status in zip(depth['distance_mm'],depth['status']) if status==5)

def test_tcp_handshake_reset_and_disconnect(body):
    server=Server(('127.0.0.1',0),Handler);server.body=body
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with socket.create_connection(server.server_address) as sock:
            stream=sock.makefile('rwb')
            def call(x):stream.write((json.dumps(x)+'\n').encode());stream.flush();return json.loads(stream.readline())
            assert 'error' in call({'op':'read'})
            assert 'error' in call({'op':'hello','protocol':1,'model_id':'microduck','contract_version':1})
            hello=call({'op':'hello','protocol':1,'model_id':'indieduck-r20','contract_version':2,'contract_sha256':CONTRACT_SHA256})
            assert hello['servo_volts']==5 and hello['contract_sha256']==CONTRACT_SHA256
            assert hello['mujoco_version']=='3.10.0'
            read=call({'op':'read'});assert read['session_id']==hello['session_id']
            reset=call({'op':'reset','pose':'stand'});assert reset['epoch']==hello['epoch']+1
            assert call({'op':'read'})['epoch']==reset['epoch']
            assert 'error' in call({'op':'torque','on':True,'session_id':hello['session_id'],'epoch':hello['epoch']})
            assert not body.torque_on
            assert 'error' in call({'op':'write','targets':read['positions'],'session_id':'stale','epoch':reset['epoch']})
            assert 'error' in call({'op':'reset','pose':'missing'})
            assert call({'op':'torque','on':True})=={}
            stream.close()
        for _ in range(100):
            if not body.torque_on:break
            threading.Event().wait(.005)
        assert not body.torque_on
    finally:server.shutdown();server.server_close();thread.join()

@pytest.mark.parametrize('scene',['scene.xml','scene_skates.xml'])
def test_all_keyframes_finite(scene):
    m=mujoco.MjModel.from_xml_path(str(MODEL_DIR/scene));d=mujoco.MjData(m)
    for i in range(m.nkey):
        mujoco.mj_resetDataKeyframe(m,d,i);mujoco.mj_step(m,d,nstep=200)
        assert np.isfinite(d.qpos).all() and np.isfinite(d.qvel).all()
        assert not sum(w.number for w in d.warning)


def test_pose_table_uses_robot_root_not_prop():
    from mjlab_microduck.sim.body_server import pose_table
    poses=json.loads((MODEL_DIR/'poses.json').read_text())['poses']
    for pose in poses:
        _,height=pose_table(MODEL_DIR/'scene.xml',pose['id'])
        assert height==pytest.approx(pose['base_position_m'][2])


@pytest.mark.parametrize('scene',['scene.xml','scene_skates.xml'])
def test_ball_settles_on_ground(scene):
    model=mujoco.MjModel.from_xml_path(str(MODEL_DIR/scene));data=mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model,data,model.key('stand').id)
    ball=int(model.joint('ball_freejoint').qposadr[0]);data.qpos[ball:ball+3]=[.8,0,.08]
    mujoco.mj_step(model,data,nstep=200)
    assert .018 < data.qpos[ball+2] < .021
    pairs=[{model.geom(c.geom1).name,model.geom(c.geom2).name} for c in data.contact]
    assert {'ground','test_ball_geom'} in pairs


def test_all_skate_wheels_contact_ground():
    model=mujoco.MjModel.from_xml_path(str(MODEL_DIR/'scene_skates.xml'));data=mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model,data,model.key('stand').id);seen=set()
    for _ in range(50):
        mujoco.mj_step(model,data)
        for contact in data.contact:
            pair={model.geom(contact.geom1).name,model.geom(contact.geom2).name}
            if 'ground' in pair:seen.update(pair-{'ground'})
    assert {f'{side}_{end}_wheel' for side in ['left','right'] for end in ['front','rear']}<=seen
