# IndieDuck R20 browser simulator

Original Three.js/React interface using MuJoCo WASM 3.10.0 and the canonical R20 model. See the [repository guide](../README.md) for setup, provenance and validation.

Node.js 22.12 or later: `npm ci`, `npm test`, `npm run dev`. Build with `npm run build`; serve `dist/` from any static server. Relative asset URLs support GitHub Pages project subpaths. Source assets are generated using `../tools/sync_indieduck_browser.py`.

Pose mode is kinematic illustration. Physics mode adds gravity, approximate PD actuators, contacts and a test ball; it has no trained controller. The direct-drive jaw is 0..30 degrees. All 15 physical joints remain visible, while policies use 14 joints and separate mouth control. The head band is rigidly attached to the shell in simulation; removability is demonstrated in the [assembly guide](https://armature-ai-labs.github.io/indieduck/).

The 19 presets have native/WASM parity evidence but are not validated behaviours. Two IMUs and 64 ideal ToF rays are simulated; NFC/audio controls are only interaction events. Cameras and sensor envelopes remain provisional. Nominal walking feet use R20 compact shoes; accessory skates retain the original provisional R07 design and require physical fit review.

Public CAD terms are in `public/CAD-NOTICE.txt`; software dependency notices are in `THIRD_PARTY_NOTICES.txt`. No MicroDuck simulator UI source, policies or meshes were reused.
