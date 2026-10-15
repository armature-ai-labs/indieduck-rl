#!/usr/bin/env bash
# Train an IndieDuck policy on any Linux machine with an NVIDIA GPU:
# a rented cloud GPU (RunPod, Lambda, Vast.ai, a cloud VM) or a lab workstation.
# The same steps the Hugging Face Jobs path runs inside its container (see
# src/mjlab_microduck/hf_jobs.py), without the Hub-specific source mount.
#
# Usage, from the repository root:
#   scripts/train_gpu.sh [--smoke] [--hub-repo <user>/<repo>] [--no-export] -- <train args>
#
#   scripts/train_gpu.sh -- Mjlab-Velocity-Flat-IndieDuck-R25 \
#       --env.scene.num-envs 4096 --agent.max-iterations 3000 --agent.logger tensorboard
#
# --smoke      Check the setup only: build the task and run two training steps
#              (works on CPU, so it also runs on a laptop).
# --hub-repo   Also push checkpoints and the exported policy to a private
#              Hugging Face model repo (needs HF_TOKEN or `hf auth login`).
# --no-export  Skip the ONNX export after training.
set -euo pipefail

UV_VERSION="0.11.30"   # same pin as the HF Jobs bootstrap
SMOKE=0; HUB_REPO=""; EXPORT=1
while [ $# -gt 0 ]; do
  case "$1" in
    --smoke) SMOKE=1; shift ;;
    --hub-repo) HUB_REPO="$2"; shift 2 ;;
    --no-export) EXPORT=0; shift ;;
    --) shift; break ;;
    *) break ;;
  esac
done
TRAIN_ARGS=("$@")

cd "$(dirname "$0")/.."
echo "[train_gpu] repository: $(pwd) at $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"

if ! command -v uv >/dev/null 2>&1; then
  echo "[train_gpu] installing uv ${UV_VERSION}"
  curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" | sh >/dev/null
  export PATH="$HOME/.local/bin:$PATH"
fi
# Copy instead of hardlinking: safe when the uv cache and the repo are on
# different filesystems (network volumes on rented machines).
export UV_LINK_MODE=copy

echo "[train_gpu] uv sync"
uv sync --frozen --no-progress

if [ "$SMOKE" = "1" ]; then
  echo "[train_gpu] smoke test: build the task and run two training steps"
  uv run python tools/verify_r20_training.py
  echo "[train_gpu] smoke test passed"
  exit 0
fi

if [ ${#TRAIN_ARGS[@]} -eq 0 ]; then
  echo "error: no training arguments. Example:" >&2
  echo "  scripts/train_gpu.sh -- Mjlab-Velocity-Flat-IndieDuck-R25 --env.scene.num-envs 4096 --agent.max-iterations 3000 --agent.logger tensorboard" >&2
  exit 2
fi

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader | sed 's/^/[train_gpu] GPU: /'
else
  echo "[train_gpu] warning: nvidia-smi not found; training will be very slow without a CUDA GPU" >&2
fi
uv run python -c "import torch; print('[train_gpu] torch', torch.__version__, '| CUDA available:', torch.cuda.is_available())"

UPLOADER_PID=""
if [ -n "$HUB_REPO" ]; then
  export CKPT_REPO="$HUB_REPO"
  mkdir -p logs/rsl_rl
  echo "[train_gpu] pushing checkpoints to https://huggingface.co/${HUB_REPO}"
  nohup uv run python scripts/hf/uploader.py > logs/uploader.log 2>&1 &
  UPLOADER_PID=$!
fi

echo "[train_gpu] uv run train ${TRAIN_ARGS[*]}"
set +e
uv run train "${TRAIN_ARGS[@]}"
TRAIN_RC=$?
set -e
echo "[train_gpu] training exited with code ${TRAIN_RC}"

if [ -n "$UPLOADER_PID" ]; then
  kill "$UPLOADER_PID" 2>/dev/null || true
  CKPT_ONE_SHOT=1 uv run python scripts/hf/uploader.py || echo "[train_gpu] final checkpoint upload failed" >&2
fi

if [ "$TRAIN_RC" -eq 0 ] && [ "$EXPORT" = "1" ]; then
  CKPT=$(ls -t logs/rsl_rl/*/*/model_*.pt logs/rsl_rl/*/model_*.pt 2>/dev/null | head -1 || true)
  if [ -n "$CKPT" ]; then
    mkdir -p exported
    echo "[train_gpu] exporting ONNX from ${CKPT}"
    if uv run python scripts/export.py "${TRAIN_ARGS[0]}" --checkpoint-file "$CKPT" --num-envs 1 --onnx-file exported/policy.onnx; then
      echo "[train_gpu] policy: $(pwd)/exported/policy.onnx"
      if [ -n "$HUB_REPO" ]; then
        uv run python -c "import os;from huggingface_hub import HfApi;HfApi().upload_file(path_or_fileobj='exported/policy.onnx',path_in_repo='exported/policy.onnx',repo_id=os.environ['CKPT_REPO'],repo_type='model');print('[train_gpu] uploaded exported/policy.onnx')"
      fi
    else
      echo "[train_gpu] ONNX export failed (training itself succeeded)" >&2
    fi
  else
    echo "[train_gpu] no checkpoint found under logs/rsl_rl" >&2
  fi
fi
exit "$TRAIN_RC"
