# IndieDuck RL

Reinforcement-learning source for the IndieDuck robotics project, maintained by Armature AI Labs.

**Status: initial source integration base. Training and simulation cannot currently start from this snapshot because the robot models are excluded.** The package imports assert that those XML models exist. An Apache-compatible IndieDuck model exported from the project CAD, updated physical parameters and tested policies remain to be implemented.

This repository contains actual Python source from [JoyandAI/microduck_rl](https://github.com/JoyandAI/microduck_rl/tree/22916b9d82f250caa563ed9a56976eb33243fb91), based on Pollen Robotics’ MicroDuck RL. It includes task configurations, observations/rewards, actuator modelling, training, evaluation and export code. It is an attributed source snapshot with excluded files recorded, not a placeholder of wrappers or a complete upstream GitHub fork. The upstream `mjlab_microduck` namespace and package version are preserved for integration work.

## Source map

- `src/mjlab_microduck/tasks/`: locomotion, stand-up, pickup, kicking and skating task source. These describe upstream training tasks, not demonstrated IndieDuck capabilities.
- `src/mjlab_microduck/actuator/` and `vendor/bam/`: actuator/friction modelling and vendored BAM source, including upstream HD-1910 parameter sets.
- `src/mjlab_microduck/robot/`: robot configuration code; required model XML and meshes are deliberately absent.
- `src/mjlab_microduck/sim/`, training/export modules and `scripts/`: simulation bridge, training and evaluation support.
- `provenance/`: exact source revision, file inventories, changes, credits and recorded checks.

## Model and policy work still needed

1. Export and document an independently redistributable MJCF model from [IndieDuck CAD](https://github.com/armature-ai-labs/indieduck), including link masses, inertias, collision geometry, joint limits and optional skate contacts.
2. Match the runtime contract for joint ordering, signs, home poses, observations/actions and recurrent state. Confirm the mouth-control path separately from the 14-joint locomotion policy.
3. Reproduce the upstream HD-1910 actuator measurements on the actual 5.0 V build before accepting those fitted parameters for IndieDuck.
4. Train and evaluate in simulation, test reset/failure behaviour and export policies with model/runtime revision metadata.
5. Validate on a supported physical robot before claiming walking, sitting, standing, pickup, getting up, kicking, skating or roulade performance.

The upstream robot model files have separate non-commercial terms and are excluded, along with trained checkpoints, media and raw local calibration captures. Existing source references to those paths have not been replaced with a fabricated model. See the [exclusion inventory](provenance/excluded-upstream-files.csv) and [validation record](provenance/validation.json).

## Contributor starting point

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [upstream provenance](provenance/upstream.json). The retained package declares Python 3.12, mjlab 1.3 and Torch 2.9.1; its lockfile records upstream dependencies. Import, environment creation, GPU training and policy export have not been validated for this filtered snapshot. Syntax and manifest checks do not establish simulator correctness. Follow the model-integration priorities above before attempting a training run.

## Project repositories

| Project | Repository | Scope |
| --- | --- | --- |
| IndieDuck | [indieduck](https://github.com/armature-ai-labs/indieduck) | Hardware CAD, fit tests and project documentation |
| IndieDuck Runtime | [indieduck-runtime](https://github.com/armature-ai-labs/indieduck-runtime) | Onboard Rust control and device integration |
| IndieDuck RL | [indieduck-rl](https://github.com/armature-ai-labs/indieduck-rl) | Python environments, actuator models, training and export |

The hardware project is **IndieDuck by Armature AI Labs, adapted from Open Duck Mini and inspired by Pollen Robotics’ MicroDuck**. The software in this repository is credited separately below.

## Licensing and credits

Eligible upstream code retains its [Apache-2.0 licence](LICENSE) and applicable third-party terms. Preserve [third-party notices](THIRD_PARTY_NOTICES.md), [upstream attribution](UPSTREAM.md), source headers and the provenance records. JoyandAI, Pollen Robotics and their contributors authored the imported code; Armature AI Labs prepared this filtered source base and the IndieDuck integration roadmap. This repository does not imply upstream endorsement.
