import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import loadMujoco from '@mujoco/mujoco';
const root = path.resolve(import.meta.dirname, '../public/model');
const mj = await loadMujoco();
const inventory = JSON.parse(fs.readFileSync(path.join(root, 'files.json'))).files;
for (const name of inventory) {
  const virtual = `/indieduck/${name}`;
  mj.FS.mkdirTree(path.dirname(virtual)); mj.FS.writeFile(virtual, fs.readFileSync(path.join(root, name)));
}
const fixturePath = path.resolve(import.meta.dirname, '../../src/mjlab_microduck/robot/indieduck/native-fixtures.json');
const fixtures = JSON.parse(fs.readFileSync(fixturePath));
const contract = JSON.parse(fs.readFileSync(path.join(root, 'contract.json')));
assert.equal(fixtures.cad_manifest_sha256, contract.cad_manifest_sha256, "native fixtures and browser CAD revision must match");
const results = [];
for (const scene of ['scene.xml', 'scene_skates.xml']) {
  test(`${scene}: WASM matches native MuJoCo for every pose and joint`, () => {
    const model = mj.MjModel.from_xml_path(`/indieduck/${scene}`), data = new mj.MjData(model);
    try {
      assert.equal(model.nu, 15); assert.equal(contract.policy_action_joints.length, 14); assert.equal(contract.policy_observation_size, 61);
      const rootJoint = mj.mj_name2id(model, 3, 'trunk_base_freejoint'); assert.ok(rootJoint >= 0);
      for (const fixture of fixtures.fixtures[scene]) {
        const key = mj.mj_name2id(model, 24, fixture.id); assert.ok(key >= 0, fixture.id);
        mj.mj_resetDataKeyframe(model, data, key); mj.mj_forward(model, data);
        let error = 0;
        for (let i = 0; i < fixture.qpos.length; i++) error = Math.max(error, Math.abs(fixture.qpos[i] - data.qpos[i]));
        assert.ok(error < 1e-7, `${fixture.id} qpos error ${error}`);
        for (const joint of contract.joints) {
          const id = mj.mj_name2id(model, 3, joint.name); assert.ok(id >= 0);
          assert.ok(model.jnt_range[id * 2] < model.jnt_range[id * 2 + 1]);
          assert.ok(Math.abs(model.jnt_range[id * 2] - joint.limits_rad[0]) < 1e-7);
          assert.ok(Math.abs(model.jnt_range[id * 2 + 1] - joint.limits_rad[1]) < 1e-7);
        }
        for (const [body, expected] of Object.entries(fixture.body_positions)) {
          const id = mj.mj_name2id(model, 1, body); assert.ok(id >= 0);
          for (let axis = 0; axis < 3; axis++) assert.ok(Math.abs(data.xpos[id * 3 + axis] - expected[axis]) < 1e-7, `${fixture.id}/${body}/${axis}`);
          const q = fixture.body_quaternions[body];
          for (let axis = 0; axis < 4; axis++) assert.ok(Math.abs(data.xquat[id * 4 + axis] - q[axis]) < 1e-7, `${fixture.id}/${body}/quaternion`);
        }
        data.ctrl.set(fixture.ctrl);
        const start = performance.now(); for (let step = 0; step < 200; step++) mj.mj_step(model, data);
        assert.ok(Array.from(data.qpos).every(Number.isFinite), fixture.id);
        assert.ok(Array.from(data.qvel).every(Number.isFinite), fixture.id);
        results.push({scene, pose: fixture.id, maximum_initial_qpos_error: error, simulated_seconds: data.time, milliseconds_for_200_steps: performance.now() - start, contacts: data.ncon});
      }
    } finally { data.delete(); model.delete(); }
  });
}
test.after(() => { fs.mkdirSync(path.resolve(import.meta.dirname, '../evidence'), { recursive: true }); fs.writeFileSync(path.resolve(import.meta.dirname, '../evidence/wasm-native-checks.json'), JSON.stringify({mujoco:'3.10.0', node:process.version, arch:process.arch, cad_manifest_sha256:contract.cad_manifest_sha256, results}, null, 2)); });
