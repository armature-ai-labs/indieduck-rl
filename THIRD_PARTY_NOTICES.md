# Third-party notices

The imported software is distributed under the upstream Apache License 2.0 in [LICENSE](LICENSE), including the original Pollen Robotics copyright. Credit is also retained for JoyandAI and the contributors listed in `provenance/UPSTREAM_AUTHORS.txt`. The Apache software license does not replace the separate license statement for 3D model files.

| Component | Source and license boundary |
| --- | --- |
| Pollen Robotics and JoyandAI RL software | [Pinned source](https://github.com/JoyandAI/microduck_rl/tree/22916b9d82f250caa563ed9a56976eb33243fb91), root Apache-2.0 license. The actual environment, observation/reward, actuator, training, evaluation and ONNX-export source is included. |
| `vendor/bam` | Better Actuator Models by Marc Duclusaud, Grégoire Passault and contributors, [Rhoban/bam](https://github.com/Rhoban/bam). Original Apache-2.0 [LICENSE](vendor/bam/LICENSE), README, package metadata and source notices are retained. JoyandAI's parent manifest identifies vendoring base `8d0025f`; this abbreviated base could not be resolved through the public Rhoban commit API. The exact included BAM files are nevertheless pinned by the JoyandAI commit and manifest hashes. Do not represent them as an unmodified, independently verified Rhoban release. |
| External Python, simulator and GPU dependencies | `pyproject.toml` and `uv.lock` retain upstream package choices. Those packages are not bundled here and have their own terms. No claim that every dependency is Apache-2.0 is made. |

## Excluded material

The [pinned upstream README](https://github.com/JoyandAI/microduck_rl/blob/22916b9d82f250caa563ed9a56976eb33243fb91/README.md#license) distinguishes software from 3D model files and labels the latter Creative Commons BY-SA-NC. It does not identify a license version. All upstream 3D assets covered by that notice remain omitted: 54 STL files, 54 `.part` files, 27 XML files and five SCAD files. Robot export-configuration JSON files are also omitted. The blanket model notice leaves the per-path treatment of the JoyandAI-added pendulum CAD unresolved; those files are conservatively excluded as well.

Raw calibration recordings, plots, logs, angle recordings, deployment/cloud setup scripts and automatic workflows are omitted. The retained numerical BAM actuator parameters are upstream data within the vendored Apache-licensed software package. They are not IndieDuck measurements or proof that either an HD1910, HLS2909 or XL330 implementation has been validated on IndieDuck.

No trained policies or binary model weights are bundled. The current R20 CAD meshes and generated MJCF have separate provenance described below. Later inclusion of geometry, assets or policies requires its own provenance and license assessment. Linking to an upstream asset does not relicense it.

## Current R20 geometry

Current meshes derive from the complete published IndieDuck R20 CAD assembly at commit `7bcdd1696516f9cff6bdefbc34e42f259c87749a`, plus the separately labelled original R07 provisional skate accessory. They include reused XGO geometry with unresolved source-specific redistribution terms. **The software Apache-2.0 licence does not license the entire geometry collection.** See [preserved CAD notices](provenance/cad-r20/THIRD_PARTY_NOTICES.md), original notices alongside them, and the component/source records. New Armature engineering and eligible Open Duck Mini adaptations retain their own attribution.

IndieDuck by Armature AI Labs, adapted from Open Duck Mini and inspired by Pollen Robotics' MicroDuck. XGO-derived head and jaw contributions are credited in the CAD notices. No source, geometry or policy from the inspected Hugging Face MicroDuck web simulator is incorporated.

The CPU review environment pins the packages below in `requirements-study.txt`. Their licence expressions were checked against the installed distributions. Packages are installed locally, not vendored into this repository, and retain their own notices and bundled third-party terms.

| Package | Version | Distribution licence expression |
| --- | --- | --- |
| MuJoCo | 3.10.0 | Apache-2.0; distribution also carries `LICENSES_THIRD_PARTY.md` |
| NumPy | 2.5.3 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| pytest | 9.1.1 | MIT |
| Pillow | 12.3.0 | MIT-CMU |
| Colorama | 0.4.6 | BSD-3-Clause, verified from installed LICENSE.txt |

The original browser interface uses MuJoCo WASM, Three.js, React and Vite. Its exact versions and notices are in `simulator/package-lock.json` and `simulator/THIRD_PARTY_NOTICES.txt`. The root Apache licence covers eligible IndieDuck-authored changes and does not replace dependency licences.

The CPU BAM diagnostic imports the retained `vendor/bam` source directly. Its m1 parameter and characterization hashes are recorded in `validation/r07-bam-native.json`. The source parameter files remain unchanged.
