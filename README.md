# IndieDuck RL and simulator

IndieDuck by Armature AI Labs, adapted from Open Duck Mini and inspired by Pollen Robotics' MicroDuck.

[Browser simulator](https://armature-ai-labs.github.io/indieduck-rl/) · [Assembly guide](https://armature-ai-labs.github.io/indieduck/) · [Editable R25 CAD](https://github.com/armature-ai-labs/indieduck-cad) · [Runtime](https://github.com/armature-ai-labs/indieduck-runtime)

This is the simulation and training repository for **IndieDuck Cyber Edition** (design R25, by Zankar Savalia) on platform P1, the shared IndieDuck mechanism. Each edition gets its own model ID (`indieduck-<edition>`), training task and policies; this repository currently holds Cyber Edition (`indieduck-cyber`). It includes actual attributed environment, reward, observation, BAM actuator, training, evaluation and ONNX-export source adapted from JoyandAI/Pollen, with an explicitly registered R25 velocity task. No trained policy or successful physical behaviour is claimed. The Apache-2.0 software licence does not cover the whole mixed-source mesh collection. Read [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Browser study

Use Node.js 22.12 or later:

```sh
cd simulator
npm ci
npm test
npm run dev
```

The production build uses relative assets and works under the GitHub Pages repository path. Controls include pose/physics modes, 15 joints, 19 illustrative presets, a 40 mm ball, provisional skates, contacts, part information, camera and two IMUs, 64 ideal ToF rays and labelled NFC/audio interaction events. The browser uses approximate XML PD actuators, not native BAM or learned balance.

## Native diagnostics and runtime connection

Use Python 3.12. Full pinned dependencies, including vendored BAM:

```sh
uv sync --frozen
uv run python -m mjlab_microduck.sim.body_server --headless
```

In the runtime repository:

```sh
cargo run -p robotd -- --sim 127.0.0.1:7801 --no-policy --socket /tmp/indieduck-cyber.sock
```

The Cyber Edition contract (model `indieduck-cyber`, design revision R25) is version 2: 15 physical joints, 14 policy actions, 61 policy observations and separate direct-drive mouth control. The logical jaw opens from 0 to +30 degrees about CAD +Y. Physical encoder sign, home and limits remain uncalibrated. No passive crank/rod mechanism remains in the current model. Reset, disconnect and incompatible contract handling are tested; simulation does not fall back to serial hardware.

## Training, evaluation and export

**Where to train:** Hugging Face Jobs, a rented GPU or a lab machine, all with the same code and settings. Step-by-step guide: [docs/TRAINING.md](docs/TRAINING.md). Check any machine first with `scripts/train_gpu.sh --smoke`.

```sh
uv run train Mjlab-Velocity-Flat-IndieDuck-Cyber --help
uv run python tools/verify_r20_training.py
# On a suitable CUDA host, after inspecting task settings:
uv run train Mjlab-Velocity-Flat-IndieDuck-Cyber
uv run play Mjlab-Velocity-Flat-IndieDuck-Cyber --help
uv run python scripts/export.py Mjlab-Velocity-Flat-IndieDuck-Cyber --help
```

The current task reuses the retained upstream velocity rewards and observations with the current R25 model and home pose, explicit 14-joint ordering and HD-1910 m1 BAM. Mouth control remains outside the policy. Training delay is 6 physics substeps (30 ms), approximating the selected 29 ms native diagnostic delay at a 5 ms timestep. Parameters are inherited estimates, not IndieDuck measurements. A one-environment CPU smoke checks reset, 14 actions, 61 actor observations and two finite steps. This does not validate GPU training, reward tuning, convergence or policy transfer. Historical task implementations remain in source, with `tasks/upstream_registry.py` retained as history; their omitted upstream CAD prevents treating them as current runnable IndieDuck tasks.

Use the existing export command for future checkpoints so normalization is included. R25 ONNX exports carry revision/contract metadata and assert policy joint order. The policy publisher rejects missing or incompatible R25 metadata before upload. There is no checkpoint included in this release.

## Canonical model and regeneration

`src/mjlab_microduck/robot/indieduck/` is the only authored model. Browser and runtime model copies are generated from it. FreeCAD remains the mechanical source. The published CAD commit is recorded in the contract and preserved source notices.

```sh
# Set these to a CAD repository checkout and a new output directory.
export INDIEDUCK_CAD=/path/to/indieduck-cad
export INDIEDUCK_ASSETS=/path/to/r25-assets
# R25 registers against the R20 display manifest, kept at the CAD tag r20-simulation-study-v1:
export INDIEDUCK_R20_MANIFEST=/path/to/r20-assembly-manifest.json
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd tools/export_r25_cad.py
uv run python tools/generate_indieduck.py "$INDIEDUCK_ASSETS/zero/manifest.json"
uv run python tools/finalize_indieduck.py
uv run python tools/verify_indieduck_native.py --output validation/r25-native.json
uv run python tools/verify_r20_cad_parity.py "$INDIEDUCK_ASSETS"
uv run python tools/sync_indieduck_browser.py
```

The R25 exporter reads all 141 visible CAD components (51 printed pieces, the rest hardware and module reference envelopes) from the single R25 native file, taking each part's joint link from its `MovingBody` property. Source identities and colours are retained. It generates posed guide meshes and unposed model inputs with explicit millimetre-to-metre conversion. Unmapped components fail generation. The additional 22 skate parts are preserved original R07 provisional accessory geometry, not measured or physically fitted R20 hardware. Meshes are presentation tessellations; use the CAD repository's manufacturing exports for printing.

## Environment notes (macOS)

Keep the Python environment outside iCloud-synced folders: iCloud's Desktop and Documents sync can mark files inside `.venv` hidden, and Python 3.12 then skips the hidden `.pth` files, so `bam` and this package stop importing. Use `export UV_PROJECT_ENVIRONMENT=$HOME/.venvs/indieduck-rl` before `uv sync`. If your shell sets `NODE_ENV=production`, install the simulator with `npm ci --include=dev`.

## Credits

[Zankar Savalia](https://www.linkedin.com/in/zankarvs/) contributed to the design of the R25 exterior and helped prepare it for publication. See [CONTRIBUTORS.md](CONTRIBUTORS.md).

## Evidence and limits

See [VALIDATION.md](VALIDATION.md). CAD clearance, physical fit, strength, cable travel and learned behaviour are different questions. Pose presets are illustrative. The neck is limited to the CAD-verified range of -65 to +27.5 degrees; other deep poses are not clearance-checked, and finite integration does not certify collision-free motion. Masses, inertias and friction are estimated. Keep head sensors auxiliary to the 61-observation policy interface.
