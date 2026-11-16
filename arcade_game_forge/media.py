"""Images of the fixed WASM package, explicitly labeled as host replay artifacts."""
import importlib
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from .play import ready_package
from .sdk import load_sdk
from .traces import traces


def render_run(run,sdk_root,output):
    output=Path(output).resolve()
    if output.exists():raise ValueError('fresh media output required')
    spec,package=ready_package(run);load_sdk(sdk_root)
    decode=importlib.import_module('labos.package').decode
    Session=importlib.import_module('labos.sdk').Session
    render=importlib.import_module('labos.display').render
    manifest,blob=decode(package);screens={};movie=[]
    sequences=traces(spec,seed=200)
    for name in ('victory','deadline'):
        session=Session(blob,manifest);now=0
        try:
            for key,dt in sequences[name]:
                now+=dt
                if session.frame(key,now):break
                phase=session.debug('debug_value')>>16
                if phase not in (0,1,2,3):raise ValueError('unknown game phase')
                bitmap=render(SimpleNamespace(mode='running',commands=session.commands))
                screens.setdefault(str(phase),bitmap.copy())
                if name=='victory':movie.append(bitmap.copy())
        finally:session.close()
    if not all(str(phase) in screens for phase in (0,1,2,3)) or len(movie)<2:
        raise ValueError('gameplay capture incomplete')
    output.mkdir(parents=True)
    for phase,bitmap in screens.items():bitmap.save(output/f'phase-{phase}.png')
    movie[0].save(output/'replay.gif',save_all=True,append_images=movie[1:],duration=180,loop=0,disposal=2)
    result=dict(source='deterministic host WASM replay',device_capture=False,real_time_video=False,
                screens={phase:f'phase-{phase}.png' for phase in screens},replay_frames=len(movie),
                package_sha256=hashlib.sha256(package).hexdigest())
    (output/'media.json').write_text(json.dumps(result,indent=2)+'\n');return result
