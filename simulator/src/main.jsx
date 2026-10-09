import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { DuckEngine } from './engine.js';
import './style.css';

const pretty = s => String(s || '').replace(/^(ref_|visual_|vis_)/, '').replace(/_visual$/, '').replaceAll('_', ' ');
const degrees = r => (r * 180 / Math.PI).toFixed(1);
const download = (name, data) => { const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })); const a = document.createElement('a'); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); };

function App() {
  const host = useRef(null), cameraHost = useRef(null), engine = useRef(null);
  const [stats, setStats] = useState({ status: 'Loading CAD and MuJoCo…', time: 0, contacts: 0, values: {}, sensors: {} });
  const [data, setData] = useState(null), [error, setError] = useState(''), [selection, setSelection] = useState(null);
  const [mode, setMode] = useState('pose'), [skates, setSkates] = useState(false), [poseId, setPoseId] = useState('');
  const [tab, setTab] = useState('Pose'), [collision, setCollision] = useState(false), [contacts, setContacts] = useState(false);
  const [poseEdited, setPoseEdited] = useState(false);
  const [event, setEvent] = useState(''), [busy, setBusy] = useState(false), [exportedPose, setExportedPose] = useState(null);
  useEffect(() => {
    const e = new DuckEngine(host.current, s => setStats(previous => ({ ...previous, ...s })), setSelection, setError); engine.current = e;
    let active = true;
    e.init().then(result => { if (!active) return; setData(result); const p = e.firstPose(); setPoseId(p.id || p.name); }).catch(err => setError(String(err)));
    return () => { active = false; e.dispose(); };
  }, []);
  useEffect(() => { if (data && tab === 'Sensors' && cameraHost.current) engine.current.attachCamera(cameraHost.current); }, [data, tab]);
  const poses = data ? (Array.isArray(data.poses) ? data.poses : data.poses.poses) : [];
  const poseList = Array.isArray(poses) ? poses : Object.entries(poses).map(([id, p]) => ({ id, ...p }));
  const chosen = poseList.find(p => p.id === poseId);
  const floorPenetration = chosen?.cad_floor_clearance?.min_z_mm < -0.001;
  const ready = !!data && !error && !busy;
  const selectPose = id => { setPoseEdited(false); setPoseId(id); engine.current.setPose(id); setStats(s => ({ ...s, running: false })); };
  const changeMode = next => { setMode(next); engine.current.setMode(next); };
  const changeSkates = value => {
    setBusy(true); requestAnimationFrame(() => { try { engine.current.load(value); setSkates(value); const id = value ? poseList.find(p => /skat/.test(p.id))?.id : engine.current.firstPose().id; if (id && poseList.some(p => p.id === id)) selectPose(id); else selectPose(poseId); } catch (err) { setError(String(err)); } finally { setBusy(false); } });
  };
  const trigger = label => setEvent(`${label}: local interaction event at ${new Date().toLocaleTimeString()}. No RF, sound propagation or physical device connection.`);
  const tof = Object.entries(stats.sensors || {}).filter(([name]) => /tof.*\d/.test(name));
  return <div className="app">
    <header><div className="identity"><h1>IndieDuck</h1><span>Armature AI Labs · <a href="https://armature-ai-labs.github.io/indieduck/">Assembly guide</a> · <a href="https://github.com/armature-ai-labs/indieduck-rl">Source</a></span></div><div className="header-right"><span className="revision">R20 simulation study</span><button disabled={!ready} onClick={() => setExportedPose(engine.current.snapshot())}>Export pose</button></div></header>
    <main>
      <section className="viewport" aria-label="Interactive IndieDuck CAD view">
        <div ref={host} className="canvas-host" />
        <div className="view-toolbar" aria-label="View direction">{['iso', 'front', 'side', 'back', 'top'].map(v => <button disabled={!ready} key={v} onClick={() => engine.current.view(v)}>{v === 'iso' ? '3D view' : v[0].toUpperCase() + v.slice(1)}</button>)}</div>
        {!ready && <div className="loading" role="status">{error ? <><strong>Unable to load the study</strong><p>{error}</p><button onClick={() => location.reload()}>Reload</button></> : <><span className="spinner"/><strong>{busy ? 'Changing foot assembly…' : stats.status}</strong></>}</div>}
        <div className="view-caption"><strong>{mode === 'pose' ? 'Pose preview' : 'Physics study'}</strong><span>{mode === 'pose' ? 'Illustrative joint configuration. Drag to orbit; select a part to inspect.' : 'Gravity and approximate actuators. No trained balance policy.'}</span></div>
        <div className="view-status"><span>{skates ? 'Inline skates · provisional wheels' : 'R20 compact feet'}</span><span>{(stats.time || 0).toFixed(2)} s <i/> {stats.contacts || 0} contacts</span></div>
      </section>
      <aside aria-label="Simulation controls">
        <div className="mode-control" role="group" aria-label="Study mode"><button className={mode === 'pose' ? 'active' : ''} disabled={!ready} onClick={() => changeMode('pose')}>Pose preview</button><button className={mode === 'physics' ? 'active' : ''} disabled={!ready} onClick={() => changeMode('physics')}>Physics</button></div>
        <div className="playback"><button className="primary" disabled={!ready || mode !== 'physics'} onClick={() => engine.current.setRunning(!stats.running)}>{stats.running ? 'Pause physics' : 'Run physics'}</button><button disabled={!ready} onClick={() => selectPose(poseId)}>Reset pose</button></div>
        <div className="tabs" role="tablist">{['Pose', 'Parts', 'Sensors'].map(t => <button role="tab" aria-selected={tab === t} className={tab === t ? 'selected' : ''} onClick={() => setTab(t)} key={t}>{t}</button>)}</div>
        <div className="panel">
          {tab === 'Pose' && <>
            <label className="field-label" htmlFor="pose">Behaviour position</label><select id="pose" value={poseId} disabled={!ready} onChange={e => selectPose(e.target.value)}>{poseList.map(p => <option key={p.id} value={p.id}>{p.label || pretty(p.id)}</option>)}</select>
            <p className="note">{poseEdited ? 'Custom joint configuration. This configuration has not been checked against the exact CAD.' : chosen?.status || 'Pose study'}{chosen?.intended_contacts?.length ? ` · Intended contact: ${chosen.intended_contacts.join(', ')}` : ''}</p>
            <div className="clearance-note" data-warning={!!chosen?.cad_clearance?.hits?.length || floorPenetration}><strong>Preset CAD check</strong><span>{chosen?.cad_clearance?.status || 'Not checked'}. This applies to the saved preset only, not slider changes or simulated motion.</span>{floorPenetration && <span>Exact CAD floor penetration: {(-chosen.cad_floor_clearance.min_z_mm).toFixed(3)} mm in the walking-feet preset. This pose needs revision.</span>}{!!chosen?.cad_clearance?.hits?.length && <details><summary>{chosen.cad_clearance.hits.length} interfering part pairs</summary><ul>{chosen.cad_clearance.hits.map((h,i) => <li key={i}>{pretty(h.a)} / {pretty(h.b)}: {h.intersection_mm3.toFixed(1)} mm³</li>)}</ul></details>}</div>
            <div className="foot-switch" role="group" aria-label="Foot assembly"><button disabled={!ready} className={!skates ? 'active' : ''} onClick={() => changeSkates(false)}>Compact feet</button><button disabled={!ready} className={skates ? 'active' : ''} onClick={() => changeSkates(true)}>Inline skates</button></div>
            <div className="ball-control"><button disabled={!ready || mode !== 'pose'} onClick={() => engine.current.setBall(.12, 0, .0201)}>Place test ball ahead</button><span>40 mm ball, 120 mm forward. Reset pose restores it.</span></div><div className="section-heading"><h2>Joint angles</h2><span>degrees</span></div>
            {(stats.jointList || []).map(j => <label className="joint" key={j.name}><span>{j.name === 'mouth' ? 'Mouth / direct-drive jaw' : pretty(j.name)}</span><output>{degrees(stats.values?.[j.name] || 0)}°</output><input aria-label={pretty(j.name)} type="range" min={j.limits[0]} max={j.limits[1]} step="any" value={stats.values?.[j.name] || 0} disabled={!ready} onChange={e => { setPoseEdited(true); engine.current.setJoint(j.name, Number(e.target.value)); }}/></label>)}
            <p className="note">Jaw opening: {data ? degrees(data.contract.mouth_linkage.motor_to_jaw_polynomial.reduceRight((v,c) => v * (stats.values?.mouth || 0) + c, 0)) : '0.0'}°. The mouth slider shows direct-drive jaw opening.</p><p className="note">In physics mode, sliders set actuator targets. Joint readings show the simulated position.</p>
          </>}
          {tab === 'Parts' && <>
            <h2>Inspect the assembly</h2><p className="note">Click a component in the 3D view to see its identity and material category.</p>
            <div className="part-detail">{selection ? <><span className="field-label">Selected component</span><h3>{pretty(selection.name)}</h3><dl><dt>Moving link</dt><dd>{pretty(selection.body)}</dd><dt>Material category</dt><dd>{selection.material}</dd>{selection.mass_kg != null && <><dt>Estimated component mass</dt><dd>{(selection.mass_kg * 1000).toFixed(1)} g</dd></>}</dl></> : <p>No component selected.</p>}</div>
            <label className="checkbox"><input type="checkbox" checked={collision} disabled={!ready} onChange={e => { setCollision(e.target.checked); engine.current.setCollisions(e.target.checked); }}/> Show collision approximations</label>
            <label className="checkbox"><input type="checkbox" checked={contacts} disabled={!ready} onChange={e => { setContacts(e.target.checked); engine.current.showContacts = e.target.checked; }}/> Show contact points</label>
            <h2 className="spaced">Materials and confidence</h2><p className="note">White shells and yellow bill/feet retain the selected design. Rigid parts are PLA fit-test candidates; soles and lips use TPU 95A. Hardware is shown as component envelopes.</p><p className="note">Colour is an appearance choice. Mass, friction, strength and grip remain estimates until measured. Collision shapes simplify the CAD. Self-collision of the hollow body proxies is disabled; exact CAD clearance is checked separately.</p>
            <a className="text-link" href="model/contract.json" target="_blank" rel="noreferrer">View the model contract</a>
          </>}
          {tab === 'Sensors' && <>
            <h2>Head camera</h2><div ref={cameraHost} className="camera-feed" aria-label="Simulated head camera"/><p className="note">Rendered view with 4:3 framing and 49° vertical field of view from the camera drawing. Optical alignment still needs a physical check.</p>
            <div className="section-heading"><h2>8 × 8 ToF</h2><span>metres</span></div><div className="tof-grid" aria-label="Simulated depth grid">{Array.from({ length: 64 }, (_, i) => { const value = tof[i]?.[1]?.[0]; const hit = Number.isFinite(value) && value >= 0; return <span key={i} title={hit ? `${value.toFixed(3)} m` : 'No return'} style={{ background: hit ? `hsl(42 68% ${Math.max(35, 88 - value * 20)}%)` : '#eceef0' }}>{hit ? value.toFixed(1) : '·'}</span>; })}</div>
            <h2 className="spaced">Body and head IMUs</h2><div className="imu-values">{Object.entries(stats.sensors || {}).filter(([n]) => /gyro|accelerometer|accel/.test(n)).map(([n,v]) => <div key={n}><span>{pretty(n)}</span><code>{v.map(x => x.toFixed(2)).join(' / ')}</code></div>)}</div><p className="note">Gyro: rad/s. Accelerometer: m/s². Virtual readings, with no measured sensor noise model.</p>
            <h2 className="spaced">Interaction events</h2><div className="event-buttons"><button disabled={!ready} onClick={() => trigger('Head NFC tap')}>Head NFC</button><button disabled={!ready} onClick={() => trigger('Bill NFC tap')}>Bill NFC</button><button disabled={!ready} onClick={() => trigger('Audio input/output')}>Audio</button></div><p className="note" role="status">{event || 'NFC and audio events are interface tests. Their modules and final mounts remain provisional.'}</p>
          </>}
        </div>
        <div className="limits"><strong>Prototype evidence</strong><span>No trained policy or physical-fit claim. CAD and physics are reviewed separately.</span><small>MuJoCo 3.10.0 · {(stats.fps || 0).toFixed(0)} fps{stats.stepMs > 0 ? ` · ${stats.stepMs.toFixed(2)} ms/step` : ''}</small></div>
      </aside>
    </main>
    {exportedPose && <div className="dialog-backdrop" onKeyDown={e => { if (e.key === 'Escape') setExportedPose(null); }}><section className="export-dialog" role="dialog" aria-modal="true" aria-labelledby="export-title"><h2 id="export-title">Export this pose</h2><p className="note">Named joint angles in radians, robot and test-ball positions in metres, with the CAD revision and source hash. This is a pose record, not a full physics checkpoint.</p><textarea autoFocus readOnly aria-label="Pose JSON" value={JSON.stringify(exportedPose, null, 2)}/><div><button onClick={() => setExportedPose(null)}>Close</button><button className="primary" onClick={() => download('indieduck-r20-pose.json', exportedPose)}>Download JSON</button></div><p className="note">You can also select and copy the JSON if your browser does not support downloads.</p></section></div>}
    <footer><span>IndieDuck by Armature AI Labs, adapted from Open Duck Mini and inspired by Pollen Robotics’ MicroDuck.</span><span><a href="LICENSE.txt" target="_blank" rel="noreferrer">Software licence</a> · <a href="CAD-NOTICE.txt" target="_blank" rel="noreferrer">CAD credits</a> · <a href="THIRD_PARTY_NOTICES.txt" target="_blank" rel="noreferrer">Software notices</a></span></footer>
  </div>;
}
createRoot(document.getElementById('root')).render(<App/>);
