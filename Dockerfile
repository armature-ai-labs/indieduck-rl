# Training image for lab machines and rented GPUs that run containers.
# Build:  docker build -t indieduck-rl .
# Run:    docker run --gpus all --rm -v "$PWD/logs:/work/logs" -v "$PWD/exported:/work/exported" indieduck-rl \
#           -- Mjlab-Velocity-Flat-IndieDuck-R25 --env.scene.num-envs 4096 --agent.max-iterations 3000 --agent.logger tensorboard
# Same base image as the Hugging Face Jobs path (src/mjlab_microduck/hf_jobs.py).
FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime
ENV DEBIAN_FRONTEND=noninteractive UV_LINK_MODE=copy PATH=/root/.local/bin:$PATH
RUN apt-get update -qq && apt-get install -qq -y --no-install-recommends git curl ca-certificates xz-utils >/dev/null \
 && rm -rf /var/lib/apt/lists/* && curl -LsSf https://astral.sh/uv/0.11.30/install.sh | sh >/dev/null
WORKDIR /work
COPY . /work
RUN uv sync --frozen --no-progress
ENTRYPOINT ["scripts/train_gpu.sh"]
