# Validation and current limitations

This is a filtered source integration base. RL tasks cannot currently be imported or trained from this snapshot because the upstream robot models are deliberately omitted. No IndieDuck model has been invented or supplied, and no policy-transfer claim is made.

## Checks performed

- All 214 imported upstream files match their pinned source hashes; source files were not modified.
- All 142 imported Python files parse with Python 3.14.6. The package declares Python 3.12; target-version execution and dependency installation were not tested.
- `pyproject.toml` retains `uv.lock` and the vendored BAM dependency source. It also retains upstream command entry points; their presence is not validation of those commands.
- A bounded scan found no GitHub/Hugging Face token patterns or private-key blocks. Public upstream examples and script defaults containing developer paths are recorded in `provenance/validation.json`. Scripts with those defaults need explicit path configuration before use.
- No GitHub Actions workflows, Git history, binary model weights or 3D model assets are present.

## Known execution blockers

`src/mjlab_microduck/robot/microduck_constants.py:38-46` asserts the presence of omitted robot XML files at import time. `src/mjlab_microduck/robot/testbench_constants.py:24` similarly asserts the omitted test-bench XML. Registered tasks import these modules. Consequently training, simulation and model-dependent evaluation are blocked before an IndieDuck robot model is integrated.

Full tests were not run because they require these omitted assets and the simulator/dependency environment. No dependencies were installed, no cloud jobs or training runs were submitted, no model was uploaded, and no motors or printers were contacted.

The actual environment configurations, observations and rewards (`tasks/mdp.py`), actuator implementation (`actuator/friction_dr_bam.py`), training code, evaluation scripts and ONNX-export code are present. Their upstream joint names, body names, dimensions, hardware assumptions and defaults still require deliberate IndieDuck adaptation. The numerical actuator parameters retain their upstream meaning and have not been measured on IndieDuck.

Before execution, supply one canonical appropriately licensed simulator model, map and validate the mechanical and control interfaces, review upstream hardware/cloud/publishing defaults, install the declared Python 3.12 environment, run relevant tests and simulation, then perform controlled hardware validation. Repository publication alone does not complete these steps.
