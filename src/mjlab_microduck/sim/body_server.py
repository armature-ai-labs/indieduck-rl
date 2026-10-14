# Modified by Armature AI Labs for the IndieDuck R20 local study, 2026-10-08.
"""Local IndieDuck R20 physics body using versioned newline JSON protocol 1.

Run with PYTHONPATH=src .venv-study/bin/python -m mjlab_microduck.sim.body_server --headless.
Position PD, current estimates, mass and contact properties are study approximations, not BAM.
A connected daemon must use --no-policy until a matching IndieDuck policy is trained.
"""
from __future__ import annotations
import argparse
import hashlib
import uuid
import math
import json
import socket
import socketserver
import threading
import time
from pathlib import Path
import mujoco
import numpy as np
from mjlab_microduck.sim.camera import FPS as CAMERA_FPS
from mjlab_microduck.sim.camera import Camera, FrameHandler, FrameServer
PROTOCOL = 1
MODEL_DIR = Path(__file__).resolve().parents[1] / 'robot' / 'indieduck'
CONTRACT_BYTES = (MODEL_DIR / 'contract.json').read_bytes()
CONTRACT = json.loads(CONTRACT_BYTES)
CONTRACT_SHA256 = hashlib.sha256(CONTRACT_BYTES).hexdigest()
POSES = json.loads((MODEL_DIR / 'poses.json').read_text())['poses']
TIMESTEP = 0.005
HOME_TRUNK_Z = next((p for p in POSES if p['id'] == 'stand'))['base_position_m'][2]
JOINT_NAMES = ('left_hip_yaw', 'left_hip_roll', 'left_hip_pitch', 'left_knee', 'left_ankle', 'neck_pitch', 'head_pitch', 'head_yaw', 'head_roll', 'mouth', 'right_hip_yaw', 'right_hip_roll', 'right_hip_pitch', 'right_knee', 'right_ankle')
MOUTH_INDEX = JOINT_NAMES.index('mouth')
HOME_POSE = tuple((next((p for p in POSES if p['id'] == 'stand'))['joint_positions_rad'][n] for n in JOINT_NAMES))
SCENES = MODEL_DIR
DEFAULT_SCENE = SCENES / 'scene.xml'
ROBOT_ONLY = SCENES / 'robot.xml'
SPACING = 0.5
NOMINAL_VOLTS = 5.0
NOMINAL_TEMP_C = 32.0

def duck_prefix(index: int) -> str:
    return '' if index == 0 else f'd{index}_'

def build_world(scene: Path, count: int) -> mujoco.MjModel:
    if count == 1:
        return mujoco.MjModel.from_xml_path(str(scene))
    spec = mujoco.MjSpec.from_file(str(scene))
    for index in range(1, count):
        robot = mujoco.MjSpec.from_file(str(ROBOT_ONLY))
        frame = spec.worldbody.add_frame(pos=[0.0, index * SPACING, 0.0])
        spec.attach(robot, prefix=duck_prefix(index), frame=frame)
    return spec.compile()

def pose_table(scene: Path, keyframe: str) -> tuple[dict[str, float] | None, float]:
    if keyframe.upper() == 'HOME':
        return (None, HOME_TRUNK_Z)
    model = mujoco.MjModel.from_xml_path(str(scene))
    names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_KEY, i) for i in range(model.nkey)]
    if keyframe not in names:
        raise SystemExit(f"no keyframe {keyframe!r} in {scene.name}. It has: {', '.join((n for n in names if n))}")
    qpos = model.key_qpos[names.index(keyframe)]
    table = {}
    for joint in range(model.njnt):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, joint)
        if name in JOINT_NAMES:
            table[name] = float(qpos[model.jnt_qposadr[joint]])
    return (table, float(qpos[int(model.joint('trunk_base_freejoint').qposadr[0]) + 2]))

def gravity_in_trunk(quat: np.ndarray) -> np.ndarray:
    rotation = np.zeros(9)
    mujoco.mju_quat2Mat(rotation, quat)
    return -rotation.reshape(3, 3).T[:, 2]

class World:

    def __init__(self, scene: Path, count: int=1):
        self.model = build_world(scene, count)
        self.session_id = str(uuid.uuid4())
        self.epoch = 0
        self.model.opt.timestep = TIMESTEP
        self.data = mujoco.MjData(self.model)
        self.lock = threading.RLock()
        self.client_lock = threading.Lock()
        self.bodies: list[Body] = []

    def step(self, times: int=1) -> None:
        with self.lock:
            for _ in range(times):
                mujoco.mj_step(self.model, self.data)
                for body in self.bodies:
                    if not body.released:
                        body.restore()

class Body:

    def __init__(self, world: World, index: int, limp: bool=False, kp: float=32.0):
        self.world = world
        self.index = index
        self.prefix = duck_prefix(index)
        model = world.model

        def ident(kind, name):
            found = mujoco.mj_name2id(model, kind, self.prefix + name)
            if found < 0:
                raise SystemExit(f'the model has no {name!r} for duck {index}')
            return found
        self.actuators = []
        self.to_wire = []
        for wire_index, name in enumerate(JOINT_NAMES):
            found = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, self.prefix + name)
            if found >= 0:
                self.actuators.append(found)
                self.to_wire.append(wire_index)
        if not self.actuators:
            raise SystemExit(f'no actuated joints for duck {index} (prefix {self.prefix!r})')
        self.qpos_adr = np.array([model.jnt_qposadr[model.actuator_trnid[a, 0]] for a in self.actuators])
        self.qvel_adr = np.array([model.jnt_dofadr[model.actuator_trnid[a, 0]] for a in self.actuators])
        self.camera: Camera | None = None
        self.trunk = int(model.jnt_qposadr[ident(mujoco.mjtObj.mjOBJ_JOINT, 'trunk_base_freejoint')])
        self.trunk_dof = int(model.jnt_dofadr[ident(mujoco.mjtObj.mjOBJ_JOINT, 'trunk_base_freejoint')])
        self.actuator_slice = np.array(self.actuators)
        self._gain = model.actuator_gainprm[self.actuator_slice, 0].copy()
        self._bias = model.actuator_biasprm[self.actuator_slice].copy()
        self.imu_sites = {n: ident(mujoco.mjtObj.mjOBJ_SITE, n) for n in ['body_imu', 'head_imu']}
        self.released = limp
        self.torque_on = not limp
        self.kp = kp
        self.held = None

    def place(self, pose: dict[str, float] | None, trunk_z: float, offset_y: float) -> None:
        data = self.world.data
        data.qpos[self.trunk + 0] = 0.0
        data.qpos[self.trunk + 1] = offset_y
        data.qpos[self.trunk + 2] = trunk_z
        data.qpos[self.trunk + 3:self.trunk + 7] = [1.0, 0.0, 0.0, 0.0]
        data.qvel[self.trunk_dof:self.trunk_dof + 6] = 0.0
        for slot, wire_index in enumerate(self.to_wire):
            name = JOINT_NAMES[wire_index]
            value = HOME_POSE[wire_index] if pose is None else pose.get(name, HOME_POSE[wire_index])
            data.qpos[self.qpos_adr[slot]] = value
            data.qvel[self.qvel_adr[slot]] = 0.0
        data.ctrl[self.actuator_slice] = data.qpos[self.qpos_adr]
        jaw = mujoco.mj_name2id(self.world.model, mujoco.mjtObj.mjOBJ_JOINT, self.prefix + 'passive_jaw')
        if jaw >= 0:
            motor = data.qpos[self.qpos_adr[self.to_wire.index(MOUTH_INDEX)]]
            data.qpos[self.world.model.jnt_qposadr[jaw]] = np.polynomial.polynomial.polyval(motor, CONTRACT['mouth_linkage']['motor_to_jaw_polynomial'])
        self._apply_torque()
        self.remember()

    def remember(self) -> None:
        data = self.world.data
        self.held = (data.qpos[self.trunk:self.trunk + 7].copy(), data.qpos[self.qpos_adr].copy())

    def restore(self) -> None:
        if self.held is None:
            return
        trunk, joints = self.held
        data = self.world.data
        data.qpos[self.trunk:self.trunk + 7] = trunk
        data.qpos[self.qpos_adr] = joints
        data.qvel[self.trunk_dof:self.trunk_dof + 6] = 0.0
        data.qvel[self.qvel_adr] = 0.0

    def sensors(self) -> dict:
        with self.world.lock:
            data, model = (self.world.data, self.world.model)

            def imu(name):
                quat = data.sensor(name + '_quat').data.copy()
                return {'gyro': data.sensor(name + '_gyro').data.tolist(), 'gravity': gravity_in_trunk(quat).tolist(), 'quat': quat.tolist(), 'accel': data.sensor(name + '_accel').data.tolist()}
            wire_pos = [0.0] * len(JOINT_NAMES)
            wire_vel = [0.0] * len(JOINT_NAMES)
            for slot, index in enumerate(self.to_wire):
                wire_pos[index] = float(data.qpos[self.qpos_adr[slot]])
                wire_vel[index] = float(data.qvel[self.qvel_adr[slot]])
            return {'positions': wire_pos, 'velocities': wire_vel, 'currents_ma': [0.0] * len(JOINT_NAMES), 'current_status': 'not modelled; zero is not a measurement', 'sim_time': float(data.time), 'session_id': self.world.session_id, 'epoch': self.world.epoch, 'trunk': data.qpos[self.trunk:self.trunk + 3].tolist(), 'trunk_z': float(data.qpos[self.trunk + 2]), 'imu': imu(self.prefix + 'body_imu'), 'head_imu': imu(self.prefix + 'head_imu')}

    def reset(self, name: str='stand') -> None:
        with self.world.lock:
            key = mujoco.mj_name2id(self.world.model, mujoco.mjtObj.mjOBJ_KEY, name)
            if key < 0:
                raise ValueError(f'unknown pose {name!r}')
            mujoco.mj_resetDataKeyframe(self.world.model, self.world.data, key)
            self.world.epoch += 1
            self.torque_on = False
            self.released = False
            self._apply_torque()
            self.remember()
            mujoco.mj_forward(self.world.model, self.world.data)

    def slow_sensors(self) -> dict:
        return {'volts': NOMINAL_VOLTS, 'temps_c': [NOMINAL_TEMP_C] * len(JOINT_NAMES), 'voltage_kind': 'regulated servo rail', 'temperature_status': 'placeholder, not thermal simulation'}

    def depth(self) -> dict:
        with self.world.lock:
            values = [float(self.world.data.sensor(self.prefix + f'tof_{row}_{col}').data[0]) for row in range(8) for col in range(8)]
        valid = [0 <= v <= 4 for v in values]
        return {'rows': 8, 'cols': 8, 'distance_mm': [round(v * 1000) if ok else 0 for v, ok in zip(values, valid)], 'status': [5 if ok else 255 for ok in valid], 'model': 'ideal rangefinder, no calibrated noise'}

    def set_targets(self, wire_targets: list[float]) -> None:
        if len(wire_targets) != len(JOINT_NAMES):
            raise ValueError(f'expected {len(JOINT_NAMES)} targets, got {len(wire_targets)}')
        for value, joint in zip(wire_targets, CONTRACT['joints']):
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError('targets must be finite numbers')
            lo, hi = joint['limits_rad']
            if value < lo - 1e-07 or value > hi + 1e-07:
                raise ValueError(f"target outside {joint['name']} study limits")
        with self.world.lock:
            self.world.data.ctrl[self.actuator_slice] = [wire_targets[i] for i in self.to_wire]

    def set_gain(self, kp: int) -> None:
        if not 0 <= kp <= 254:
            raise ValueError('gain must be in 0..254')
        with self.world.lock:
            self.kp = float(kp)
            self._apply_torque()

    def set_torque(self, on: bool) -> None:
        with self.world.lock:
            self.torque_on = bool(on)
            if on:
                self.released = True
                self.world.data.ctrl[self.actuator_slice] = self.world.data.qpos[self.qpos_adr]
            self._apply_torque()

    def _apply_torque(self) -> None:
        scale = self.kp / 32.0 if self.torque_on else 0.0
        model = self.world.model
        model.actuator_gainprm[self.actuator_slice, 0] = self._gain * scale
        model.actuator_biasprm[self.actuator_slice] = self._bias * scale

class Handler(socketserver.StreamRequestHandler):

    def handle(self) -> None:
        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.connection.settimeout(2.0)
        self.ready = False
        body: Body = self.server.body
        if not body.world.client_lock.acquire(blocking=False):
            self.wfile.write(b'{"error":"one controlling client is already connected"}\n')
            self.wfile.flush()
            return
        try:
            while (raw := self.rfile.readline(65537)):
                if len(raw) > 65536:
                    break
                try:
                    request = json.loads(raw)
                    answer = self.dispatch(body, request)
                except (ValueError, KeyError, TypeError) as error:
                    answer = {'error': str(error)}
                self.wfile.write((json.dumps(answer, allow_nan=False) + '\n').encode())
                self.wfile.flush()
        except (OSError, TimeoutError):
            pass
        finally:
            body.set_torque(False)
            body.world.client_lock.release()

    def dispatch(self, body: Body, request: dict) -> dict:
        with body.world.lock:
            if request.get('op') != 'hello':
                if request.get('session_id', body.world.session_id) != body.world.session_id:
                    raise ValueError('simulation session changed; reconnect required')
                if request.get('epoch', body.world.epoch) != body.world.epoch:
                    raise ValueError('simulation reset; reconnect required')
            return self._dispatch(body, request)

    def _dispatch(self, body: Body, request: dict) -> dict:
        op = request.get('op')
        if op == 'hello':
            for key, value in [('protocol', PROTOCOL), ('model_id', CONTRACT['model_id']), ('contract_version', CONTRACT['contract_version'])]:
                if request.get(key) != value:
                    raise ValueError(f'incompatible {key}; expected {value!r}')
            if request.get('contract_sha256', CONTRACT_SHA256) != CONTRACT_SHA256:
                raise ValueError('incompatible CAD joint contract hash')
            self.ready = True
            return {'protocol': PROTOCOL, 'mujoco_version': mujoco.__version__, 'model_id': CONTRACT['model_id'], 'contract_version': CONTRACT['contract_version'], 'cad_revision': CONTRACT['cad_revision'], 'contract_sha256': CONTRACT_SHA256, 'joint_names': list(JOINT_NAMES), 'policy_action_joints': CONTRACT['policy_action_joints'], 'servo_volts': 5.0, 'session_id': body.world.session_id, 'epoch': body.world.epoch}
        if not getattr(self, 'ready', False):
            raise ValueError('hello handshake required')
        if op == 'read':
            return body.sensors()
        if op == 'slow':
            return body.slow_sensors()
        if op == 'tof':
            return body.depth()
        if op == 'write':
            body.set_targets(request['targets'])
        elif op == 'gain':
            body.set_gain(int(request['kp']))
        elif op == 'torque':
            if not isinstance(request['on'], bool):
                raise ValueError('on must be boolean')
            body.set_torque(request['on'])
        elif op == 'reset':
            body.reset(request.get('pose', 'stand'))
            return {'session_id': body.world.session_id, 'epoch': body.world.epoch}
        else:
            raise ValueError(f'unknown op {op!r}')
        return {}

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

def run(world: World, headless: bool) -> None:
    viewer = None
    if not headless:
        try:
            import mujoco.viewer
            viewer = mujoco.viewer.launch_passive(world.model, world.data, show_left_ui=False, show_right_ui=False)
        except Exception as error:
            print(f'== no viewer ({error}); running headless', flush=True)
    dt = world.model.opt.timestep
    batch = max(1, round(0.02 / dt))
    period = batch * dt
    passes_per_frame = max(1, round(1.0 / 30.0 / period))
    eyes = [b for b in world.bodies if b.camera is not None]
    passes_per_eye = max(1, round(1.0 / CAMERA_FPS / period))
    step = 0
    next_step = time.perf_counter()
    behind = 0
    try:
        while True:
            world.step(batch)
            if viewer is not None and (not viewer.is_running()):
                break
            next_step += period
            slack = next_step - time.perf_counter()
            if slack > 0.002:
                time.sleep(slack)
            elif slack < -0.25:
                behind += 1
                print(f'== behind real time by {-slack:.2f}s (x{behind}) , fewer ducks, or --headless', flush=True)
                next_step = time.perf_counter()
            step += 1
            if viewer is not None and step % passes_per_frame == 0:
                viewer.sync()
            if eyes and step % passes_per_eye == 0:
                for body in eyes:
                    if body.camera is not None:
                        body.camera.render(world)
    except KeyboardInterrupt:
        pass
    finally:
        if viewer is not None:
            viewer.close()

def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or '').split('\n')[0])
    parser.add_argument('--scene', type=Path, default=DEFAULT_SCENE)
    parser.add_argument('--ducks', type=int, default=1, help='how many, sharing one world')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=7801, help="the first duck's port; +1 each")
    parser.add_argument('--headless', action='store_true', help='no viewer window')
    parser.add_argument('--cameras', default='', help='which ducks render a head camera, by letter , `a`, `a,c`, or `all`. Opt in, because a rendered frame costs 12 ms and four cameras is most of a core; four ducks without them is nothing. Each becomes a frame port at --frame-port + its index')
    parser.add_argument('--frame-port', type=int, default=7901, help="the first camera's port")
    parser.add_argument('--camera-fps', type=int, default=CAMERA_FPS)
    parser.add_argument('--limp', action='store_true', help="start with no torque, so a duck collapses where it stands , a robot found on the floor, which is what `robotd`'s seated-boot path is for")
    parser.add_argument('--keyframe', default='stand', help="where to start. SIT is a duck folded on the floor, which is stable while it waits and which the standing policy rises from on its own. HOME is infer_policy.py's placement , home pose, trunk 0.125 m, upright , and STAND and FOLD are the scene's other poses")
    args = parser.parse_args()
    if not args.scene.exists():
        raise SystemExit(f'no scene at {args.scene}. Available:\n  ' + '\n  '.join(sorted((p.name for p in SCENES.glob('scene*.xml')))))
    if args.ducks != 1:
        raise SystemExit('R20 study supports one duck per process')
    world = World(args.scene, args.ducks)
    pose, trunk_z = pose_table(args.scene, args.keyframe)
    wanted = set()
    if args.cameras.strip() == 'all':
        wanted = set(range(args.ducks))
    elif args.cameras.strip():
        wanted = {ord(c.strip()) - ord('a') for c in args.cameras.split(',') if c.strip()}
    servers = []
    for index in range(args.ducks):
        body = Body(world, index, limp=args.limp)
        body.place(pose, trunk_z, offset_y=index * SPACING)
        world.bodies.append(body)
        if args.keyframe != 'HOME':
            body.reset(args.keyframe)
        mujoco.mj_forward(world.model, world.data)
        server = Server((args.host, args.port + index), Handler)
        server.body = body
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        if index in wanted:
            body.camera = Camera(world.model, f'{body.prefix}head_camera')
            frames = FrameServer((args.host, args.frame_port + index), FrameHandler)
            frames.camera = body.camera
            frames.fps = args.camera_fps
            threading.Thread(target=frames.serve_forever, daemon=True).start()
            servers.append(frames)
    print(f'== {args.scene.name}: {args.ducks} duck(s), starting at {args.keyframe}', flush=True)
    for index in range(args.ducks):
        eye = f' · camera on {args.host}:{args.frame_port + index}' if index in wanted else ''
        print(f'==   duck {index}: robotd --sim {args.host}:{args.port + index} --no-policy --socket /tmp/indieduck-r25.sock{eye}', flush=True)
    run(world, headless=args.headless)
if __name__ == '__main__':
    main()
