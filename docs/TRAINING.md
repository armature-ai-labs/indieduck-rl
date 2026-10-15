# Training IndieDuck policies

Policies train in MuJoCo (mjlab) on an NVIDIA GPU. There are three ways to get one, and all three run the same code, task and settings, so results are comparable whichever you use:

| Path | Best for | What you need |
|---|---|---|
| [Hugging Face Jobs](#1-hugging-face-jobs) | No machine to manage; workshops where each team uses its own account | A Hugging Face account with billing enabled |
| [Rented GPU](#2-rented-gpu) | Longer runs, or when you want a full Linux machine for a few hours | An account with a GPU cloud (RunPod, Lambda, Vast.ai, or a cloud VM) |
| [Lab machine](#3-lab-machine) | Repeated runs at no per-hour cost | A Linux workstation with an NVIDIA GPU |

The current task is `Mjlab-Velocity-Flat-IndieDuck-Cyber` (walking on flat ground, IndieDuck Cyber Edition model, HD-1910 actuator model). No Cyber Edition policy has been trained yet: the settings below are starting points, and the first runs are experiments.

## Before any path: check the setup on your laptop

This builds the task and runs two training steps on the CPU, so it works on a Mac:

```sh
git clone https://github.com/armature-ai-labs/indieduck-rl.git && cd indieduck-rl
scripts/train_gpu.sh --smoke
```

On macOS, keep the Python environment outside iCloud-synced folders first: `export UV_PROJECT_ENVIRONMENT=$HOME/.venvs/indieduck-rl`.

## Recommended starting settings

```
Mjlab-Velocity-Flat-IndieDuck-Cyber --env.scene.num-envs 4096 --agent.max-iterations 3000 --agent.logger tensorboard
```

- `--env.scene.num-envs 4096`: parallel simulations. The default is 1, which is far too few on a GPU.
- `--agent.max-iterations 3000`: a first run. The default (50000) is for long runs; checkpoints are saved every 250 iterations.
- `--agent.logger tensorboard`: logs locally, so no Weights & Biases account is needed. Omit it to log to W&B (run `wandb login` first).

## 1. Hugging Face Jobs

The repository submits itself as a Hugging Face Job: it uploads a snapshot of your working copy to a private dataset repo, runs training on a cloud GPU, pushes checkpoints to a private model repo as they are saved, and exports the final policy to ONNX in the same repo.

1. Create a Hugging Face account and enable billing (Jobs are paid per minute; see Hugging Face's pricing page for the current hardware rates).
2. Log in once on your machine: `uv run python -c "from huggingface_hub import login; login()"` (paste a token with write access).
3. Check what would be submitted, at no cost:

   ```sh
   uv run train Mjlab-Velocity-Flat-IndieDuck-Cyber --env.scene.num-envs 4096 \
       --agent.max-iterations 3000 --agent.logger tensorboard \
       --hf-jobs --namespace <your-hf-username> --no-wandb --dry-run
   ```

4. Remove `--dry-run` to submit. The command prints the job and the checkpoint repo, `https://huggingface.co/<your-hf-username>/<task>-<timestamp>`.
5. Results: checkpoints under the run folder in that repo, and `exported/policy.onnx` when training finishes.

Useful options: `--flavor` (hardware, default `l4x1`), `--timeout` (default `12h`), `--run-name`. `--namespace` can be an organisation you belong to. Implementation: `src/mjlab_microduck/hf_jobs.py`; more detail in `scripts/hf/README.md`.

## 2. Rented GPU

Any provider that gives you a Linux machine with an NVIDIA GPU works. Choose an Ubuntu 22.04 or 24.04 image with the NVIDIA driver and CUDA 12 installed; a GPU with 16 GB or more is a comfortable start.

```sh
ssh <your-machine>
git clone https://github.com/armature-ai-labs/indieduck-rl.git && cd indieduck-rl
scripts/train_gpu.sh --smoke     # about a minute: confirms the machine is set up
scripts/train_gpu.sh -- Mjlab-Velocity-Flat-IndieDuck-Cyber --env.scene.num-envs 4096 \
    --agent.max-iterations 3000 --agent.logger tensorboard
```

The script installs `uv` if needed, installs the pinned dependencies, checks the GPU, trains, and exports `exported/policy.onnx`. Checkpoints are in `logs/rsl_rl/`.

To keep results after the machine is deleted, either copy them back (`scp -r <your-machine>:indieduck-rl/exported .`), or add `--hub-repo <your-hf-username>/<repo-name>` before `--` to push checkpoints and the policy to a private Hugging Face repo as training runs (log in to Hugging Face on that machine first). Run long jobs inside `tmux` so a dropped connection does not stop them, and **stop or delete the machine when training finishes**: rented GPUs bill by the hour.

Providers that run Docker images can use the `Dockerfile` instead (see below).

## 3. Lab machine

A Linux workstation with an NVIDIA GPU, driver installed (`nvidia-smi` shows the GPU). Either run the script directly:

```sh
git clone https://github.com/armature-ai-labs/indieduck-rl.git && cd indieduck-rl
scripts/train_gpu.sh --smoke
scripts/train_gpu.sh -- Mjlab-Velocity-Flat-IndieDuck-Cyber --env.scene.num-envs 4096 \
    --agent.max-iterations 3000 --agent.logger tensorboard
```

or use the container, which needs Docker and the NVIDIA Container Toolkit:

```sh
docker build -t indieduck-rl .
docker run --gpus all --rm -v "$PWD/logs:/work/logs" -v "$PWD/exported:/work/exported" indieduck-rl \
    -- Mjlab-Velocity-Flat-IndieDuck-Cyber --env.scene.num-envs 4096 --agent.max-iterations 3000 --agent.logger tensorboard
```

Watch training with `uv run tensorboard --logdir logs/rsl_rl` and open the printed address. When several people share one machine, give each person their own clone so logs and checkpoints stay separate, and use `--gpu-ids` to pick a GPU on multi-GPU machines. ARM machines such as NVIDIA DGX Spark are handled by `pyproject.toml`, which selects the CUDA build of PyTorch there.

## Outputs

| Output | Where |
|---|---|
| Checkpoints and saved settings | `logs/rsl_rl/<experiment>/<run>/` (`model_<iteration>.pt`, `params/`) |
| Exported policy for the runtime | `exported/policy.onnx` (Hugging Face Jobs: `exported/policy.onnx` in the checkpoint repo) |
| Training curves | TensorBoard files in the run folder, or your W&B project |

Exported policies carry the edition's model, revision and contract metadata, and the runtime refuses a policy built for a different robot model. See the README's training, evaluation and export section for evaluation and publishing.
