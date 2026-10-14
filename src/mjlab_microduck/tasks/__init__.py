"""Register the current IndieDuck task; historical upstream tasks remain source references."""
from mjlab_microduck.train_hook import maybe_submit_to_hf_jobs
maybe_submit_to_hf_jobs()
from mjlab.tasks.registry import register_mjlab_task
from mjlab.tasks.velocity.rl import VelocityOnPolicyRunner
from .indieduck_velocity_env_cfg import make_indieduck_velocity_env_cfg, IndieDuckRlCfg
register_mjlab_task(
    task_id="Mjlab-Velocity-Flat-IndieDuck-R25",
    env_cfg=make_indieduck_velocity_env_cfg(),
    play_env_cfg=make_indieduck_velocity_env_cfg(play=True),
    rl_cfg=IndieDuckRlCfg,
    runner_cls=VelocityOnPolicyRunner,
)
