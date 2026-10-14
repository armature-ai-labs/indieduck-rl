"""Generate the R20/R25 SI model from eligible CAD meshes and the joint contract."""
from __future__ import annotations
import argparse, hashlib, json, math, shutil, struct
from pathlib import Path
import xml.etree.ElementTree as E
import numpy as np

MODEL = Path(__file__).resolve().parents[1] / 'src/mjlab_microduck/robot/indieduck'
def read(name): return json.loads((MODEL/name).read_text())
def write(name,obj): (MODEL/name).write_text(json.dumps(obj,indent=2)+'\n')
def nums(v): return ' '.join(f'{x:.10g}' for x in v)
def add(parent,tag,**kw): return E.SubElement(parent,tag,{k:str(v) for k,v in kw.items()})

def load_stl(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,80)[0]
    if len(raw)!=84+50*n: raise ValueError(f'Expected binary STL: {path}')
    rows=np.frombuffer(raw, dtype=np.dtype([('n','<f4',3),('v','<f4',(3,3)),('a','<u2')]),offset=84,count=n).copy()
    return rows

def save_stl(path, rows):
    path.write_bytes(b'IndieDuck SI body-local CAD mesh'.ljust(80,b' ')+struct.pack('<I',len(rows))+rows.tobytes())

def generate(manifest_path):
    c=read('contract.json');mapping=read('part-bodies.json');mapping['ref_ToFOptics']='head_roll_link'; manifest=json.loads(manifest_path.read_text())
    rev=manifest.get('revision')
    if rev not in ('R20','R25'): raise ValueError('generator supports R20 and R25 CAD manifests')
    if rev=='R25': mapping.update({p['name']:p['body'] for p in manifest['parts'] if p.get('body')})
    missing={p['name'] for p in manifest['parts']}-set(mapping)
    if missing: raise ValueError(f'Unmapped CAD components: {sorted(missing)}')
    skate_path=manifest_path.parent/'skate-manifest.json'
    skate_manifest=json.loads(skate_path.read_text()) if skate_path.exists() else {'parts':[]}
    for part in skate_manifest['parts']:
        part['include_when']='skates'
        side='left' if part['name'].endswith('_L') else 'right'
        wheel='front' if part['name'].startswith('Front') else 'rear'
        mapping[part['name']]=side+'_'+wheel+'_wheel_link' if any(t in part['name'] for t in ['Tire','Rim']) else side+'_ankle_link'
    manifest['parts']+=skate_manifest['parts']
    c['skates']['wheel_centres_mm']={side:{'front':[14.75,46*sign,-20],'rear':[-50.25,46*sign,-20]} for side,sign in [('left',1),('right',-1)]}
    c['skates']['wheel_width_m']=.0076
    c['skates']['cad_accessory_included']=bool(skate_manifest['parts'])
    if skate_manifest['parts']:c['skates']['manifest_sha256']=hashlib.sha256(skate_path.read_bytes()).hexdigest()
    for n in ['neck_pitch','head_yaw','head_roll']:
        j=next(j for j in c['joints'] if j['name']==n)
        mapping['ref_servo_'+n]=j['body'];mapping['ref_horn_'+n]=j['parent_body']
    write('part-bodies.json',mapping)
    origins={'trunk_base':np.array(c['root_origin_mm'])/1000}
    for j in c['joints']+c['passive_joints']:origins[j['body']]=np.array(j['origin_mm'])/1000
    for side in ['left','right']:
        for wheel in ['front','rear']:origins[side+'_'+wheel+'_wheel_link']=np.array(c['skates']['wheel_centres_mm'][side][wheel])/1000
    meshdir=MODEL/'meshes';meshdir.mkdir(exist_ok=True)
    parts=[];mass_by_body={b:[] for b in origins}
    for p in manifest['parts']:
        name=p['name'];src=manifest_path.parent/p['mesh'];body=mapping[name]
        rows=load_stl(src);v=rows['v'].reshape(-1,3).astype(float)/1000
        bounds=np.array([v.min(axis=0),v.max(axis=0)]);com=np.array(p.get('center_of_mass_mm',(bounds.mean(axis=0)*1000).tolist()))/1000
        local=rows.copy();local['v']=(rows['v']/1000-origins[body]).astype('f4');dst=meshdir/(name+'.stl');save_stl(dst,local)
        ref=p.get('reference',name.startswith('ref_'))
        material='TPU 95A fit study' if any(t in name for t in ['Sole','Lip','Edge']) else 'PLA fit study'
        mass=float(p.get('volume_mm3',0))*(1.20e-6 if 'TPU' in material else 1.24e-6)
        if ref:
            material='Reference module, estimated mass'
            if 'servo_' in name:mass=.021
            elif 'Battery' in name:mass=.095
            elif 'PCB' in name:mass=.012 if 'Radxa' in name else .009 if 'HAT' in name else .0015
            elif 'horn_' in name:mass=.001
            elif 'Tire' in name:mass=float(p['volume_mm3'])*1.20e-6
            elif 'Rim' in name:mass=float(p['volume_mm3'])*1.24e-6
            elif 'Axle' in name or 'LocatorPin' in name:mass=float(p['volume_mm3'])*7.85e-6
            else:mass=.0005
        if mass<=0:mass=.001
        color=p.get('color',[.85,.85,.83]);color=list(color[:3])+[1.]
        parts.append({'name':name,'label':p.get('label',name),'mesh':'meshes/'+name+'.stl','body':body,'color':color,'material':material,'mass_kg':mass,'mass_status':'estimated full-solid density: PLA 1.24, TPU 1.20 g/cm3; purchased modules nominal estimates; unmeasured','bounds_world_m':bounds.tolist(),'com_world_m':com.tolist(),'reference':ref,'include_when':p.get('include_when','always'),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
        mass_by_body[body].append((mass,com,bounds,p.get('include_when','always')))
    c['cad_revision']=manifest.get('revision','R20');c['cad_manifest_sha256']=hashlib.sha256(manifest_path.read_bytes()).hexdigest();c['visual_mesh_source']='Complete '+c['cad_revision']+' visible CAD assembly plus attributed provisional skate accessory; see asset notices';c['mouth_motor_limits_rad']=[0,math.pi/6]
    next(j for j in c['joints'] if j['name']=='mouth')['limits_rad']=c['mouth_motor_limits_rad']
    # Use explicit CAD sensor envelopes to place optical origin at outward lens/front plane.
    for name,part in [('head_camera','ref_CameraLens'),('tof','ref_ToFOptics'),('head_imu','ref_HeadIMU'),('body_imu','ref_HAT_IMU')]:
        ps=next((p for p in parts if p['name']==part),None)
        if ps:
            lo,hi=np.array(ps['bounds_world_m']);pt=(lo+hi)/2
            if name in ['head_camera','tof']:pt[0]=hi[0]+.0001
            c['sensors'][name]['origin_mm']=(pt*1000).tolist()
    c['sensors']['head_camera']['status']=c['cad_revision']+' camera envelope lens plane, physical mount and field of view unverified'
    c['actuators']={'xml': 'Estimated position PD, kp 4 Nm/rad, kv 0.08 Nms/rad, torque cap 0.85 Nm at nominal 5V. Not BAM.', 'selected_native_bam': {'model': 'hd1910/m1', 'implementation': 'src/mjlab_microduck/sim/bam_native.py', 'scope': 'CPU diagnostic on the canonical '+c['cad_revision']+' model; GPU task migration and IndieDuck measurement pending', 'decision': 'D8 in decisions-2026-10-06.md', 'servo_voltage_v': 5.0, 'command_delay_s': 0.029, 'source_command_delay_s': 0.03240342471539083, 'source_params_sha256': 'fda4366b2610bfb1911e67d8543ff157d86414c72dc4c2292683e995793f1c59', 'delay_status': 'D8 override selected; pinned-file delay tested separately, source JSON unchanged'}, 'retained_upstream_training_reference': 'Existing upstream task source selects HD-1910 m5 BAM, 4.75..5.25V and 4..7 physical-substep delays. This configuration is not migrated or selected for IndieDuck; D8 m1 remains selected.', 'servo_voltage_v': 5, 'kp_firmware_reference': 32, 'mass_and_friction_status': 'Body mass/contact estimates; BAM uses upstream m1 fitted friction. IndieDuck physical measurements pending'}
    write('contract.json',c);write('visual-parts.json',{'model_id':c['model_id'],'cad_revision':c['cad_revision'],'mesh_coordinates':'SI body-local, orientation equal CAD world at zero','parts':parts})
    coeff=[0,1,0,0,0]
    write('contract.json',c)
    def build(skates=False,scene=True):
        root=E.Element('mujoco',model=c['model_id']+('_skates' if skates else ''))
        add(root,'compiler',angle='radian',autolimits='true',meshdir='meshes',inertiafromgeom='false',fusestatic='false')
        add(root,'option',timestep='.005',gravity='0 0 -9.81',integrator='implicitfast',iterations='50')
        vis=add(root,'visual');add(vis,'global',offwidth='640',offheight='480');add(vis,'map',znear='.001',zfar='10');add(vis,'headlight',ambient='.4 .4 .4',diffuse='.7 .7 .7')
        defaults=add(root,'default');add(defaults,'joint',damping='.008',armature='.0002',frictionloss='.014');add(defaults,'geom',condim='3',friction='0.8 0.005 0.0001',solref='.01 1',solimp='.9 .95 .001')
        asset=add(root,'asset')
        for p in parts:
            if p['include_when']=='skates' and not skates:continue
            add(asset,'mesh',name=p['name'],file=p['name']+'.stl')
        world=add(root,'worldbody')
        if scene:
            add(world,'light',pos='1 -1 2',dir='-1 1 -2',directional='true')
            add(world,'geom',name='ground',type='plane',size='2 2 .02',rgba='.25 .28 .29 1',group='0',contype='1',conaffinity='2')
            ball=add(world,'body',name='test_ball',pos='.22 0 .021');add(ball,'freejoint',name='ball_freejoint');add(ball,'inertial',mass='.02',pos='0 0 0',diaginertia='0.0000032 0.0000032 0.0000032');add(ball,'geom',name='test_ball_geom',type='sphere',size='.02',rgba='.9 .35 .1 1',contype='1',conaffinity='3')
        bodies={'trunk_base':add(world,'body',name='trunk_base',pos=nums(origins['trunk_base']))};add(bodies['trunk_base'],'freejoint',name='trunk_base_freejoint')
        for j in c['joints']+c['passive_joints']:
            body=add(bodies[j['parent_body']],'body',name=j['body'],pos=nums(origins[j['body']]-origins[j['parent_body']]))
            add(body,'joint',name=j['name'],type='hinge',axis=nums(j['axis']),range=nums(j['limits_rad']));bodies[j['body']]=body
        if skates:
            for side in ['left','right']:
                for label in ['front','rear']:
                    name=side+'_'+label+'_wheel_link';wp=origins[name]
                    b=add(bodies[side+'_ankle_link'],'body',name=name,pos=nums(wp-origins[side+'_ankle_link']))
                    add(b,'joint',name='passive_'+side+'_'+label+'_wheel',type='hinge',axis='0 1 0',limited='false',damping='.00002',armature='0',frictionloss='0')
                    add(b,'geom',name=side+'_'+label+'_wheel',type='cylinder',size='.015 .0038',quat='.7071067812 .7071067812 0 0',rgba='.03 .035 .04 0' if skate_manifest['parts'] else '.03 .035 .04 1',group='3' if skate_manifest['parts'] else '0',contype='2',conaffinity='1',mass='0',friction='1 .002 .0001')
                    bodies[name]=b
        # Native inertias use one aggregate bounding-box estimate per articulated body. Not measured.
        for b,el in bodies.items():
            groups=[(m,pt,bb) for m,pt,bb,variant in mass_by_body[b] if skates or variant!='skates']
            if groups:
                mass=sum(m for m,_,_ in groups);com=sum(m*pt for m,pt,_ in groups)/mass
                lo=np.min([bb[0] for _,_,bb in groups],axis=0);hi=np.max([bb[1] for _,_,bb in groups],axis=0);d=np.maximum(hi-lo,.001)
            else:mass=.001;com=origins[b];d=np.array([.003]*3)
            inertia=mass/12*np.array([d[1]**2+d[2]**2,d[0]**2+d[2]**2,d[0]**2+d[1]**2])
            add(el,'inertial',mass=mass,pos=nums(com-origins[b]),diaginertia=nums(inertia))
        for p in parts:
            if p['include_when']=='skates' and not skates:continue
            add(bodies[p['body']],'geom',name=p['name']+'_visual',type='mesh',mesh=p['name'],rgba=nums(p['color']),group='2',contype='0',conaffinity='0',mass='0')
        # Separate broad conservative proxies. They interact with ground/props, not each other;
        # precise self clearance is measured in CAD, not inferred from these hollow-part boxes.
        collision_parts=(['Trunk','TorsoFront','TorsoRear','HelmetRoof','HelmetLower','HeadBase','AngularJaw','Thigh_L','Thigh_R','ShankStructure_L','ShankStructure_R','Yaw_L','Yaw_R','FacetedSole_L','FacetedSole_R']
            if c.get('cad_revision')=='R25' else
            ['Trunk','BodyFront','BodyBack','SoftHeadShell','O2_HeadBase','O2_Jaw','Thigh_L','Thigh_R','Shank_L','Shank_R','Yaw_L','Yaw_R','RoundedSole_L','RoundedSole_R'])
        for name in collision_parts:
            p=next((p for p in parts if p['name']==name),None)
            if not p:continue
            lo,hi=np.array(p['bounds_world_m']);centre=(lo+hi)/2;size=(hi-lo)/2
            if name=='Trunk':size=np.minimum(size,[.037,.023,.035])
            if name=='SoftHeadShell':size*=.9
            if 'Sole' in name:collision_name=('left' if name.endswith('_L') else 'right')+'_foot_collision'
            else:collision_name=name+'_collision'
            add(bodies[p['body']],'geom',name=collision_name,type='box',pos=nums(centre-origins[p['body']]),size=nums(np.maximum(size,.0005)),rgba='.9 .2 .2 0',group='3',contype='2',conaffinity='1',mass='0')
        for side in ['left','right']:
            ankle=origins[side+'_ankle_link'];add(bodies[side+'_ankle_link'],'site',name=side+'_foot',pos=nums(np.array([-5,64 if side=='left' else -64,0])/1000-ankle),size='.001')
        sensors=add(root,'sensor')
        for name,s in c['sensors'].items():
            pt=np.array(s['origin_mm'])/1000-origins[s['body']]
            add(bodies[s['body']],'site',name=name,pos=nums(pt),size='.001',rgba='.1 .7 .7 1')
            if 'imu' in name:
                add(sensors,'gyro',name=name+'_gyro',site=name);add(sensors,'accelerometer',name=name+'_accel',site=name);add(sensors,'framequat',name=name+'_quat',objtype='site',objname=name)
            if name=='head_camera':add(bodies[s['body']],'camera',name='head_camera',pos=nums(pt),xyaxes='0 -1 0 0 0 1',fovy=s['fovy_deg'])
            if name=='tof':
                centers=np.linspace(-math.radians(45)/2,math.radians(45)/2,9);centers=(centers[:-1]+centers[1:])/2
                for row,elev in enumerate(-centers):
                    for col,az in enumerate(-centers):
                        ray=[math.cos(elev)*math.cos(az),math.cos(elev)*math.sin(az),math.sin(elev)];n=f'tof_{row}_{col}'
                        add(bodies[s['body']],'site',name=n,pos=nums(pt),zaxis=nums(ray),size='.0003',group='4');add(sensors,'rangefinder',name=n,site=n,cutoff='4')
        act=add(root,'actuator')
        for j in c['joints']:add(act,'position',name=j['name'],joint=j['name'],kp='4',kv='.08',ctrlrange=nums(j['limits_rad']),forcerange='-.85 .85')
        return root
    for skates in [False,True]:
        for scene in [False,True]:
            name=('scene' if scene else 'robot')+('_skates' if skates else '')+'.xml';root=build(skates,scene);E.indent(root);E.ElementTree(root).write(MODEL/name,encoding='unicode',xml_declaration=True)
    # Runtime parser ignores visual/dynamic tags; no upstream geometry or hidden solids retained.
    tree=E.parse(MODEL/'robot.xml');root=tree.getroot()
    for child in list(root):
        if child.tag!='worldbody':root.remove(child)
    for parent in root.iter():
        for child in list(parent):
            if child.tag not in ['body','joint','site','worldbody']:parent.remove(child)
    for site in root.findall('.//site'):
        if site.attrib['name'].startswith('tof_'):continue
    E.ElementTree(root).write(MODEL/'kinematics.xml',encoding='unicode',xml_declaration=True)
    files=[p.relative_to(MODEL).as_posix() for p in MODEL.rglob('*') if p.is_file() and p.suffix in ['.xml','.stl','.json'] and p.name!='files.json'];write('files.json',{'files':sorted(files),'default_scene':'scene.xml','skates_scene':'scene_skates.xml'})
    print(f'Generated {len(parts)} CAD meshes in {MODEL}')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);args=p.parse_args();generate(args.manifest)
