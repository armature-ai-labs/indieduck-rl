"""Copy generated canonical model files into the local browser asset directory."""
import json
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=root/'src/mjlab_microduck/robot/indieduck'
target=root/'simulator/public/model'
if target.exists(): shutil.rmtree(target)
files=sorted(p.relative_to(source).as_posix() for p in source.rglob('*') if p.suffix in ['.json','.xml','.stl'] and p.name!='files.json')
(source/'files.json').write_text(json.dumps({'files':files,'default_scene':'scene.xml','skates_scene':'scene_skates.xml'},indent=2)+'\n')
for name in files+['files.json']:
    dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/name,dest)
print(f'Synced {len(files)} canonical assets to {target}')
