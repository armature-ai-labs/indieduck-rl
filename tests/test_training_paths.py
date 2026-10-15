"""The three training paths (Hugging Face Jobs, rented GPU, lab machine) stay wired up."""
import ast, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_hf_jobs_bootstrap_scripts_exist_and_parse():
    src = (ROOT / "src/mjlab_microduck/hf_jobs.py").read_text()
    for rel in set(re.findall(r"scripts/[\w/]+\.py", src)):
        path = ROOT / rel
        assert path.is_file(), f"HF Jobs bootstrap calls missing {rel}"
        ast.parse(path.read_text())


def test_gpu_host_script_is_valid_bash_and_executable():
    script = ROOT / "scripts/train_gpu.sh"
    assert script.stat().st_mode & 0o111, "train_gpu.sh must be executable"
    subprocess.run(["bash", "-n", str(script)], check=True)
    text = script.read_text()
    assert "scripts/hf/uploader.py" in text and "scripts/export.py" in text


def test_dockerfile_uses_the_host_script_and_hf_image():
    docker = (ROOT / "Dockerfile").read_text()
    hf = (ROOT / "src/mjlab_microduck/hf_jobs.py").read_text()
    image = re.search(r'DEFAULT_IMAGE = "([^"]+)"', hf).group(1)
    assert f"FROM {image}" in docker
    assert 'ENTRYPOINT ["scripts/train_gpu.sh"]' in docker


def test_training_guide_covers_all_three_paths():
    guide = (ROOT / "docs/TRAINING.md").read_text()
    for heading in ("Hugging Face Jobs", "Rented GPU", "Lab machine"):
        assert heading in guide
    assert "Mjlab-Velocity-Flat-IndieDuck-R25" in guide
