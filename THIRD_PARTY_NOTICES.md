# Third-party notices

The imported software is distributed under the upstream Apache License 2.0 in [LICENSE](LICENSE), including the original Pollen Robotics copyright. Credit is also retained for JoyandAI and the contributors listed in `provenance/UPSTREAM_AUTHORS.txt`. The Apache software license does not replace the separate license statement for 3D model files.

| Component | Source and license boundary |
| --- | --- |
| Pollen Robotics and JoyandAI RL software | [Pinned source](https://github.com/JoyandAI/microduck_rl/tree/22916b9d82f250caa563ed9a56976eb33243fb91), root Apache-2.0 license. The actual environment, observation/reward, actuator, training, evaluation and ONNX-export source is included. |
| `vendor/bam` | Better Actuator Models by Marc Duclusaud, Grégoire Passault and contributors, [Rhoban/bam](https://github.com/Rhoban/bam). Original Apache-2.0 [LICENSE](vendor/bam/LICENSE), README, package metadata and source notices are retained. JoyandAI's parent manifest identifies vendoring base `8d0025f`; this abbreviated base could not be resolved through the public Rhoban commit API. The exact included BAM files are nevertheless pinned by the JoyandAI commit and manifest hashes. Do not represent them as an unmodified, independently verified Rhoban release. |
| External Python, simulator and GPU dependencies | `pyproject.toml` and `uv.lock` retain upstream package choices. Those packages are not bundled here and have their own terms. No claim that every dependency is Apache-2.0 is made. |

## Excluded material

The [pinned upstream README](https://github.com/JoyandAI/microduck_rl/blob/22916b9d82f250caa563ed9a56976eb33243fb91/README.md#license) distinguishes software from 3D model files and labels the latter Creative Commons BY-SA-NC. It does not identify a license version. All 3D assets are omitted: 54 STL files, 54 `.part` files, 27 XML files and five SCAD files. Robot export-configuration JSON files are also omitted. The blanket model notice leaves the per-path treatment of the JoyandAI-added pendulum CAD unresolved; those files are conservatively excluded as well.

Raw calibration recordings, plots, logs, angle recordings, deployment/cloud setup scripts and automatic workflows are omitted. The retained numerical BAM actuator parameters are upstream data within the vendored Apache-licensed software package. They are not IndieDuck measurements or proof that either an HD1910, HLS2909 or XL330 implementation has been validated on IndieDuck.

No trained policies or binary model files are bundled. Later inclusion of geometry, assets or policies requires its own provenance and license assessment. Linking to an upstream asset does not relicense it.
