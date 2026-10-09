import * as THREE from 'three';
import { toCreasedNormals } from 'three/addons/utils/BufferGeometryUtils.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import loadMujoco from '@mujoco/mujoco';
import wasmUrl from '@mujoco/mujoco/mujoco.wasm?url';

const json = async url => { const r = await fetch(url); if (!r.ok) throw new Error(`${url}: ${r.status}`); return r.json(); };
const matrix = new THREE.Matrix4();
const rotation = (out, values, offset) => {
  matrix.set(values[offset], values[offset + 1], values[offset + 2], 0,
    values[offset + 3], values[offset + 4], values[offset + 5], 0,
    values[offset + 6], values[offset + 7], values[offset + 8], 0, 0, 0, 0, 1);
  out.setFromRotationMatrix(matrix);
};

export class DuckEngine {
  constructor(host, onStats, onSelect, onError) {
    this.host = host; this.onStats = onStats; this.onSelect = onSelect; this.onError = onError;
    this.running = false; this.mode = 'pose'; this.showContacts = false; this.collisions = false;
    this.scene = new THREE.Scene(); this.scene.background = new THREE.Color('#f4f5f6');
    this.renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true; this.renderer.shadowMap.type = THREE.PCFShadowMap;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping; this.renderer.toneMappingExposure = 1;
    host.appendChild(this.renderer.domElement);
    this.camera = new THREE.PerspectiveCamera(34, 1, 0.005, 20); this.camera.up.set(0, 0, 1);
    this.camera.position.set(.54, .48, .36);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.target.set(0, 0, .145); this.controls.enableDamping = true;
    this.controls.minDistance = .15; this.controls.maxDistance = 2;
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x8c919b, 2.4));
    const key = new THREE.DirectionalLight(0xffffff, 3.5); key.position.set(.7, .4, 1);
    key.castShadow = true; key.shadow.mapSize.set(2048, 2048);
    Object.assign(key.shadow.camera, { left: -.4, right: .4, top: .4, bottom: -.4, near: .05, far: 3 });
    key.shadow.bias = -.0001; this.scene.add(key);
    const fill = new THREE.DirectionalLight(0xd8e8ff, 1.1); fill.position.set(-1, -1, .7); this.scene.add(fill);
    const grid = new THREE.GridHelper(1.5, 30, 0xc5c9cd, 0xe2e4e7); grid.rotation.x = Math.PI / 2; grid.position.z = -.0005; this.scene.add(grid);
    this.contactMarkers = new THREE.InstancedMesh(new THREE.SphereGeometry(.0018, 6, 6), new THREE.MeshBasicMaterial({ color: '#c44c14', depthTest: false }), 256);
    this.contactMarkers.count = 0; this.contactMarkers.renderOrder = 5; this.scene.add(this.contactMarkers);
    this.pointer = new THREE.Vector2(); this.ray = new THREE.Raycaster();
    this.pointerDown = e => { this.down = [e.clientX, e.clientY]; };
    this.pointerUp = e => {
      if (!this.down || Math.hypot(e.clientX - this.down[0], e.clientY - this.down[1]) > 5) return;
      const box = host.getBoundingClientRect(); this.pointer.set((e.clientX - box.left) / box.width * 2 - 1, 1 - (e.clientY - box.top) / box.height * 2);
      this.ray.setFromCamera(this.pointer, this.camera);
      const hit = this.ray.intersectObjects((this.meshes || []).filter(m => m.visible && m.userData.type !== 0))[0];
      this.select(hit?.object || null);
    };
    host.addEventListener('pointerdown', this.pointerDown); host.addEventListener('pointerup', this.pointerUp);
    this.resize = new ResizeObserver(() => { const w = host.clientWidth, h = host.clientHeight; if (!w || !h) return; this.camera.aspect = w / h; this.camera.updateProjectionMatrix(); this.renderer.setSize(w, h); if (!this.userViewed) this.fitView(); });
    this.resize.observe(host);
    this.sensorCamera = new THREE.PerspectiveCamera(49, 4 / 3, .005, 10);
    this.lastTime = performance.now(); this.lastStats = 0; this.accumulator = 0; this.frameCount = 0; this.stepMs = [];
    this.loop = this.loop.bind(this); this.frameId = requestAnimationFrame(this.loop);
  }
  async init(skates = false) {
    this.onStats({ status: 'Loading CAD and MuJoCo…' });
    const [mj, contract, poses, inventory, visualParts] = await Promise.all([
      loadMujoco({ locateFile: p => p.endsWith('.wasm') ? wasmUrl : p }), json('model/contract.json'), json('model/poses.json'), json('model/files.json'), json('model/visual-parts.json')
    ]);
    this.mj = mj; this.contract = contract; this.poses = poses; this.visualParts = visualParts.parts;
    const files = Array.isArray(inventory) ? inventory : inventory.files;
    await Promise.all(files.map(async entry => {
      const name = typeof entry === 'string' ? entry : entry.path;
      if (!name || name.startsWith('/') || name.includes('..')) throw new Error('Invalid model inventory path');
      const response = await fetch(`model/${name}`); if (!response.ok) throw new Error(`Missing model asset ${name}`);
      const path = `/indieduck/${name}`; mj.FS.mkdirTree(path.slice(0, path.lastIndexOf('/')));
      mj.FS.writeFile(path, new Uint8Array(await response.arrayBuffer()));
    }));
    if (!this.disposed) this.load(skates); return { contract, poses };
  }
  id(kind, name) { return this.mj.mj_name2id(this.model, kind, name); }
  load(skates) {
    this.running = false; this.skates = skates;
    this.clearModel();
    this.model = this.mj.MjModel.from_xml_path(`/indieduck/${skates ? 'scene_skates.xml' : 'scene.xml'}`);
    this.data = new this.mj.MjData(this.model);
    this.rootQadr = this.model.jnt_qposadr[this.id(3, 'trunk_base_freejoint')];
    this.joints = this.contract.joints.map(j => {
      const id = this.id(3, j.name), aid = Array.from(this.model.actuator_trnid).findIndex((x, i) => i % 2 === 0 && x === id) / 2;
      if (id < 0) throw new Error(`Contract joint missing: ${j.name}`);
      return { ...j, id, qadr: this.model.jnt_qposadr[id], actuator: aid, limits: Array.from(this.model.jnt_range.slice(id * 2, id * 2 + 2)) };
    });
    this.camId = this.id(7, 'head_camera'); this.meshes = []; this.geometries = new Map();
    for (let i = 0; i < this.model.ngeom; i++) {
      const type = this.model.geom_type[i], group = this.model.geom_group[i], size = this.model.geom_size.slice(i * 3, i * 3 + 3);
      let geometry;
      if (type === 7) {
        const mid = this.model.geom_dataid[i];
        if (!this.geometries.has(mid)) {
          const va = this.model.mesh_vertadr[mid] * 3, vn = this.model.mesh_vertnum[mid] * 3;
          const fa = this.model.mesh_faceadr[mid] * 3, fn = this.model.mesh_facenum[mid] * 3;
          const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(this.model.mesh_vert.slice(va, va + vn)), 3));
          g.setIndex(new THREE.BufferAttribute(new Uint32Array(this.model.mesh_face.slice(fa, fa + fn)), 1)); g.computeVertexNormals(); this.geometries.set(mid, toCreasedNormals(g, Math.PI / 5)); g.dispose();
        }
        geometry = this.geometries.get(mid);
      } else if (type === 0) { geometry = new THREE.PlaneGeometry(3, 3); }
      else if (type === 2 || type === 4) { geometry = new THREE.SphereGeometry(1, 24, 16); geometry.scale(size[0], type === 2 ? size[0] : size[1], type === 2 ? size[0] : size[2]); }
      else if (type === 6) { geometry = new THREE.BoxGeometry(size[0] * 2, size[1] * 2, size[2] * 2); }
      else if (type === 5 || type === 3) { geometry = type === 5 ? new THREE.CylinderGeometry(size[0], size[0], size[1] * 2, 24) : new THREE.CapsuleGeometry(size[0], size[1] * 2, 4, 12); geometry.rotateX(Math.PI / 2); }
      else continue;
      const c = this.model.geom_rgba.slice(i * 4, i * 4 + 4);
      const name = this.mj.mj_id2name(this.model, 5, i) || `Geometry ${i}`;
      const body = this.mj.mj_id2name(this.model, 1, this.model.geom_bodyid[i]);
      const metadata = this.visualParts.find(p => name === p.name || name === p.name + '_visual' || name.endsWith('_' + p.name));
      const metal = /horn|bearing|pin|stud|retention/i.test(name);
      const material = new THREE.MeshStandardMaterial({ color: new THREE.Color().setRGB(c[0], c[1], c[2], THREE.SRGBColorSpace), roughness: metal ? .32 : .62, metalness: metal ? .65 : 0, transparent: group === 3 || c[3] < 1, opacity: group === 3 ? .24 : c[3], wireframe: group === 3 });
      if (type === 0) { material.color.set('#e9ebed'); material.roughness = 1; }
      const mesh = new THREE.Mesh(geometry, material); mesh.castShadow = type !== 0 && group !== 3; mesh.receiveShadow = true;
      mesh.userData = { id: i, name, body, type, group, material: metal ? 'Metal hardware envelope' : /sole|lip|edge/i.test(name) ? 'TPU 95A study' : /ref_|sensor|camera|pcb/i.test(name) ? 'Component envelope' : 'PLA fit-test study' };
      if (metadata) { mesh.userData.material = metadata.material; mesh.userData.mass_kg = metadata.mass_kg; mesh.userData.mass_status = metadata.mass_status; }
      mesh.visible = group !== 3 || this.collisions; this.meshes.push(mesh); this.scene.add(mesh);
    }
    this.setPose(this.firstPose()); this.onStats({ status: 'Ready', skates, jointList: this.joints });
  }
  poseList() { return Array.isArray(this.poses) ? this.poses : this.poses.poses; }
  firstPose() { const p = this.poseList(); return Array.isArray(p) ? p.find(x => /standing|stand/.test(x.id || x.name)) || p[0] : p.standing || Object.values(p)[0]; }
  setPose(pose) {
    if (typeof pose === 'string') { const ps = this.poseList(); pose = Array.isArray(ps) ? ps.find(p => (p.id || p.name) === pose) : ps[pose]; }
    if (!pose) return;
    this.running = false; this.accumulator = 0; this.currentPose = pose;
    this.mj.mj_resetData(this.model, this.data);
    const poseName = pose.id || pose.name;
    const keyId = poseName ? this.id(24, poseName) : -1;
    if (keyId >= 0) this.mj.mj_resetDataKeyframe(this.model, this.data, keyId);
    const base = pose.base_pose || pose.base || pose.base_qpos || (pose.base_position_m ? {position_m: pose.base_position_m, quaternion_wxyz: pose.base_quaternion_wxyz} : null);
    if (keyId < 0 && Array.isArray(base)) this.data.qpos.set(base, this.rootQadr);
    else if (keyId < 0 && base) { this.data.qpos.set(base.position_m || base.position || [0, 0, .143], this.rootQadr); this.data.qpos.set(base.quaternion_wxyz || base.quaternion || [1, 0, 0, 0], this.rootQadr + 3); }
    const angles = pose.joint_positions_rad || pose.joints_rad || pose.joint_angles_rad || pose.joints || {};
    for (const joint of this.joints) { const angle = angles[joint.name] ?? 0; this.data.qpos[joint.qadr] = angle; if (joint.actuator >= 0) this.data.ctrl[joint.actuator] = angle; }
    if (keyId < 0) this.updateMouth(angles.mouth || 0);
    const ball = this.id(3, 'ball_freejoint');
    if (ball >= 0 && pose.ball_pose_m_wxyz) this.data.qpos.set(pose.ball_pose_m_wxyz, this.model.jnt_qposadr[ball]);
    this.mj.mj_forward(this.model, this.data); this.updateTransforms();
    this.onStats({ running: false, pose, values: this.values(), time: 0 });
  }
  setJoint(name, angle) {
    const j = this.joints.find(x => x.name === name); if (!j) return;
    const a = THREE.MathUtils.clamp(angle, ...j.limits);
    if (j.actuator >= 0) this.data.ctrl[j.actuator] = a;
    if (this.mode === 'pose') { this.data.qpos[j.qadr] = a; if (name === 'mouth') this.updateMouth(a); this.mj.mj_forward(this.model, this.data); }
    this.onStats({ values: this.values() });
  }
  updateMouth(motor) {
    // R20 jaw is the physical mouth joint, without a passive linkage.
  }

  setMode(mode) {
    this.running = false; this.accumulator = 0; this.mode = mode; this.data.qvel.fill(0);
    this.mj.mj_forward(this.model, this.data); this.updateTransforms();
    this.onStats({ running: false, values: this.values(), sensors: this.sensors() });
  }
  setRunning(value) { this.running = value && this.mode === 'physics'; this.lastTime = performance.now(); this.accumulator = 0; this.onStats({ running: this.running }); }
  setCollisions(value) { this.collisions = value; this.meshes?.forEach(m => { if (m.userData.group === 3) m.visible = value; }); }
  select(mesh) { if (this.selected) this.selected.material.emissive.set(0x000000); this.selected = mesh; if (mesh) mesh.material.emissive.set(0x323013); this.onSelect(mesh?.userData || null); }
  fitView() { const dir = new THREE.Vector3(.54, .48, .215).normalize(); const distance = Math.max(.70, .46 / this.camera.aspect); this.camera.position.copy(this.controls.target).addScaledVector(dir, distance); this.controls.update(); }
  view(name) {
    this.userViewed = true;
    const p = { front: [.7, 0, .145], side: [0, -.7, .145], back: [-.7, 0, .145], top: [.001, 0, .9], iso: [.54, .48, .36] }[name];
    this.camera.position.set(...p); this.controls.target.set(0, 0, .145); this.controls.update();
  }
  setBall(x, y, z) {
    const id = this.id(3, 'ball_freejoint');
    if (id < 0 || this.mode !== 'pose') return;
    const qa = this.model.jnt_qposadr[id], va = this.model.jnt_dofadr[id];
    this.data.qpos.set([x, y, Math.max(.0201, z), 1, 0, 0, 0], qa);
    this.data.qvel.fill(0, va, va + 6); this.mj.mj_forward(this.model, this.data);
  }
  values() { return Object.fromEntries(this.joints.map(j => [j.name, this.data.qpos[j.qadr]])); }
  snapshot() {
    const ball = this.id(3, 'ball_freejoint'), ballQadr = ball >= 0 ? this.model.jnt_qposadr[ball] : null;
    return { schema_version: 1, scope: 'robot pose and test-ball placement; velocities and controller history are not included', cad_revision: this.contract.cad_revision, cad_manifest_sha256: this.contract.cad_manifest_sha256, model_id: this.contract.model_id, mode: this.mode, simulated_time_s: this.data.time, skates: this.skates, base_pose: Array.from(this.data.qpos.slice(this.rootQadr, this.rootQadr + 7)), joints_rad: this.values(), ball_pose_m_wxyz: ballQadr == null ? null : Array.from(this.data.qpos.slice(ballQadr, ballQadr + 7)), status: 'local study, not trained behaviour' };
  }
  updateTransforms() {
    for (const mesh of this.meshes) { const i = mesh.userData.id; mesh.position.fromArray(this.data.geom_xpos, i * 3); rotation(mesh.quaternion, this.data.geom_xmat, i * 9); }
  }
  sensors() {
    const values = {}; for (let i = 0; i < this.model.nsensor; i++) { const name = this.mj.mj_id2name(this.model, 20, i); values[name] = Array.from(this.data.sensordata.slice(this.model.sensor_adr[i], this.model.sensor_adr[i] + this.model.sensor_dim[i])); }
    return values;
  }
  attachCamera(host) {
    this.cameraRenderer?.dispose(); this.cameraRenderer?.domElement.remove();
    this.cameraRenderer = new THREE.WebGLRenderer({ antialias: true }); this.cameraRenderer.setSize(320, 240); this.cameraRenderer.outputColorSpace = THREE.SRGBColorSpace; this.cameraRenderer.toneMapping = THREE.ACESFilmicToneMapping; host.appendChild(this.cameraRenderer.domElement);
  }
  updateContacts() {
    this.contactMarkers.count = 0; if (!this.showContacts || !this.data.ncon) return;
    const contacts = this.data.contact;
    try { const n = Math.min(contacts.size(), 256); for (let i = 0; i < n; i++) { const c = contacts.get(i); try { matrix.makeTranslation(c.pos[0], c.pos[1], c.pos[2]); this.contactMarkers.setMatrixAt(i, matrix); } finally { c?.delete(); } } this.contactMarkers.count = n; this.contactMarkers.instanceMatrix.needsUpdate = true; } finally { contacts.delete(); }
  }
  loop(now) {
    this.frameId = requestAnimationFrame(this.loop);
    const delta = Math.min((now - this.lastTime) / 1000, .04); this.lastTime = now;
    if (document.hidden || !this.data) return;
    try {
      if (this.running && this.mode === 'physics') {
        this.accumulator += delta; const t = performance.now(); let steps = 0;
        while (this.accumulator >= .005 && steps < 8) { this.mj.mj_step(this.model, this.data); this.accumulator -= .005; steps++; }
        if (steps) this.stepMs.push((performance.now() - t) / steps); if (this.stepMs.length > 400) this.stepMs.splice(0, 200);
        if (!this.data.qpos.every(Number.isFinite) || !this.data.qvel.every(Number.isFinite)) throw new Error('Physics produced a non-finite state. Reset the study.');
      }
      this.updateTransforms(); this.updateContacts(); this.controls.update(); this.renderer.render(this.scene, this.camera); this.frameCount++;
      if (now - this.lastStats > 200) {
        if (this.camId >= 0 && this.cameraRenderer?.domElement.isConnected) { this.sensorCamera.position.fromArray(this.data.cam_xpos, this.camId * 3); rotation(this.sensorCamera.quaternion, this.data.cam_xmat, this.camId * 9); this.sensorCamera.fov = this.model.cam_fovy[this.camId]; this.sensorCamera.updateProjectionMatrix(); this.contactMarkers.visible = false; const proxies = this.meshes.filter(m => m.userData.group === 3 && m.visible); proxies.forEach(m => { m.visible = false; }); this.cameraRenderer.render(this.scene, this.sensorCamera); proxies.forEach(m => { m.visible = true; }); this.contactMarkers.visible = true; }
        this.onStats({ time: this.data.time, contacts: this.data.ncon, values: this.values(), sensors: this.sensors(), fps: this.frameCount / ((now - this.lastStats) / 1000), stepMs: this.stepMs.length ? this.stepMs.reduce((a,b) => a+b, 0) / this.stepMs.length : 0 });
        this.frameCount = 0; this.lastStats = now;
      }
    } catch (error) { this.running = false; this.onError(String(error)); cancelAnimationFrame(this.frameId); }
  }
  clearModel() {
    this.select(null); for (const mesh of this.meshes || []) { this.scene.remove(mesh); mesh.material.dispose(); }
    const geometries = new Set((this.meshes || []).map(m => m.geometry)); geometries.forEach(g => g.dispose());
    this.data?.delete(); this.model?.delete(); this.data = null; this.model = null;
  }
  dispose() {
    this.disposed = true;
    cancelAnimationFrame(this.frameId); this.resize.disconnect(); this.controls.dispose(); this.clearModel();
    this.host.removeEventListener('pointerdown', this.pointerDown); this.host.removeEventListener('pointerup', this.pointerUp);
    this.renderer.dispose(); this.renderer.domElement.remove(); this.cameraRenderer?.dispose(); this.cameraRenderer?.domElement.remove();
    this.contactMarkers.geometry.dispose(); this.contactMarkers.material.dispose();
  }
}
