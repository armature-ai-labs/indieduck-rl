// Scripted keyframe motions for previewing IndieDuck's joints within the Cyber Edition limits.
// Kinematic playback only: no physics, no balance. Joints are clamped to the model's joint ranges
// (the R25 contract limits) and any request beyond a limit is reported.

const D = Math.PI / 180;

export const MOTIONS = [
  { id: 'standup', label: 'Stand up', loop: false,
    note: 'From the CAD zero configuration into the standing pose.',
    keys: [{ pose: 'zero', t: 0.8 }, { pose: 'stand', t: 1.6 }, { pose: 'stand', t: 1.0 }] },
  { id: 'sit', label: 'Sit and stand', loop: true,
    note: 'The sit pose asks for 89 deg at each ankle; the Cyber Edition ankle stops at 78 deg, so it is clamped and shown in red.',
    keys: [{ pose: 'stand', t: 0.8 }, { pose: 'sit_transition', t: 1.2 }, { pose: 'sit', t: 1.2 }, { pose: 'sit', t: 1.2 }, { pose: 'sit_transition', t: 1.2 }, { pose: 'stand', t: 1.2 }] },
  { id: 'talk', label: 'Talk', loop: true,
    note: 'Jaw opening and closing at speaking pace, with small head movements. In the Cyber Edition CAD the head rims block the jaw surrounds, so the real jaw cannot open yet (open design item); watch the rims.',
    keys: [0, 18, 6, 24, 4, 14, 26, 8, 0].map((m, i) => ({ pose: 'stand', t: 0.22, joints: { mouth: m * D, head_pitch: (i % 2 ? 4 : -2) * D, head_yaw: (i % 3 - 1) * 6 * D } })) },
  { id: 'run', label: 'Gait cycle', loop: true, tempo: 2.2,
    note: 'Alternating stepping poses at running tempo, in place. A real run needs a trained policy and physics; this checks that the leg joints move through the gait within their limits.',
    keys: [{ pose: 'walk_left', t: 0.35 }, { pose: 'stand', t: 0.2 }, { pose: 'walk_right', t: 0.35 }, { pose: 'stand', t: 0.2 }] },
  { id: 'getup', label: 'Fall and get up', loop: true,
    note: 'Falls onto its back, tucks and rises through sitting to standing. Scripted poses, not a balancing controller; the tuck asks for 40 deg of neck and 89 deg of ankle, beyond the Cyber Edition limits.',
    keys: [{ pose: 'stand', t: 1.0 }, { pose: 'getup_back', t: 0.7 }, { pose: 'getup_back', t: 1.0 }, { pose: 'getup_tuck', t: 1.4 }, { pose: 'getup_tuck', t: 0.6 }, { pose: 'sit', t: 1.2 }, { pose: 'sit_transition', t: 1.0 }, { pose: 'stand', t: 1.2 }] },
];

const smooth = x => x * x * (3 - 2 * x);
function slerp(a, b, t) {
  let dot = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3];
  if (dot < 0) { b = b.map(v => -v); dot = -dot; }
  if (dot > 0.9995) { const r = a.map((v, i) => v + (b[i] - v) * t); const n = Math.hypot(...r); return r.map(v => v / n); }
  const th = Math.acos(dot), s = Math.sin(th);
  return a.map((v, i) => (Math.sin((1 - t) * th) * v + Math.sin(t * th) * b[i]) / s);
}

export class MotionPlayer {
  constructor(engine, poses, onFrame) {
    this.engine = engine; this.poses = Object.fromEntries(poses.map(p => [p.id, p])); this.onFrame = onFrame;
    this.motion = null; this.playing = false; this.speed = 1; this.time = 0; this.last = 0;
    this.tick = this.tick.bind(this);
  }
  frame(key) {
    const p = this.poses[key.pose];
    return { joints: { ...p.joint_positions_rad, ...(key.joints || {}) }, pos: p.base_position_m || [0, 0, 0.143], quat: p.base_quaternion_wxyz || [1, 0, 0, 0] };
  }
  start(id) {
    this.motion = MOTIONS.find(m => m.id === id); this.time = 0; this.peak = {}; this.playing = true;
    this.engine.setMode?.('pose'); this.last = performance.now(); cancelAnimationFrame(this.raf); this.raf = requestAnimationFrame(this.tick);
  }
  toggle() { this.playing = !this.playing; this.last = performance.now(); if (this.playing) this.raf = requestAnimationFrame(this.tick); }
  stop() { this.playing = false; cancelAnimationFrame(this.raf); }
  tick(now) {
    if (!this.playing || !this.motion) return;
    const m = this.motion, dt = Math.min(0.05, (now - this.last) / 1000) * this.speed * (m.tempo || 1); this.last = now; this.time += dt;
    const total = m.keys.reduce((s, k) => s + k.t, 0);
    if (this.time >= total) { if (m.loop) this.time %= total; else { this.time = total; this.playing = false; } }
    // locate segment: key i blends from key i-1 over key i's duration
    let acc = 0, i = 0;
    while (i < m.keys.length - 1 && acc + m.keys[i].t < this.time) { acc += m.keys[i].t; i++; }
    const prev = this.frame(m.keys[(i - 1 + m.keys.length) % m.keys.length]), cur = this.frame(m.keys[i]);
    const u = smooth(Math.min(1, Math.max(0, (this.time - acc) / m.keys[i].t)));
    const requested = {}, applied = {}, clamped = {};
    for (const j of this.engine.joints) {
      const a = prev.joints[j.name] ?? 0, b = cur.joints[j.name] ?? 0, q = a + (b - a) * u;
      const [lo, hi] = j.limits; const c = Math.min(hi, Math.max(lo, q));
      requested[j.name] = q; applied[j.name] = c;
      if (Math.abs(c - q) > 1e-4) { clamped[j.name] = q; this.peak[j.name] = Math.max(this.peak[j.name] || 0, Math.abs(c - q)); }
    }
    const pos = prev.pos.map((v, k) => v + (cur.pos[k] - v) * u), quat = slerp(prev.quat, cur.quat, u);
    this.engine.setPose({ joint_positions_rad: applied, base_position_m: pos, base_quaternion_wxyz: quat });
    this.onFrame({ motion: m.id, segment: m.keys[i].pose, time: this.time, total, requested, applied, clamped, peak: { ...this.peak }, playing: this.playing });
    if (this.playing) this.raf = requestAnimationFrame(this.tick);
  }
}
