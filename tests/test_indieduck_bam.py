import json
import mujoco
import numpy as np
import pytest
from bam.simulate import fractional_delay_shift
from mjlab_microduck.sim.bam_native import NativeBamStudy,D8_DELAY_S,VENDOR_PARAMS


def test_m1_source_and_motor_equation():
    study=NativeBamStudy(delay_s=0)
    params=json.loads((VENDOR_PARAMS/'m1.json').read_text())
    assert study.bam.name=='m1' and study.bam.actuator.vin==5.0
    assert study.source_delay_s==params['command_delay']
    np.testing.assert_allclose(study.model.dof_armature[study.controller.dof_indexes],params['armature'])
    target=study.target.copy();target[5]+=.01
    study.controller.q_target=target
    study.controller.update()
    expected=params['kt']*5/params['R']*.01*32*params['error_gain']
    assert study.data.ctrl[study.model.actuator('neck_pitch').id]==pytest.approx(expected)
    assert np.all(study.model.actuator_gainprm[:,0]==1)
    assert not study.model.actuator_biasprm.any()
    np.testing.assert_allclose(study.model.dof_damping[study.controller.dof_indexes],params['friction_viscous'])


def test_fractional_command_delay_matches_vendored_reference():
    study=NativeBamStudy();original=study.target.copy()
    sequence=np.tile(original,(18,1));sequence[1:,5]+=.02
    reference=fractional_delay_shift(sequence,D8_DELAY_S,.005)
    for target,expected in zip(sequence,reference):
        study.set_target(target);study.step()
        np.testing.assert_allclose(study.controller.q_target,expected,atol=1e-14)


def test_bam_reset_repeatability_and_torque_disable():
    study=NativeBamStudy()
    traces=[]
    for _ in range(2):
        study.reset();target=study.target.copy();target[7]=.15;study.set_target(target)
        trace=[]
        for _ in range(40):study.step();trace.append(study.data.qpos.copy())
        traces.append(trace)
    np.testing.assert_allclose(traces[0],traces[1],atol=1e-13)
    study.step(torque_enabled=False)
    np.testing.assert_array_equal(study.data.ctrl,np.zeros(15))
    study.reset();assert not study.data.ctrl.any()
    old=study.target.copy()
    with pytest.raises(ValueError):study.set_target([float('nan')]*15)
    np.testing.assert_array_equal(study.target,old)


@pytest.mark.parametrize('scene',['scene.xml','scene_skates.xml'])
def test_bam_contacts_and_all_keyframes_finite(scene):
    study=NativeBamStudy(scene)
    for i in range(study.model.nkey):
        study.reset(study.model.key(i).name)
        for _ in range(200):study.step()
        assert np.isfinite(study.data.qpos).all() and np.isfinite(study.data.qvel).all()
        assert not sum(w.number for w in study.data.warning)
    study.reset('stand');seen=set()
    for _ in range(50):
        study.step()
        for contact in study.data.contact:
            pair={study.model.geom(contact.geom1).name,study.model.geom(contact.geom2).name}
            if 'ground' in pair:seen.update(pair-{'ground'})
    assert 'test_ball_geom' in seen
    if scene=='scene_skates.xml':
        assert {f'{side}_{end}_wheel' for side in ['left','right'] for end in ['front','rear']}<=seen
