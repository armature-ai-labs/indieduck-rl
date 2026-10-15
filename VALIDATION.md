# Validation

IndieDuck Cyber Edition (design R25, platform P1), verified locally on 14 October 2026 on macOS (arm64), Python 3.12.8, native MuJoCo 3.10.0. No physical hardware, trained policy or learned behaviour is claimed.

- CAD source: `armature-ai-labs/indieduck-cad` release `r25-cad-study-v5` (exact geometry throughout, no XGO-Duck geometry). Display bundle exported by `tools/export_r25_cad.py`: 141 parts, 51 printed. Registration against the R20 display manifest: 94 of 97 retained parts within 0.05 mm; the three exceptions are the hip brackets (R25 cowl mounting lands) and the roll-servo cradle (changed between R20 and R25).
- Canonical model `indieduck-cyber`: generated and finalized; native verification passes all 19 poses for `scene.xml` and `scene_skates.xml` (`validation/r25-native.json`). Estimated mass 1.092 kg (1.170 kg with skates), full-solid density estimates.
- CAD parity: all 141 meshes, posed by the model's own joint chain, within 0.035 mm of the CAD standing pose (`validation/r25-cad-standing-parity.json`).
- Contract: neck pitch limits -65 to +27.5 degrees, the range CAD-verified clear of every other part every 2.5 degrees with head joints at zero (was -90 to +60, not clearance-checked).
- Python: 75 tests pass (the 63-test source regression suite for numerical guards, observations, head bias, job flags and policy publication, plus the 12 simulator-server tests for handshake, model identity and contract). The publisher requires matching R25 ONNX model, revision and contract metadata.
- Training: `Mjlab-Velocity-Flat-IndieDuck-Cyber` builds (61 actor observations) and `tools/verify_r20_training.py` completes two training steps on CPU. No policy was trained or uploaded.
- Browser: `npm test` 4 tests pass, including WebAssembly matching native MuJoCo for every pose and joint on both scenes; production build succeeds.

Not verified: physical fit, actuator identification on IndieDuck hardware, deep-pose clearance beyond the neck, cables, any gait.

R20 validation records remain in `validation/r20-*.json` and at the tag `r20-simulation-study-v1`.
