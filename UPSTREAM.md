# Upstream attribution and snapshot provenance

This repository contains a filtered source snapshot from [JoyandAI/microduck_rl](https://github.com/JoyandAI/microduck_rl/tree/22916b9d82f250caa563ed9a56976eb33243fb91), branch `develop`, commit `22916b9d82f250caa563ed9a56976eb33243fb91`. It is an integration base for IndieDuck. It is not a complete robot release or a claim that upstream code runs on IndieDuck hardware.

JoyandAI's repository is a GitHub fork of [pollen-robotics/microduck_rl](https://github.com/pollen-robotics/microduck_rl). Credit belongs to Pollen Robotics, JoyandAI and the upstream contributors. The source authors found in the history of the included paths are retained in [provenance/UPSTREAM_AUTHORS.txt](provenance/UPSTREAM_AUTHORS.txt). This list is supplemental; source copyright notices and third-party credits remain authoritative.

The initial publication was a clean filtered import with each included source file byte-identical to the selected upstream Git blob. Original Git history was not imported, so this is not a GitHub-native fork. That baseline remains documented in the unchanged provenance manifests. The historical [R07 study record](provenance/r07-local.json) describes the earlier integration. The current R20 study replaces its robot geometry and contract, uses a direct-drive jaw, adds an original browser simulator and binds the retained RL source to the canonical IndieDuck model. CAD geometry has source-specific terms described in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md); it is not all independently authored or cleared under Apache-2.0.

## Verified ancestry

The selected JoyandAI commit and the Pollen comparison commit `273afe0b31c4ab365b9ff806a927b63ac92b5ddd` share common ancestor `cb70b792312d559a4da09064d92009079671815f`. The selected JoyandAI commit is 30 commits ahead of that common ancestor; the Pollen comparison commit is 18 commits ahead. The Pollen comparison commit is **not** an ancestor of the selected JoyandAI commit. These pins describe divergent histories, not a containment or compatibility guarantee.

## Included and excluded source

- [Included source manifest](provenance/included-upstream-files.csv): 214 imported paths, upstream Git blob IDs and SHA-256 hashes.
- [Excluded source manifest](provenance/excluded-upstream-files.csv): 759 omitted upstream paths and reasons.
- [Machine-readable source record](provenance/upstream.json).
- [Static validation record](provenance/validation.json).
- [License boundaries](THIRD_PARTY_NOTICES.md).
- [Current build and execution limitations](VALIDATION.md).

Neither selected upstream tree contains Git submodule entries or a `.gitmodules` file. Third-party code is vendored or obtained through package dependencies. The retained root lockfile records training dependencies. The current R20 configuration has passed a clean locked installation and two CPU environment steps with the BAM actuator model; policy training and hardware transfer remain untested. The CPU study requirements and browser lockfile pin the diagnostic dependencies.

Upstream developer paths in test fixtures and examples remain unchanged for source fidelity. They are public upstream examples, not paths from an IndieDuck maintainer's machine. Some manual scripts retain upstream-specific defaults that need review before use. The R20 Pages workflow builds the original browser simulator. No deployment keys are included.
