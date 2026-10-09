import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import * as THREE from 'three';
import loadMujoco from '@mujoco/mujoco';

// Evaluate the real engine methods without instantiating its browser/WebGL constructor.
// Vite's wasm URL import is replaced by the native Node package loader for this test.
const source = fs.readFileSync(new URL('../src/engine.js', import.meta.url), 'utf8')
  .replace(/^import .*;\n/gm, '').replace('export class DuckEngine', 'class DuckEngine');
const DuckEngine = new Function('THREE', `${source}\nreturn DuckEngine;`)(THREE);
const directory = path.resolve(import.meta.dirname, '../public/model');
const mj = await loadMujoco();
for (const name of JSON.parse(fs.readFileSync(path.join(directory, 'files.json'))).files) {
  const target = `/indieduck/${name}`;
  mj.FS.mkdirTree(path.dirname(target));
  mj.FS.writeFile(target, fs.readFileSync(path.join(directory, name)));
}

test('switching study mode clears velocity and refreshes actual WASM sensor state', () => {
  const engine = Object.create(DuckEngine.prototype);
  engine.mj = mj;
  engine.model = mj.MjModel.from_xml_path('/indieduck/scene.xml');
  engine.data = new mj.MjData(engine.model);
  const contract = JSON.parse(fs.readFileSync(path.join(directory, 'contract.json')));
  engine.joints = contract.joints.map(joint => ({ ...joint,
    qadr: engine.model.jnt_qposadr[engine.id(3, joint.name)] }));
  let published, transforms = 0;
  engine.onStats = value => { published = value; };
  engine.updateTransforms = () => { transforms++; };
  try {
    for (const mode of ['pose', 'physics']) {
      mj.mj_resetDataKeyframe(engine.model, engine.data, engine.id(24, 'stand'));
      engine.data.qvel[engine.model.jnt_dofadr[engine.id(3, 'head_pitch')]] = 2;
      mj.mj_forward(engine.model, engine.data);
      assert.ok(Math.abs(engine.sensors().head_imu_gyro[1]) > 1);
      const pose = Array.from(engine.data.qpos);
      engine.running = true; engine.accumulator = .04;
      engine.setMode(mode);
      assert.equal(engine.mode, mode);
      assert.equal(engine.running, false);
      assert.equal(engine.accumulator, 0);
      assert.ok(engine.data.qvel.every(value => value === 0));
      assert.deepEqual(Array.from(engine.data.qpos), pose);
      assert.equal(published.running, false);
      for (const name of ['body_imu_gyro', 'head_imu_gyro']) {
        assert.ok(engine.sensors()[name].every(value => Math.abs(value) < 1e-12), name);
        assert.deepEqual(published.sensors[name], engine.sensors()[name]);
      }
      assert.deepEqual(published.values, engine.values());
    }
    assert.equal(transforms, 2);
  } finally {
    engine.data.delete(); engine.model.delete();
  }
});

test('exported named pose replays root, joints, ball and direct-drive jaw', () => {
  const engine = Object.create(DuckEngine.prototype);
  engine.mj = mj;
  engine.model = mj.MjModel.from_xml_path('/indieduck/scene.xml');
  engine.data = new mj.MjData(engine.model);
  engine.contract = JSON.parse(fs.readFileSync(path.join(directory, 'contract.json')));
  engine.poses = JSON.parse(fs.readFileSync(path.join(directory, 'poses.json')));
  engine.rootQadr = engine.model.jnt_qposadr[engine.id(3, 'trunk_base_freejoint')];
  engine.joints = engine.contract.joints.map(joint => ({ ...joint,
    qadr: engine.model.jnt_qposadr[engine.id(3, joint.name)],
    actuator: engine.id(19, joint.name), limits: joint.limits_rad }));
  engine.onStats = () => {}; engine.updateTransforms = () => {};
  engine.mode = 'pose'; engine.skates = false;
  try {
    engine.setPose('jaw_30');
    engine.data.qpos.set([.01, -.02, .15, Math.cos(.1), 0, 0, Math.sin(.1)], engine.rootQadr);
    engine.setJoint('head_roll', .05);
    engine.setBall(.12, -.02, .0201);
    const jawAddress = engine.model.jnt_qposadr[engine.id(3, 'mouth')];
    const jaw = engine.data.qpos[jawAddress];
    const snapshot = JSON.parse(JSON.stringify(engine.snapshot()));
    assert.equal(snapshot.id, undefined);
    assert.match(snapshot.scope, /velocities.*not included/);
    engine.setPose('stand');
    engine.setPose(snapshot);
    assert.deepEqual(Array.from(engine.data.qpos.slice(engine.rootQadr, engine.rootQadr + 7)), snapshot.base_pose);
    assert.deepEqual(engine.values(), snapshot.joints_rad);
    const ballAddress = engine.model.jnt_qposadr[engine.id(3, 'ball_freejoint')];
    assert.deepEqual(Array.from(engine.data.qpos.slice(ballAddress, ballAddress + 7)), snapshot.ball_pose_m_wxyz);
    const tolerance = engine.contract.mouth_linkage.max_fit_error_rad + 1e-9;
    assert.ok(Math.abs(engine.data.qpos[jawAddress] - jaw) <= tolerance);
    assert.ok(engine.data.qvel.every(value => value === 0));
  } finally {
    engine.data.delete(); engine.model.delete();
  }
});
