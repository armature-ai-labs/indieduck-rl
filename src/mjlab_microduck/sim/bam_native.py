"""CPU BAM diagnostic on the canonical R07 geometry, with the selected D8 m1 fit."""
from collections import deque
import math
from pathlib import Path
import mujoco
import numpy as np
from bam.model import load_model
from bam.mujoco import MujocoController
from mjlab_microduck.sim.indieduck import MODEL_DIR, contract

D8_DELAY_S = 0.029
VENDOR_PARAMS = Path(__file__).resolve().parents[3] / 'vendor/bam/bam/params/hd1910'


class NativeBamStudy:
    def __init__(self, scene='scene.xml', *, delay_s=D8_DELAY_S, volts=5.0):
        if not math.isfinite(delay_s) or not 0 <= delay_s <= 0.05:
            raise ValueError('Command delay must be finite and within 0..0.05 s')
        if not math.isfinite(volts) or not 4.75 <= volts <= 5.25:
            raise ValueError('Study voltage must stay within the 5 V rail tolerance')
        self.model = mujoco.MjModel.from_xml_path(str(MODEL_DIR / scene))
        self.data = mujoco.MjData(self.model)
        self.names = contract()['physical_joint_names']
        self.limits = np.array([j['limits_rad'] for j in contract()['joints']])
        self.bam = load_model(motor_name='hd1910', model='m1')
        self.bam.actuator.vin = volts
        self.bam.actuator.kp = 32.0
        self.source_delay_s = self.bam.command_delay.value
        self.delay_s = delay_s
        self.model.actuator_gainprm[:] = 0
        self.model.actuator_gainprm[:, 0] = 1
        self.model.actuator_biasprm[:] = 0
        self.model.actuator_gaintype[:] = mujoco.mjtGain.mjGAIN_FIXED
        self.model.actuator_biastype[:] = mujoco.mjtBias.mjBIAS_NONE
        self.model.actuator_ctrllimited[:] = False
        self.model.actuator_forcelimited[:] = False
        self.controller = MujocoController(self.bam, self.names, self.model, self.data)
        delay_steps = delay_s / self.model.opt.timestep
        self.lag = int(math.floor(delay_steps))
        self.fraction = delay_steps - self.lag
        self.history = deque(maxlen=self.lag + 2)
        self.reset()

    def reset(self, pose='stand'):
        mujoco.mj_resetDataKeyframe(self.model, self.data, self.model.key(pose).id)
        self.model.dof_frictionloss[self.controller.dof_indexes] = self.bam.friction_base.value
        self.model.dof_damping[self.controller.dof_indexes] = self.bam.friction_viscous.value
        self.bam.reset()
        self.controller.reset()
        self.target = self.data.qpos[self.controller.qpos_indexes].copy()
        self.controller.q_target = self.target.copy()
        self.history.clear()
        self.history.extend(self.target.copy() for _ in range(self.history.maxlen))
        self.data.ctrl[:] = 0
        mujoco.mj_forward(self.model, self.data)

    def set_target(self, target):
        values = np.asarray(target, dtype=float)
        if values.shape != (15,) or not np.isfinite(values).all():
            raise ValueError('Expected 15 finite physical joint targets')
        if np.any(values < self.limits[:, 0]) or np.any(values > self.limits[:, 1]):
            raise ValueError('Target exceeds the R07 joint study range')
        self.target = values.copy()

    def step(self, *, torque_enabled=True):
        self.history.append(self.target.copy())
        self.controller.q_target = ((1 - self.fraction) * self.history[-self.lag - 1]
                                    + self.fraction * self.history[-self.lag - 2])
        self.controller.update()
        if not torque_enabled:
            self.data.ctrl[self.controller.act_indexes] = 0
        mujoco.mj_step(self.model, self.data)
        return self.data
