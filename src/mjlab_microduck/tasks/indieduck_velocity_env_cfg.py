"""R25 adaptation of the attributed upstream velocity reward and observation recipe."""
import json
from pathlib import Path
import mujoco
from mjlab.actuator import XmlActuatorCfg
from mjlab.entity import EntityArticulationInfoCfg, EntityCfg
from mjlab.managers import SceneEntityCfg
from mjlab_microduck.actuator import FrictionDRBamActuatorCfg
from .microduck_velocity_env_cfg import make_microduck_velocity_env_cfg, MicroduckRlCfg

MODEL = Path(__file__).resolve().parents[1] / "robot/indieduck"
CONTRACT = json.loads((MODEL / "contract.json").read_text())
POLICY_JOINTS = tuple(CONTRACT["policy_action_joints"])
STAND = next(p for p in json.loads((MODEL / "poses.json").read_text())["poses"] if p["id"] == "stand")
IndieDuckRlCfg = MicroduckRlCfg

def get_r20_spec():
    spec = mujoco.MjSpec.from_file(str(MODEL / "robot.xml"))
    spec.add_sensor(name="root_angmom", type=mujoco.mjtSensor.mjSENS_SUBTREEANGMOM, objtype=mujoco.mjtObj.mjOBJ_BODY, objname="trunk_base")
    return spec

def make_indieduck_velocity_env_cfg(play=False):
    cfg = make_microduck_velocity_env_cfg(play=play)
    bam = FrictionDRBamActuatorCfg(
        motor_name="hd1910", model="m1", target_names_expr=POLICY_JOINTS,
        kp_fw=32., vin_range=(4.75, 5.25), vin_min=4.,
        vin_drop_resistance_range=(0., .069), delay_min_lag=6, delay_max_lag=6,
    )
    cfg.scene.entities["robot"] = EntityCfg(
        spec_fn=get_r20_spec,
        init_state=EntityCfg.InitialStateCfg(
            pos=tuple(STAND["base_position_m"]),
            joint_pos=STAND["joint_positions_rad"], joint_vel={".*": 0.},
        ),
        articulation=EntityArticulationInfoCfg(
            actuators=(bam, XmlActuatorCfg(target_names_expr=("mouth",))),
            soft_joint_pos_limit_factor=.9,
        ),
    )
    cfg.events["reset_base"].params["pose_range"]["z"] = (0., .005)
    cfg.rewards["body_pose_tracking"].params["nominal_height"] = STAND["base_position_m"][2]
    cfg.actions["joint_pos"].actuator_names = POLICY_JOINTS
    cfg.actions["joint_pos"].preserve_order = True
    for group in ("actor", "critic"):
        for term in ("joint_pos", "joint_vel"):
            cfg.observations[group].terms[term].params["asset_cfg"] = SceneEntityCfg(
                "robot", joint_names=POLICY_JOINTS, preserve_order=True,
            )
    cfg.observations["critic"].terms["base_ang_vel"].params["sensor_name"] = "robot/body_imu_gyro"
    # R25 legs and head have explicit link names, unlike the upstream mesh-named bodies.
    for event in cfg.events.values():
        asset = event.params.get("asset_cfg")
        if asset is not None and getattr(asset, "body_names", None) and any(
            name in str(asset.body_names) for name in ("bottom_head_shell", "yaw_roll_motion", "bearing_roll")
        ):
            asset.body_names = ("neck_pitch_link", "head_pitch_link", "head_yaw_link", "head_roll_link")
    cfg.rewards["pose"].params["asset_cfg"].joint_names = tuple(
        name for name in POLICY_JOINTS if name.startswith(("left_", "right_"))
    )
    return cfg
